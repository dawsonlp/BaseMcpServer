import datetime

import tool_config


def test_get_stock_quote_normalizes_symbol_and_formats_payload(monkeypatch):
    monkeypatch.setattr(
        tool_config,
        "_fetch_alpha_vantage_quote",
        lambda symbol: {
            "quote": {
                "02. open": "12.8400",
                "03. high": "12.8797",
                "04. low": "12.5750",
                "05. price": "12.6300",
                "06. volume": "23896024",
                "07. latest trading day": "2026-04-22",
                "08. previous close": "12.7800",
                "09. change": "-0.1500",
                "10. change percent": "-1.1737%",
            }
        },
    )
    monkeypatch.setattr(tool_config.config, "get", lambda *args, **kwargs: "configured-key")

    result = tool_config.get_stock_quote(" f ")

    assert result["symbol"] == "F"
    assert result["price"] == "12.6300"
    assert result["previous_close"] == "12.7800"
    assert result["api_key_status"] == "configured"
    assert result["note"] == "Live market data"


def test_get_stock_market_overview_uses_market_status_and_handles_errors(monkeypatch):
    def fake_fetch(symbol):
        if symbol == "SPY":
            return {
                "quote": {
                    "05. price": "711.2100",
                    "07. latest trading day": "2026-04-22",
                    "09. change": "7.1300",
                    "10. change percent": "1.0127%",
                }
            }
        return {"error": "Unexpected response format", "response_keys": ["Information"]}

    monkeypatch.setattr(tool_config, "_fetch_alpha_vantage_quote", fake_fetch)
    monkeypatch.setattr(
        tool_config,
        "_get_us_market_status",
        lambda now=None: {
            "status": "Closed",
            "checked_at": "2026-04-22 16:01:00 EDT",
            "timezone": "America/New_York",
        },
    )
    monkeypatch.setattr(tool_config.config, "get", lambda *args, **kwargs: "configured-key")

    result = tool_config.get_stock_market_overview()

    assert result["market_status"] == "Closed"
    assert result["market_timezone"] == "America/New_York"
    assert result["indices"]["SPY"]["price"] == "711.2100"
    assert result["indices"]["DIA"]["error"] == "Unexpected response format"
    assert result["indices"]["DIA"]["response_keys"] == ["Information"]


def test_get_us_market_status_uses_eastern_trading_hours():
    closed = tool_config._get_us_market_status(
        datetime.datetime(2026, 4, 22, 13, 0, tzinfo=datetime.timezone.utc)
    )
    open_result = tool_config._get_us_market_status(
        datetime.datetime(2026, 4, 22, 15, 0, tzinfo=datetime.timezone.utc)
    )

    assert closed["status"] == "Closed"
    assert open_result["status"] == "Open"
