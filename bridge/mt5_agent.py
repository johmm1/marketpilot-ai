"""MARKETPILOT AI Windows MT5 read-only bridge agent.

Run on a Windows machine with MetaTrader 5 installed and logged into a DEMO account.
This companion reports account, positions and recent orders only. It never calls order_send.
"""
from __future__ import annotations
import os, time, json, logging
import requests
import MetaTrader5 as mt5

API_BASE=os.environ["MARKETPILOT_API_BASE"].rstrip("/")
BRIDGE_TOKEN=os.environ["MARKETPILOT_MT5_BRIDGE_TOKEN"]
POLL_SECONDS=max(3,int(os.getenv("MARKETPILOT_MT5_POLL_SECONDS","10")))
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
session=requests.Session()
session.headers.update({"Authorization":f"Bearer {BRIDGE_TOKEN}","Content-Type":"application/json"})

def snapshot():
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        account=mt5.account_info()
        terminal=mt5.terminal_info()
        if account is None: raise RuntimeError(f"MT5 account_info failed: {mt5.last_error()}")
        positions=mt5.positions_get()
        orders=mt5.orders_get()
        history=mt5.history_orders_get()
        def safe(x):
            return x._asdict() if hasattr(x,"_asdict") else x
        return {
            "account":{"login":int(account.login),"server":str(account.server),
                       "company":str(account.company),"currency":str(account.currency),
                       "balance":float(account.balance),"equity":float(account.equity),
                       "margin":float(account.margin),"margin_free":float(account.margin_free),
                       "profit":float(account.profit),"trade_allowed":bool(account.trade_allowed)},
            "terminal":{"connected":bool(terminal.connected) if terminal else False},
            "positions":[safe(x) for x in (positions or [])],
            "pending_orders":[safe(x) for x in (orders or [])],
            "history_orders":[safe(x) for x in (history or [])][-100:],
            "mode":"read_only_snapshot","live_order_submission":False
        }
    finally:
        mt5.shutdown()

def normalize(value):
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [normalize(v) for v in value]
    if hasattr(value,"isoformat"): return value.isoformat()
    if isinstance(value,(str,int,float,bool)) or value is None: return value
    return str(value)

def main():
    logging.info("Starting read-only MT5 bridge; no order execution is available.")
    while True:
        try:
            payload=normalize(snapshot())
            response=session.post(API_BASE+"/api/brokers/mt5-bridge/snapshot",json=payload,timeout=15)
            response.raise_for_status()
            logging.info("Read-only account snapshot delivered.")
        except Exception as exc:
            logging.warning("Bridge cycle failed: %s",type(exc).__name__)
        time.sleep(POLL_SECONDS)

if __name__=="__main__": main()
