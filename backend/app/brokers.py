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
