import main
from tests.conftest import FakeResponse, price_frame

CLOSES = [100.0 + i for i in range(30)]


def test_index_renders_with_disclaimer(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Educational project, not financial advice." in body
    assert "Predictions are not reliable." in body
    assert "alphavantage.co" not in body


def test_about_explains_the_model_and_limits(client):
    response = client.get("/about")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "LinearRegression" in body
    assert "No accuracy has been measured." in body
    assert "not financial advice" in body


def test_static_script_never_calls_alpha_vantage(client):
    script = client.get("/static/script.js").get_data(as_text=True)
    assert "alphavantage" not in script.lower()
    assert "apikey" not in script.lower()


def test_predict_requires_a_symbol(client):
    response = client.get("/predict_stock")
    assert response.status_code == 400
    assert "Enter a stock symbol" in response.get_json()["error"]


def test_predict_rejects_bad_symbol_before_any_fetch(client, yahoo):
    calls = yahoo(price_frame(CLOSES))
    response = client.get("/predict_stock", query_string={"symbol": "<script>"})
    assert response.status_code == 400
    assert calls == []


def test_predict_without_key_uses_yahoo_only(client, yahoo):
    yahoo(price_frame(CLOSES))
    response = client.get("/predict_stock", query_string={"symbol": "aapl"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["symbol"] == "AAPL"
    assert data["company_name"] is None
    assert data["latest"]["price"] == 129.0
    assert data["latest"]["source"] == "Yahoo Finance close"
    assert data["predictions"] == [130.0, 131.0, 132.0, 133.0, 134.0]
    assert len(data["history"]) == len(data["trend"]) == 30
    assert data["model"]["points"] == 30
    assert any("ALPHA_VANTAGE_API_KEY" in notice for notice in data["notices"])
    assert "not financial advice" in data["disclaimer"]


def test_predict_unknown_symbol_is_404(client, yahoo):
    yahoo(price_frame([]))
    response = client.get("/predict_stock", query_string={"symbol": "ZZZZQ"})
    assert response.status_code == 404
    assert "No price history" in response.get_json()["error"]


def test_predict_short_history_is_404(client, yahoo):
    yahoo(price_frame([1.0, 2.0, 3.0]))
    response = client.get("/predict_stock", query_string={"symbol": "NEWCO"})
    assert response.status_code == 404


def test_predict_yahoo_failure_is_502(client, yahoo):
    yahoo(ConnectionError("offline"))
    response = client.get("/predict_stock", query_string={"symbol": "AAPL"})
    assert response.status_code == 502
    assert "Yahoo Finance" in response.get_json()["error"]


def test_predict_unexpected_error_is_500(client, monkeypatch):
    def boom(symbol):
        raise TypeError("bug")

    monkeypatch.setattr(main, "fetch_price_history", boom)
    response = client.get("/predict_stock", query_string={"symbol": "AAPL"})
    assert response.status_code == 500
    assert response.get_json()["error"] == "Something went wrong on the server."


def test_predict_with_key_adds_name_and_quote(client, yahoo, alpha_vantage):
    yahoo(price_frame(CLOSES))
    sent = alpha_vantage(
        {
            "SYMBOL_SEARCH": {
                "bestMatches": [
                    {"1. symbol": "AAPL.TRT", "2. name": "Apple CDR"},
                    {"1. symbol": "AAPL", "2. name": "Apple Inc"},
                ]
            },
            "GLOBAL_QUOTE": {
                "Global Quote": {"05. price": "131.2500", "07. latest trading day": "2026-02-12"}
            },
        },
        key="server-side-key",
    )
    response = client.get("/predict_stock", query_string={"symbol": "AAPL"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["company_name"] == "Apple Inc"
    assert data["latest"] == {"price": 131.25, "as_of": "2026-02-12", "source": "Alpha Vantage quote"}
    assert data["notices"] == []
    assert all(call["params"]["apikey"] == "server-side-key" for call in sent)
    assert all(call["timeout"] for call in sent)
    assert "server-side-key" not in response.get_data(as_text=True)


def test_predict_survives_alpha_vantage_rate_limit(client, yahoo, alpha_vantage):
    yahoo(price_frame(CLOSES))
    alpha_vantage({"SYMBOL_SEARCH": {"Note": "rate limited"}, "GLOBAL_QUOTE": {"Note": "rate limited"}})
    response = client.get("/predict_stock", query_string={"symbol": "AAPL"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["latest"]["source"] == "Yahoo Finance close"
    assert any("rate limit" in notice for notice in data["notices"])


def test_predict_survives_alpha_vantage_outage(client, yahoo, alpha_vantage):
    yahoo(price_frame(CLOSES))
    alpha_vantage(
        {
            "SYMBOL_SEARCH": main.requests.ConnectionError("down"),
            "GLOBAL_QUOTE": main.requests.ConnectionError("down"),
        }
    )
    response = client.get("/predict_stock", query_string={"symbol": "AAPL"})
    assert response.status_code == 200
    assert response.get_json()["predictions"]


def test_search_without_key_is_503(client):
    response = client.get("/symbol_search", query_string={"q": "apple"})
    assert response.status_code == 503
    assert response.get_json()["matches"] == []


def test_search_rejects_bad_query(client):
    for q in ["", "x" * 41, "<script>"]:
        assert client.get("/symbol_search", query_string={"q": q}).status_code == 400


def test_search_proxies_matches(client, alpha_vantage):
    sent = alpha_vantage(
        {"SYMBOL_SEARCH": {"bestMatches": [{"1. symbol": "MSFT", "2. name": "Microsoft Corporation"}]}},
        key="server-side-key",
    )
    response = client.get("/symbol_search", query_string={"q": "micro"})
    assert response.status_code == 200
    assert response.get_json() == {"matches": [{"symbol": "MSFT", "name": "Microsoft Corporation"}]}
    assert sent[0]["params"]["keywords"] == "micro"
    assert "server-side-key" not in response.get_data(as_text=True)


def test_search_upstream_errors_are_502(client, alpha_vantage):
    alpha_vantage({"SYMBOL_SEARCH": FakeResponse({}, status=500)})
    assert client.get("/symbol_search", query_string={"q": "apple"}).status_code == 502
    alpha_vantage({"SYMBOL_SEARCH": FakeResponse(ValueError("not json"))})
    assert client.get("/symbol_search", query_string={"q": "apple"}).status_code == 502
    alpha_vantage({"SYMBOL_SEARCH": {"Error Message": "bad"}})
    assert client.get("/symbol_search", query_string={"q": "apple"}).status_code == 502
