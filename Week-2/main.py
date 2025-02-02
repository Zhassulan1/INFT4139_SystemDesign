import time
import secrets

from pydantic import BaseModel
from fastapi import FastAPI, Request

import redis

expiry_seconds = 3600
TOKEN_LENGTH = 50


app = FastAPI()

pool = redis.ConnectionPool(host='localhost', port=6379, db=0, max_connections=1000)

class User(BaseModel):
    user_id: int

def verify(token: str):
    r = redis.Redis(connection_pool=pool)
    data = r.get(token)
    if data:
        return True, r.ttl(token)
    return False, None


@app.post("/token")
async def get_token(user: User, req: Request):
    token = req.headers["Authorization"]
    valid, ttl = verify(token)

    if valid and ttl >= expiry_seconds * 0.25 :
        return {"token": token}

    token = secrets.token_hex(TOKEN_LENGTH)

    r = redis.Redis(connection_pool=pool)
    r.setex(token, expiry_seconds, user.user_id)
    return {"token": token}


@app.get("/check")
async def check_token(req: Request):
    token = req.headers["Authorization"]
    return {"valid": verify(token)[0]}
