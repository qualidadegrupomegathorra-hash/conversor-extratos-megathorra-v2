import io, re
import pdfplumber
from decimal import Decimal
from ..models import AccountMeta, Transaction, ConversionResult
from ..utils import clean_text, parse_decimal

ROW_RE=re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(?:\d{2}/\d{2}/\d{4}\s+)?(.+?)\s+([0-9Xx.-]+)\s+([0-9.]+)\s+([0-9.,]+)\s+([CD])(?:\s+[0-9.,]+\s+[CD])?$")


def parse(data: bytes) -> ConversionResult:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        text="\n".join((p.extract_text(x_tolerance=1, y_tolerance=3) or "") for p in pdf.pages)
    ma=re.search(r"Ag[eê]ncia:\s*([0-9]+)-([0-9Xx])",text,re.I)
    mc=re.search(r"Conta:\s*([0-9]+)-([0-9Xx])",text,re.I)
    meta=AccountMeta("Banco Brasil Poupanca", agency=ma.group(1) if ma else "", account=mc.group(1) if mc else "", digit=mc.group(2) if mc else "", source_format="pdf")
    tx=[]
    for raw in text.splitlines():
        line=clean_text(raw)
        m=ROW_RE.match(line)
        if not m: continue
        date, desc, origem, doc, val_s, dc=m.groups()
        val=parse_decimal(val_s) or Decimal("0")
        if dc=="D" and val>0: val=-val
        tx.append(Transaction(date, desc, doc, dc, val, None))
    # Saldo anterior pode ter estrutura diferente e não faz parte do modelo manual observado em abril.
    return ConversionResult(meta,tx, warnings=[] if tx else ["Nenhum lançamento reconhecido no PDF do BB Poupança."])
