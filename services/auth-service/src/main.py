from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from pydantic import BaseModel, EmailStr
import datetime, asyncio
from prometheus_fastapi_instrumentator import Instrumentator

from .db import init_db, get_db, User
from .config import settings
from .nats_client import publish

app = FastAPI(title="auth-service")
Instrumentator().instrument(app).expose(app)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}

@app.post("/register", status_code=201)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=req.email, hashed_password=pwd_ctx.hash(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    await publish("auth.user_registered", {"userId": str(user.id), "email": user.email})
    return {"id": str(user.id), "email": user.email}

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not pwd_ctx.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.jwt_expire_minutes)},
        settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return {"access_token": token, "token_type": "bearer"}
