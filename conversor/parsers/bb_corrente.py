import io, re
import pdfplumber
from decimal import Decimal
from ..models import AccountMeta, Transaction, ConversionResult
from ..utils import clean_text, parse_decimal

DATE_RE=re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(.*)$")
VALUE_RE=re.compile(r"([0-9][0-9.]*,[0-9]{2})\s*([CD])(?:\s+([0-9][0-9.]*,[0-9]{2})\s*[CD])?\s*$")
KNOWN_PREFIXES=("Transfer", "TED ", "Resgate", "Pix ", "Pagamento", "Tarifa", "Pgto ", "Saldo ", "Aplic", "Cobran")


def parse(data: bytes) -> ConversionResult:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        text="\n".join((p.extract_text(x_tolerance=1, y_tolerance=3) or "") for p in pdf.pages)
    ma=re.search(r"Ag[eê]ncia:\s*([0-9]+)-([0-9Xx])",text,re.I)
    mc=re.search(r"Conta:\s*([0-9]+)-([0-9Xx])",text,re.I)
    meta=AccountMeta("Banco Brasil Corrente", agency=ma.group(1) if ma else "", account=mc.group(1) if mc else "", digit=mc.group(2) if mc else "", source_format="pdf")
    lines=[clean_text(x) for x in text.splitlines() if clean_text(x)]
    tx=[]
    for i,line in enumerate(lines):
        dm=DATE_RE.match(line)
        if not dm: continue
        date, tail=dm.groups()
        vm=VALUE_RE.search(tail)
        if not vm: continue
        val_s,dc,_saldo=vm.groups()
        val=parse_decimal(val_s) or Decimal("0")
        if dc=="D" and val>0: val=-val
        pre=tail[:vm.start()].strip()

        # A descrição principal no PDF do BB normalmente aparece na linha imediatamente anterior.
        prev=lines[i-1] if i>0 else ""
        desc_parts=[]
        if prev and not DATE_RE.match(prev) and "Data Movim" not in prev and not prev.startswith("Agência:"):
            desc_parts.append(prev)

        # Documento: último token numérico/dotado antes do valor. Evita capturar datas/horas curtas.
        tokens=pre.split()
        doc=""
        doc_index=None
        for j in range(len(tokens)-1,-1,-1):
            tok=tokens[j]
            if re.fullmatch(r"[0-9][0-9.]{2,}", tok) and not re.fullmatch(r"\d{2}/\d{2}",tok):
                doc=tok; doc_index=j; break
        if doc_index is not None:
            before=" ".join(tokens[:doc_index]).strip()
        else:
            before=pre
        # Retira agência origem isolada no começo, mas preserva dados úteis (data/hora/nome).
        before=re.sub(r"^\d{1,5}-[0-9Xx](?:\s+|$)", "", before)
        if before:
            desc_parts.append(before)

        # Continuação textual logo após a linha do lançamento, até antes de uma nova descrição/data.
        if i+1 < len(lines):
            nxt=lines[i+1]
            if not DATE_RE.match(nxt) and "SISBB" not in nxt and "Data Movim" not in nxt:
                # Se a próxima linha é claramente uma nova descrição, não anexar.
                if not nxt.startswith(KNOWN_PREFIXES):
                    desc_parts.append(nxt)

        desc=clean_text(" ".join(dict.fromkeys(desc_parts)))
        if not desc:
            desc="Lançamento"
        tx.append(Transaction(date, desc, doc, dc, val, None))
    return ConversionResult(meta,tx, warnings=[] if tx else ["Nenhum lançamento reconhecido no PDF do BB Corrente."])
