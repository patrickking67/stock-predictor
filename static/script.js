function getStockData() {
    const symbol = document.getElementById('stockSymbol').value;
    fetch(`/predict_stock?symbol=${encodeURIComponent(symbol)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching data:', data.error);
                return;
            }
            document.getElementById('companyName').textContent = data.company_name || data.symbol;
            document.getElementById('realTimePrice').textContent = data.latest.price.toFixed(2);
            createStockGraph(data.history);

            // Display Predictions
            document.getElementById('prediction1d').textContent = `$${data.predictions[0].toFixed(2)}`;
            document.getElementById('prediction5d').textContent = `$${data.predictions[4].toFixed(2)}`;
        })
        .catch(error => console.error('Error:', error));
}

function selectDemoStock(stockSymbol) {
    document.getElementById('stockSymbol').value = stockSymbol;
}

$("#stockSymbol").autocomplete({
    source: function(request, response) {
        $.ajax({
            url: "/symbol_search",
            dataType: "json",
            data: { q: request.term },
            success: function(data) {
                response((data.matches || []).map(function(match) {
                    return match.symbol + " - " + match.name;
                }));
            },
            error: function(xhr, status, error) {
                console.error("AJAX Error:", status, error);
                response([]);
            }
        });
    },
    minLength: 2,
    select: function(event, ui) {
        $("#stockSymbol").val(ui.item.value.split(" - ")[0]);
    }
});



function createStockGraph(history) {
    var stockChart = document.getElementById('stockChart').getContext('2d');
    var labels = history.map(function(point) { return point.date; });
    var dataPoints = history.map(function(point) { return point.close; });

    new Chart(stockChart, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Stock Price',
                data: dataPoints,
                backgroundColor: 'rgba(0, 123, 255, 0.5)',
                borderColor: 'rgba(0, 123, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

