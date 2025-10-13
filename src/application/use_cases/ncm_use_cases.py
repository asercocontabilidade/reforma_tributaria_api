# application/use_cases/ncm_use_cases.py  (ou onde está seu service)
from __future__ import annotations
import os
import time
import unicodedata
import re
import pandas as pd
from typing import List, Dict, Any, Optional
from importlib.resources import files, as_file  # resolve recurso do pacote

# -----------------------------
# Constantes & regex
# -----------------------------
WANTED_COLUMNS = [
    "ITEM",
    "DESCRIÇÃO DO PRODUTO",
    "NCM",
    "DESCRIÇÃO TIPI",
    "CST IBS E CBS",
    "CCLASSTRIB",
]
IGNORE_SHEETS = {"TIPI"}
SPACE_RE = re.compile(r"\s+", flags=re.UNICODE)
NON_ALNUM_RE = re.compile(r"[^0-9A-Za-zÀ-ÿ]+", flags=re.UNICODE)

# -----------------------------
# Utils de normalização
# -----------------------------
def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def normalize_visible(text):
    if text is None:
        return ""
    t = str(text)
    if t.strip().lower() in {"nan", "none", "nat"}:
        return ""
    t = SPACE_RE.sub(" ", t).strip()
    return t

def normalize_for_compare(text, remove_accents: bool = True) -> str:
    if text is None:
        t = ""
    else:
        t = str(text)
    if t.strip().lower() in {"nan", "none", "nat"}:
        t = ""
    t = SPACE_RE.sub(" ", t).strip()
    if remove_accents:
        t = strip_accents(t)
    t = NON_ALNUM_RE.sub(" ", t)
    t = SPACE_RE.sub(" ", t).strip().lower()
    return t

def _normalize_list_for_compare(vals: list[str], remove_accents: bool = True) -> list[str]:
    """NEW: normaliza uma lista de strings para comparação."""
    return [normalize_for_compare(v, remove_accents=remove_accents) for v in vals]

def map_columns_to_canonical(columns: List[str]) -> dict:
    canon_norm_map = {normalize_for_compare(w, True): w for w in WANTED_COLUMNS}
    mapping = {}
    for col in columns:
        key = normalize_for_compare(col, True)
        if key in canon_norm_map:
            mapping[col] = canon_norm_map[key]
            continue
        for ckey, cname in canon_norm_map.items():
            if key == ckey or key.startswith(ckey) or ckey.startswith(key):
                mapping[col] = cname
                break
    return mapping

def choose_engine(path: str) -> str:
    p = path.lower()
    if p.endswith(".xls"):
        return "xlrd"
    if p.endswith(".xlsx"):
        return "openpyxl"
    return "openpyxl"

def _detect_header_row(raw: pd.DataFrame, max_scan: int = 10) -> int | None:
    """
    NEW: Varre as primeiras `max_scan` linhas procurando um 'header' plausível.
    Considera header se >= 4 colunas baterem (normalizadas) com WANTED_COLUMNS.
    """
    target = set(_normalize_list_for_compare(WANTED_COLUMNS, True))
    n_rows = min(len(raw), max_scan)
    for ridx in range(n_rows):
        row_vals = [str(x) if x is not None else "" for x in list(raw.iloc[ridx].values)]
        row_norm = set(_normalize_list_for_compare(row_vals, True))
        score = sum(1 for x in row_norm if any(x == t or x.startswith(t) or t.startswith(x) for t in target))
        if score >= 4:
            return ridx
    return None

# -----------------------------
# Cache e carregamento
# -----------------------------
class ItemsCache:
    """
    Carrega e cacheia o Excel (todas as abas exceto TIPI) em um DataFrame.
    - Se 'excel_path' for fornecido e existir, usa-o.
    - Caso contrário, resolve o recurso empacotado: infrastructure.spreadsheet_database/Planilha_NCM.xls
    """
    def __init__(
        self,
        excel_path: Optional[str] = None,
        package: str = "infrastructure.spreadsheet_database",
        resource: str = "Planilha_NCM.xls",
    ):
        self._explicit_path = excel_path
        self._package = package
        self._resource = resource

        self._resolved_path: Optional[str] = None
        self._df: Optional[pd.DataFrame] = None
        self._mtime: Optional[float] = None
        self._debug_sheets: Dict[str, Dict[str, Any]] = {}

    # --- path resolution ---
    def _resolve_excel_path(self) -> str:
        if self._explicit_path and os.path.exists(self._explicit_path):
            return self._explicit_path
        try:
            ref = files(self._package) / self._resource
            with as_file(ref) as p:
                return str(p)
        except Exception as exc:
            raise FileNotFoundError(
                f"Could not resolve Excel resource '{self._resource}' in package '{self._package}': {exc}"
            )

    def _needs_reload(self) -> bool:
        try:
            path = self._resolved_path or self._resolve_excel_path()
            mtime = os.path.getmtime(path)
        except FileNotFoundError:
            return True
        return (self._df is None) or (self._mtime != mtime)

    def _normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = map_columns_to_canonical(list(df.columns))
        if mapping:
            df = df.rename(columns=mapping)

        # garante colunas e ordem
        out = pd.DataFrame()
        for c in WANTED_COLUMNS:
            out[c] = df[c] if c in df.columns else ""

        # normalização "visual"
        for c in WANTED_COLUMNS:
            out[c] = out[c].map(normalize_visible)

        # 🔧 CORREÇÃO p/ células mescladas:
        # 1) converte vazio/whitespace em NaN
        cols_to_ffill = ["DESCRIÇÃO DO PRODUTO"]  # adicione "ITEM" se também vier mesclado
        for c in cols_to_ffill:
            if c in out.columns:
                out[c] = out[c].replace(r"^\s*$", pd.NA, regex=True).ffill()

        # 2) se quiser aplicar em todas as colunas (opcional):
        # for c in WANTED_COLUMNS:
        #     out[c] = out[c].replace(r"^\s*$", pd.NA, regex=True).ffill()

        # 3) volta NaN -> ""
        out = out.fillna("")

        # remove linhas totalmente vazias (NCM + descrição vazias)
        empty_mask = (out["NCM"] == "") & (out["DESCRIÇÃO DO PRODUTO"] == "")
        out = out.loc[~empty_mask].reset_index(drop=True)
        return out

    def _load_excel(self) -> pd.DataFrame:
        path = self._resolve_excel_path()
        self._resolved_path = path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Excel not found at: {path}")

        engine = choose_engine(path)
        # Lemos sem header para detectar dinamicamente a linha de cabeçalho
        sheets = pd.read_excel(
            path,
            sheet_name=None,
            engine=engine,
            dtype=str,
            header=None,      # <--- importante
            na_filter=False,  # mantém "" ao invés de NaN
        )

        frames: List[pd.DataFrame] = []
        self._debug_sheets = {}

        for raw_name, raw in sheets.items():
            name = str(raw_name).strip()
            if name.upper() in IGNORE_SHEETS:
                continue

            hdr_idx = _detect_header_row(raw, max_scan=10)
            if hdr_idx is None:
                header_vals = [str(x) if x is not None else "" for x in list(raw.iloc[0].values)]
                body = raw.iloc[1:].copy()
            else:
                header_vals = [str(x) if x is not None else "" for x in list(raw.iloc[hdr_idx].values)]
                body = raw.iloc[hdr_idx + 1:].copy()

            body = body.reset_index(drop=True)

            # Garante mesmo número de colunas entre header e body
            max_cols = max(len(header_vals), body.shape[1])
            while len(header_vals) < max_cols:
                header_vals.append("")
            if body.shape[1] < max_cols:
                for k in range(body.shape[1], max_cols):
                    body[k] = ""

            body.columns = header_vals

            before_rows = int(body.shape[0])
            before_cols = list(map(str, body.columns))

            normalized = self._normalize_df(body)
            after_rows = int(normalized.shape[0])

            self._debug_sheets[name] = {
                "header_row_detected": hdr_idx,
                "rows_before": before_rows,
                "cols_before": before_cols[:20],
                "rows_after": after_rows,
            }

            if after_rows > 0:
                frames.append(normalized)

        if not frames:
            return pd.DataFrame(columns=WANTED_COLUMNS)

        df_all = pd.concat(frames, ignore_index=True)
        df_all = self._normalize_df(df_all)
        return df_all

    def df(self) -> pd.DataFrame:
        if self._needs_reload():
            df = self._load_excel()
            try:
                self._mtime = os.path.getmtime(self._resolved_path or "")
            except Exception:
                self._mtime = time.time()
            self._df = df
        return self._df.copy()

    def search(self, q: str, field: Optional[str], remove_accents: bool = True) -> pd.DataFrame:
        df = self.df()
        q_norm = normalize_for_compare(q or "", remove_accents=remove_accents)
        if not q_norm:
            return df

        def series_norm(s: pd.Series) -> pd.Series:
            return s.map(lambda x: normalize_for_compare(x, remove_accents=remove_accents))

        search_cols = ["ITEM", "DESCRIÇÃO DO PRODUTO", "NCM", "DESCRIÇÃO TIPI"]

        if not field or field.upper() == "ALL":
            mask = None
            for col in search_cols:
                if col in df.columns:
                    part = series_norm(df[col]).str.contains(q_norm, na=False, regex=False)  # regex=False
                    mask = part if mask is None else (mask | part)
            return df.loc[mask] if mask is not None else df.iloc[0:0]

        # coluna específica (tolerante a variações)
        col_map = map_columns_to_canonical([field])
        canon = col_map.get(field, field)
        if canon not in df.columns:
            return df.iloc[0:0]
        return df.loc[series_norm(df[canon]).str.contains(q_norm, na=False, regex=False)]

    # Debug opcional
    def debug_info(self) -> Dict[str, Any]:
        path = self._resolved_path or self._resolve_excel_path()
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        engine = choose_engine(path)
        return {
            "resolved_path": path,
            "exists": exists,
            "size_bytes": size,
            "engine_guess": engine,
            "sheets_loaded": self._debug_sheets,
            "total_rows_after_concat": int(self._df.shape[0]) if self._df is not None else 0,
            "columns_final": list(self._df.columns) if self._df is not None else WANTED_COLUMNS,
        }

    # dentro da classe ItemsCache

    def search_multi(
            self,
            filters: list[tuple[str | None, str | None]],
            remove_accents: bool = True
    ) -> pd.DataFrame:
        """
        Aplica 1 ou 2 filtros em AND.
        Cada filtro: (field, q)
          - field pode ser None ou "ALL"
          - q pode ser None/"" -> ignorado
        Se nenhum filtro for válido, retorna DF completo.
        """
        df = self.df()

        def series_norm(s: pd.Series) -> pd.Series:
            return s.map(lambda x: normalize_for_compare(x, remove_accents=remove_accents))

        def mask_for(field: str | None, q: str | None) -> pd.Series | None:
            q_norm = normalize_for_compare(q or "", remove_accents=remove_accents)
            if not q_norm:
                return None
            search_cols = ["ITEM", "DESCRIÇÃO DO PRODUTO", "NCM", "DESCRIÇÃO TIPI"]
            # ALL -> busca em todas as colunas alvo
            if not field or field.upper() == "ALL":
                m = None
                for col in search_cols:
                    if col in df.columns:
                        part = series_norm(df[col]).str.contains(q_norm, na=False, regex=False)
                        m = part if m is None else (m | part)
                return m
            # coluna específica (tolerante)
            col_map = map_columns_to_canonical([field])
            canon = col_map.get(field, field)
            if canon not in df.columns:
                return None
            return series_norm(df[canon]).str.contains(q_norm, na=False, regex=False)

        masks = []
        for f, q in filters[:2]:  # máximo 2
            m = mask_for(f, q)
            if m is not None:
                masks.append(m)

        if not masks:
            return df
        # AND entre máscaras
        combined = masks[0]
        for m in masks[1:]:
            combined = combined & m
        return df.loc[combined]

def to_api_rows(df_page: pd.DataFrame) -> list[dict]:
    """Retorna dicts com chaves internas pythonic; FastAPI/Pydantic serializa com aliases."""
    out = []
    for _, r in df_page.iterrows():
        out.append({
            "item": r.get("ITEM", ""),
            "descricao_do_produto": r.get("DESCRIÇÃO DO PRODUTO", ""),
            "ncm": r.get("NCM", ""),
            "descricao_tipi": r.get("DESCRIÇÃO TIPI", ""),
            "cst_ibs_e_cbs": r.get("CST IBS E CBS", ""),
            "cclasstrib": r.get("CCLASSTRIB", ""),
        })
    return out








