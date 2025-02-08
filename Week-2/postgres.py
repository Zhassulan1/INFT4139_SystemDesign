# record 22k rps

import os
import secrets
import dotenv
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel
from fastapi import FastAPI, Request
import psycopg2
import psycopg2.pool

dotenv.load_dotenv()

EXPIRY_SECONDS = 3600
TOKEN_LENGTH = 50
PASSWORD = os.getenv('PASSWORD')

pool = psycopg2.pool.SimpleConnectionPool(
    minconn=6,
    maxconn=50,
    user='zhk',
    password=PASSWORD,
    host='localhost',
    port='5432',
    database='oauth_adr'
)

app = FastAPI()

class User(BaseModel):
    user_id: int


# def verify(user_id: int, token: str):
#     conn = pool.getconn()
#     cursor = conn.cursor()
#     cursor.execute("SELECT token, expiry FROM tokens WHERE user_id = %s", (user_id,))
#     record = cursor.fetchone()
#     pool.putconn(conn)
    
#     if record and record[0] == token and record[1] > datetime.now(tz=timezone.utc):
#         return True, (record[1] - datetime.now(tz=timezone.utc)).total_seconds()
#     return False, None


# @app.get("/user_id")
# def get_user_id():
#     conn = pool.getconn()
#     cursor = conn.cursor()
#     cursor.execute("SELECT COALESCE(MAX(user_id), 1) + 1 FROM tokens")
#     user_id = cursor.fetchone()[0]
#     cursor.execute(
#         "INSERT INTO tokens (user_id, token, expiry) VALUES (%s, %s, %s)", 
#         (user_id, "", datetime.now(tz=timezone.utc))
#     )
#     pool.putconn(conn)
#     return {"user_id": user_id}


@app.post("/token")
async def get_token(user: User):
    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT token, expiry FROM tokens WHERE user_id = %s", (user.user_id,))
    record = cursor.fetchone()
    
    if record and (record[1] - datetime.now(tz=timezone.utc)).total_seconds() >= EXPIRY_SECONDS * 0.25:
        pool.putconn(conn)
        return {"token": record[0]}

    token = secrets.token_hex(TOKEN_LENGTH)
    expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=EXPIRY_SECONDS)
    cursor.execute("INSERT INTO tokens (user_id, token, expiry) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET token = EXCLUDED.token, expiry = EXCLUDED.expiry", (user.user_id, token, expiry))
    # cursor.execute("DELETE FROM tokens WHERE user_id = %s", (user.user_id,))
    # conn.commit()

    # cursor.execute("INSERT INTO tokens (user_id, token, expiry) VALUES (%s, %s, %s)", (user.user_id, token, expiry))
    conn.commit()
    
    pool.putconn(conn)
    return {"token": token}


@app.post("/check")
async def check_token(user: User, req: Request):
    token = req.headers["Authorization"]

    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT token, expiry FROM tokens WHERE user_id = %s", (user.user_id,))
    record = cursor.fetchone()
    pool.putconn(conn)
    
    if record and record[0] == token and record[1] > datetime.now(tz=timezone.utc):
        return {"valid": True}
    return {"valid": False}