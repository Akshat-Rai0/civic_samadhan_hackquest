from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    mock_id_number: str
    name: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    mock_id_number: str
    otp: str = '123456'

class UserOut(BaseModel):
    id: int
    name: str
    mock_id_number: str
    preferred_lang: str

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
