from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional
from jose import jwt, JWTError
import os
import uuid
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

class UserLogin(BaseModel):
    mock_id_number: str
    otp: str

class UserCreate(BaseModel):
    mock_id_number: str
    name: str

class UserOut(BaseModel):
    id: int
    mock_id_number: str
    name: str
    session_id: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    session_id: str
    user: UserOut

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        session_id = payload.get("sid", f"SES-2026-{uuid.uuid4().hex[:8].upper()}")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            user = User(id=int(user_id), mock_id_number=f"ID_{user_id}", name="Citizen")
            db.add(user)
            db.commit()
            db.refresh(user)

        return {
            "id": user.id,
            "mock_id_number": user.mock_id_number,
            "name": user.name,
            "session_id": session_id
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login", response_model=LoginResponse)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    if data.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    user = db.query(User).filter(User.mock_id_number == data.mock_id_number).first()
    if not user:
        user = User(mock_id_number=data.mock_id_number, name="Citizen")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    session_id = f"SES-2026-{uuid.uuid4().hex[:8].upper()}"
    token = create_access_token({"sub": str(user.id), "sid": session_id})
    
    user_out = UserOut(
        id=user.id,
        mock_id_number=user.mock_id_number,
        name=user.name,
        session_id=session_id
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        session_id=session_id,
        user=user_out
    )

@router.post("/register", response_model=UserOut)
async def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.mock_id_number == data.mock_id_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
        
    user = User(mock_id_number=data.mock_id_number, name=data.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, mock_id_number=user.mock_id_number, name=user.name)

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=current_user["id"],
        mock_id_number=current_user["mock_id_number"],
        name=current_user["name"],
        session_id=current_user.get("session_id")
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {
        "status": "success",
        "message": f"Session {current_user.get('session_id')} closed successfully."
    }
