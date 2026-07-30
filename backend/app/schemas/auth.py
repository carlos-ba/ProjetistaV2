from uuid import UUID

from pydantic import BaseModel, field_validator, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
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
    email_verified: bool = False


class TokenRefreshRequest(BaseModel):
    refresh: str


class TokenRefreshResponse(BaseModel):
    access: str


class UserOut(BaseModel):
    id: UUID
    username: str
    email: str
    is_active: bool
    email_verified: bool = False
    modo_engenharia: bool = False

    model_config = {"from_attributes": True}


class PreferenciasUpdate(BaseModel):
    modo_engenharia: bool


class MessageResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    nova_senha: str

    @field_validator("nova_senha")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Senha deve ter ao menos 6 caracteres.")
        return v
