from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CustomerBase(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    cnae_company: Optional[str] = None
    tax_regime: Optional[str] = None
    erp_code: Optional[str] = None
    user_id: Optional[int] = None