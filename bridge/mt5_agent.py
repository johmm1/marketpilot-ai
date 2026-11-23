"""MARKETPILOT AI Windows MT5 read-only bridge agent.

Run on a Windows machine with MetaTrader 5 installed and logged into a DEMO account.
This companion reports account snapshots and submits queued orders on DEMO accounts only.
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
        if int(account.trade_mode) != 0:
            raise RuntimeError("Safety stop: this bridge reads DEMO accounts only. Log into a DEMO account in the MT5 terminal.")
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
                       "profit":float(account.profit),"trade_allowed":bool(account.trade_allowed),"trade_mode":int(account.trade_mode)},
            "terminal":{"connected":bool(terminal.connected) if terminal else False},
            "positions":[safe(x) for x in (positions or [])],
            "pending_orders":[safe(x) for x in (orders or [])],
            "history_orders":[safe(x) for x in (history or [])][-100:],
            "mode":"read_only_snapshot","live_order_submission":False
        }
    finally:
        mt5.shutdown()


def execute_demo_order(order):
    """Submit one small, protected market order on a verified MT5 demo account."""
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        account=mt5.account_info()
        if account is None or int(account.trade_mode)!=0:
            raise RuntimeError("SAFETY BLOCK: MT5 account is not a demo account.")
        if not account.trade_allowed:
            raise RuntimeError("MT5 terminal/account currently disallows trading.")
        symbol=str(order["symbol"]).upper()
        side=str(order["side"]).upper()
        volume=float(order["volume"])
        sl=float(order["stop_loss"]); tp=float(order["take_profit"])
        if side not in {"BUY","SELL"} or not (0 < volume <= 0.10) or sl<=0 or tp<=0:
            raise RuntimeError("Order failed local demo safety validation.")
        if not mt5.symbol_select(symbol,True):
            raise RuntimeError(f"Symbol unavailable in this MT5 account: {symbol}")
        info=mt5.symbol_info(symbol); tick=mt5.symbol_info_tick(symbol)
        if info is None or tick is None: raise RuntimeError("Could not read current symbol quote.")
        if volume<info.volume_min or volume>min(info.volume_max,0.10):
            raise RuntimeError(f"Volume outside symbol limits (min {info.volume_min}, max {min(info.volume_max,0.10)}).")
        steps=(volume-info.volume_min)/info.volume_step
        if abs(steps-round(steps))>1e-7: raise RuntimeError("Volume does not match this symbol's lot step.")
        price=float(tick.ask if side=="BUY" else tick.bid)
        point=float(info.point); min_gap=max(float(info.trade_stops_level)*point,point)
        if side=="BUY" and not (sl<price-min_gap and tp>price+min_gap):
            raise RuntimeError("For BUY, stop-loss must be below market and take-profit above market.")
        if side=="SELL" and not (sl>price+min_gap and tp<price-min_gap):
            raise RuntimeError("For SELL, stop-loss must be above market and take-profit below market.")
        request={"action":mt5.TRADE_ACTION_DEAL,"symbol":symbol,"volume":volume,
            "type":mt5.ORDER_TYPE_BUY if side=="BUY" else mt5.ORDER_TYPE_SELL,
            "price":price,"sl":sl,"tp":tp,"deviation":20,"magic":26001123,
            "comment":"MARKETPILOT DEMO","type_time":mt5.ORDER_TIME_GTC,
            "type_filling":mt5.ORDER_FILLING_IOC}
        check=mt5.order_check(request)
        if check is None or check.retcode not in (0,mt5.TRADE_RETCODE_DONE):
            raise RuntimeError(f"MT5 order check rejected: {getattr(check,'comment',mt5.last_error())}")
        result=mt5.order_send(request)
        if result is None or result.retcode not in (mt5.TRADE_RETCODE_DONE,mt5.TRADE_RETCODE_DONE_PARTIAL):
            raise RuntimeError(f"MT5 rejected order: {getattr(result,'comment',mt5.last_error())}")
        return {"retcode":int(result.retcode),"order":int(result.order),"deal":int(result.deal),
            "volume":float(result.volume),"price":float(result.price),"comment":str(result.comment),
            "account_login":int(account.login),"server":str(account.server),"environment":"demo"}
    finally:
        mt5.shutdown()

def poll_demo_orders():
    response=session.get(API_BASE+"/api/brokers/mt5-bridge/demo-orders/next",timeout=12)
    response.raise_for_status()
    order=response.json().get("order")
    if not order: return
    order_id=order["id"]
    try:
        result=execute_demo_order(order)
        status="executed"
        logging.info("Demo order executed: %s %s %s",order["side"],order["volume"],order["symbol"])
    except Exception as exc:
        result={"error":str(exc)[:500]}
        status="rejected"
        logging.warning("Demo order rejected: %s",str(exc)[:300])
    report=session.post(API_BASE+f"/api/brokers/mt5-bridge/demo-orders/{order_id}/result",
                        json={"status":status,"result":result},timeout=12)
    report.raise_for_status()

def normalize(value):
    if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [normalize(v) for v in value]
    if hasattr(value,"isoformat"): return value.isoformat()
    if isinstance(value,(str,int,float,bool)) or value is None: return value
    return str(value)

def main():
    logging.info("Starting MARKETPILOT MT5 bridge. DEMO order execution only; live accounts are blocked.")
    while True:
        try:
            payload=normalize(snapshot())
            response=session.post(API_BASE+"/api/brokers/mt5-bridge/snapshot",json=payload,timeout=15)
            response.raise_for_status()
            logging.info("MT5 demo account snapshot delivered.")
            poll_demo_orders()
        except Exception as exc:
            logging.warning("Bridge cycle failed: %s",type(exc).__name__)
        time.sleep(POLL_SECONDS)

if __name__=="__main__": main()
