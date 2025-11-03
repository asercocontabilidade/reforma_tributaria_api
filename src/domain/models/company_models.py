from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from typing import Literal
from enum import Enum

class RoleType(str, Enum):
    administrator = "basic"
    client = "pro"

class CompanyCreate(BaseModel):
    customer_name: str | None = None
    role: RoleType
    company_name: str | None = None
    phone_number: str | None = None
    address: str | None = None
    contract_start_date: datetime | None = None
    contract_end_date: datetime | None = None
    cnae_company: str | None = None
    tax_regime: str | None = None
    erp_code: str | None = None
    monthly_value: float | None = None

class CompanyRead(BaseModel):
    id: int
    customer_name: str | None = None
    role: RoleType
    company_name: str | None = None
    phone_number: str | None = None
    address: str | None = None
    contract_start_date: datetime | None = None
    contract_end_date: datetime | None = None
    cnae_company: str | None = None
    tax_regime: str | None = None
    erp_code: str | None = None
    monthly_value: float | None = None
