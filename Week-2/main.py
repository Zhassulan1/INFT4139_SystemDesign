"""
oauth with JWT in fastapi
"""
import os
import datetime
import hashlib

from dotenv import load_dotenv
from pydantic import BaseModel, Field

import jwt
import psycopg2
import psycopg2.pool
import redis
from fastapi import FastAPI, HTTPException, Depends, Header

load_dotenv()
SECRET_KEY = os.getenv("SECRET")
ALGORITHM = os.getenv("ALGORITHM")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
EXPIRE_TIME = 3600
REFRESH_THRESHOLD = int(EXPIRE_TIME * 0.25)

HASH_SALT = os.getenv("HASH_SALT")

app = FastAPI()


class UserRegister(BaseModel):
    """
    model for user registration
    """
    name: str
    password: str
    scopes: str = Field(default="user")

class TokenRequest(BaseModel):
    """
    model for token request
    """
    user_id: int
    password: str

class TokenResponse(BaseModel):
    """
    model for token response
    """
    access_token: str
    token_type: str = "bearer"

class CheckRequest(BaseModel):
    """
    model for check request
    """
    user_id: int


pg_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=30,
    maxconn=90,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)

redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0, max_connections=1000)


@app.on_event("shutdown")
def shutdown_event():
    """
    close the database connection pool on application shutdown
    """
    if pg_pool:
        pg_pool.closeall()
        print("Postgres pool closed")


def create_access_token(data: dict, expires_delta: int = EXPIRE_TIME) -> str:
    """
    create a jwt token
    """
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire, "iat": datetime.datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_authorization_token(authorization: str = Header(...)):
    """
    get the authorization token from the request header
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    return authorization.split(" ")[1]


@app.post("/user")
async def register_user(user: UserRegister):
    """
    register a new user
    """
    conn = pg_pool.getconn()

    cur = conn.cursor()
    hashed_password = hashlib.md5((HASH_SALT + user.password).encode()).hexdigest()
    cur.execute(
        "INSERT INTO users (name, password, scopes) VALUES (%s, %s, %s) RETURNING id",
        (user.name, hashed_password, user.scopes)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    pg_pool.putconn(conn)
    return {"user_id": user_id, "name": user.name, "scopes": user.scopes}


@app.post("/token", response_model=TokenResponse)
async def access_token(token_request: TokenRequest):
    """
    get token for a user
    """
    conn = pg_pool.getconn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, password, name, scopes FROM users WHERE id = %s", 
        (token_request.user_id,)
    )
    result = cur.fetchone()
    if not result:
        raise HTTPException(status_code=401)
    user_id, password, name, scopes = result
    if hashlib.md5((HASH_SALT + token_request.password).encode()).hexdigest() != password:
        raise HTTPException(status_code=401)
    cur.close()
    pg_pool.putconn(conn)

    redis_client = redis.Redis(connection_pool=redis_pool)
    old_token = redis_client.get(user_id)
    if old_token:
        old_token = old_token.decode()
        ttl = redis_client.ttl(old_token)

        if ttl is not None and ttl < REFRESH_THRESHOLD:
            payload = {"user_id": user_id, "name": name, "scopes": scopes}
            new_token = create_access_token(payload)

            redis_client.setex(new_token, EXPIRE_TIME, user_id)
            redis_client.setex(user_id, EXPIRE_TIME, new_token)
            return {"access_token": new_token}
        return {"access_token": old_token}
    payload = {"user_id": user_id, "name": name, "scopes": scopes}
    new_token = create_access_token(payload)

    redis_client.setex(new_token, EXPIRE_TIME, int(user_id))
    redis_client.setex(user_id, EXPIRE_TIME, new_token)
    return {"access_token": new_token}


@app.post("/check")
async def check(check_request: CheckRequest, token: str = Depends(get_authorization_token)):
    """
    check token status
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    scopes = payload.get("scopes")
    if scopes is None:
        return {"status": "inactive", "scope": None}

    redis_client = redis.Redis(connection_pool=redis_pool)
    if int(redis_client.get(token)) == int(check_request.user_id):
        return {"status": "active", "scope": scopes}
    return {"status": "inactive", "scope": None}
