from datetime import datetime

from pydantic import BaseModel

class ContractCreate(BaseModel):
    user_id: int
    type_of_contract: str | None
    # date_time_accepted: datetime | None
    is_signature_accepted: bool
    term_content: str | None
    # ip_address: str | None