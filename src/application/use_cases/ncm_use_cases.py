# application/use_cases/ncm_use_cases.py
from __future__ import annotations
import os
import time
import unicodedata
import re
from typing import List, Dict, Any, Optional

import pandas as pd
from importlib.resources import files, as_file  # resolve recurso do pacote

# -----------------------------
# Constantes & regex
# -----------------------------
WANTED_COLUMNS = [
    "ITEM",
    "ANEXO",
    "DESCRIÇÃO DO PRODUTO",
    "NCM",
    "DESCRIÇÃO TIPI",
    "CST IBS E CBS",
    "CCLASSTRIB",
    # >>> NOVAS COLUNAS
    "DESCRIÇÃO COMPLETA",
    "IBS",
    "CBS",
]

# Ignorar apenas TIPI (NÃO ignore Exceções)
IGNORE_SHEETS = {"TIPI"}

SPACE_RE = re.compile(r"\s+", flags=re.UNICODE)
NON_ALNUM_RE = re.compile(r"[^0-9A-Za-zÀ-ÿ]+", flags=re.UNICODE)

# Detector de texto jurídico (“Art…”, parágrafo, inciso…)
LEGAL_TEXT_RE = re.compile(
    r"""(?ix)
    ^\s*
    (art(igo)?\.?|art[ºo]?)      # Art., Artigo, Artº, Arto
    [\s\-]*\d+                    # número do artigo
    | \s*§                        # parágrafo
    | \binciso\b | \bal[ií]nea\b | \bcap[uú]t\b
    """,
)

# -----------------------------
# Utils
# -----------------------------
def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def normalize_visible(text):
    if text is None:
        return ""
    try:
        if pd.isna(text):
            return ""
    except Exception:
        pass
    t = str(text)
    low = t.strip().lower()
    if low in {"nan", "none", "nat", "<na>", "<nan>", "<null>"}:
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
    return [normalize_for_compare(v, remove_accents=remove_accents) for v in vals]

def map_columns_to_canonical(columns: List[str]) -> dict:
    canon_norm_map = {normalize_for_compare(w, True): w for w in WANTED_COLUMNS}
    synonyms = {
        "descricao completa": "DESCRIÇÃO COMPLETA",
        "descricao do produto completa": "DESCRIÇÃO COMPLETA",
        "descricao_produto_completa": "DESCRIÇÃO COMPLETA",
        "base legal": "DESCRIÇÃO COMPLETA",   # 👈 importante para a aba de exceções

        "ibs,cbs": "CST IBS E CBS",
        "cst ibs cbs": "CST IBS E CBS",

        "descricao tipi": "DESCRIÇÃO TIPI",
        "descricao da tipi": "DESCRIÇÃO TIPI",
        "descricao_tipi": "DESCRIÇÃO TIPI",
        "desc tipi": "DESCRIÇÃO TIPI",

        "ibs": "IBS",
        "cbs": "CBS",
    }
    for k, v in synonyms.items():
        canon_norm_map[normalize_for_compare(k, True)] = v

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
# Helpers para ANEXO
# -----------------------------
_STANDALONE_ROMAN = re.compile(r"\b([IVXLCDM]+)\b", re.IGNORECASE)

def _to_roman(num: int) -> str:
    if num <= 0 or num >= 4000:
        return str(num)
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    out = []
    for v, sym in vals:
        while num >= v:
            out.append(sym)
            num -= v
    return "".join(out)

def _extract_anexo_token(sheet_name: str) -> str:
    name = (sheet_name or "").strip()
    m = re.search(r"\banexo\S*[\s:–—\-]*(\d{1,4})\b", name, flags=re.IGNORECASE)
    if m:
        try:
            return _to_roman(int(m.group(1)))
        except Exception:
            pass
    romans = _STANDALONE_ROMAN.findall(name)
    if romans:
        return romans[-1].upper()
    return "-"

def _extract_anexo_label(sheet_name: str) -> str:
    token = _extract_anexo_token(sheet_name)
    return f"Anexo {token}" if token != "-" else "-"

def _is_long_header_text(s: str) -> bool:
    if not s:
        return False
    t = str(s).strip()
    return (len(t) >= 40) and any(ch.isalpha() for ch in t)

# -----------------------------
# Cache e carregamento
# -----------------------------
class ItemsCache:
    """
    Em 'Exceções':
      - Move texto jurídico que cair em ITEM -> DESCRIÇÃO COMPLETA (mesmo com NCM presente)
      - Cria blocos por linha-âncora (DESCRIÇÃO COMPLETA != "" e NCM == "")
      - Ffill dentro do bloco **apenas** DESCRIÇÃO COMPLETA e DESCRIÇÃO TIPI
      - Não propaga ITEM/Descrição do Produto; colunas vazias permanecem vazias
      - Remove linhas-âncora “puras” (sem NCM, ITEM e DESCRIÇÃO DO PRODUTO vazios)
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

    def _normalize_df(self, df: pd.DataFrame, *, exceptions_mode: bool = False) -> pd.DataFrame:
        # 1) Renomeia
        mapping = map_columns_to_canonical(list(df.columns))
        if mapping:
            df = df.rename(columns=mapping)

        # 2) Junta colunas duplicadas
        out = pd.DataFrame()
        for c in WANTED_COLUMNS:
            if c not in df.columns:
                out[c] = ""
                continue
            same_named_cols = [col for col in df.columns if col == c]
            if len(same_named_cols) == 1:
                out[c] = df[same_named_cols[0]]
            else:
                merged = (
                    df[same_named_cols]
                    .replace(r"^\s*$", pd.NA, regex=True)
                    .bfill(axis=1)
                    .iloc[:, 0]
                )
                out[c] = merged

        # 3) Normalização visual
        for c in WANTED_COLUMNS:
            if c in out.columns:
                out[c] = out[c].map(normalize_visible)

        # 4) Preenchimentos
        if not exceptions_mode:
            # === MODO NORMAL ===
            for c in ["ITEM", "DESCRIÇÃO DO PRODUTO", "DESCRIÇÃO COMPLETA"]:
                if c in out.columns:
                    out[c] = out[c].replace(r"^\s*$", pd.NA, regex=True)
            for c in ["ITEM", "DESCRIÇÃO DO PRODUTO"]:
                if c in out.columns:
                    out[c] = out[c].ffill()
            if "DESCRIÇÃO COMPLETA" in out.columns:
                if "ANEXO" in out.columns and "ITEM" in out.columns:
                    out["DESCRIÇÃO COMPLETA"] = (
                        out.groupby(["ANEXO", "ITEM"])["DESCRIÇÃO COMPLETA"]
                        .transform(lambda s: s.ffill().bfill())
                    )
                else:
                    out["DESCRIÇÃO COMPLETA"] = out["DESCRIÇÃO COMPLETA"].ffill().bfill()
            for c in out.columns:
                out[c] = out[c].fillna("")
        else:
            # === MODO EXCEÇÕES ===
            # 4.1) mover texto jurídico do ITEM -> DESCRIÇÃO COMPLETA (sempre que possível)
            if "ITEM" in out.columns and "DESCRIÇÃO COMPLETA" in out.columns:
                item_s = out["ITEM"].astype(str)
                move_mask = item_s.str.contains(LEGAL_TEXT_RE, na=False) & \
                            (out["DESCRIÇÃO COMPLETA"].astype(str).str.strip() == "")
                out.loc[move_mask, "DESCRIÇÃO COMPLETA"] = item_s.loc[move_mask].values
                out.loc[move_mask, "ITEM"] = ""

            # 4.2) define âncora de bloco: linha com DESCRIÇÃO COMPLETA != "" e NCM == ""
            descc_s = out.get("DESCRIÇÃO COMPLETA", pd.Series([""]*len(out))).astype(str).str.strip()
            ncm_s   = out.get("NCM", pd.Series([""]*len(out))).astype(str).str.strip()
            anchor_mask = (descc_s != "") & (ncm_s == "")

            # 4.3) block_id por cumulativo de âncoras
            block_id = anchor_mask.astype(int).cumsum()
            out["__BLOCK_ID"] = block_id

            # 4.4) propaga por bloco apenas DESCRIÇÃO COMPLETA e DESCRIÇÃO TIPI
            for col in ["DESCRIÇÃO COMPLETA", "DESCRIÇÃO TIPI"]:
                if col in out.columns:
                    out[col] = (
                        out.groupby("__BLOCK_ID")[col]
                        .apply(lambda s: s.replace(r"^\s*$", pd.NA, regex=True).ffill())
                        .fillna("")
                        .values
                    )

            # 4.5) fallback para TIPI em exceções (há planilhas sem âncoras formais)
            if "DESCRIÇÃO TIPI" in out.columns:
                out["DESCRIÇÃO TIPI"] = (
                    out["DESCRIÇÃO TIPI"]
                    .replace(r"^\s*$", pd.NA, regex=True)
                    .ffill()
                    .fillna("")
                )

            # 4.6) NÃO propagar ITEM/Descrição do Produto (permanece como veio)
            for c in out.columns:
                out[c] = out[c].fillna("")

            # 4.7) remover âncoras “puras” (sem NCM/ITEM/DESC PRODUTO)
            only_anchor = anchor_mask & \
                          out.get("ITEM", "").astype(str).str.strip().eq("") & \
                          out.get("DESCRIÇÃO DO PRODUTO", "").astype(str).str.strip().eq("")
            out = out.loc[~only_anchor].reset_index(drop=True)

            if "__BLOCK_ID" in out.columns:
                del out["__BLOCK_ID"]

        # 5) Remove linhas totalmente vazias
        empty_mask = (
            (out.get("NCM", "") == "") &
            (out.get("DESCRIÇÃO DO PRODUTO", "") == "") &
            (out.get("DESCRIÇÃO COMPLETA", "") == "")
        )
        out = out.loc[~empty_mask].reset_index(drop=True)

        # 6) rastro opcional
        if "__SHEET_TAG" in df.columns:
            out["__SHEET_TAG"] = df["__SHEET_TAG"].iloc[:len(out)].fillna("").values

        return out

    def _load_excel(self) -> pd.DataFrame:
        path = self._resolve_excel_path()
        self._resolved_path = path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Excel not found at: {path}")

        engine = choose_engine(path)
        sheets = pd.read_excel(
            path,
            sheet_name=None,
            engine=engine,
            dtype=str,
            header=None,      # detecta cabeçalho dinamicamente
            na_filter=False,
        )

        frames: List[pd.DataFrame] = []
        self._debug_sheets = {}

        for raw_name, raw in sheets.items():
            name = str(raw_name).strip()
            upper_name = strip_accents(name).upper()

            # Ignora apenas TIPI
            if name.upper() in IGNORE_SHEETS:
                continue

            is_exceptions = "EXCE" in upper_name  # Exceções/Excecoes

            hdr_idx = _detect_header_row(raw, max_scan=10)
            if hdr_idx is None:
                header_vals = [str(x) if x is not None else "" for x in list(raw.iloc[0].values)]
                body = raw.iloc[1:].copy()
            else:
                header_vals = [str(x) if x is not None else "" for x in list(raw.iloc[hdr_idx].values)]
                body = raw.iloc[hdr_idx + 1:].copy()

            body = body.reset_index(drop=True)

            # equaliza colunas
            max_cols = max(len(header_vals), body.shape[1])
            while len(header_vals) < max_cols:
                header_vals.append("")
            if body.shape[1] < max_cols:
                for k in range(body.shape[1], max_cols):
                    body[k] = ""
            body.columns = header_vals

            # Em Exceções NÃO inferir "DESCRIÇÃO COMPLETA" por cabeçalho longo
            if "DESCRIÇÃO COMPLETA" not in body.columns and not is_exceptions:
                long_headers = [(i, h) for i, h in enumerate(header_vals) if _is_long_header_text(h)]
                if long_headers:
                    chosen_idx, chosen_text = max(long_headers, key=lambda x: len(str(x[1])))
                    body["DESCRIÇÃO COMPLETA"] = str(chosen_text).strip()

            # ANEXO
            if "TRIBUT" in upper_name:
                anexo_label = "Tributado"
            else:
                anexo_label = "Exceções" if is_exceptions else _extract_anexo_label(name)
            body["ANEXO"] = anexo_label

            # rastro opcional
            body["__SHEET_TAG"] = ("EXC::" + name) if is_exceptions else ("ANX::" + anexo_label)

            before_rows = int(body.shape[0])
            before_cols = list(map(str, body.columns))

            normalized = self._normalize_df(body, exceptions_mode=is_exceptions)

            after_rows = int(normalized.shape[0])
            self._debug_sheets[name] = {
                "header_row_detected": hdr_idx,
                "rows_before": before_rows,
                "cols_before": before_cols[:20],
                "rows_after": after_rows,
                "is_exceptions": is_exceptions,
            }

            if after_rows > 0:
                frames.append(normalized)

        if not frames:
            return pd.DataFrame(columns=WANTED_COLUMNS)

        # NÃO re-normalizar aqui; já normalizado por aba
        df_all = pd.concat(frames, ignore_index=True)
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

    # -----------------------------
    # Buscas
    # -----------------------------
    def search(self, q: str, field: Optional[str], remove_accents: bool = True) -> pd.DataFrame:
        df = self.df()
        q_norm = normalize_for_compare(q or "", remove_accents=remove_accents)
        if not q_norm:
            return df

        def series_norm(s: pd.Series) -> pd.Series:
            return s.map(lambda x: normalize_for_compare(x, remove_accents=remove_accents))

        search_cols = ["ITEM", "ANEXO", "DESCRIÇÃO DO PRODUTO", "NCM", "DESCRIÇÃO TIPI"]

        if not field or field.upper() == "ALL":
            mask = None
            for col in search_cols:
                if col in df.columns:
                    part = series_norm(df[col]).str.contains(q_norm, na=False, regex=False)
                    mask = part if mask is None else (mask | part)
            return df.loc[mask] if mask is not None else df.iloc[0:0]

        col_map = map_columns_to_canonical([field])
        canon = col_map.get(field, field)
        if canon not in df.columns:
            return df.iloc[0:0]
        return df.loc[series_norm(df[canon]).str.contains(q_norm, na=False, regex=False)]

    def search_multi(
        self,
        filters: list[tuple[str | None, str | None]],
        remove_accents: bool = True
    ) -> pd.DataFrame:
        df = self.df()

        def series_norm(s: pd.Series) -> pd.Series:
            return s.map(lambda x: normalize_for_compare(x, remove_accents=remove_accents))

        def mask_for(field: str | None, q: str | None) -> pd.Series | None:
            q_norm = normalize_for_compare(q or "", remove_accents=remove_accents)
            if not q_norm:
                return None
            search_cols = ["ITEM", "ANEXO", "DESCRIÇÃO DO PRODUTO", "NCM", "DESCRIÇÃO TIPI"]
            if not field or field.upper() == "ALL":
                m = None
                for col in search_cols:
                    if col in df.columns:
                        part = series_norm(df[col]).str.contains(q_norm, na=False, regex=False)
                        m = part if m is None else (m | part)
                return m
            col_map = map_columns_to_canonical([field])
            canon = col_map.get(field, field)
            if canon not in df.columns:
                return None
            return series_norm(df[canon]).str.contains(q_norm, na=False, regex=False)

        masks = []
        for f, q in filters[:2]:
            m = mask_for(f, q)
            if m is not None:
                masks.append(m)

        if not masks:
            return df
        combined = masks[0]
        for m in masks[1:]:
            combined = combined & m
        return df.loc[combined]

    # ---------------------------------------
    # Detalhes
    # ---------------------------------------
    def find_details(self, ncm: Optional[str] = None, item: Optional[str] = None) -> pd.DataFrame:
        df = self.df()
        if ncm:
            key = normalize_for_compare(ncm, True)
            mask = df["NCM"].map(lambda x: normalize_for_compare(x, True) == key)
            out = df.loc[mask]
        elif item:
            key = normalize_for_compare(item, True)
            mask = df["ITEM"].map(lambda x: normalize_for_compare(x, True) == key)
            out = df.loc[mask]
        else:
            out = df.iloc[0:0]

        cols = ["ANEXO", "ITEM", "NCM", "DESCRIÇÃO DO PRODUTO", "DESCRIÇÃO COMPLETA", "IBS", "CBS"]
        existing = [c for c in cols if c in out.columns]
        return out[existing].reset_index(drop=True)

# -----------------------------
# Serializadores para API
# -----------------------------
def _viz(v):  # atalho
    return normalize_visible(v)

def _fmt_pct(v):
    if v is None or str(v).strip() == "":
        return ""
    s = str(v).replace(",", ".")
    try:
        n = float(s)
        if 0 <= n <= 1:
            n *= 100
        s = f"{int(n)}%" if float(n).is_integer() else f"{n:.2f}%".rstrip("0").rstrip(".") + "%"
        return s
    except Exception:
        return str(v)

def to_api_rows(df_page: pd.DataFrame) -> list[dict]:
    out = []
    for _, r in df_page.iterrows():
        out.append({
            "ITEM": _viz(r.get("ITEM", "")),
            "ANEXO": _viz(r.get("ANEXO", "")),
            "DESCRIÇÃO DO PRODUTO": _viz(r.get("DESCRIÇÃO DO PRODUTO", "")),
            "NCM": _viz(r.get("NCM", "")),
            "DESCRIÇÃO TIPI": _viz(r.get("DESCRIÇÃO TIPI", "")),
            "CST IBS E CBS": _viz(r.get("CST IBS E CBS", "")),
            "CCLASSTRIB": _viz(r.get("CCLASSTRIB", "")),
            "DESCRIÇÃO COMPLETA": _viz(r.get("DESCRIÇÃO COMPLETA", "")),
            "IBS": _viz(r.get("IBS", "")),
            "CBS": _viz(r.get("CBS", "")),
        })
    return out

def to_api_details(df: pd.DataFrame) -> list[dict]:
    out = []
    for _, r in df.iterrows():
        out.append({
            "ANEXO": r.get("ANEXO", ""),
            "ITEM": r.get("ITEM", ""),
            "NCM": r.get("NCM", ""),
            "DESCRIÇÃO DO PRODUTO": r.get("DESCRIÇÃO DO PRODUTO", ""),
            "DESCRIÇÃO COMPLETA": normalize_visible(r.get("DESCRIÇÃO COMPLETA", "")),
            "IBS": _fmt_pct(r.get("IBS", "")),
            "CBS": _fmt_pct(r.get("CBS", "")),
        })
    return out








