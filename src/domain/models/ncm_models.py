from typing import List, Literal, Optional, TypedDict
from typing import List
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict  # pydantic v2


# allowed filter fields
FilterField = Literal[
    "ITEM",
    "ANEXO",
    "DESCRIÇÃO DO PRODUTO",
    "NCM",
    "DESCRIÇÃO TIPI",
    "ALL"
]


class RowItem(BaseModel):
    ITEM: Optional[str] = None
    ANEXO: Optional[str] = None
    DESCRIÇÃO_DO_PRODUTO: Optional[str] = None
    NCM: Optional[str] = None
    DESCRIÇÃO_TIPI: Optional[str] = None
    CST_IBS_E_CBS: Optional[float] = None
    CCLASSTRIB: Optional[str] = None
    DESCRIÇÃO_COMPLETA: Optional[str] = None
    REDUÇÃO_IBS: Optional[float] = None
    REDUÇÃO_CBS: Optional[float] = None

class SearchResponse(BaseModel):
    page: int
    total_pages: int
    total_items: int
    data: List[dict]  # mantém como antes


class CstDetailsResponse(BaseModel):
    reduction_percent_ibs: Optional[str] = None
    reduction_percent_cbs: Optional[str] = None
    legal_basis: str = ""