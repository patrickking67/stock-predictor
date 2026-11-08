import os

from flask import Flask, render_template, request, jsonify
import requests
import yfinance as yf
from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)

ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")

def fetch_real_time_stock_price(symbol):
    symbol = symbol.split('-')[0].strip()
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()
    if "Time Series (5min)" not in data:
        return None, {"error": "Data not found", "details": data}
    latest_data = data['Time Series (5min)']
    latest_time = list(latest_data.keys())[0]
    latest_price = latest_data[latest_time]['1. open']
    return float(latest_price), None

def fetch_historical_stock_data(symbol, time_range='1d'):
    # Adjust the function parameter based on time range
    function = 'TIME_SERIES_DAILY'
    if time_range != '1d':
        function = 'TIME_SERIES_INTRADAY'

    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval=5min&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()
    key = 'Time Series (5min)' if time_range != '1d' else 'Time Series (Daily)'
    return data.get(key) if key in data else None

def fetch_company_name(symbol):
    try:
        symbol = symbol.split('-')[0].strip()
        url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={symbol}&apikey={ALPHA_VANTAGE_API_KEY}&datatype=json'
        response = requests.get(url)
        data = response.json()
        if "bestMatches" in data and len(data["bestMatches"]) > 0:
            return data["bestMatches"][0].get("2. name")
        return None
    except Exception as e:
        print(f"Error fetching company name: {e}")
        return None

def predict_future_prices(symbol, days=5):
    try:
        stock_data = yf.download(symbol, period="1y")['Close']
        stock_data = stock_data.reset_index()
        X = np.arange(len(stock_data)).reshape(-1, 1)
        y = stock_data['Close'].values
        model = LinearRegression().fit(X, y)
        future = np.array([len(stock_data) + i for i in range(days)]).reshape(-1, 1)
        predicted_prices = model.predict(future)
        return predicted_prices
    except Exception as e:
        print(f"Error in price prediction: {e}")
        return [None] * days

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/symbol_search')
def symbol_search():
    # Server-side proxy so the API key never reaches the browser.
    keywords = request.args.get('q', '').strip()
    if not keywords or not ALPHA_VANTAGE_API_KEY:
        return jsonify({"matches": []})
    response = requests.get(
        'https://www.alphavantage.co/query',
        params={'function': 'SYMBOL_SEARCH', 'keywords': keywords, 'apikey': ALPHA_VANTAGE_API_KEY},
        timeout=10,
    )
    data = response.json()
    matches = [
        {"symbol": m.get("1. symbol"), "name": m.get("2. name")}
        for m in data.get("bestMatches", [])
    ]
    return jsonify({"matches": matches})

@app.route('/predict_stock')
def predict_stock():
    symbol = request.args.get('symbol')
    real_time_price, error = fetch_real_time_stock_price(symbol)
    if error:
        return jsonify(error), 500
    if real_time_price is None:
        return jsonify({"error": "Unable to fetch real-time data for the symbol."})
    
    company_name = fetch_company_name(symbol)
    if company_name is None:
        return jsonify({"error": "Unable to fetch company name."})
    
    historical_data = fetch_historical_stock_data(symbol)
    predictions = predict_future_prices(symbol, days=5)

    return jsonify({
        "company_name": company_name,
        "stock_symbol": symbol,
        "stock_price": real_time_price,
        "historical_data": historical_data,
        "predictions": predictions.tolist() if predictions[0] is not None else None
    })

if __name__ == '__main__':
    app.run(debug=True)


