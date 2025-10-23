# entities.py
from dataclasses import dataclass
from enum import Enum

class RoleType(str, Enum):
    administrator = "administrator"
    client = "client"

@dataclass(frozen=True)
class UserEntity:
    id: int
    email: str
    cnpj_cpf: str
    ip_address: str | None
    full_name: str | None
    role: RoleType
    is_active: bool
    company_id: int | None
