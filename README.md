
This is a project I had to do for the Harvard Computer Science course on edX.  It is a web app made with Python, Flask, Javascript, SQL, HTML, and CSS.  I just used sqlite3 db to persist the data.

To start out you can register for an account which will then log the user in and start them off with a $10K cash balance.  I used regex to enforce the 8 character minimum and alphanumeric characters.  

![register](/static/images/readme/register.png)  

Validation includes checking for empty data and ensuring passwords match or else you get a meme error message.  

![apology](/static/images/readme/apology.png)  
  
Once successfully registered redirects to root and flashes success message.  

![registered](/static/images/readme/registered.png)  
If you logout or close your browser you will need to login again.  Login compares hashed password from request to hashed password in database to login successfully. 
![login](/static/images/readme/login.png)

The quote tab allows user to input stock symbol to findout the latest price.  Uses an api call to IEX.
![quote](/static/images/readme/quote.png)  

A successful quote is flashed on the dashboard.  

![quoted](/static/images/readme/quoted.png)

Buying stock requires stock symbol and number of shares.  Combination of frontend validation from browser and backend validation ensures proper input.  I used Javascript to add a feature that when a user enters a symbol the script uses a blur event listener on the text field that will fetch a quote via json and then inform the user the maximum number of shares possible to purchase that stock based on the latest price of the stock and their current cash balance.  

![buy_first](/static/images/readme/buy_first.png)
![buy_two](/static/images/readme/buy_two.png)
![bought](/static/images/readme/bought.png)  

Selling is similar to buying except using the change event listener on the select input field to find out via sql query how many shares of that symbol the user owns in order to display the maximum number of shares allowed to sell.  The options in the select input field are populated via an sql query which finds the symbols they currently own.  


![sell_dropdown](/static/images/readme/sell_dropdown.png)
![sell_two](/static/images/readme/sell_two.png)
![sold](/static/images/readme/sold.png)  

The history tab will display all the users transactions ordered by company name first, then by transaction date ascending.
![history](/static/images/readme/history.png)





