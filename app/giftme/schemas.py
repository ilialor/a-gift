from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict


class ProfilePydantic(BaseModel):
    first_name: str
    last_name: str | None
    date_of_birth: datetime.date | None
    interests: List[str] | None
    contacts: dict | None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserPydantic(BaseModel):
    username: str
    email: str
    profile: ProfilePydantic | None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UsernameIdPydantic(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)
