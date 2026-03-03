from pydantic import BaseModel


class GoogleLoginRequest(BaseModel):
    token: str


class AppleLoginRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str
