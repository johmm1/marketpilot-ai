# MARKETPILOT AI

Responsive Next.js PWA + FastAPI market-intelligence prototype.

## Current market-data and chart features
- Interactive candlestick chart with volume histogram, crosshair, and 5m / 15m / 1h / 4h / 1d timeframe selection.
- `GET /api/candles?symbol=BTC%2FUSD&timeframe=1h&limit=150` returns OHLCV candle data.
- BTC/USD and ETH/USD candles and quote snapshots use Binance public market endpoints when reachable.
- Other instruments remain illustrative demo data until suitable licensed providers are configured.
- Charts refresh every 30 seconds and show their source (`BINANCE` or `DEMO`).

## Safety defaults
- Demo candles are synthetic illustrative data, never historical exchange records.
- Signal logic is a transparent demo heuristic, not trained ML.
- Paper orders are simulated in-memory; no broker is connected.
- Live execution is not implemented or enabled.
- OpenAI is optional and configured on the backend only. Never expose API keys in frontend variables.

## Run backend
```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Run frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Open http://localhost:3000 and API docs at http://localhost:8000/docs.

## Before production
Connect licensed feeds for each asset class; persist portfolios and audit events; train and walk-forward validate ML models with realistic transaction costs; implement broker paper trading and strict risk controls. Live execution requires separate authorization, account limits, a kill switch, idempotency, reconciliation and monitoring. No profitability is guaranteed.
