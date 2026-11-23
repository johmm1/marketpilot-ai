"""Multi-broker integration registry and safe, read-only connectivity probes.

No broker credentials are accepted from the browser and no live orders are sent here.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Protocol, Any
import os
import httpx


@dataclass(frozen=True)
class BrokerProvider:
    id: str
    name: str
    category: str
    integration_type: str
    auth_type: str
    environments: tuple[str, ...]
    capabilities: tuple[str, ...]
    setup_required: tuple[str, ...]
    official_docs: str
    status: str = "adapter_scaffold"


class BrokerAdapter(Protocol):
    provider: BrokerProvider

    async def probe(self) -> dict[str, Any]: ...


class BinanceSpotAdapter:
    """Official Binance Spot REST public connectivity probe (no account access)."""

    def __init__(self) -> None:
        self.testnet = os.getenv("BINANCE_API_ENV", "testnet").lower() != "production"
        self.base_url = (
            "https://testnet.binance.vision"
            if self.testnet else "https://api.binance.com"
        )
        self.provider = PROVIDERS["binance"]

    async def probe(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(f"{self.base_url}/api/v3/ping")
                response.raise_for_status()
            return {
                "provider": self.provider.id,
                "reachable": True,
                "environment": "testnet" if self.testnet else "production_public_api",
                "scope": "public_market_connectivity_only",
                "live_trading_enabled": False,
            }
        except (httpx.HTTPError, ValueError) as exc:
            return {
                "provider": self.provider.id,
                "reachable": False,
                "environment": "testnet" if self.testnet else "production_public_api",
                "scope": "public_market_connectivity_only",
                "error": type(exc).__name__,
                "live_trading_enabled": False,
            }


PROVIDERS: dict[str, BrokerProvider] = {
    "binance": BrokerProvider(
        id="binance", name="Binance Spot", category="crypto_exchange",
        integration_type="official_signed_rest_and_websocket",
        auth_type="api_key_and_secret",
        environments=("testnet", "production"),
        capabilities=("market_data", "account_read", "spot_orders", "order_updates"),
        setup_required=("Create a Binance API key", "Keep withdrawals disabled",
                        "Use Spot Testnet credentials for initial account/order tests"),
        official_docs="https://developers.binance.com/en/docs/introduction",
        status="read_only_probe_available",
    ),
    "ctrader": BrokerProvider(
        id="ctrader", name="cTrader",
        category="multi_asset_broker_platform",
        integration_type="official_open_api_json_or_protobuf",
        auth_type="oauth2_authorization_code",
        environments=("demo", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Register a cTrader Open API application",
                        "Obtain client ID and client secret",
                        "Authorize each cTrader ID and select demo or live account"),
        official_docs="https://help.ctrader.com/open-api/",
        status="authorization_setup_required",
    ),

    "metatrader4": BrokerProvider(
        id="metatrader4", name="MetaTrader 4", category="multi_asset_trading_platform",
        integration_type="official_mql4_expert_advisor_bridge",
        auth_type="local_terminal_bridge", environments=("demo", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Install MT4 desktop terminal", "Install MARKETPILOT MQL4 bridge/Expert Advisor",
                        "Pair locally and verify a demo account before execution"),
        official_docs="https://docs.mql4.com/", status="bridge_development_required",
    ),
    "tradingview": BrokerProvider(
        id="tradingview", name="TradingView", category="charting_and_alert_platform",
        integration_type="official_webhook_alerts",
        auth_type="signed_webhook_secret", environments=("alerts",),
        capabilities=("chart_analysis", "watchlist_workflow", "alert_ingestion"),
        setup_required=("Enable two-factor authentication on TradingView",
                        "Create an alert and send its JSON message to the MARKETPILOT webhook",
                        "Use a connected broker's own API for order execution"),
        official_docs="https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/",
        status="webhook_adapter_planned",
    ),
    "deriv": BrokerProvider(
        id="deriv", name="Deriv", category="multi_asset_broker",
        integration_type="official_websocket_api", auth_type="oauth_or_api_token",
        environments=("demo", "live"),
        capabilities=("market_data", "account_read", "proposal", "orders", "portfolio"),
        setup_required=("Create a Deriv demo account", "Create an API token with only required scopes",
                        "Test proposals and demo orders before any live use"),
        official_docs="https://developers.deriv.com/", status="adapter_development_required",
    ),
    "interactivebrokers": BrokerProvider(
        id="interactivebrokers", name="Interactive Brokers", category="multi_asset_broker",
        integration_type="official_tws_client_portal_api", auth_type="local_gateway_or_oauth",
        environments=("paper", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Install Trader Workstation or IB Gateway", "Enable API access",
                        "Use a paper trading account for initial tests"),
        official_docs="https://interactivebrokers.github.io/tws-api/", status="adapter_development_required",
    ),
    "oanda": BrokerProvider(
        id="oanda", name="OANDA", category="forex_broker",
        integration_type="official_v20_rest_streaming", auth_type="personal_access_token",
        environments=("practice", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Open an OANDA v20 demo account", "Generate an API token",
                        "Connect to the practice environment first"),
        official_docs="https://developer.oanda.com/rest-live-v20/introduction/",
        status="adapter_development_required",
    ),
    "ig": BrokerProvider(
        id="ig", name="IG", category="multi_asset_broker",
        integration_type="official_rest_streaming_api", auth_type="api_key_and_oauth",
        environments=("demo", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Create an IG demo account", "Generate a demo API key",
                        "Authorise the account and test against demo-api.ig.com"),
        official_docs="https://labs.ig.com/gettingstarted", status="adapter_development_required",
    ),
    "saxo": BrokerProvider(
        id="saxo", name="Saxo", category="multi_asset_broker",
        integration_type="official_openapi_rest_websocket", auth_type="oauth2",
        environments=("simulation", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Register a Saxo OpenAPI application", "Authorise a simulation account",
                        "Validate order flows in SIM before requesting live permissions"),
        official_docs="https://www.developer.saxo/openapi/learn/environments",
        status="adapter_development_required",
    ),
    "capitalcom": BrokerProvider(
        id="capitalcom", name="Capital.com", category="cfd_broker",
        integration_type="official_rest_websocket_api", auth_type="api_key_and_password",
        environments=("demo", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Enable 2FA and create an API key", "Use the demo API host first",
                        "Keep live permissions disabled during testing"),
        official_docs="https://open-api.capital.com/", status="adapter_development_required",
    ),
    "tastytrade": BrokerProvider(
        id="tastytrade", name="tastytrade", category="options_and_equities_broker",
        integration_type="official_rest_streaming_api", auth_type="oauth",
        environments=("sandbox", "production"),
        capabilities=("account_read", "positions", "orders", "order_updates"),
        setup_required=("Create a sandbox developer account", "Use separate sandbox credentials",
                        "Validate simulated orders in sandbox"),
        official_docs="https://developer.tastytrade.com/sandbox/",
        status="adapter_development_required",
    ),
    "etoro": BrokerProvider(
        id="etoro", name="eToro", category="multi_asset_broker",
        integration_type="official_api_access_limited", auth_type="provider_authorization",
        environments=("demo_if_enabled", "live_if_eligible"),
        capabilities=("market_data", "account_read", "portfolio"),
        setup_required=("Check API eligibility for your account and region",
                        "Use only documented permissions and approved access"),
        official_docs="https://www.etoro.com/", status="eligibility_and_scope_verification_required",
    ),
    "trading212": BrokerProvider(
        id="trading212", name="Trading 212", category="equities_broker",
        integration_type="official_rest_api_limited_beta", auth_type="api_key",
        environments=("live_account_data",),
        capabilities=("account_read", "portfolio", "orders_scope_subject_to_api"),
        setup_required=("Check API availability for your account type and region",
                        "Do not assume the Invest API applies to CFD accounts"),
        official_docs="https://www.trading212.com/", status="limited_api_scope_verification_required",
    ),
    "fxcm": BrokerProvider(
        id="fxcm", name="FXCM", category="forex_cfd_broker",
        integration_type="official_rest_or_fix_api", auth_type="provider_credentials",
        environments=("demo", "live"),
        capabilities=("market_data", "account_read", "positions", "orders"),
        setup_required=("Confirm current API access for your FXCM entity",
                        "Use a demo account and supported SDK/API version"),
        official_docs="https://www.fxcm.com/markets/algorithmic-trading/",
        status="adapter_development_required",
    ),
    "bybit": BrokerProvider(
        id="bybit", name="Bybit", category="crypto_exchange",
        integration_type="official_v5_rest_websocket", auth_type="api_key_and_secret",
        environments=("testnet", "demo", "production"),
        capabilities=("market_data", "account_read", "spot_orders", "derivatives_orders", "order_updates"),
        setup_required=("Create a testnet or demo API key", "Restrict key permissions and IP access",
                        "Keep withdrawals disabled"),
        official_docs="https://bybit-exchange.github.io/docs/v5/intro",
        status="adapter_development_required",
    ),
    "okx": BrokerProvider(
        id="okx", name="OKX", category="crypto_exchange",
        integration_type="official_v5_rest_websocket", auth_type="api_key_secret_passphrase",
        environments=("demo", "production"),
        capabilities=("market_data", "account_read", "spot_orders", "derivatives_orders", "order_updates"),
        setup_required=("Create a demo trading API key", "Use demo trading mode headers",
                        "Restrict permissions and disable withdrawals"),
        official_docs="https://www.okx.com/docs-v5/en/", status="adapter_development_required",
    ),
    "coinbase": BrokerProvider(
        id="coinbase", name="Coinbase Advanced", category="crypto_exchange",
        integration_type="official_rest_websocket", auth_type="scoped_api_key",
        environments=("sandbox_limited", "production"),
        capabilities=("market_data", "account_read", "spot_orders", "order_updates"),
        setup_required=("Create a scoped Advanced Trade API key",
                        "Use sandbox only for supported simulated endpoints",
                        "Disable transfers/withdrawals"),
        official_docs="https://docs.cdp.coinbase.com/advanced-trade/docs/welcome",
        status="adapter_development_required",
    ),
    "kraken": BrokerProvider(
        id="kraken", name="Kraken", category="crypto_exchange",
        integration_type="official_rest_websocket", auth_type="api_key_and_secret",
        environments=("futures_demo", "production"),
        capabilities=("market_data", "account_read", "spot_orders", "derivatives_orders", "order_updates"),
        setup_required=("Create API keys with minimum permissions",
                        "Use Futures demo for derivatives testing where available"),
        official_docs="https://docs.kraken.com/api/", status="adapter_development_required",
    ),
    "bitget": BrokerProvider(
        id="bitget", name="Bitget", category="crypto_exchange",
        integration_type="official_rest_websocket", auth_type="api_key_secret_passphrase",
        environments=("demo", "production"),
        capabilities=("market_data", "account_read", "spot_orders", "derivatives_orders", "order_updates"),
        setup_required=("Create demo API credentials", "Use demo trading mode",
                        "Disable withdrawal permission"),
        official_docs="https://www.bitget.com/api-doc/common/intro",
        status="adapter_development_required",
    ),
    "pocket_option": BrokerProvider(
        id="pocket_option", name="Pocket Option", category="options_trading_platform",
        integration_type="screen_analysis_only_no_verified_public_api",
        auth_type="none_for_analysis",
        environments=("screen_analysis",),
        capabilities=("chart_analysis", "screenshot_analysis", "manual_trade_assistance"),
        setup_required=("Use MARKETPILOT screen sharing or upload a chart screenshot",
                        "Place trades manually on the platform",
                        "Do not share browser cookies, SSIDs, passwords or session tokens"),
        official_docs="https://pocketoption.com/en/cabinet/try-demo/",
        status="analysis_only_no_verified_public_trading_api",
    ),
    "quotex": BrokerProvider(
        id="quotex", name="Quotex", category="options_trading_platform",
        integration_type="screen_analysis_only_no_verified_public_api",
        auth_type="none_for_analysis", environments=("screen_analysis",),
        capabilities=("chart_analysis", "screenshot_analysis", "manual_trade_assistance"),
        setup_required=("Use screen sharing or chart screenshots for analysis",
                        "Execute trades manually unless an official API is documented"),
        official_docs="https://quotex.com/", status="analysis_only_api_not_verified",
    ),
    "olymptrade": BrokerProvider(
        id="olymptrade", name="Olymp Trade", category="options_trading_platform",
        integration_type="screen_analysis_only_api_not_verified",
        auth_type="none_for_analysis", environments=("screen_analysis",),
        capabilities=("chart_analysis", "screenshot_analysis", "manual_trade_assistance"),
        setup_required=("Use screen sharing or chart screenshots for analysis",
                        "Confirm official API access directly with the provider"),
        official_docs="https://olymptrade.com/", status="analysis_only_api_not_verified",
    ),
    "dxtrade": BrokerProvider(
        id="dxtrade", name="DXtrade", category="broker_trading_platform",
        integration_type="broker_or_vendor_authorised_integration",
        auth_type="broker_authorized",
        environments=("demo_if_broker_enabled", "live_if_broker_enabled"),
        capabilities=("market_data", "account_read", "orders_if_authorized"),
        setup_required=("Identify the broker operating the DXtrade instance",
                        "Request approved API access from that broker"),
        official_docs="https://devexperts.com/dxtrade/", status="broker_authorization_required",
    ),
    "matchtrader": BrokerProvider(
        id="matchtrader", name="Match-Trader", category="broker_trading_platform",
        integration_type="broker_or_vendor_authorised_integration",
        auth_type="broker_authorized",
        environments=("demo_if_broker_enabled", "live_if_broker_enabled"),
        capabilities=("market_data", "account_read", "orders_if_authorized"),
        setup_required=("Identify the broker operating the Match-Trader instance",
                        "Request approved API access from that broker"),
        official_docs="https://match-trader.com/", status="broker_authorization_required",
    ),
    "tradovate": BrokerProvider(
        id="tradovate", name="Tradovate", category="futures_broker",
        integration_type="official_rest_websocket_api",
        auth_type="oauth_or_api_credentials", environments=("demo", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Create a Tradovate demo account", "Register an API application",
                        "Use demo endpoints and credentials first"),
        official_docs="https://api.tradovate.com/", status="adapter_development_required",
    ),

    "metatrader5": BrokerProvider(
        id="metatrader5", name="MetaTrader 5",
        category="multi_asset_trading_platform",
        integration_type="official_terminal_python_integration",
        auth_type="terminal_account_login",
        environments=("demo", "live"),
        capabilities=("market_data", "account_read", "positions", "orders", "order_updates"),
        setup_required=("Install the official MetaTrader 5 terminal on a Windows host",
                        "Install the official MetaTrader5 Python package in the local bridge",
                        "Connect and validate a demo account before enabling any execution"),
        official_docs="https://www.mql5.com/en/docs/python_metatrader5",
        status="windows_bridge_required",
    ),
}


def list_providers() -> list[dict[str, Any]]:
    return [asdict(provider) for provider in PROVIDERS.values()]


def get_provider(provider_id: str) -> BrokerProvider:
    provider = PROVIDERS.get(provider_id.lower())
    if not provider:
        raise ValueError("Unsupported broker provider")
    return provider


async def probe_provider(provider_id: str) -> dict[str, Any]:
    get_provider(provider_id)
    if provider_id.lower() == "binance":
        return await BinanceSpotAdapter().probe()
    provider = PROVIDERS[provider_id.lower()]
    return {
        "provider": provider.id,
        "reachable": None,
        "status": provider.status,
        "scope": "not_connected",
        "message": "Provider authorization or its local bridge must be configured before a connection test.",
        "live_trading_enabled": False,
    }
