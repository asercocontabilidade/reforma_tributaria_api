from typing import List, Literal, Optional, TypedDict
from typing import List
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict  # pydantic v2


# allowed filter fields
FilterField = Literal[
    "ITEM",
    "DESCRIÇÃO DO PRODUTO",
    "NCM",
    "DESCRIÇÃO TIPI",
    "ALL"
]


class ItemRow(BaseModel):
    # nomes internos pythonic:
    item: str = Field(..., serialization_alias="ITEM")
    descricao_do_produto: str = Field(..., serialization_alias="DESCRIÇÃO DO PRODUTO")
    ncm: str = Field(..., serialization_alias="NCM")
    descricao_tipi: str = Field(..., serialization_alias="DESCRIÇÃO TIPI")
    cst_ibs_e_cbs: str = Field(..., serialization_alias="CST IBS E CBS")
    cclasstrib: str = Field(..., serialization_alias="CCLASSTRIB")

    model_config = ConfigDict(populate_by_name=True)  # permite usar nomes internos


class SearchResponse(BaseModel):
    page: int
    total_pages: int
    total_items: int
    data: List[ItemRow]

    model_config = ConfigDict(populate_by_name=True)


# opcional: se você usa FilterField aqui
from typing import Literal

FilterField = Literal[
    "ITEM",
    "DESCRIÇÃO DO PRODUTO",
    "NCM",
    "DESCRIÇÃO TIPI",
    "ALL",
]

