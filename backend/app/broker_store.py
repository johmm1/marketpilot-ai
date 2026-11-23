"""Encrypted per-user broker credential storage and one-time authorization tokens."""
from __future__ import annotations
import hashlib, json, secrets, uuid
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from .db import connect
from .config import settings

def _fernet():
    key=settings.broker_encryption_key.strip()
    if not key: raise HTTPException(503,"Broker vault is not configured. Set BROKER_ENCRYPTION_KEY on the backend.")
    try: return Fernet(key.encode())
    except (ValueError,TypeError) as exc: raise HTTPException(503,"BROKER_ENCRYPTION_KEY must be a valid Fernet key.") from exc

def initialize_broker_store():
    with connect() as db:
        if not db.is_postgres:
            db.execute("""CREATE TABLE IF NOT EXISTS broker_connections (
                id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),provider TEXT NOT NULL,
                label TEXT NOT NULL,environment TEXT NOT NULL,secret_blob TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
                UNIQUE(user_id,provider,label))""")
            db.execute("""CREATE TABLE IF NOT EXISTS broker_oauth_states (
                state_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),
                provider TEXT NOT NULL,expires_at TEXT NOT NULL,created_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS mt5_bridge_tokens (
                token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL,last_seen_at TEXT)""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_broker_connections_user ON broker_connections(user_id,provider)")

def encrypt_payload(payload: dict) -> str:
    return _fernet().encrypt(json.dumps(payload,separators=(",",":")).encode()).decode()

def decrypt_payload(blob: str) -> dict:
    try: return json.loads(_fernet().decrypt(blob.encode()).decode())
    except (InvalidToken,ValueError,TypeError) as exc:
        raise HTTPException(503,"Unable to decrypt broker credentials. Check that BROKER_ENCRYPTION_KEY has not changed.") from exc

def save_connection(user_id: str, provider: str, label: str, environment: str,
                    secrets_payload: dict, metadata: dict | None = None) -> dict:
    now=datetime.now(timezone.utc); blob=encrypt_payload(secrets_payload)
    metadata_json=json.dumps(metadata or {},separators=(",",":"))
    with connect() as db:
        existing=db.execute("SELECT id FROM broker_connections WHERE user_id=? AND provider=? AND label=?",
                            (user_id,provider,label)).fetchone()
        if existing:
            connection_id=str(existing["id"])
            db.execute("""UPDATE broker_connections SET environment=?,secret_blob=?,metadata_json=?,updated_at=?
                          WHERE id=?""",(environment,blob,metadata_json,now,connection_id))
        else:
            connection_id=str(uuid.uuid4())
            db.execute("""INSERT INTO broker_connections
                (id,user_id,provider,label,environment,secret_blob,metadata_json,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)""",(connection_id,user_id,provider,label,environment,blob,metadata_json,now,now))
    return {"id":connection_id,"provider":provider,"label":label,"environment":environment,"status":"credentials_saved"}

def get_connection(user_id: str, provider: str, label: str | None = None):
    with connect() as db:
        if label:
            row=db.execute("SELECT * FROM broker_connections WHERE user_id=? AND provider=? AND label=?",(user_id,provider,label)).fetchone()
        else:
            row=db.execute("SELECT * FROM broker_connections WHERE user_id=? AND provider=? ORDER BY updated_at DESC LIMIT 1",(user_id,provider)).fetchone()
    if not row: raise HTTPException(404,"No connection found for this provider")
    result=dict(row); result["secrets"]=decrypt_payload(result.pop("secret_blob"))
    result["metadata"]=json.loads(result.pop("metadata_json") or "{}")
    return result

def list_connections(user_id: str):
    with connect() as db:
        rows=db.execute("""SELECT id,provider,label,environment,metadata_json,created_at,updated_at
                           FROM broker_connections WHERE user_id=? ORDER BY provider,label""",(user_id,)).fetchall()
    return [{"id":str(r["id"]),"provider":r["provider"],"label":r["label"],"environment":r["environment"],
             "metadata":json.loads(r["metadata_json"] or "{}"),"created_at":r["created_at"],
             "updated_at":r["updated_at"]} for r in rows]

def delete_connection(user_id: str, connection_id: str):
    with connect() as db:
        row=db.execute("SELECT provider FROM broker_connections WHERE id=? AND user_id=?",(connection_id,user_id)).fetchone()
        if not row: raise HTTPException(404,"Connection not found")
        db.execute("DELETE FROM broker_connections WHERE id=? AND user_id=?",(connection_id,user_id))
        if row["provider"]=="metatrader5": db.execute("DELETE FROM mt5_bridge_tokens WHERE user_id=?",(user_id,))
    return {"ok":True}

def create_oauth_state(user_id: str, provider: str, ttl_seconds: int=600) -> str:
    state=secrets.token_urlsafe(32); now=datetime.now(timezone.utc)
    with connect() as db:
        db.execute("DELETE FROM broker_oauth_states WHERE expires_at<=?",(now,))
        db.execute("INSERT INTO broker_oauth_states (state_hash,user_id,provider,expires_at,created_at) VALUES (?,?,?,?,?)",
                   (hashlib.sha256(state.encode()).hexdigest(),user_id,provider,now+timedelta(seconds=ttl_seconds),now))
    return state

def consume_oauth_state(state: str, provider: str) -> str:
    if not state or len(state)>256: raise HTTPException(400,"Invalid OAuth state")
    digest=hashlib.sha256(state.encode()).hexdigest(); now=datetime.now(timezone.utc)
    with connect() as db:
        row=db.execute("SELECT user_id,provider,expires_at FROM broker_oauth_states WHERE state_hash=?",(digest,)).fetchone()
        db.execute("DELETE FROM broker_oauth_states WHERE state_hash=?",(digest,))
    expires_at=row["expires_at"] if row else now
    if isinstance(expires_at,str):
        expires_at=datetime.fromisoformat(expires_at)
    if not row or row["provider"]!=provider or expires_at<=now:
        raise HTTPException(400,"OAuth state is invalid or expired. Start the connection again.")
    return str(row["user_id"])

def create_mt5_bridge_token(user_id: str) -> str:
    token=secrets.token_urlsafe(40); digest=hashlib.sha256(token.encode()).hexdigest(); now=datetime.now(timezone.utc)
    with connect() as db:
        db.execute("DELETE FROM mt5_bridge_tokens WHERE user_id=?",(user_id,))
        db.execute("INSERT INTO mt5_bridge_tokens (token_hash,user_id,created_at,last_seen_at) VALUES (?,?,?,NULL)",(digest,user_id,now))
    return token

def verify_mt5_bridge_token(token: str) -> str:
    if not token or len(token)>256: raise HTTPException(401,"Invalid bridge token")
    digest=hashlib.sha256(token.encode()).hexdigest(); now=datetime.now(timezone.utc)
    with connect() as db:
        row=db.execute("SELECT user_id FROM mt5_bridge_tokens WHERE token_hash=?",(digest,)).fetchone()
        if row: db.execute("UPDATE mt5_bridge_tokens SET last_seen_at=? WHERE token_hash=?",(now,digest))
    if not row: raise HTTPException(401,"Invalid bridge token")
    return str(row["user_id"])
