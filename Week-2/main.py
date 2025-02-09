import os
import datetime
# from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

import jwt
import psycopg2
from psycopg2 import pool
import redis
from fastapi import FastAPI, HTTPException, Depends, Header
from passlib.context import CryptContext
# from fastapi.security import OAuth2PasswordBearer


load_dotenv()
SECRET_KEY = os.getenv("SECRET")
ALGORITHM = os.getenv("ALGORITHM")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
ACCESS_TOKEN_EXPIRE_SECONDS = 3600
REFRESH_THRESHOLD = int(ACCESS_TOKEN_EXPIRE_SECONDS * 0.25)

# The password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()


class UserRegister(BaseModel):
    name: str
    password: str
    scopes: str = Field(default="user", description="Comma-separated list of permission scopes.")

class TokenRequest(BaseModel):
    user_id: int
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CheckRequest(BaseModel):
    user_id: int


pg_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=36,
    maxconn=195,
    user=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)

redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0, max_connections=1000)


@app.on_event("shutdown")
def shutdown_event():
    if pg_pool:
        pg_pool.closeall()
        print("Postgres pool closed")


def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_SECONDS) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire, "iat": datetime.datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_authorization_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    return authorization.split(" ")[1]


@app.post("/user")
async def register_user(user: UserRegister):
    conn = pg_pool.getconn()

    # try:
    cur = conn.cursor()
    # Hash the password before storing it in the database.
    hashed_password = pwd_context.hash(user.password)
    cur.execute(
        "INSERT INTO users (name, password, scopes) VALUES (%s, %s, %s) RETURNING id",
        (user.name, hashed_password, user.scopes)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    # except Exception as e:
        # conn.rollback()
        # raise HTTPException(status_code=500, detail=str(e))
    # finally:
    cur.close()
    pg_pool.putconn(conn)
    return {"user_id": user_id, "name": user.name, "scopes": user.scopes}


@app.post("/token", response_model=TokenResponse)
async def login_for_access_token(token_request: TokenRequest):
    # Authenticate a user using their id and password and return a JWT token.

    conn = pg_pool.getconn()

    # try:
    cur = conn.cursor()
    cur.execute("SELECT id, password, name, scopes FROM users WHERE id = %s", (token_request.user_id,))
    result = cur.fetchone()
    if not result:
        raise HTTPException(status_code=401, detail="Invalid user id or password")
    user_id, stored_password, name, scopes = result
    
    if not pwd_context.verify(token_request.password, stored_password):
        raise HTTPException(status_code=401, detail="Invalid user id or password")
    # except Exception as e:
        # print(f"Error verifying user credentials: {e}")
        # raise HTTPException(status_code=500, detail=str(e))
    # finally:
    cur.close()
    pg_pool.putconn(conn)

    # Redis, check for an existing token.
    # global redis_client
    redis_client = redis.Redis(connection_pool=redis_pool)
    old_token = redis_client.get(user_id)

    if old_token:
        old_token = old_token.decode('utf-8')
        ttl = redis_client.ttl(old_token)

        if ttl is not None and ttl < REFRESH_THRESHOLD:
            payload = {"user_id": user_id, "name": name, "scopes": scopes}
            new_token = create_access_token(payload)

            redis_client.setex(new_token, ACCESS_TOKEN_EXPIRE_SECONDS, user_id)
            redis_client.setex(user_id, ACCESS_TOKEN_EXPIRE_SECONDS, new_token)
            return {"access_token": new_token}
        else:
            # Return the still-valid token.
            return {"access_token": old_token}
    else:
        payload = {"user_id": user_id, "name": name, "scopes": scopes}
        new_token = create_access_token(payload)

        redis_client.setex(new_token, ACCESS_TOKEN_EXPIRE_SECONDS, int(user_id))
        redis_client.setex(user_id, ACCESS_TOKEN_EXPIRE_SECONDS, new_token)
        return {"access_token": new_token}


@app.post("/check")
async def check_token(check_request: CheckRequest, token: str = Depends(get_authorization_token)):
    """
    Verify that a token is valid.
    
    The token is expected to be sent in the Authorization header (e.g., "Bearer <token>").
    The endpoint decodes the JWT and confirms that it exists in Redis.
    Returns only the token status and the user's scopes if the token is valid.
    """
    try:
        # Decode and verify token (this checks signature and expiration).
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        scopes = payload.get("scopes")
        if scopes is None:
            return {"status": "inactive", "scope": None}
            # raise HTTPException(status_code=401, detail="Invalid token payload")
    # except jwt.ExpiredSignatureError:
        # raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        return {"status": "inactive", "scope": None}
        # raise HTTPException(status_code=401, detail="Token verification failed")

    redis_client = redis.Redis(connection_pool=redis_pool)
    if int(redis_client.get(token)) == check_request.user_id:
        return {"status": "active", "scope": scopes}
    else:
        return {"status": "inactive", "scope": None}
        # raise HTTPException(status_code=401, detail="Token not found or expired in store")







# def get_pg_conn():
#     """
#     Get a connection from the Postgres pool.
#     """
#     global pg_pool
#     if not pg_pool:
#         print("\n\n\n ERROR: Postgres pool not initialized\n\n\n")
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail="Postgres pool not initialized")
#     try:
#         conn = pg_pool.getconn()
#         return conn
#     except Exception as e:
#         print("\n\n\nException in get_pg_conn:")
#         print(e)
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail="Error getting DB connection")


# def release_pg_conn(conn):
#     """
#     Return a connection to the Postgres pool.
#     """
#     global pg_pool
#     if pg_pool and conn:
#         pg_pool.putconn(conn)








# Startup and Shutdown events
# @app.on_event("startup")
# def startup_event():
    # global pg_pool, redis_client
    # # Initialize PostgreSQL connection pool.
    # try:
    #     pg_pool = psycopg2.pool.SimpleConnectionPool(
    #         minconn=20,
    #         maxconn=95,
    #         dsn=f"dbname={DB_NAME} user={DB_USERNAME} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
    #     )
    #     print("Postgres pool created")
    # except Exception as e:
    #     print("Error initializing Postgres pool:", e)
    #     raise e

    # Initialize Redis connection pool.
    # try:
    #     redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    #     redis_client = redis.Redis(connection_pool=redis_pool)
    #     print("Redis client created")
    # except Exception as e:
    #     print("Error initializing Redis client:", e)
    #     raise e
