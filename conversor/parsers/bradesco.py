import csv, io, re
from decimal import Decimal
from ..models import AccountMeta, Transaction, ConversionResult
from ..utils import clean_text, parse_date, parse_decimal, split_account


def decode(data: bytes):
    for enc in ("utf-8-sig", "cp1252", "latin1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("latin1", errors="replace")


def _find_primary_table(lines: list[str]) -> tuple[int, int]:
    """Retorna o intervalo da tabela principal de movimentações do extrato.

    CSVs do Bradesco podem trazer, depois do período solicitado, uma seção
    chamada "Últimos Lançamentos" com movimentos recentes de outro mês. Essa
    seção NÃO pertence ao período exportado e não deve ir para o CIGAM.

    A tabela principal começa no primeiro cabeçalho Data;Lançamento... e termina
    no primeiro Total subsequente (ou antes de uma nova seção/cabeçalho).
    """
    start = next(
        (i for i, line in enumerate(lines) if line.lower().startswith("data;lan")),
        None,
    )
    if start is None:
        raise ValueError("Cabeçalho de lançamentos do Bradesco não encontrado.")

    end = len(lines)
    for i in range(start + 1, len(lines)):
        norm = clean_text(lines[i]).lower()
        # O Bradesco fecha a movimentação do período com a linha Total.
        if norm.startswith("total;") or norm == "total":
            end = i
            break
        # Proteções para variações do arquivo exportado.
        if "últimos lançamentos" in norm or "ultimos lancamentos" in norm:
            end = i
            break
        if i > start + 1 and lines[i].lower().startswith("data;lan"):
            end = i
            break
    return start, end


def parse(data: bytes) -> ConversionResult:
    text = decode(data)
    lines = text.splitlines()

    agency = ""
    raw_account = ""
    for line in lines[:10]:
        m = re.search(
            r"Ag[eê]ncia:\s*([0-9Xx-]+)\s+Conta:\s*([0-9Xx.-]+)",
            line,
            re.I,
        )
        if m:
            agency = m.group(1).split("-")[0]
            raw_account = m.group(2)
            break

    account, digit = split_account(raw_account)
    meta = AccountMeta(
        "Bradesco",
        agency=agency,
        account=account,
        digit=digit,
        source_format="csv",
    )

    start, end = _find_primary_table(lines)
    reader = csv.reader(io.StringIO("\n".join(lines[start:end])), delimiter=";")
    next(reader, None)

    transactions = []
    for row in reader:
        if len(row) < 6:
            continue

        date, desc, doc, cred, deb, saldo = row[:6]
        date = clean_text(date)
        desc_clean = clean_text(desc)
        if not re.match(r"\d{2}/\d{2}/\d{4}$", date):
            continue

        credit = parse_decimal(cred)
        debit = parse_decimal(deb)
        balance = parse_decimal(saldo)

        if credit is None and debit is None:
            if "saldo anterior" in desc_clean.lower():
                value = Decimal("0")
                dc = "C"
            else:
                continue
        elif debit is not None:
            value = debit if debit <= 0 else -debit
            dc = "D"
        else:
            value = credit
            dc = "C"

        transactions.append(
            Transaction(
                parse_date(date),
                desc_clean,
                clean_text(doc) or "0",
                dc,
                value,
                balance,
            )
        )

    # Transparência: se houver uma seção de lançamentos recentes, informamos
    # que foi deliberadamente ignorada para evitar misturar períodos.
    tail = "\n".join(lines[end:]).lower()
    warnings = []
    if "últimos lançamentos" in tail or "ultimos lancamentos" in tail:
        warnings.append(
            "O arquivo contém a seção 'Últimos Lançamentos' após o período principal. "
            "Ela foi ignorada para não misturar movimentações de outros meses."
        )

    return ConversionResult(meta, transactions, warnings=warnings)
