"""Persistent, user-scoped paper order journal. Never sends orders to a broker."""
from uuid import uuid4
from datetime import datetime, timezone
from .db import connect

def initialize():
    with connect() as db:
        if not db.is_postgres:
            db.execute("""CREATE TABLE IF NOT EXISTS paper_orders (
                id TEXT PRIMARY KEY,symbol TEXT NOT NULL,side TEXT NOT NULL,quantity REAL NOT NULL,
                reference_price REAL NOT NULL,notional REAL NOT NULL,created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PAPER_FILLED',user_id TEXT)""")
            cols={row["name"] for row in db.execute("PRAGMA table_info(paper_orders)")}
            if "user_id" not in cols: db.execute("ALTER TABLE paper_orders ADD COLUMN user_id TEXT")
        db.execute("CREATE INDEX IF NOT EXISTS idx_paper_orders_created ON paper_orders(created_at)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_paper_orders_user ON paper_orders(user_id,created_at)")

def create_order(user_id,symbol,side,quantity,reference_price):
    side=side.upper()
    if side not in {"BUY","SELL"}: raise ValueError("Side must be BUY or SELL")
    if quantity<=0 or reference_price<=0: raise ValueError("Quantity and reference price must be positive")
    notional=quantity*reference_price
    if notional>100000: raise ValueError("Paper order notional exceeds the demo risk limit of 100,000 quote units")
    order={"id":str(uuid4()),"symbol":symbol.upper(),"side":side,"quantity":quantity,
        "reference_price":reference_price,"notional":notional,"created_at":datetime.now(timezone.utc).isoformat(),
        "status":"PAPER_FILLED","live_execution":False}
    with connect() as db:
        db.execute("""INSERT INTO paper_orders
            (id,symbol,side,quantity,reference_price,notional,created_at,status,user_id)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (order["id"],order["symbol"],side.lower(),quantity,reference_price,notional,order["created_at"],order["status"],user_id))
    return order

def get_portfolio(user_id):
    with connect() as db:
        rows=db.execute("""SELECT id,symbol,side,quantity,reference_price,notional,created_at,status
            FROM paper_orders WHERE user_id=? ORDER BY created_at DESC LIMIT 200""",(user_id,)).fetchall()
        orders=[]
        for row in rows:
            item=dict(row); item["side"]=str(item["side"]).upper()
            orders.append(item)
    positions={}
    for order in reversed(orders):
        item=positions.setdefault(order["symbol"],{"symbol":order["symbol"],"quantity":0.0,"net_cost":0.0})
        signed=float(order["quantity"]) if order["side"]=="BUY" else -float(order["quantity"])
        item["quantity"]+=signed; item["net_cost"]+=signed*float(order["reference_price"])
    clean=[]
    for item in positions.values():
        qty=item["quantity"]; clean.append({"symbol":item["symbol"],"quantity":round(qty,8),
            "average_entry":round(item["net_cost"]/qty,8) if qty else None})
    return {"mode":"PAPER_ONLY","live_execution":False,"positions":clean,"recent_orders":orders,
        "order_count":len(orders),"note":"Persistent account-scoped demo journal; positions are derived from the latest 200 paper orders."}
