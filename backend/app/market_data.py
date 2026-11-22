"""Market quote adapters.

Crypto quotes use Binance's public 24-hour ticker endpoint when reachable.
All other instruments remain explicitly labelled DEMO until licensed providers
are configured. A failed live request never gets presented as live data.
"""
import httpx

DEMO_QUOTES = [
 {"symbol":"EUR/USD","name":"Euro / US Dollar","asset_class":"forex","price":1.0842,"change_pct":0.18,"source":"DEMO","delayed":True},
 {"symbol":"GBP/USD","name":"British Pound / US Dollar","asset_class":"forex","price":1.2715,"change_pct":-0.12,"source":"DEMO","delayed":True},
 {"symbol":"XAU/USD","name":"Gold / US Dollar","asset_class":"forex","price":2378.4,"change_pct":0.42,"source":"DEMO","delayed":True},
 {"symbol":"BTC/USD","name":"Bitcoin","asset_class":"crypto","price":67420.0,"change_pct":1.86,"source":"DEMO","delayed":True},
 {"symbol":"ETH/USD","name":"Ethereum","asset_class":"crypto","price":3520.0,"change_pct":0.94,"source":"DEMO","delayed":True},
 {"symbol":"AAPL","name":"Apple Inc.","asset_class":"stocks","price":212.3,"change_pct":0.31,"source":"DEMO","delayed":True},
 {"symbol":"NVDA","name":"NVIDIA","asset_class":"stocks","price":124.8,"change_pct":2.14,"source":"DEMO","delayed":True},
 {"symbol":"SPX","name":"S&P 500","asset_class":"indices","price":5420.1,"change_pct":0.27,"source":"DEMO","delayed":True},
 {"symbol":"NAS100","name":"NASDAQ 100","asset_class":"indices","price":19040.2,"change_pct":0.55,"source":"DEMO","delayed":True},
]

BINANCE_SYMBOLS = {"BTC/USD": "BTCUSDT", "ETH/USD": "ETHUSDT"}

async def get_market_snapshot(asset_class=None):
    """Return quotes plus honest per-provider status."""
    quotes = [dict(q) for q in DEMO_QUOTES]
    live_symbols = []
    provider_status = {"crypto": "unavailable", "other_markets": "demo_only"}
    if asset_class in (None, "crypto"):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.binance.com/api/v3/ticker/24hr",
                    params={"symbols": '["BTCUSDT","ETHUSDT"]'},
                )
                response.raise_for_status()
                payload = response.json()
            by_symbol = {item.get("symbol"): item for item in payload}
            for quote in quotes:
                provider_symbol = BINANCE_SYMBOLS.get(quote["symbol"])
                item = by_symbol.get(provider_symbol)
                if quote["asset_class"] == "crypto" and item:
                    quote["price"] = float(item["lastPrice"])
                    quote["change_pct"] = float(item["priceChangePercent"])
                    quote["source"] = "BINANCE"
                    quote["delayed"] = False
                    live_symbols.append(quote["symbol"])
            provider_status["crypto"] = "live" if live_symbols else "unavailable"
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            provider_status["crypto"] = "fallback_demo"
    filtered = [q for q in quotes if asset_class is None or q["asset_class"] == asset_class]
    if asset_class == "crypto":
        mode = "LIVE" if live_symbols else "DEMO_FALLBACK"
    elif asset_class:
        mode = "DEMO"
    else:
        mode = "PARTIAL_LIVE" if live_symbols else "DEMO_FALLBACK"
    return {
        "mode": mode,
        "provider_status": provider_status,
        "live_symbols": live_symbols,
        "quotes": filtered,
    }
