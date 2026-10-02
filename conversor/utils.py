import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation


def clean_text(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def digits(value) -> str:
    return re.sub(r"\D", "", clean_text(value))


def normalize_key(value) -> str:
    s = clean_text(value).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def parse_date(value) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    s = clean_text(value)
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:10], fmt).strftime("%d/%m/%Y")
        except ValueError:
            pass
    m = re.search(r"(\d{2}/\d{2}/\d{4})", s)
    return m.group(1) if m else s


def parse_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    s = clean_text(value).upper().replace("R$", "").replace(" ", "")
    dc = None
    if s.endswith("C") or s.endswith("D"):
        dc = s[-1]
        s = s[:-1]
    s = s.replace("−", "-")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s or s in {"-", "."}:
        return None
    try:
        n = Decimal(s)
        if dc == "D" and n > 0:
            n = -n
        return n
    except InvalidOperation:
        return None


def split_account(raw: str) -> tuple[str, str]:
    s = clean_text(raw)
    if "-" in s:
        a, d = s.rsplit("-", 1)
        return digits(a), clean_text(d)
    ds = digits(s)
    return (ds[:-1], ds[-1:]) if len(ds) > 1 else (ds, "")


def dc_from_value(value: Decimal | None, default="C") -> str:
    if value is None:
        return default
    return "D" if value < 0 else "C"


def format_decimal_br(value: Decimal | None) -> str:
    if value is None:
        return "0"
    q = value.normalize()
    s = format(q, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")
