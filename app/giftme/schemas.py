from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserFilterPydantic(BaseModel):
    telegram_id: int

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class ProfilePydantic(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    interests: Optional[List[str]] = None
    contacts: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class PaymentCreate(BaseModel):
    user_id: int
    gift_id: int
    amount: float
    telegram_payment_charge_id: str

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None 
    profile: Optional[ProfilePydantic] = None
    telegram_id: int  

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class UserPydantic(BaseModel):
    id: int
    username: str
    email: Optional[str] = None 
    profile: Optional[ProfilePydantic] = None
    telegram_id: int  

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UsernameIdPydantic(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)

class GiftCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    owner_id: int

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class GiftUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class GiftResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    owner_id: int

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class GiftListCreate(BaseModel):
    name: str = Field(..., min_length=1)
    owner_id: int

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class GiftListResponse(BaseModel):
    id: int
    name: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class GiftListUpdate(BaseModel):
    name: Optional[str] = None
    owner_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class UserListCreate(BaseModel):
    user_id: int
    gift_list_id: int
    added_user_id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserListResponse(BaseModel):
    id: int
    user_id: int
    gift_list_id: int
    added_user_id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class DeleteResponse(BaseModel):
    status: str

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
