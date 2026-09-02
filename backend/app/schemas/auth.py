import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, field_validator, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    telefone: str

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

    @field_validator("telefone")
    @classmethod
    def telefone_valido(cls, v: str) -> str:
        # Só dígitos, DDD + número (10 = fixo, 11 = celular com 9º dígito) — sem
        # exigir formatação específica do usuário (aceita com ou sem máscara).
        digitos = re.sub(r"\D", "", v or "")
        if len(digitos) not in (10, 11):
            raise ValueError("Telefone inválido — informe DDD + número.")
        return digitos


class UserLogin(BaseModel):
    username: str
    password: str


class EncerrarSessaoLoginRequest(BaseModel):
    username: str
    password: str
    sessao_id: UUID


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
    # Multi-tenancy: o escopo dos dados é a empresa; o id do usuário é só autoria
    empresa_id: UUID | None = None
    papel: str = "admin_empresa"
    empresa_nome: str | None = None
    empresa_plano: str | None = None
    empresa_status: str | None = None
    empresa_assinatura_fim: date | None = None
    empresa_trial_expirado: bool = False
    empresa_recursos_avancados_habilitados: bool = False

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
