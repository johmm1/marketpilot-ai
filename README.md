# MARKETPILOT AI

Responsive Next.js PWA + FastAPI market-intelligence and paper-trading workspace.

## Dashboard
- Multi-asset watchlist: forex, crypto, stocks and indices.
- Interactive candlestick and volume charts with 5m / 15m / 1h / 4h / 1d intervals.
- Technical-analysis panel: RSI(14), MACD, EMA(20/50/200), Bollinger Bands, 20-candle support/resistance and volume comparison.
- Transparent rule-based signal summary derived from candle indicators.
- Paper portfolio, position summary and recent order journal.
- Optional OpenAI market-education analyst. API key is backend-only.
- Responsive browser UI and PWA manifest support.

## Market data provenance
- BTC/USD and ETH/USD quotes/candles use Binance public endpoints when reachable.
- Forex, stocks, indices and other unavailable instruments use illustrative demo data until suitable licensed providers are configured.
- Every quote, chart and technical-analysis response includes a source/mode label.
- Synthetic candles are not historical market records. Indicators calculated from them are also DEMO.
- Provider outages fall back to demo candles; the app labels this rather than implying a live feed.

## API
- `GET /health` — service status and live-execution lock.
- `GET /api/markets?asset_class=crypto` — quotes and feed status.
- `GET /api/candles?symbol=BTC%2FUSD&timeframe=1h&limit=250` — OHLCV candles.
- `GET /api/technical-analysis?symbol=BTC%2FUSD&timeframe=1h` — computed indicators and rule score.
- `POST /api/signals` — candle-based educational signal.
- `POST /api/paper-orders` — validated simulated paper order.
- `GET /api/portfolio` — recent paper orders and derived positions.
- `POST /api/analyst` — optional OpenAI educational analyst.

## Paper trading and storage
Paper orders are recorded in SQLite, not sent to a broker. The default database path is `backend/marketpilot.db`. Set `MARKETPILOT_DB_PATH` to an absolute path on a persistent mounted disk in production. Many hosting filesystems are ephemeral; without a persistent disk, database contents may be lost on redeploy/restart. The API caps each paper order at 100,000 quote-currency units and retains the latest 200 orders in the portfolio response. This is a prototype journal, not a complete accounting ledger.

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

## Deployment configuration
- Set `NEXT_PUBLIC_API_URL` to the deployed backend origin in the frontend environment.
- Set `FRONTEND_ORIGIN` to the deployed frontend origin in the backend environment.
- Set `MARKETPILOT_DB_PATH` to a persistent-disk path for a durable paper journal.
- Set `OPENAI_API_KEY` only in backend secrets; never use a `NEXT_PUBLIC_` prefix for secrets.
- Configure HTTPS and restrict CORS to the exact frontend origin.
- Confirm health, market, candle, technical-analysis, portfolio and paper-order endpoints after deployment.

## Important limitations and production gates
- Technical analysis is deterministic rule-based computation, not trained machine learning.
- Signals are educational, not personalized financial advice or return forecasts.
- Paper order positions are derived from a limited recent-order window; no realized P&L, fees, margin, FX conversion or broker reconciliation is implemented.
- No broker is connected. Live trading is not implemented and must remain disabled.
- Other asset classes require suitable licensed data providers and exchange/session handling.
- Before production trading: implement authentication, authorization, rate limiting, persistent audit logs, a full accounting ledger, realistic fees/slippage, broker paper trading, model evaluation/walk-forward validation, risk limits, kill switch, idempotency, reconciliation, monitoring and explicit user authorization.
- No profitability is guaranteed. Trading can result in loss.
