# MARKETPILOT AI

Responsive Next.js PWA + FastAPI market-intelligence and paper-trading workspace, with a Windows desktop shell.

## Dashboard
- Multi-asset watchlist: forex, crypto, stocks and indices.
- Interactive candlestick and volume charts with 5m / 15m / 1h / 4h / 1d intervals.
- Technical-analysis panel: RSI(14), MACD, EMA(20/50/200), Bollinger Bands, 20-candle support/resistance and volume comparison.
- Transparent rule-based signal summary derived from candle indicators.
- Paper portfolio, position summary and recent order journal.
- Optional OpenAI market-education analyst. API key is backend-only.
- Responsive browser UI and installable PWA support.

## Cross-platform clients

### Web
Deploy the Next.js frontend and FastAPI backend separately. Set `NEXT_PUBLIC_API_URL` to the HTTPS backend origin at frontend build time.

### Android
The responsive PWA can be installed from a supported mobile browser using its browser menu's **Install app** or **Add to Home screen** action. The service worker caches the offline information page and static Next.js assets. Market data, analyst requests and portfolio services still require an internet connection. This PWA route does not yet produce a Play Store APK.

### Windows desktop
The Electron shell displays the deployed web application in a hardened desktop window. It does not automate or inject into broker dashboards.

Requirements: Windows 10/11 x64 and Node.js 20 or later.

PowerShell:
```powershell
cd desktop
npm install
$env:MARKETPILOT_WEB_URL="https://YOUR-DEPLOYED-FRONTEND"
npm run package:win
```

The installer is generated under `desktop/release/`. For local development, start the frontend on `http://localhost:3000`, then run `npm start` from `desktop`. Production requires HTTPS. The desktop client needs an internet connection and a deployed frontend/backend; it is not a self-contained offline trading engine.

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

## Accounts and session security

- The dashboard requires an account. Register with an email address and a password of at least 12 characters.
- Passwords are stored as PBKDF2-HMAC-SHA256 hashes with per-password random salts; raw passwords are not stored.
- Successful sign-in creates a random, opaque server-side session. The browser receives it in an HttpOnly cookie; the database stores only its SHA-256 hash. Sessions expire after 7 days.
- Paper orders, the paper portfolio and the AI analyst endpoint require an authenticated session. Each paper order is associated with its account; one account cannot read another account's paper journal through these endpoints.
- Set `APP_ENV=production`, use HTTPS, and set `FRONTEND_ORIGIN` to the exact deployed frontend origin. Cross-origin frontend requests must include credentials.
- This is an initial account system, not yet a complete identity platform: email verification, password reset, MFA, account deletion, admin roles, login throttling, security-event audit logs and formal CSRF protections remain to be implemented before public production use. Do not reuse a sensitive password.

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
``
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
- The Android client is currently an installable PWA, not a signed APK. The Windows Electron installer has not been built or tested by this repository change.
- Before production trading: implement authentication, authorization, rate limiting, persistent audit logs, a full accounting ledger, realistic fees/slippage, broker paper trading, model evaluation/walk-forward validation, risk limits, kill switch, idempotency, reconciliation, monitoring and explicit user authorization.
- No profitability is guaranteed. Trading can result in loss.
