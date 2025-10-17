from fastapi import APIRouter, Query, Depends, HTTPException
from domain.models.ncm_models import SearchResponse, FilterField
from application.use_cases.ncm_use_cases import ItemsCache, to_api_rows, to_api_details

router = APIRouter(prefix="/itens", tags=["Items"])

def get_cache() -> ItemsCache:
    return ItemsCache()

@router.get("/search", response_model=SearchResponse, summary="Search items from Excel (except TIPI sheet)")
def search_items(
    q: str = Query("", description="Keyword or code (first filter)"),
    field: FilterField = Query("ALL", description="Column for first filter"),
    q2: str = Query("", description="Keyword or code (second filter)", alias="q2"),
    field2: FilterField | None = Query(None, description="Column for second filter", alias="field2"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(15, ge=1, le=200, description="Page size (default 15)"),
    cache: ItemsCache = Depends(get_cache),
):
    """
    Suporta até **dois** filtros combinados com AND.
    - Filtro 1: (field, q) — aceita "ALL"
    - Filtro 2: (field2, q2) — opcional
    """
    try:
        df_filtered = cache.search_multi([(field, q), (field2, q2)])
        # >>> sanitize contra pd.NA para não quebrar Pydantic
        df_filtered = df_filtered.astype(object).where(df_filtered.notna(), "")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Excel file not found in package.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search error: {exc}")

    total_items = int(df_filtered.shape[0])
    total_pages = max(1, (total_items + limit - 1) // limit)
    page = min(max(page, 1), total_pages)

    start = (page - 1) * limit
    end = start + limit
    df_page = df_filtered.iloc[start:end]

    return {
        "page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "data": to_api_rows(df_page),
    }


# ---------------------------
# NOVO ENDPOINT: /itens/details
# ---------------------------
@router.get(
    "/details",
    summary="Retorna DESCRIÇÃO COMPLETA, IBS e CBS por NCM (ou ITEM). Ignora aba de Exceções.",
)
def get_details(
    ncm: str = Query("", description="Código NCM para busca exata (recomendado)"),
    item: str = Query("", description="ITEM alternativo se NCM não for informado"),
    cache: ItemsCache = Depends(get_cache),
):
    """
    Regras:
    - Se 'ncm' informado: busca por igualdade (normalizada) em NCM.
    - Senão, se 'item' informado: busca por igualdade (normalizada) em ITEM.
    - Retorna DESCRIÇÃO COMPLETA, IBS e CBS; inclui também chaves de contexto (ANEXO, ITEM, NCM, DESCRIÇÃO DO PRODUTO).
    - Ignora a(s) aba(s) de Exceções.
    """
    if not (ncm or item):
        raise HTTPException(status_code=400, detail="Informe 'ncm' ou 'item' para pesquisar.")

    try:
        df = cache.find_details(ncm=ncm, item=item)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Excel file not found in package.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Details error: {exc}")

    return {
        "count": int(df.shape[0]),
        "data": to_api_details(df),
    }

