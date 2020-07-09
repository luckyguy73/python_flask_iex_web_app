const buy_symbol_input = document.querySelector('#buy_symbol');
const buy_div = document.querySelector('#buy_shares-div');

buy_symbol_input.addEventListener('blur', () => {
    const symbol = buy_symbol_input.value;
    fetch('/buy_symbol', {
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
            buy_div.innerHTML = `<small class="text-muted">You can buy up to ${data['max']} shares of ${data['name']}</small>`;
            buy_symbol_input.value = data['symbol'];
        })
        .catch(error => {
            console.log(error);
            buy_div.innerHTML = `<small>Enter a valid stock symbol</small>`;
            buy_symbol_input.value = '';
        });
});
