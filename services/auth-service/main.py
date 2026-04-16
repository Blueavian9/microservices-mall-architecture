import os, asyncio
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext
from prometheus_fastapi_instrumentator import Instrumentator
from nats.aio.client import Client as NATS
import json

SECRET_KEY = os.getenv("JWT_SECRET", "changeme-in-production")
ALGORITHM  = "HS256"
NATS_URL   = os.getenv("NATS_URL", "nats://nats:4222")

app  = FastAPI(title="auth-service")
pwd  = CryptContext(schemes=["bcrypt"], deprecated="auto")
Instrumentator().instrument(app).expose(app)
nc = NATS()
users_db: dict = {}

@app.on_event("startup")
async def startup():
    await nc.connect(NATS_URL)

@app.on_event("shutdown")
async def shutdown():
    await nc.drain()

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    if req.username in users_db:
        raise HTTPException(400, "Username already exists")
    users_db[req.username] = pwd.hash(req.password)
    await nc.publish(
        "auth.user_registered",
        json.dumps({"username": req.username}).encode()
    )
    return {"message": "registered"}

@app.post("/login")
async def login(req: LoginRequest):
    hashed = users_db.get(req.username)
    if not hashed or not pwd.verify(req.password, hashed):
        raise HTTPException(401, "Invalid credentials")
    token = jwt.encode({"sub": req.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
