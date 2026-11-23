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

## Multi-broker integration foundation

The backend now has a provider registry and a read-only connectivity probe. The initial provider targets are:

- **Binance Spot** — official REST/WebSocket API family. The current probe checks public API reachability only; it does not authenticate to an account or place orders. It defaults to Spot Testnet. Set `BINANCE_API_ENV=production` only to probe the production public endpoint.
- **cTrader** — official cTrader Open API using OAuth 2.0 authorization and JSON/Protobuf messaging. Each user must authorize their own cTrader ID and choose a demo/live account.
- **MetaTrader 5** — official MetaTrader Python integration communicates with a locally installed Windows terminal. This requires a separate Windows bridge/agent; it is not a cloud REST API and cannot be safely treated as a browser plugin.

Endpoints:
- `GET /api/brokers/providers` — supported provider metadata, capabilities and setup requirements.
- `GET /api/brokers/probe/binance` — read-only public connectivity probe (testnet by default).
- `GET /api/brokers/probe/ctrader` and `GET /api/brokers/probe/metatrader5` — report setup requirements; they do not pretend a connection exists.

Broker connection workflows are now implemented as follows:
- **Credential vault:** per-user credentials and OAuth tokens are encrypted at rest using Fernet. Configure a persistent `BROKER_ENCRYPTION_KEY`; losing/changing it makes existing encrypted connections unreadable. Generate one with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
- **Binance Spot Testnet:** the dashboard can save a Testnet API key/secret and request signed account information. It does not expose order endpoints. Use read-only permissions and disable withdrawals.
- **cTrader:** OAuth authorization requests the `accounts` read-only scope. Configure `CTRADER_CLIENT_ID`, `CTRADER_CLIENT_SECRET`, and `CTRADER_REDIRECT_URI`; register that exact redirect URI in the cTrader developer portal. Authorization-code exchange and token refresh are implemented. The Spotware-maintained Python SDK worker performs the read-only account-list handshake and demo-account reconciliation; run it as a separate scheduled worker.
- **MetaTrader 5:** `bridge/mt5_agent.py` is a Windows companion that pairs using a one-time bearer token and uploads account/positions/pending-order snapshots. It refuses non-demo accounts by default and contains no order-submission calls. Install `bridge/requirements.txt`, configure `MARKETPILOT_API_BASE` and `MARKETPILOT_MT5_BRIDGE_TOKEN`, then run the agent from a Windows host with the official MT5 terminal installed and logged into a demo account.
- Disconnecting a saved connection removes its encrypted credential record. Generating a new MT5 bridge token invalidates the previous token.

Never paste API secrets into chat. Enter Binance credentials only into the HTTPS dashboard and create them in the broker's official portal. Keep withdrawals disabled. Broker demo-account tests and explicit user consent must pass before any live execution is considered.

## API
- `GET /health` — service status and live-execution lock.
- `GET /api/markets?asset_class=crypto` — quotes and feed status.
- `GET /api/candles?symbol=BTC%2FUSD&timeframe=1h&limit=250` — OHLCV candles.
- `GET /api/technical-analysis?symbol=BTC%2FUSD&timeframe=1h` — computed indicators and rule score.
- `POST /api/signals` — candle-based educational signal.
- `POST /api/paper-orders` — validated simulated paper order.
- `GET /api/portfolio` — recent paper orders and derived positions.
- `POST /api/analyst` — optional OpenAI educational analyst.
- `GET /api/brokers/connections` — signed-in user's saved broker connection metadata (never secrets).
- `POST /api/brokers/binance/connect` and `GET /api/brokers/binance/account` — save encrypted Binance Testnet credentials and read balances.
- `GET /api/brokers/ctrader/connect`, `/callback`, and `/status` — OAuth authorization, token exchange and refresh.
- `POST /api/brokers/mt5-bridge/token`, `POST /api/brokers/mt5-bridge/snapshot`, and `GET /api/brokers/mt5-bridge/snapshot` — pair and inspect the read-only Windows bridge.
- `DELETE /api/brokers/connections/{id}` — remove a saved connection.

## Accounts and session security

- The dashboard requires an account. Register with an email address and a password of at least 12 characters.
- Passwords are stored as PBKDF2-HMAC-SHA256 hashes with per-password random salts; raw passwords are not stored.
- Successful sign-in creates a random, opaque server-side session. The browser receives it in an HttpOnly cookie; the database stores only its SHA-256 hash. Sessions expire after 7 days.
- Paper orders, the paper portfolio and the AI analyst endpoint require an authenticated session. Each paper order is associated with its account; one account cannot read another account's paper journal through these endpoints.
- Set `APP_ENV=production`, use HTTPS, and set `FRONTEND_ORIGIN` to the exact deployed frontend origin. Cross-origin frontend requests must include credentials.
- This is an initial account system, not yet a complete identity platform: email verification, password reset, MFA, account deletion, admin roles, login throttling and security-event audit logs remain to be implemented before public production use. Strict Origin checks protect browser state-changing requests; the MT5 bridge uses a separate bearer token. Do not reuse a sensitive password.

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
- Set `OPENAI_API_KEY`, `BROKER_ENCRYPTION_KEY`, and cTrader OAuth credentials only in backend secrets; never use a `NEXT_PUBLIC_` prefix for secrets.
- Configure HTTPS and restrict CORS to the exact frontend origin.
- Confirm health, market, candle, technical-analysis, portfolio and paper-order endpoints after deployment.

## cTrader read-only account sync worker

After cTrader OAuth is configured and a user authorizes the app, run this worker periodically from the repository root. It uses Spotware's official Python SDK, discovers authorized accounts, and reconciles one DEMO account. It does not send trading requests.
```bash
pip install -r connectors/ctrader/requirements.txt
python connectors/ctrader/sync_accounts.py
```
The worker needs the same `MARKETPILOT_DB_PATH`, `BROKER_ENCRYPTION_KEY`, `CTRADER_CLIENT_ID`, and `CTRADER_CLIENT_SECRET` values as the backend. Run it as a separate process/scheduled worker; it is not started by the web API automatically.

## Windows MT5 read-only bridge setup

On the Windows computer that has the official MetaTrader 5 terminal installed:
```powershell
cd bridge
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
$env:MARKETPILOT_API_BASE="https://YOUR-BACKEND-URL"
$env:MARKETPILOT_MT5_BRIDGE_TOKEN="ONE-TIME-TOKEN-FROM-DASHBOARD"
py mt5_agent.py
```
Keep the terminal logged into a DEMO account. The bridge deliberately rejects real-account mode. Do not expose the bridge port to the public internet; it makes outbound HTTPS requests to the backend.

## Important limitations and production gates
- Technical analysis is deterministic rule-based computation, not trained machine learning.
- Signals are educational, not personalized financial advice or return forecasts.
- Paper order positions are derived from a limited recent-order window; no realized P&L, fees, margin, FX conversion or broker reconciliation is implemented.
- Broker account connections require the operator's own API credentials and provider approval; repository CI does not authenticate against external user accounts. Live trading is not implemented and must remain disabled.
- Other asset classes require suitable licensed data providers and exchange/session handling.
- The Android client is currently an installable PWA, not a signed APK. A Windows Electron installer was built in an earlier workflow, but it has not been re-tested against a live deployment after these broker changes.
- Before production trading: implement authentication, authorization, rate limiting, persistent audit logs, a full accounting ledger, realistic fees/slippage, broker paper trading, model evaluation/walk-forward validation, risk limits, kill switch, idempotency, reconciliation, monitoring and explicit user authorization.
- No profitability is guaranteed. Trading can result in loss.
