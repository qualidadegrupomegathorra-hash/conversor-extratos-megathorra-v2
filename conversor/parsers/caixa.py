import glob
import os
import re
import shutil
import unicodedata
from decimal import Decimal
from typing import Iterable

import fitz
import numpy as np
import pytesseract
from PIL import Image

from ..models import AccountMeta, Transaction, ConversionResult


ACCOUNT_RE = re.compile(
    r"Conta\s+([0-9]+)\s*/\s*([0-9]+)\.([0-9]+)-([0-9Xx])",
    re.I,
)
HEAD_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s*-?\s*\d{2}:?\d{2}:?\d{2}[.,]?\s+\(?([0-9]{6})\s+(.+)$"
)
# A Caixa usa vírgula como decimal. O OCR pode trocar o ponto de milhar por vírgula
# (ex.: 1.000,00 -> 1,000,00), então aceitamos ambos antes da última vírgula.
MONEY_RE = re.compile(r"(?<!\d)(\d[\d.,]*,\d{2})(?!\d)")

DEBIT_DESCRIPTIONS = {
    "DEB PIX CHAVE",
    "DEB PIX QR COD EST",
    "DEB PIX QR COD DIN",
    "PAGAMENTO DE BOLETO",
    "PAGAMENTO AGUA",
    "PAGAMENTO ORGAO GOVERNO",
    "ENVIO TRANSF INTERNET TEV",
    "ENVIO DE TED",
    "TARIFA TRANSF RECURSO E/I",
    "TARIFA TED INTERNET",
    "PAG BOLETO IBC",
    "PIX ENVIADO",
}


def _configure_tesseract() -> None:
    """Localiza o Tesseract no Windows sem depender do PATH.

    A V1.4.1 aceita o caminho repassado pelo INICIAR.bat e também procura
    instalações comuns/WinGet diretamente.
    """
    configured = os.environ.get("TESSERACT_CMD", "").strip().strip('"')
    if configured and os.path.isfile(configured):
        pytesseract.pytesseract.tesseract_cmd = configured
        return

    found = shutil.which("tesseract")
    if found:
        pytesseract.pytesseract.tesseract_cmd = found
        return

    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\tesseract.exe"),
    ]

    winget_root = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    if winget_root and os.path.isdir(winget_root):
        candidates.extend(
            glob.glob(os.path.join(winget_root, "**", "tesseract.exe"), recursive=True)
        )

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            return

    raise RuntimeError(
        "O OCR necessário para ler extratos da Caixa não foi localizado. "
        "Execute uma única vez o arquivo INSTALAR_OCR_CAIXA.bat e depois abra novamente o sistema."
    )


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9/]+", " ", text).strip()


def _compact(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", _norm(text))


def _canonical_description(text: str) -> str | None:
    n = _norm(text)
    c = _compact(text)

    if "SALDO" in n and "DIA" in n:
        return "SALDO DIA"
    if "SALDODIA" in c:
        return "SALDO DIA"
    if "DEBPIXCHAVE" in c:
        return "DEB PIX CHAVE"
    if "CREDPIXCHAVE" in c:
        return "CRED PIX CHAVE"
    if "DEBPIXQRCODEST" in c:
        return "DEB PIX QR COD EST"
    if "DEBPIXQRCODDIN" in c:
        return "DEB PIX QR COD DIN"
    if "PIXRECEBIDO" in c:
        return "PIX RECEBIDO"
    if "PIXENVIADO" in c:
        return "PIX ENVIADO"
    if "DEP" in n and "DINHEIRO" in n and "CAIXA" in n and "AG" in n:
        return "DEP DINHEIRO CAIXA AG"
    if "DEPOSITO" in n or "DEPOSIT" in n:
        if "LOTERICO" in n:
            return "DEPOSITO DINH LOTERICO"
        if "DINHEIRO" in n and "ATM" in n:
            return "DEPOSITO DINHEIRO ATM"
    if "DEP" in n and "DINHEIRO" in n and "CORBAN" in n:
        return "DEP DINHEIRO CORBAN"
    if "TARIFA" in n and "TRANSF" in n and "RECURSO" in n:
        return "TARIFA TRANSF RECURSO E/I"
    if "TARIFA" in n and "TED" in n and "INTERNET" in n:
        return "TARIFA TED INTERNET"
    if "ENVIO" in n and "TRANSF" in n and "INTERNET" in n and "TEV" in n:
        return "ENVIO TRANSF INTERNET TEV"
    if "ENVIO" in n and "TED" in n:
        return "ENVIO DE TED"
    if "CREDITO" in n and "JUROS" in n:
        return "CREDITO JUROS"
    if "CORRECAO" in n and "MONETARIA" in n:
        return "CORRECAO MONETARIA"
    if "PAG" in n and "BOLETO" in n and "IBC" in n:
        return "PAG BOLETO IBC"
    if "PAGAMENTO" in n and "BOLETO" in n:
        return "PAGAMENTO DE BOLETO"
    if "PAGAMENTO" in n and "AGUA" in n:
        return "PAGAMENTO AGUA"
    if "PAGAMENTO" in n and "ORGAO" in n and "GOVERNO" in n:
        return "PAGAMENTO ORGAO GOVERNO"
    return None


def _parse_money(token: str) -> Decimal:
    """Converte números monetários do OCR da Caixa, inclusive pontuação defeituosa."""
    token = token.strip().replace(" ", "")
    # Remove caracteres claramente espúrios que aparecem no OCR.
    token = re.sub(r"[^0-9,.-]", "", token)
    if not token:
        raise ValueError("valor monetário vazio")
    if "," in token:
        head, decimals = token.rsplit(",", 1)
        # OCR às vezes gera '11,.064,75'. Os separadores anteriores à última vírgula são milhar.
        head = re.sub(r"[^0-9-]", "", head)
        decimals = re.sub(r"[^0-9]", "", decimals)
        if len(decimals) != 2:
            raise ValueError(f"valor monetário inválido: {token}")
        return Decimal(f"{head or '0'}.{decimals}")
    # Ex.: '2.99430' / '1.37217' -> 2994,30 / 1372,17.
    compact = re.sub(r"[^0-9-]", "", token)
    if len(compact.lstrip("-")) >= 3:
        sign = "-" if compact.startswith("-") else ""
        digits = compact.lstrip("-")
        return Decimal(f"{sign}{digits[:-2]}.{digits[-2:]}")
    return Decimal(compact or "0")


MONEY_TOKEN_RE = re.compile(r"(?<!\d)(?:\d[\d.,]*,\d{2}|\d[\d.,]*\.\d{2}|\d[\d.]*\d{2})(?!\d)")


def _money_matches(line: str):
    """Retorna tokens monetários, incluindo formas OCR sem vírgula decimal."""
    return list(MONEY_TOKEN_RE.finditer(line))


def _document_clean(document: str) -> str:
    digits = re.sub(r"\D", "", document or "")
    if not digits:
        return ""
    return str(int(digits))


def _parse_line(line: str) -> Transaction | None:
    head = HEAD_RE.match(line)
    if not head:
        return None

    date, document, remainder = head.groups()
    description = _canonical_description(remainder)
    if not description:
        return None

    money = _money_matches(remainder)
    if len(money) < 2:
        # Há linhas em que o OCR degrada a primeira moeda; uma segunda tentativa isolada
        # é feita pelo chamador antes de desistir.
        return None

    value_match, balance_match = money[-2], money[-1]
    try:
        value = _parse_money(value_match.group(0))
        balance = _parse_money(balance_match.group(0))
    except ValueError:
        return None

    between = remainder[value_match.end(): balance_match.start()].upper()
    dc_match = re.search(r"\b([CD])\b", between)
    dc = dc_match.group(1) if dc_match else (
        "D" if description in DEBIT_DESCRIPTIONS else "C"
    )

    if description == "SALDO DIA":
        return Transaction(date, description, "0", "", Decimal("0"), balance)

    value = abs(value) if dc == "C" else -abs(value)
    return Transaction(date, description, _document_clean(document), dc, value, balance)


def _fallback_ocr_row(image: Image.Image, y: int) -> str:
    """OCR alternativo apenas para linhas que o OCR principal não conseguiu interpretar."""
    crop = image.crop((0, max(0, y - 15), image.width, min(image.height, y + 26)))
    crop = crop.resize((image.width * 2, 82))
    # PSM 11 separa melhor a moeda do histórico em algumas linhas difíceis.
    return re.sub(r"\s+", " ", pytesseract.image_to_string(crop, lang="eng", config="--psm 11")).strip()

def _candidate_rows(image: Image.Image) -> list[int]:
    """Detecta as linhas visuais do extrato pela coluna de data.

    O PDF da Caixa não contém texto; as linhas ficam em uma grade visual regular. Detectar
    primeiro a posição das linhas e só então fazer OCR reduz muito os erros de leitura.
    """
    arr = np.asarray(image)
    gray = arr.mean(axis=2)
    # Coluna esquerda onde ficam data/hora. Uma linha de texto gera uma faixa de pixels escuros.
    mask = (gray[:, 10:270] < 150).sum(axis=1) > 5

    groups: list[tuple[int, int]] = []
    start = None
    for y, active in enumerate(mask):
        if active and start is None:
            start = y
        elif not active and start is not None:
            if y - start >= 2:
                groups.append((start, y - 1))
            start = None
    if start is not None:
        groups.append((start, len(mask) - 1))

    merged: list[tuple[int, int]] = []
    for group in groups:
        if merged and group[0] - merged[-1][1] <= 5:
            merged[-1] = (merged[-1][0], group[1])
        else:
            merged.append(group)

    # Limites compatíveis com o layout A4 da amostra da Caixa.
    return [
        (a + b) // 2
        for a, b in merged
        if 100 < a < 1600 and 5 <= (b - a + 1) <= 30
    ]


def _page_row_items(image: Image.Image) -> list[tuple[str, int]]:
    """OCR das linhas mantendo a coordenada para uma segunda tentativa pontual."""
    ys = _candidate_rows(image)
    if not ys:
        return []

    row_height = 82
    spacing = 90
    width = image.width * 2
    strips: list[Image.Image] = []

    for y in ys:
        crop = image.crop(
            (0, max(0, y - 15), image.width, min(image.height, y + 26))
        ).resize((width, row_height))
        strips.append(crop)

    canvas = Image.new("RGB", (width, len(strips) * spacing), "white")
    for idx, crop in enumerate(strips):
        canvas.paste(crop, (0, idx * spacing))

    text = pytesseract.image_to_string(canvas, lang="eng", config="--psm 6")
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if re.match(r"^\d{2}/\d{2}/\d{4}", line):
            lines.append(line)

    # O layout tem uma linha por coordenada detectada; normalmente os comprimentos coincidem.
    # Se o OCR omitir alguma linha, não fazemos pareamento por posição para não inventar dados.
    return list(zip(lines, ys)) if len(lines) == len(ys) else [(line, None) for line in lines]


def _page_row_lines(image: Image.Image) -> list[str]:
    return [line for line, _ in _page_row_items(image)]

def _header_text(first_page: Image.Image) -> str:
    # A identificação da conta fica no topo da primeira página.
    crop = first_page.crop((0, 0, first_page.width, min(520, first_page.height)))
    return pytesseract.image_to_string(crop, lang="eng", config="--psm 6")


def _rebuild_balances(transactions: list[Transaction]) -> int:
    """Confere/corrige saldos usando o saldo mais recente como âncora.

    O extrato da Caixa vem do mais recente para o mais antigo. Para cada linha i:
    saldo_da_linha_mais_antiga = saldo_da_linha_mais_nova - valor_da_linha_mais_nova.
    Assim, um saldo final incorreto não contamina todo o extrato, como acontecia na V2.1.
    """
    if len(transactions) < 2:
        return 0

    anchor = next((t.balance for t in transactions if t.balance is not None), None)
    if anchor is None:
        return 0

    corrected = 0
    running = anchor
    transactions[0].balance = running

    for i in range(0, len(transactions) - 1):
        newer = transactions[i]
        older = transactions[i + 1]
        expected_older = running - newer.value
        if older.balance is None or older.balance != expected_older:
            older.balance = expected_older
            corrected += 1
        running = older.balance
    return corrected

def parse(data: bytes) -> ConversionResult:
    _configure_tesseract()
    doc = fitz.open(stream=data, filetype="pdf")
    if not doc.page_count:
        return ConversionResult(AccountMeta("Caixa", source_format="pdf/ocr"), [], ["PDF vazio."])

    meta = AccountMeta("Caixa", source_format="pdf/ocr")
    transactions: list[Transaction] = []
    unrecognized = 0

    first_image: Image.Image | None = None
    for page_index, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        if page_index == 0:
            first_image = image

        for line, y in _page_row_items(image):
            tx = _parse_line(line)
            if tx is None and y is not None:
                fallback = _fallback_ocr_row(image, y)
                tx = _parse_line(fallback)
            if tx is None:
                unrecognized += 1
            else:
                transactions.append(tx)

    if first_image is not None:
        header = _header_text(first_image)
        match = ACCOUNT_RE.search(header)
        if match:
            # CIGAM utiliza os campos sem zeros à esquerda nas amostras validadas.
            meta.agency = str(int(match.group(1)))
            meta.operation = str(int(match.group(2)))
            meta.account = str(int(match.group(3)))
            meta.digit = match.group(4)
        else:
            meta.warnings.append(
                "Agência, operação, conta e dígito não foram reconhecidos automaticamente. Revise antes de exportar."
            )

    corrected_balances = _rebuild_balances(transactions)
    warnings: list[str] = []
    if unrecognized:
        warnings.append(
            f"{unrecognized} linha(s) visual(is) não puderam ser interpretadas. "
            "Revise a quantidade de lançamentos antes de exportar."
        )
    if corrected_balances:
        warnings.append(
            f"{corrected_balances} saldo(s) foram recalculados pela sequência matemática do próprio extrato "
            "para corrigir leitura OCR."
        )
    if not transactions:
        warnings.append(
            "Nenhum lançamento da Caixa foi reconhecido. Confirme se o PDF segue o layout 'Extrato por período'."
        )

    return ConversionResult(meta, transactions, warnings)
