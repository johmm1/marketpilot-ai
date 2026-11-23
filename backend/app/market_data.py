"""Market quote and candle adapters with explicit live/demo provenance."""
import math
from datetime import datetime, timezone
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
INTERVALS = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}
BINANCE_INTERVALS = {"5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}

def list_quotes(asset_class=None):
    return [q for q in DEMO_QUOTES if asset_class is None or q["asset_class"] == asset_class]

def find_quote(symbol: str):
    return next((q for q in DEMO_QUOTES if q["symbol"].upper() == symbol.upper()), None)

async def get_market_snapshot(asset_class=None):
    quotes = [dict(q) for q in DEMO_QUOTES]
    live_symbols = []
    provider_status = {"crypto": "unavailable", "other_markets": "demo_only"}
    if asset_class in (None, "crypto"):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://api.binance.com/api/v3/ticker/24hr", params={"symbols": '["BTCUSDT","ETHUSDT"]'})
                response.raise_for_status()
                by_symbol = {item.get("symbol"): item for item in response.json()}
            for quote in quotes:
                item = by_symbol.get(BINANCE_SYMBOLS.get(quote["symbol"]))
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
    return {"mode": mode, "provider_status": provider_status, "live_symbols": live_symbols, "quotes": filtered}

def _demo_candles(symbol: str, timeframe: str, limit: int):
    quote = find_quote(symbol)
    base = float(quote["price"] if quote else 100.0)
    step = INTERVALS[timeframe]
    now = int(datetime.now(timezone.utc).timestamp())
    end = now - (now % step)
    candles = []
    previous = base * 0.985
    for index in range(limit):
        wave = math.sin(index * 0.43) * 0.003 + math.sin(index * 0.13) * 0.002
        close = base * (0.985 + (0.015 * index / max(limit - 1, 1)) + wave)
        open_price = previous
        high = max(open_price, close) * (1 + 0.0015 + abs(math.sin(index)) * 0.001)
        low = min(open_price, close) * (1 - 0.0015 - abs(math.cos(index)) * 0.001)
        candles.append({
            "time": end - (limit - index - 1) * step,
            "open": round(open_price, 6), "high": round(high, 6),
            "low": round(low, 6), "close": round(close, 6),
            "volume": round(100 + abs(math.sin(index * 0.7)) * 900, 3),
        })
        previous = close
    return candles

async def get_candles(symbol: str, timeframe: str = "1h", limit: int = 150):
    if timeframe not in INTERVALS:
        raise ValueError("Unsupported timeframe")
    if not find_quote(symbol):
        raise ValueError("Unsupported symbol")
    provider_symbol = BINANCE_SYMBOLS.get(symbol.upper())
    if provider_symbol:
        try:
            async with httpx.AsyncClient(timeout=7.0) as client:
                if limit <= 1000:
                    response = await client.get(
                        "https://api.binance.com/api/v3/klines",
                        params={"symbol": provider_symbol, "interval": BINANCE_INTERVALS[timeframe], "limit": limit},
                    )
                    response.raise_for_status()
                    rows = response.json()
                else:
                    # Binance caps each klines request at 1,000; fetch the
                    # latest 1,000 and then the preceding candles in a second call.
                    latest_response = await client.get(
                        "https://api.binance.com/api/v3/klines",
                        params={"symbol": provider_symbol, "interval": BINANCE_INTERVALS[timeframe], "limit": 1000},
                    )
                    latest_response.raise_for_status()
                    latest_rows = latest_response.json()
                    if latest_rows:
                        earlier_response = await client.get(
                            "https://api.binance.com/api/v3/klines",
                            params={
                                "symbol": provider_symbol,
                                "interval": BINANCE_INTERVALS[timeframe],
                                "limit": limit - 1000,
                                "endTime": int(latest_rows[0][0]) - 1,
                            },
                        )
                        earlier_response.raise_for_status()
                        rows = earlier_response.json() + latest_rows
                    else:
                        rows = []
            candles = [{
                "time": int(row[0]) // 1000,
                "open": float(row[1]), "high": float(row[2]),
                "low": float(row[3]), "close": float(row[4]),
                "volume": float(row[5]),
            } for row in rows]
            if candles:
                return {"symbol": symbol, "timeframe": timeframe, "source": "BINANCE", "mode": "LIVE", "candles": candles}
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
            pass
    return {"symbol": symbol, "timeframe": timeframe, "source": "DEMO", "mode": "DEMO", "candles": _demo_candles(symbol, timeframe, limit)}
