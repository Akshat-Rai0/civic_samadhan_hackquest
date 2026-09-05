from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional
from jose import jwt, JWTError
import os

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# Use environment variable or default secret
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

# Mock DB for demo
mock_users_db = {}
next_user_id = 1

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Check mock db
        user = next((u for u in mock_users_db.values() if str(u["id"]) == str(user_id)), None)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
async def login(data: UserLogin):
    if data.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    user = next((u for u in mock_users_db.values() if u["mock_id_number"] == data.mock_id_number), None)
    
    if not user:
        # Auto-create for ease of use in demo if not exists, or just fail
        # The prompt says "Finds or creates a User by mock_id_number"
        global next_user_id
        user = {"id": next_user_id, "mock_id_number": data.mock_id_number, "name": "Citizen"}
        mock_users_db[next_user_id] = user
        next_user_id += 1
        
    token = create_access_token({"sub": str(user["id"])})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register", response_model=UserOut)
async def register(data: UserCreate):
    global next_user_id
    if any(u["mock_id_number"] == data.mock_id_number for u in mock_users_db.values()):
        raise HTTPException(status_code=400, detail="User already exists")
        
    user = {"id": next_user_id, "mock_id_number": data.mock_id_number, "name": data.name}
    mock_users_db[next_user_id] = user
    next_user_id += 1
    return user

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
