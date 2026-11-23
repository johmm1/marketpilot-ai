"""Cookie-based authentication with persistent SQLite/PostgreSQL storage."""
import hashlib, hmac, re, secrets, uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Response
from .db import connect

SESSION_COOKIE = "marketpilot_session"
SESSION_DAYS = 7
PBKDF2_ITERATIONS = 310_000

def initialize_auth():
    with connect() as db:
        if not db.is_postgres:
            db.execute("""CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL, created_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS user_sessions (
                token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
                expires_at TEXT NOT NULL, created_at TEXT NOT NULL)""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id)")

def _hash_password(password, salt=None):
    salt=salt or secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,PBKDF2_ITERATIONS)
    return "pbkdf2_sha256$"+str(PBKDF2_ITERATIONS)+"$"+salt.hex()+"$"+digest.hex()

def _verify_password(password, stored):
    try:
        scheme,iterations,salt_hex,digest_hex=stored.split("$")
        if scheme!="pbkdf2_sha256": return False
        candidate=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt_hex),int(iterations))
        return hmac.compare_digest(candidate.hex(),digest_hex)
    except (ValueError,TypeError): return False

def _new_session(user_id,response,secure):
    token=secrets.token_urlsafe(48); now=datetime.now(timezone.utc); expires=now+timedelta(days=SESSION_DAYS)
    with connect() as db:
        db.execute("INSERT INTO user_sessions (token_hash,user_id,expires_at,created_at) VALUES (?,?,?,?)",
                   (hashlib.sha256(token.encode()).hexdigest(),user_id,expires,now))
        db.execute("DELETE FROM user_sessions WHERE expires_at <= ?",(now,))
    response.set_cookie(SESSION_COOKIE,token,httponly=True,secure=secure,
        samesite="none" if secure else "lax",max_age=SESSION_DAYS*86400,path="/")

def register(email,password,response,secure):
    email=email.strip().lower()
    if len(email)>254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email):
        raise HTTPException(400,"Enter a valid email address")
    if len(password)<12 or len(password)>128:
        raise HTTPException(400,"Password must be 12–128 characters")
    user_id=str(uuid.uuid4()); now=datetime.now(timezone.utc)
    try:
        with connect() as db:
            db.execute("INSERT INTO users (id,email,password_hash,created_at) VALUES (?,?,?,?)",
                       (user_id,email,_hash_password(password),now))
    except Exception as exc:
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(409,"An account with this email already exists")
        raise
    _new_session(user_id,response,secure)
    return {"id":user_id,"email":email,"created_at":now}

def login(email,password,response,secure):
    with connect() as db:
        user=db.execute("SELECT * FROM users WHERE lower(email)=lower(?)",(email.strip(),)).fetchone()
    if not user or not _verify_password(password,user["password_hash"]):
        raise HTTPException(401,"Invalid email or password")
    _new_session(str(user["id"]),response,secure)
    return {"id":str(user["id"]),"email":user["email"],"created_at":user["created_at"]}

def current_user(request: Request):
    token=request.cookies.get(SESSION_COOKIE)
    if not token: raise HTTPException(401,"Please sign in")
    token_hash=hashlib.sha256(token.encode()).hexdigest(); now=datetime.now(timezone.utc)
    with connect() as db:
        row=db.execute("""SELECT users.id,users.email,users.created_at FROM user_sessions
            JOIN users ON users.id=user_sessions.user_id
            WHERE user_sessions.token_hash=? AND user_sessions.expires_at>?""",(token_hash,now)).fetchone()
    if not row: raise HTTPException(401,"Session expired. Please sign in again")
    return {**dict(row),"id":str(row["id"])}

def logout(request: Request,response: Response,secure: bool):
    token=request.cookies.get(SESSION_COOKIE)
    if token:
        with connect() as db:
            db.execute("DELETE FROM user_sessions WHERE token_hash=?",(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie(SESSION_COOKIE,path="/",httponly=True,secure=secure,samesite="none" if secure else "lax")
    return {"ok":True}
