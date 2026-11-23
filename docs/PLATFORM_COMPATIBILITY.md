# MARKETPILOT AI — Trading Platform Compatibility

Last reviewed: 23 November 2026

This catalogue is an integration roadmap, not a claim that every listed platform is already connected. A provider appears in the dashboard registry so the app can explain its support level and required setup. Execution is available only after a provider-specific adapter has been implemented, tested, and explicitly authorised.

## Support levels

- **Analysis:** screenshots, charts, indicators and manual trade planning; no account control.
- **Alerts/read-only:** official alerts or market/account data; no order submission.
- **Demo execution:** official demo, paper or test environment; no live orders.
- **Authorised live execution:** only after the provider grants the required API permission and the user explicitly enables it. Live execution remains locked in the current release.

## Trading terminals and charting

| Provider | Integration path | Current registry status |
|---|---|---|
| MetaTrader 5 | Official terminal Python integration through the Windows companion | MT5 demo bridge exists; demo-only execution safeguards are in place, deployment/runtime validation still required |
| MetaTrader 4 | Official MQL4 Expert Advisor/local bridge | Bridge development required |
| cTrader | cTrader Open API and OAuth | Account-read authorization scaffold; trading scope not enabled |
| TradingView | Official webhook alerts; broker execution remains a separate broker connection | Webhook adapter planned |
| TradeLocker | Broker/vendor-authorised integration only | Access and API scope must be confirmed per broker |
| DXtrade | Broker/vendor-authorised integration only | Access and API scope must be confirmed per broker |
| Match-Trader | Broker/vendor-authorised integration only | Access and API scope must be confirmed per broker |

TradingView webhook notes: TradingView sends HTTP POST requests to a configured URL. Webhook alerts require two-factor authentication; only ports 80/443 are accepted; a slow endpoint may time out after three seconds; delivery can occasionally fail. Never place passwords, broker tokens or other secrets in an alert body. Source: https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/

## Direct brokers and multi-asset providers

| Provider | Official API / route | Demo or simulation |
|---|---|---|
| Interactive Brokers | TWS API / IB Gateway and Client Portal API | Paper trading |
| OANDA | v20 REST and streaming API | Practice account |
| IG | REST and streaming API | Demo account and demo API key |
| Saxo | OpenAPI REST and streaming | SIM environment |
| Capital.com | REST and WebSocket API | Dedicated demo API host |
| Deriv | WebSocket API | Demo account |
| tastytrade | REST and streaming API | Sandbox with simulated money |
| FXCM | Provider API / FIX / supported SDKs | Demo availability must be confirmed for account/entity |
| eToro | API access subject to eligibility and scope | Verify availability by account and region |
| Trading 212 | API scope is account/product limited; do not assume CFD support | Verify current account eligibility |
| Tradovate | REST and WebSocket API | Demo environment |

Official references:
- OANDA: https://developer.oanda.com/rest-live-v20/introduction/
- IG: https://labs.ig.com/gettingstarted
- Saxo environments: https://www.developer.saxo/openapi/learn/environments
- Capital.com: https://open-api.capital.com/
- tastytrade sandbox: https://developer.tastytrade.com/sandbox/
- Interactive Brokers TWS API: https://interactivebrokers.github.io/tws-api/

## Crypto exchanges

| Provider | API route | Test environment / notes |
|---|---|---|
| Binance | Official REST and WebSocket APIs | Spot Testnet; MARKETPILOT currently has a read-only Testnet account check scaffold |
| Bybit | V5 REST and WebSocket APIs | Testnet/demo |
| OKX | V5 REST and WebSocket APIs | Demo trading |
| Coinbase Advanced | REST and WebSocket APIs | Sandbox capabilities are limited and must not be treated as a full market simulator |
| Kraken | REST and WebSocket APIs | Futures demo; spot test/UAT access varies |
| Bitget | REST and WebSocket APIs | Demo trading |

API documentation:
- Binance: https://developers.binance.com/en/docs/introduction
- Bybit: https://bybit-exchange.github.io/docs/v5/intro
- OKX: https://www.okx.com/docs-v5/en/
- Coinbase: https://docs.cdp.coinbase.com/advanced-trade/docs/welcome
- Kraken: https://docs.kraken.com/api/
- Bitget: https://www.bitget.com/api-doc/common/intro

## Analysis-first platforms

Pocket Option, Quotex and Olymp Trade are listed for screen/screenshot analysis and manual trade assistance only unless an official, documented and provider-authorised API becomes available. Third-party browser-session automation, reverse-engineered WebSockets, copied cookies, SSIDs and session tokens are not accepted as safe integrations.

Pocket Option demo page: https://pocketoption.com/en/cabinet/try-demo/

## Build and release rules

1. A catalogue entry is not a working connector. Never display "connected" until authentication and a real provider health/account check succeeds.
2. Keep provider credentials on the backend or local companion; never put secrets in frontend code, webhook bodies, logs or Git.
3. Start with demo/paper/testnet. Use separate credentials for demo and live.
4. Use least-privilege keys. Disable withdrawals and transfers wherever possible.
5. Require preview, explicit confirmation, symbol allowlists, quantity/notional caps, stop-loss checks, duplicate-order protection, idempotency, audit logs and an emergency stop before any live order path.
6. A screen share is for observation and analysis only. It does not grant permission or technical ability to click buttons or place orders.
7. Confirm regional availability, broker entity, account type, API permissions, rate limits and current provider terms before enabling each adapter.
