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



@app.post("/token")
async def get_token(user: User):
    r = redis.Redis(connection_pool=pool)
    data = r.get(user.user_id)
    ttl = r.ttl(user.user_id)

    if data and ttl >= expiry_seconds * 0.25 :
        return {"token": data.decode()}

    token = secrets.token_hex(TOKEN_LENGTH)

    r = redis.Redis(connection_pool=pool)
    r.setex(user.user_id, expiry_seconds, token)
    return {"token": token}


@app.post("/check")
async def check_token(user:User, req: Request):
    token = req.headers["Authorization"]
    r = redis.Redis(connection_pool=pool)
    data = r.get(user.user_id)
    
    if data and data.decode() == token:
        return {"valid": True}
    return {"valid": False}
