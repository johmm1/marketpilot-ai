# MARKETPILOT AI — Public Platform Architecture and Delivery Plan

Status: Architecture baseline for public multi-user product
Repository: johmm1/marketpilot-ai
Branch: main

## 1. Product decisions

- Audience: public users, from first-time learners to experienced traders.
- Markets: forex, crypto, equities, indices and commodities, only where reliable data, provider permissions, and supported execution routes exist.
- Learning: historical model training plus continuous ingestion/monitoring. Model updates are promoted only after independent validation.
- User modes: Learn, Analysis only, Assisted trading, Demo automation, and Live automation (feature-gated).
- AI-generated analysis is not a guarantee, personalized advice, or an order. The deterministic risk and execution services retain final control.
- Never use browser automation, screen scraping, stored passwords, or session-cookie replay to bypass a broker's documented integration. Screen sharing is user-initiated visual analysis only.

## 2. Existing application baseline

The repository currently contains:
- Next.js frontend and Electron desktop companion.
- FastAPI backend.
- Authenticated analyst, visual-analysis, signal, paper-order and portfolio endpoints.
- AI provider routing for Gemini, Groq and optional OpenAI.
- Broker registry and encrypted credential vault.
- Binance Spot Testnet account-read integration.
- cTrader OAuth currently requests account-read scope; it is not a live order adapter.
- MT5 Windows bridge currently accepts DEMO account snapshots and tightly limited DEMO orders only.
- Live order submission is deliberately disabled.

Do not represent the existing broker registry as completed integrations. Each provider must expose its actual status and supported capabilities.

## 3. Target logical architecture

### Client applications
- Responsive web dashboard: onboarding, learning, analysis, portfolio, connections, consent and audit history.
- Windows companion: MT5/MT4 terminal bridges and optional user-started screen analysis.
- Mobile web/PWA: monitoring, education, alerts and user-approved actions; avoid heavy local ML workloads.

### Backend domains
1. Identity and access: registration, MFA, sessions, roles, account recovery, consent and regional eligibility.
2. User suitability and safeguards: experience questionnaire, knowledge checks, risk profile, leverage warnings, limits and mode eligibility.
3. Market data gateway: normalized instruments, OHLCV, quotes, spreads, timestamps, source, latency and data entitlements.
4. Feature pipeline: causal/time-safe indicators and features computed from point-in-time data.
5. ML research and inference: model registry, training jobs, evaluation, champion/challenger promotion and inference API.
6. AI explanation service: converts structured model outputs and evidence into plain-language explanations; cannot alter model scores or send orders.
7. Strategy service: explicit, versioned strategy rules and signal generation.
8. Risk service: independent pre-trade checks, sizing, exposure, loss limits, margin checks and kill switches.
9. Broker adapters: isolated, provider-specific authentication, account discovery, order lifecycle, reconciliation and capability checks.
10. Execution service: idempotent order intents, approvals, submission, cancel/replace, fills and reconciliation.
11. Audit and notification service: immutable event history, user-visible explanations, alerts and incident records.
12. Operations: health checks, metrics, logs, tracing, rate limits, secrets, backups and disaster recovery.

Start as well-separated FastAPI modules and background workers; split into independent services only when scale, isolation or reliability justifies it. Do not introduce microservices prematurely.

## 4. Market data and instrument coverage

Use a canonical instrument model:
- asset class, provider, provider symbol, canonical symbol, venue, quote currency and contract type;
- tick size, lot/contract size, minimum quantity, quantity step and trading hours where supplied;
- bid/ask, last price, OHLCV, event time, receive time, source and quality flags.

Keep provider data provenance visible. Never label delayed, indicative, simulated or demo data as live executable prices. Build adapters independently for crypto exchanges, FX/CFD brokers, equity venues and commodity feeds. Check market-data redistribution rights, exchange licensing, user-region availability and broker permissions before public release.

Initial integration order:
1. Stabilize Binance Spot Testnet and its live-market-data distinction.
2. Complete MT5 demo bridge status, order lifecycle and reconciliation.
3. Complete cTrader demo account discovery and demo order lifecycle.
4. Add one additional officially documented provider only after the adapter contract and tests are in place.
5. Add live environments only per-provider, per-account and only after legal, security and operational gates.

A broker/platform that only provides chart alerts or read-only APIs must be labelled analysis-only or read-only; it must not appear as auto-trading capable.

## 5. Machine-learning research design

### Research targets
- Regime classification: trend, range, high/low volatility and uncertain conditions.
- Pattern features: momentum, mean reversion, volatility expansion, volume/liquidity context and cross-timeframe structure.
- Forecast targets: probability distributions or calibrated probabilities for defined horizons, not unqualified BUY/SELL labels.
- Strategy outcomes: net returns after realistic spread, fees, funding, slippage and execution constraints.

### Candidate model families
Begin with transparent baselines (rules, logistic regression and tree-based gradient boosting). Add sequence models only when they demonstrate incremental out-of-sample value and can be operated reliably. Use ensembles only when component diversity and calibration are demonstrated.

### Training and validation controls
- Store point-in-time raw data and version every dataset, feature definition, label, code revision and model artifact.
- Split chronologically. Do not randomly shuffle time-series observations.
- Use rolling or expanding walk-forward validation, with purge/embargo where label windows overlap.
- Prevent look-ahead, survivorship, symbol-selection and data-revision leakage.
- Include realistic fees, spread, slippage, funding, borrow costs and rejected/partial fills.
- Evaluate net returns, drawdown, tail loss, turnover, capacity, calibration, stability by regime and instrument, and performance versus simple baselines.
- Keep a final untouched holdout. Repeated tuning against it is prohibited.
- Run a champion/challenger process and shadow inference before promotion.
- A model failing data-quality, calibration, drift, risk or minimum-sample gates is rejected or rolled back.
- Log the exact model version and input data timestamp for every recommendation.

### Continuous learning
Continuously ingest and monitor new data, but do not let production predictions automatically retrain and deploy themselves. Schedule retraining or trigger a research job after drift/data thresholds. Candidate models remain offline until they pass the complete validation suite, shadow period and explicit promotion approval. Provide a rollback to the previous champion.

## 6. Recommendation contract

Every recommendation should return structured evidence:
- instrument, venue/provider, timeframe, data timestamp and whether data is live/delayed/demo;
- action: BUY / SELL / WAIT, or probability distribution;
- calibrated probability/confidence with its definition and validation period;
- entry zone or trigger condition, invalidation level, stop and target only when supported;
- estimated spread/fees/slippage, risk/reward and position-size assumptions;
- supporting and conflicting evidence, model/strategy versions and expiry;
- clear uncertainty and risk disclosures.

Never invent an entry, stop or target when data is insufficient. WAIT is a valid result. The language model explains the structured result; it does not manufacture a trade thesis or raise a confidence score.

## 7. Independent risk and execution controls

All execution modes use the same pre-trade risk service. Controls include:
- user-defined risk per trade and maximum aggregate exposure;
- max daily/weekly loss and drawdown lockout;
- instrument, leverage, notional and order-size limits;
- mandatory protective orders where the instrument/provider supports them;
- stale-price, spread, volatility, market-hours and margin checks;
- duplicate-order idempotency keys and client order IDs;
- order state machine: proposed, awaiting approval, accepted, submitted, partially filled, filled, cancelled, rejected or unknown;
- reconciliation against broker state after timeouts and reconnects;
- per-user, per-account, per-strategy and global kill switches.

A timeout after sending an order is an UNKNOWN state, not permission to blindly retry. Reconcile with the broker first. Never silently switch a user from demo to live.

### Automation unlock policy
Live auto-trading remains disabled by default. Unlock only when all gates are satisfied:
1. Legal/compliance review confirms the product, target market, marketing, recommendation and execution model may be offered as configured, and required licences/partners/approvals are in place.
2. User identity, region, age, eligibility, disclosures and consent checks are complete where legally required.
3. User completes beginner knowledge checks and suitability/appropriateness workflow appropriate to the product.
4. A supported broker account is explicitly authorised for the required trading scope and its live/demo environment is positively verified.
5. The user selects a strategy, instruments, risk limits and maximum loss; the platform displays a final confirmation.
6. Strategy/model has passed backtests, out-of-sample validation, forward demo testing and operational readiness review.
7. Monitoring, reconciliation, incident response and emergency stop are active.

A user may revoke automation at any time. The system must show active strategies, account, positions, open orders, limits and last execution status.

## 8. Beginner-first product experience

- Guided onboarding: what markets are, what can be lost, how brokers work, demo versus live, and how MARKETPILOT uses data.
- Learning path: market basics, candles, spread, order types, leverage/margin, stop-loss, take-profit, position sizing, drawdown and scams.
- Interactive practice with simulated orders and explanations.
- Recommendation cards with plain-language "why", "what could go wrong", "what would invalidate this", and "how much could be lost".
- Assisted mode with a confirmation screen showing exact order details before submission.
- No dark patterns, profit guarantees, fabricated win rates, or pressure to enable automation.
- Clear data-source, delay, model-version and service-status labels.

## 9. Security, privacy and governance

- Keep API keys and broker tokens server-side or in the local companion where the provider architecture requires it; encrypt at rest with managed key rotation.
- Request least-privilege broker scopes. Disable withdrawals/transfers wherever possible. Separate market-data, account-read and trade permissions.
- Never collect broker passwords or ask users to paste secrets into support chat.
- MFA, secure session handling, rate limiting, abuse detection, CSRF/origin protection and security event logging.
- Tenant isolation for every account, connection, order, feature record and model-specific user output.
- Data minimization, retention controls, deletion/export processes and explicit consent for screen/image uploads.
- Audit all recommendations, approvals, model versions, risk decisions, broker requests, fills, overrides and incidents.
- Perform threat modelling, dependency scanning, penetration testing and incident-response exercises before public live trading.

## 10. Kenya and cross-border launch gate

The business must obtain qualified Kenyan regulatory advice and engage the Capital Markets Authority as appropriate before offering public investment recommendations, algorithm-driven advisory, portfolio management, broker/intermediary services or live automated execution. Determine whether the proposed activities require a licence, a licensed partner, regulatory sandbox engagement or another approval. Assess virtual-asset rules separately for crypto products. Do not assume that a software disclaimer removes licensing obligations.

Also assess each target country, broker entity, asset class, market-data licence, marketing restriction, KYC/AML and consumer-protection obligation. Restrict regions/products until approved.

Reference starting points:
- CMA licensing checklists: https://www.cma.or.ke/licensing/
- CMA regulatory framework: https://www.cma.or.ke/regulatory-framework/
- Binance developer documentation: https://developers.binance.com/en/docs/introduction
- cTrader Open API: https://help.ctrader.com/open-api/
- MetaTrader 5 Python integration: https://www.mql5.com/en/docs/python_metatrader5

This document is an engineering plan, not legal advice or confirmation that any licence has been granted.

## 11. Delivery phases and acceptance criteria

### Phase 0 — Product and regulatory definition
- Map exact public services, revenue model, target countries and user journey.
- Obtain legal classification and licensing/partner plan.
- Define data-provider rights, instruments and service exclusions.
- Acceptance: signed-off scope and go/no-go gates before public advice or live execution.

### Phase 1 — Reliability and data foundation
- Verify production database schema/migrations, tenant isolation, auth/session persistence and backup/restore.
- Fix and test paper portfolio API; add endpoint-level health and deployment smoke tests.
- Add canonical instruments, provider metadata, quote freshness and data quality.
- Acceptance: reliable sign-in, portfolio, market data and audit records; no simulated quote mislabelled as live.

### Phase 2 — Beginner experience and recommendations
- Build learning academy, glossary, walkthroughs and practice lessons.
- Improve recommendations with structured evidence, risk explanations and WAIT state.
- Add assisted-order confirmation and clear broker capability labels.
- Acceptance: usability testing with true beginners; no order is sent without explicit approval in assisted mode.

### Phase 3 — ML research pipeline
- Add market-data history storage, feature/label pipeline, training jobs, model registry and reproducible evaluation.
- Start with baseline and gradient-boosting models; add regime detection.
- Add walk-forward tests, cost-aware backtests, calibration and shadow inference.
- Acceptance: reproducible out-of-sample reports and forward demo evidence; model promotion/rollback audited.

### Phase 4 — Demo execution across providers
- Finish MT5 demo order status/reconciliation.
- Implement cTrader demo trading only after account scope and protocol tests.
- Complete Binance Spot Testnet order lifecycle, permissions and reconciliation.
- Add adapter conformance suite and fault injection.
- Acceptance: repeatable demo orders, duplicate prevention, partial-fill handling, timeout reconciliation and kill switches.

### Phase 5 — Live execution pilot (gated)
- Only after legal approval, security review and operational readiness.
- Start with one broker, one asset class, opt-in users and conservative caps.
- Require explicit live account confirmation, trade scope, risk limits and automation consent.
- Acceptance: monitored pilot, incident drills, reconciliation, audit and rollback proven before expansion.

### Phase 6 — Public scale and additional markets
- Add providers and asset classes incrementally.
- Scale data ingestion, training queues and inference workers.
- Add model monitoring, customer support, complaint handling and regulatory reporting where applicable.
- Acceptance: each provider/market separately passes data, legal, security, execution and support gates.

## 12. Immediate engineering backlog

1. Add automated tests for current auth, paper portfolio, AI provider status, visual analysis and broker routes.
2. Diagnose production database initialization and missing PostgreSQL schema/migrations before building more user features.
3. Add a broker capability registry that distinguishes scaffold, read-only, demo execution and live execution.
4. Add portfolio API error visibility and order status lifecycle.
5. Create beginner academy routes and accessible dashboard navigation.
6. Define market-data provider contracts and source/freshness labels.
7. Build offline ML research package and model registry before exposing predictions to customers.
8. Keep live execution endpoints feature-flagged and unavailable until the compliance and technical gates are explicitly approved.

## 13. Non-negotiable release rules

- No live orders from an LLM response.
- No model promotion without time-safe validation.
- No execution when data is stale, incomplete or provider/account state is uncertain.
- No public claim of guaranteed returns, a guaranteed win rate or "beating strong-form EMH".
- No live auto-trading unlock by default.
- No broker integration advertised beyond what has actually been implemented and tested.
