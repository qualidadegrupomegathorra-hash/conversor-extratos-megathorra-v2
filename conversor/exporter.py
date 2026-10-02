import csv
import io
from .models import ConversionResult
from .utils import format_decimal_br

LAYOUTS = {
    "Santander": ["AG","CONTA","DIGITOD","DATA","COMPLEMENTO","DOCTO","C/D","VALOR","SALDO"],
    "Bradesco": ["AG","CONTA","DIGITOD","DATA","COMPLEMENTO","DOCTO","C/D","VALOR","SALDO"],
    "Itau": ["AG","CONTA","DIGITOD","DATA","COMPLEMENTO","C/D","VALOR","SALDO"],
    "Caixa": ["AG","OP","CONTA","DIGITOD","DATA","COMPLEMENTO","DOCTO","C/D","VALOR","SALDO"],
    "Banco Brasil Corrente": ["AG","CONTA","DIGITOD","DATA","COMPLEMENTO","DOCTO","C/D","VALOR"],
    "Banco Brasil Poupanca": ["AG","CONTA","DIGITOD","DATA","COMPLEMENTO","C/D","VALOR"],
}


def to_rows(result: ConversionResult):
    m = result.meta
    bank = m.bank
    rows=[]
    for t in result.transactions:
        common = {
            "AG": m.agency,
            "OP": m.operation,
            "CONTA": m.account,
            "DIGITOD": m.digit,
            "DATA": t.date,
            "COMPLEMENTO": t.description,
            "DOCTO": t.document or ("-" if bank == "Santander" else ""),
            "C/D": t.dc,
            "VALOR": format_decimal_br(t.value),
            "SALDO": format_decimal_br(t.balance),
        }
        rows.append([common[h] for h in LAYOUTS[bank]])
    return rows


def to_csv_bytes(result: ConversionResult) -> bytes:
    buf=io.StringIO(newline="")
    writer=csv.writer(buf, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(LAYOUTS[result.meta.bank])
    writer.writerows(to_rows(result))
    return ("\ufeff" + buf.getvalue()).encode("utf-8")
