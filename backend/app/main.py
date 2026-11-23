from uuid import uuid4
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .market_data import get_market_snapshot, get_candles
from .schemas import SignalRequest, PaperOrderRequest, PaperOrder
from .signals import create_baseline_signal
from .technical_analysis import analyze_candles
from .paper_ledger import initialize, create_order, get_portfolio

app = FastAPI(title="MARKETPILOT AI API", version="0.4.0", description="Market data, technical analysis and paper trading; live execution disabled.")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    initialize()

@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env, "live_trading_enabled": False, "paper_ledger": "sqlite"}

@app.get("/api/markets")
async def markets(asset_class: str | None = None):
    if asset_class and asset_class not in {"forex", "crypto", "stocks", "indices"}:
        raise HTTPException(400, "Unsupported asset class")
    return await get_market_snapshot(asset_class)

@app.get("/api/candles")
async def candles(symbol: str = Query(min_length=2, max_length=30), timeframe: str = Query(default="1h"),
                  limit: int = Query(default=250, ge=30, le=500)):
    try:
        return await get_candles(symbol, timeframe, limit)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.get("/api/technical-analysis")
async def technical_analysis(symbol: str = Query(min_length=2, max_length=30),
                             timeframe: str = Query(default="1h")):
    try:
        payload = await get_candles(symbol, timeframe, 250)
        return analyze_candles(payload)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.post("/api/signals")
async def signal(req: SignalRequest):
    try:
        payload = await get_candles(req.symbol, req.timeframe, 250)
        analysis = analyze_candles(payload)
        action = analysis["signal"]["action"]
        return {"symbol": req.symbol, "action": action,
                "confidence": min(75, 40 + abs(analysis["signal"]["score"]) * 8),
                "rationale": "Candle-based rule score. Review the full indicator panel, spread, news and risk before acting.",
                "entry_reference": analysis["last_price"] if action != "HOLD" else None,
                "model": "technical-rules-v1 (not trained ML)", "source": analysis["source"],
                "disclaimer": "Educational signal only; not personalized financial advice."}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.post("/api/paper-orders")
def paper_order(req: PaperOrderRequest):
    try:
        return create_order(req.symbol, req.side, req.quantity, req.reference_price)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.get("/api/portfolio")
def portfolio():
    return get_portfolio()

@app.post("/api/analyst")
def analyst(payload: dict):
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(400, "Question is required")
    if not settings.openai_api_key:
        return {"mode": "offline", "answer": "OpenAI is not configured. Add OPENAI_API_KEY to backend environment. Check the source label on market quotes and charts."}
    try:
        from openai import OpenAI
        response = OpenAI(api_key=settings.openai_api_key).responses.create(
            model=settings.openai_model,
            instructions="You are a cautious market education assistant. Never guarantee returns or claim live data unless supplied. Do not give personalized financial advice.",
            input=question,
        )
        return {"mode": "openai", "answer": response.output_text}
    except Exception as exc:
        raise HTTPException(502, f"Analyst unavailable: {type(exc).__name__}")
