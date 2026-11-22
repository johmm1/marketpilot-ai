from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .market_data import get_market_snapshot
from .schemas import SignalRequest, PaperOrderRequest, PaperOrder
from .signals import create_baseline_signal

app = FastAPI(title="MARKETPILOT AI API", version="0.2.0", description="Market data adapters and demo intelligence; live execution disabled.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env, "live_trading_enabled": False}

@app.get("/api/markets")
async def markets(asset_class: str | None = None):
    if asset_class and asset_class not in {"forex", "crypto", "stocks", "indices"}:
        raise HTTPException(400, "Unsupported asset class")
    return await get_market_snapshot(asset_class)

@app.post("/api/signals")
def signal(req: SignalRequest):
    return create_baseline_signal(req)

@app.post("/api/paper-orders", response_model=PaperOrder)
def paper_order(req: PaperOrderRequest):
    return PaperOrder(id=str(uuid4()), symbol=req.symbol, side=req.side, quantity=req.quantity, reference_price=req.reference_price)

@app.post("/api/analyst")
def analyst(payload: dict):
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(400, "Question is required")
    if not settings.openai_api_key:
        return {"mode": "offline", "answer": "OpenAI is not configured. Add OPENAI_API_KEY to backend environment. Market coverage may include demo quotes; check each quote's source."}
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
