"""One-shot cTrader read-only account synchronizer using Spotware's official Python SDK.

Run periodically as a separate worker process:
    python connectors/ctrader/sync_accounts.py
It only authenticates DEMO accounts and requests account reconciliation. It has no order-send calls.
"""
from __future__ import annotations
import json, os, sqlite3, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / "backend" / ".env")
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
from google.protobuf.json_format import MessageToDict
from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import ProtoHeartbeatEvent
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAApplicationAuthReq, ProtoOAApplicationAuthRes,
    ProtoOAGetAccountListByAccessTokenReq, ProtoOAGetAccountListByAccessTokenRes,
    ProtoOAAccountAuthReq, ProtoOAAccountAuthRes, ProtoOAReconcileReq, ProtoOAReconcileRes,
)
from twisted.internet import reactor
from backend.app.paper_ledger import DB_PATH
from backend.app.broker_store import get_connection, save_connection

CLIENT_ID=os.getenv("CTRADER_CLIENT_ID","")
CLIENT_SECRET=os.getenv("CTRADER_CLIENT_SECRET","")
if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit("CTRADER_CLIENT_ID and CTRADER_CLIENT_SECRET are required")


def connected_users():
    db=sqlite3.connect(DB_PATH)
    try:
        rows=db.execute("SELECT DISTINCT user_id FROM broker_connections WHERE provider='ctrader'").fetchall()
        return [r[0] for r in rows]
    finally:
        db.close()


def refresh_if_needed(user_id):
    connection=get_connection(user_id,"ctrader")
    meta=connection["metadata"]
    expiry=datetime.fromisoformat(meta.get("expires_at","2000-01-01T00:00:00+00:00"))
    if expiry>datetime.now(timezone.utc)+timedelta(minutes=5):
        return connection
    response=requests.post("https://openapi.ctrader.com/apps/token",params={
        "grant_type":"refresh_token","refresh_token":connection["secrets"]["refresh_token"],
        "client_id":CLIENT_ID,"client_secret":CLIENT_SECRET},timeout=15)
    response.raise_for_status()
    tokens=response.json()
    if not tokens.get("accessToken") or not tokens.get("refreshToken"):
        raise RuntimeError("cTrader refresh response did not include tokens")
    expires=int(tokens.get("expiresIn",2628000))
    meta["expires_at"]=(datetime.now(timezone.utc)+timedelta(seconds=expires)).isoformat()
    refreshed_secrets=connection["secrets"]
    refreshed_secrets["access_token"]=tokens["accessToken"]
    refreshed_secrets["refresh_token"]=tokens["refreshToken"]
    save_connection(user_id,"ctrader","cTrader account authorization","authorized",refreshed_secrets,meta)
    return get_connection(user_id,"ctrader")


def run():
    users=connected_users()
    if not users:
        print("No cTrader connections to synchronize.")
        return
    pending={"count":len(users)}
    clients=[]

    def finished():
        pending["count"]-=1
        if pending["count"]<=0 and reactor.running:
            reactor.callLater(0.2,reactor.stop)

    def start_user(user_id):
        try:
            connection=refresh_if_needed(user_id)
            access_token=connection["secrets"]["access_token"]
        except Exception as exc:
            print(f"cTrader token preparation failed for one connection: {type(exc).__name__}")
            finished()
            return
        client=Client(EndPoints.PROTOBUF_DEMO_HOST,EndPoints.PROTOBUF_PORT,TcpProtocol)
        clients.append(client)
        state={"done":False,"account_ids":[],"user_id":user_id,"heartbeat_call":None}
        def complete():
            if state["done"]: return
            state["done"]=True
            if state["heartbeat_call"] and state["heartbeat_call"].active():
                state["heartbeat_call"].cancel()
            try: client.stopService()
            except Exception: pass
            finished()
        def fail(_failure):
            print("cTrader read-only sync failed for one connection.")
            complete()
        def heartbeat():
            if state["done"]: return
            client.send(ProtoHeartbeatEvent()).addErrback(fail)
            state["heartbeat_call"]=reactor.callLater(10,heartbeat)
        def on_connected(c):
            state["heartbeat_call"]=reactor.callLater(10,heartbeat)
            req=ProtoOAApplicationAuthReq()
            req.clientId=CLIENT_ID
            req.clientSecret=CLIENT_SECRET
            c.send(req).addErrback(fail)
        def on_message(c,message):
            if message.payloadType==ProtoHeartbeatEvent().payloadType:
                return
            if message.payloadType==ProtoOAApplicationAuthRes().payloadType:
                req=ProtoOAGetAccountListByAccessTokenReq()
                req.accessToken=access_token
                c.send(req).addErrback(fail)
                return
            if message.payloadType==ProtoOAGetAccountListByAccessTokenRes().payloadType:
                response=Protobuf.extract(message)
                accounts=[]
                for account in response.ctidTraderAccount:
                    accounts.append({
                        "account_id":int(account.ctidTraderAccountId),
                        "is_live":bool(account.isLive),
                        "login":int(getattr(account,"traderLogin",0) or 0),
                        "broker_title":str(getattr(account,"brokerTitle","") or ""),
                        "deposit_asset_name":str(getattr(account,"depositAssetName","") or "")
                    })
                meta=connection["metadata"]
                secrets_payload=connection["secrets"]
                secrets_payload["accounts"]=accounts
                meta["accounts_synced_count"]=len(accounts)
                meta["last_account_sync"]=datetime.now(timezone.utc).isoformat()
                save_connection(user_id,"ctrader","cTrader account authorization","authorized",
                                secrets_payload,meta)
                demo=next((a for a in accounts if not a["is_live"]),None)
                if not demo:
                    complete()
                    return
                state["account_id"]=demo["account_id"]
                req=ProtoOAAccountAuthReq()
                req.ctidTraderAccountId=demo["account_id"]
                req.accessToken=access_token
                c.send(req).addErrback(fail)
                return
            if message.payloadType==ProtoOAAccountAuthRes().payloadType:
                req=ProtoOAReconcileReq()
                req.ctidTraderAccountId=state["account_id"]
                c.send(req).addErrback(fail)
                return
            if message.payloadType==ProtoOAReconcileRes().payloadType:
                response=Protobuf.extract(message)
                meta=connection["metadata"]
                secrets_payload=connection["secrets"]
                secrets_payload["demo_account_id"]=state["account_id"]
                secrets_payload["demo_reconciliation"]=MessageToDict(response,preserving_proto_field_name=True)
                meta["last_demo_reconcile"]=datetime.now(timezone.utc).isoformat()
                save_connection(user_id,"ctrader","cTrader account authorization","authorized",
                                secrets_payload,meta)
                complete()
        client.setConnectedCallback(on_connected)
        client.setDisconnectedCallback(lambda _c,_reason: complete())
        client.setMessageReceivedCallback(on_message)
        client.startService()
        reactor.callLater(35,complete)

    for uid in users:
        start_user(uid)
    if pending["count"]>0:
        reactor.run(installSignalHandlers=False)


if __name__=="__main__":
    run()
