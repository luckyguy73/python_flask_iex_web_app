const sell_symbol_input = document.querySelector('#sell_symbol');
const sell_div = document.querySelector('#sell_shares-div');

sell_symbol_input.addEventListener('change', () => {
    const symbol = sell_symbol_input.value;
    fetch('/sell_symbol', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symbol: symbol
        })
    })
        .then(r => r.json())
        .then(data => {
            console.log(data);
            sell_div.innerHTML = `<small class="text-muted">You can sell up to ${data['shares']} shares of ${symbol}</small>`;
        })
        .catch(error => {
            console.log(error);
        });
});
