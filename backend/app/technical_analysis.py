"""Deterministic technical indicators calculated from the supplied OHLCV candles."""
from math import sqrt

def _ema(values, period):
    if len(values) < period:
        return None
    alpha = 2 / (period + 1)
    current = sum(values[:period]) / period
    for value in values[period:]:
        current = value * alpha + current * (1 - alpha)
    return current

def _rsi(values, period=14):
    if len(values) <= period:
        return None
    changes = [values[i] - values[i-1] for i in range(1, len(values))]
    gains = [max(x, 0) for x in changes]
    losses = [max(-x, 0) for x in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))

def analyze_candles(payload):
    candles = payload.get("candles", [])
    closes = [float(c["close"]) for c in candles]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    volumes = [float(c.get("volume", 0)) for c in candles]
    if len(closes) < 30:
        raise ValueError("At least 30 candles are required for technical analysis")
    last = closes[-1]
    ema20, ema50, ema200 = (_ema(closes, n) for n in (20, 50, 200))
    rsi = _rsi(closes)
    fast = _ema(closes, 12)
    slow = _ema(closes, 26)
    macd_line = fast - slow if fast is not None and slow is not None else None
    macd_series = []
    if len(closes) >= 34:
        for end in range(26, len(closes) + 1):
            f, s = _ema(closes[:end], 12), _ema(closes[:end], 26)
            if f is not None and s is not None:
                macd_series.append(f - s)
    signal_line = _ema(macd_series, 9) if macd_series else None
    histogram = macd_line - signal_line if macd_line is not None and signal_line is not None else None
    window = closes[-20:]
    middle = sum(window) / len(window)
    variance = sum((x-middle)**2 for x in window) / len(window)
    deviation = sqrt(variance)
    avg_volume = sum(volumes[-20:]) / min(20, len(volumes))
    recent_volume = volumes[-1]
    support = min(lows[-20:])
    resistance = max(highs[-20:])
    score = 0
    if rsi is not None:
        score += 1 if rsi > 55 else -1 if rsi < 45 else 0
    if ema20 is not None:
        score += 1 if last > ema20 else -1
    if ema50 is not None:
        score += 1 if last > ema50 else -1
    if histogram is not None:
        score += 1 if histogram > 0 else -1 if histogram < 0 else 0
    action = "BUY" if score >= 3 else "SELL" if score <= -3 else "HOLD"
    return {
        "symbol": payload["symbol"], "timeframe": payload["timeframe"],
        "source": payload["source"], "mode": payload["mode"],
        "candle_count": len(candles), "last_price": last,
        "indicators": {
            "rsi_14": round(rsi, 4) if rsi is not None else None,
            "macd": round(macd_line, 8) if macd_line is not None else None,
            "macd_signal": round(signal_line, 8) if signal_line is not None else None,
            "macd_histogram": round(histogram, 8) if histogram is not None else None,
            "ema_20": round(ema20, 8) if ema20 is not None else None,
            "ema_50": round(ema50, 8) if ema50 is not None else None,
            "ema_200": round(ema200, 8) if ema200 is not None else None,
            "bollinger_upper": round(middle + 2*deviation, 8),
            "bollinger_middle": round(middle, 8),
            "bollinger_lower": round(middle - 2*deviation, 8),
            "support_20": support, "resistance_20": resistance,
            "volume": recent_volume, "average_volume_20": round(avg_volume, 4),
        },
        "signal": {"action": action, "score": score, "components": 4},
        "limitations": ["Rule-based technical indicators, not trained ML.",
          "Technical signals are not forecasts or personalized financial advice.",
          "Source provenance follows the candle feed; DEMO candles produce DEMO analysis."]
    }
