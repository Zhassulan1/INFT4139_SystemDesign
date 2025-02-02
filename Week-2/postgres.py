# record is 12k rps
import os
import time
import secrets
from datetime import timedelta, datetime, timezone
import dotenv

from pydantic import BaseModel
# import jwt
from fastapi import FastAPI, Request
import psycopg2
import psycopg2.pool


dotenv.load_dotenv()

EXPIRY = timedelta(minutes=120)
TOKEN_LENGTH = 100
PASSWORD = os.getenv('PASSWORD')



pool = psycopg2.pool.SimpleConnectionPool( 
    minconn=36, 
    maxconn=195, 
    user='zhk', 
    password=PASSWORD, 
    host='localhost', 
    port='5432', 
    database='oauth_adr'
)


app = FastAPI()


class User(BaseModel):
    user_id: int


def verify(token: str):
    if len(token) < 1:
        return False, None
    
    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT expiry FROM tokens WHERE token = %s", (token,))
    expiry = cursor.fetchone()
    pool.putconn(conn)
    
    if not expiry:
        return False, None

    if datetime.now(tz=timezone.utc) < expiry[0]:
        return True, expiry[0]
    else:
        return False, expiry[0]    



@app.post("/token")
async def get_token(user: User, req: Request):
    token = req.headers["Authorization"]
    valid, expiry = verify(token)
    if valid and expiry - datetime.now(tz=timezone.utc) > (EXPIRY * 0.25):
        return {"token": token}

    token = secrets.token_hex(TOKEN_LENGTH)
    expiry = datetime.now(tz=timezone.utc) + EXPIRY
    values = (token, user.user_id, expiry)
    
    conn = pool.getconn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tokens (token, user_id, expiry) VALUES (%s, %s, %s)", values)
    conn.commit()
    pool.putconn(conn)
    return {"token": token}


@app.get("/check")
async def check_token(req: Request):
    token = req.headers["Authorization"]
    return {"valid": verify(token)[0]}
