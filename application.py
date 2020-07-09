import json
import os
import re
from tempfile import mkdtemp

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db", connect_args={'check_same_thread': False})

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # add group by symbol having sum(shares) > 0 order by name
    stocks = db.execute("SELECT *, sum(shares) as total_shares FROM user_transactions WHERE user_id = ? "
                        "GROUP BY symbol HAVING sum(shares) > 0 ORDER BY company_name", session['user_id'])
    cash = session['cash']
    prices, un = {}, session['username']
    for stock in stocks:
        prices[stock['symbol']] = lookup(stock['symbol'])['price']
    total = round(sum(prices[stock['symbol']] * stock['total_shares'] for stock in stocks), 2) + cash
    return render_template('index.html', stocks=stocks, username=un, cash=cash, total=total, prices=prices, usd=usd)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # assign variables needed for transaction
        cash, name, price, shares, symbol = getFields()

        # check for valid symbol
        if not symbol:
            return apology('please enter a valid stock symbol', 422)

        # check number of shares is positive
        if not shares or shares < 1:
            return apology("please enter the number of shares", 422)

        # check there is enough cash for purchase
        total = price * shares
        if cash < total:
            return apology("not enough cash for this purchase", 403)

        # record transaction in db
        row_id = db.execute("INSERT INTO user_transactions (user_id, type, company_name, symbol, price, shares,"
                            "transaction_date) VALUES (?, 'bought', ?, ?, ?, ?, datetime('now'))", session['user_id'],
                            name, symbol, price, shares)

        # check transaction was successful
        sqlProblem(row_id)

        # adjust users cash balance
        row_id = db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - total, session['user_id'])

        # check transaction was successful
        sqlProblem(row_id)
        session['cash'] = cash - total

        # flash success message
        flash(f'{shares} shares of {name} ({symbol}) purchased for {usd(total)}')

        # Redirect user to home page
        return redirect("/")

    return render_template('buy.html')


def getFields():
    symbol = request.form.get('symbol')

    try:
        shares = int(request.form.get('shares'))
    except ValueError:
        shares = 0

    quote = lookup(symbol)

    if not quote:
        return 0, 0, 0, 0, 0

    symbol = quote['symbol']
    name = quote['name']
    price = round(quote['price'], 2)
    cash = round(session['cash'], 2)
    return cash, name, price, shares, symbol


@app.route("/buy_symbol", methods=["POST"])
@login_required
def buy_symbol():
    symbol = request.json['symbol']
    quote = lookup(symbol)
    if not quote:
        return apology('please enter a valid stock symbol', 422)

    quote['max'] = session['cash'] // quote['price']
    return json.dumps(quote)


@app.route("/sell_symbol", methods=["POST"])
@login_required
def sell_symbol():
    symbol = request.json['symbol']
    row = db.execute("SELECT sum(shares) as shares FROM user_transactions WHERE symbol = ? "
                     "and user_id = ?", symbol, session['user_id'])
    data = {'shares': row[0]['shares']}
    if not data['shares']:
        data['shares'] = 0

    return json.dumps(data)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    stocks = db.execute("SELECT * FROM user_transactions WHERE user_id = ? "
                        "ORDER BY company_name, transaction_date", session['user_id'])
    return render_template('history.html', stocks=stocks, username=session['username'], usd=usd)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        session["cash"] = rows[0]["cash"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)

        if not quote:
            return apology('please enter a valid stock symbol', 422)

        flash(f"A share of {quote['name']} ({quote['symbol']}) costs {usd(quote['price'])}")
        return redirect("/")

    return render_template('quote.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        un = request.form.get("username")
        pw = request.form.get("password")
        cf = request.form.get("confirmation")

        # check password is 8 or more alphanumeric characters
        pattern = r'^[a-zA-Z0-9]{8,}$'
        validPassword = re.match(pattern, pw)

        # Ensure username was submitted
        if not un:
            return apology("must provide username", 403)

        # Ensure password was submitted and is 8 or more alphanumeric characters
        if not validPassword:
            return apology("must provide password with 8 or more alphanumeric characters", 403)

        # Ensure confirmation password was submitted
        if not cf:
            return apology("must provide confirmation password", 403)

        # Ensure password and confirmation password match
        if cf != pw:
            return apology("password and confirmation password must match", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Check to make sure username doesn't already exist
        if len(rows) > 0:
            return apology("username already taken", 403)

        # Insert user into db with username and hashed password
        pw_hash = generate_password_hash(pw, method='pbkdf2:sha256', salt_length=8)
        row_id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=un, hash=pw_hash)

        # check if insert was successful
        sqlProblem(row_id)

        # Remember which user has logged in
        session["user_id"] = row_id
        session["username"] = un
        session["cash"] = 10000

        # Redirect user to home page
        flash('You have been registered!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # assign variables for transaction
        cash, name, price, shares, symbol = getFields()

        # check valid symbol
        if not symbol:
            return apology('please enter a valid stock symbol', 422)

        # check number of shares is positive
        if not shares or shares < 1:
            return apology("please enter the number of shares", 422)

        total = price * shares
        row = db.execute("SELECT sum(shares) as total_shares FROM user_transactions WHERE symbol = ? "
                         "and user_id = ?", symbol, session['user_id'])
        total_shares = row[0]['total_shares']
        if shares > total_shares:
            return apology(f"there are only {total_shares} {symbol} shares available to sell", 403)

        # process transaction in db
        row_id = db.execute("INSERT INTO user_transactions (user_id, type, company_name, symbol, price, shares,"
                            "transaction_date) VALUES (?, 'sold', ?, ?, ?, ?, datetime('now'))", session['user_id'],
                            name, symbol, price, -shares)

        # make sure sql went through
        sqlProblem(row_id)

        # update cash
        row_id = db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + total, session['user_id'])

        # make sure sql went through
        sqlProblem(row_id)
        session['cash'] = cash + total

        # Flash success message and redirect user to home page
        flash(f"{shares} shares of {name} ({symbol}) sold for {usd(total)}")
        return redirect('/')

    stocks = db.execute("SELECT *, sum(shares) as total_shares FROM user_transactions WHERE user_id = ? "
                        "GROUP BY symbol HAVING sum(shares) > 0 ORDER BY company_name", session['user_id'])
    return render_template('sell.html', stocks=stocks)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


def sqlProblem(row_id):
    if not row_id:
        return apology("something went wrong", 500)
