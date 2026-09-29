from __future__ import annotations

import re
from datetime import date, datetime

from .registry import norm

_ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
_WORD = {"primer": 1, "primero": 1, "1": 1, "segundo": 2, "2": 2, "tercer": 3, "tercero": 3, "3": 3, "cuarto": 4, "4": 4}


def canonical_period(value: object, *, allowed_styles: tuple[str, ...] = ("canonical", "quarter_text", "compact_roman", "date")) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)) and "date" in allowed_styles:
        quarter = (value.month - 1) // 3 + 1
        return f"{value.year:04d}-Q{quarter}"
    raw = str(value).strip()
    if not raw:
        return None
    low = norm(raw)
    if "canonical" in allowed_styles:
        m = re.search(r"\b(20\d{2})\s*q\s*([1-4])\b", low)
        if m:
            return f"{m.group(1)}-Q{m.group(2)}"
    if "quarter_text" in allowed_styles:
        m = re.search(r"\b(primer|primero|segundo|tercer|tercero|cuarto|[1-4])\w*\s+trimestre(?:\s+de)?\s+(20\d{2})\b", low)
        if m:
            return f"{m.group(2)}-Q{_WORD[m.group(1)]}"
    if "compact_roman" in allowed_styles:
        compact = raw.lower().replace(" ", "")
        m = re.fullmatch(r"(i{1,3}|iv)[.\-/]?(\d{2}|20\d{2})", compact)
        if m and m.group(1) in _ROMAN:
            year = int(m.group(2))
            year = 2000 + year if year < 100 else year
            return f"{year:04d}-Q{_ROMAN[m.group(1)]}"
    if "date" in allowed_styles:
        m = re.fullmatch(r"(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])", raw)
        if m:
            year, month = int(m.group(1)), int(m.group(2))
            return f"{year:04d}-Q{(month - 1) // 3 + 1}"
    return None


def iter_quarters(start: str, end: str) -> list[str]:
    sy, sq = int(start[:4]), int(start[-1])
    ey, eq = int(end[:4]), int(end[-1])
    out = []
    y, q = sy, sq
    while (y, q) <= (ey, eq):
        out.append(f"{y:04d}-Q{q}")
        q += 1
        if q == 5:
            y += 1
            q = 1
    return out
