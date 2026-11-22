from .market_data import find_quote
from .schemas import SignalRequest, Signal
# Transparent sample heuristic; this is NOT a trained ML model.
def create_baseline_signal(req: SignalRequest) -> Signal:
 quote = find_quote(req.symbol)
 if not quote:
  return Signal(symbol=req.symbol, action="HOLD", confidence=0, rationale="Instrument not found in demo feed.", model="baseline-demo-v1")
 move = quote["change_pct"]
 action = "BUY" if move > 0.65 else "SELL" if move < -0.65 else "HOLD"
 confidence = min(65, int(42 + abs(move) * 8))
 rationale = f"Demo heuristic: sample move is {move:+.2f}%. Verify trend, volume, spread, news and risk/reward; one price change is insufficient evidence."
 return Signal(symbol=req.symbol, action=action, confidence=confidence, rationale=rationale, entry_reference=quote["price"] if action != "HOLD" else None, model="baseline-demo-v1 (not trained ML)")
