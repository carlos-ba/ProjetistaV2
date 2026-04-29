from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Senha deve ter ao menos 6 caracteres.")
        return v

    @field_validator("username")
    @classmethod
    def username_minimo(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Username deve ter ao menos 3 caracteres.")
        return v.strip()


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access: str
    refresh: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh: str


class TokenRefreshResponse(BaseModel):
    access: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
