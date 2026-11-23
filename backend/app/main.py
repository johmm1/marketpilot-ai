from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .market_data import get_market_snapshot,get_candles
from .schemas import SignalRequest,PaperOrderRequest
from .technical_analysis import analyze_candles
from .paper_ledger import initialize,create_order,get_portfolio
from .auth import initialize_auth,register,login,logout,current_user
app=FastAPI(title="MARKETPILOT AI API",version="0.5.0",description="Market data and authenticated paper trading; live execution disabled.")
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin],allow_credentials=True,allow_methods=["GET","POST"],allow_headers=["Content-Type"])
@app.on_event("startup")
def startup():
    initialize(); initialize_auth()
@app.get("/health")
def health(): return {"status":"ok","environment":settings.app_env,"live_trading_enabled":False,"paper_ledger":"sqlite","authentication":"cookie_session"}
@app.post("/api/auth/register")
def auth_register(payload:dict,response:Response):
    return register(str(payload.get("email","")),str(payload.get("password","")),response,settings.app_env=="production")
@app.post("/api/auth/login")
def auth_login(payload:dict,response:Response):
    return login(str(payload.get("email","")),str(payload.get("password","")),response,settings.app_env=="production")
@app.post("/api/auth/logout")
def auth_logout(request:Request,response:Response): return logout(request,response)
@app.get("/api/auth/me")
def auth_me(user=Depends(current_user)): return user
@app.get("/api/markets")
async def markets(asset_class:str|None=None):
    if asset_class and asset_class not in {"forex","crypto","stocks","indices"}: raise HTTPException(400,"Unsupported asset class")
    return await get_market_snapshot(asset_class)
@app.get("/api/candles")
async def candles(symbol:str=Query(min_length=2,max_length=30),timeframe:str=Query(default="1h"),limit:int=Query(default=250,ge=30,le=500)):
    try: return await get_candles(symbol,timeframe,limit)
    except ValueError as exc: raise HTTPException(400,str(exc)) from exc
@app.get("/api/technical-analysis")
async def technical_analysis(symbol:str=Query(min_length=2,max_length=30),timeframe:str=Query(default="1h")):
    try: return analyze_candles(await get_candles(symbol,timeframe,250))
    except ValueError as exc: raise HTTPException(400,str(exc)) from exc
@app.post("/api/signals")
async def signal(req:SignalRequest):
    try:
        analysis=analyze_candles(await get_candles(req.symbol,req.timeframe,250)); action=analysis["signal"]["action"]
        return {"symbol":req.symbol,"action":action,"confidence":min(75,40+abs(analysis["signal"]["score"])*8),
            "rationale":"Candle-based rule score. Review indicators, spread, news and risk before acting.",
            "entry_reference":analysis["last_price"] if action!="HOLD" else None,
            "model":"technical-rules-v1 (not trained ML)","source":analysis["source"],
            "disclaimer":"Educational signal only; not personalized financial advice."}
    except ValueError as exc: raise HTTPException(400,str(exc)) from exc
@app.post("/api/paper-orders")
def paper_order(req:PaperOrderRequest,user=Depends(current_user)):
    try: return create_order(user["id"],req.symbol,req.side,req.quantity,req.reference_price)
    except ValueError as exc: raise HTTPException(400,str(exc)) from exc
@app.get("/api/portfolio")
def portfolio(user=Depends(current_user)): return get_portfolio(user["id"])
@app.post("/api/analyst")
def analyst(payload:dict,user=Depends(current_user)):
    question=str(payload.get("question","")).strip()
    if not question or len(question)>4000: raise HTTPException(400,"Question must be 1–4000 characters")
    if not settings.openai_api_key: return {"mode":"offline","answer":"OpenAI is not configured. Add OPENAI_API_KEY to backend environment. Check source labels on quotes and charts."}
    try:
        from openai import OpenAI
        response=OpenAI(api_key=settings.openai_api_key).responses.create(model=settings.openai_model,
            instructions="You are a cautious market education assistant. Never guarantee returns or claim live data unless supplied. Do not give personalized financial advice.",input=question)
        return {"mode":"openai","answer":response.output_text}
    except Exception as exc: raise HTTPException(502,f"Analyst unavailable: {type(exc).__name__}")
