
from pydantic import BaseModel, Field

class STokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Токен обновления")

class STokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
