"""SQLite-backed paper order journal. No broker connectivity or live execution."""
import os, sqlite3
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

DB_PATH = os.getenv("MARKETPILOT_DB_PATH", str(Path(__file__).resolve().parent.parent / "marketpilot.db"))

def _connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection

def initialize():
    with _connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS paper_orders (
            id TEXT PRIMARY KEY, symbol TEXT NOT NULL, side TEXT NOT NULL,
            quantity REAL NOT NULL, reference_price REAL NOT NULL,
            notional REAL NOT NULL, created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PAPER_FILLED')""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_paper_orders_created ON paper_orders(created_at)")

def create_order(symbol, side, quantity, reference_price):
    notional = quantity * reference_price
    if notional > 100000:
        raise ValueError("Paper order notional exceeds the demo risk limit of 100,000 quote units")
    order = {"id": str(uuid4()), "symbol": symbol.upper(), "side": side,
             "quantity": quantity, "reference_price": reference_price, "notional": notional,
             "created_at": datetime.now(timezone.utc).isoformat(), "status": "PAPER_FILLED",
             "live_execution": False}
    with _connect() as db:
        db.execute("INSERT INTO paper_orders VALUES (?,?,?,?,?,?,?,?)",
            (order["id"], order["symbol"], side, quantity, reference_price, notional,
             order["created_at"], order["status"]))
    return order

def get_portfolio():
    with _connect() as db:
        orders = [dict(row) for row in db.execute(
            "SELECT * FROM paper_orders ORDER BY created_at DESC LIMIT 200").fetchall()]
    positions = {}
    for order in reversed(orders):
        item = positions.setdefault(order["symbol"], {"symbol": order["symbol"], "quantity": 0.0, "net_cost": 0.0})
        signed = order["quantity"] if order["side"] == "BUY" else -order["quantity"]
        item["quantity"] += signed
        item["net_cost"] += signed * order["reference_price"]
    clean = []
    for item in positions.values():
        qty = item["quantity"]
        clean.append({"symbol": item["symbol"], "quantity": round(qty, 8),
                      "average_entry": round(item["net_cost"] / qty, 8) if qty else None})
    return {"mode": "PAPER_ONLY", "live_execution": False, "positions": clean,
            "recent_orders": orders, "order_count": len(orders),
            "note": "Demo journal; positions are derived from the latest 200 paper orders and are not broker holdings."}
