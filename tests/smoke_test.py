"""Teste básico. Ajuste SAMPLE_ROOT para a pasta de amostras locais; nenhum extrato é incluído no projeto."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conversor.parsers import PARSERS

SAMPLE_ROOT = Path(__file__).resolve().parents[2] / "conversor_work" / "Conversor_Extratos_MegaThorra"

CASES = [
    ("Santander", SAMPLE_ROOT / "03_Arquivos_Convertidos_Manualmente/Santander/Extrato_Original_Abril_2026.xlsx"),
    ("Itau", SAMPLE_ROOT / "03_Arquivos_Convertidos_Manualmente/Itau/Extrato_Original_Abril_2026.xlsx"),
    ("Bradesco", SAMPLE_ROOT / "03_Arquivos_Convertidos_Manualmente/Bradesco/Extrato_Original_Abril_2026.CSV"),
    ("Banco Brasil Poupanca", SAMPLE_ROOT / "03_Arquivos_Convertidos_Manualmente/Banco_Brasil_Poupanca/Extrato_Original_Marco_2026.pdf"),
]

for bank, path in CASES:
    if not path.exists():
        print(f"SKIP {bank}: amostra não encontrada")
        continue
    r = PARSERS[bank](path.read_bytes())
    assert r.meta.agency, f"{bank}: agência vazia"
    assert r.meta.account, f"{bank}: conta vazia"
    assert r.meta.digit, f"{bank}: dígito vazio"
    assert r.transactions, f"{bank}: sem lançamentos"
    print(f"OK {bank}: {r.meta.agency}/{r.meta.account}-{r.meta.digit} | {len(r.transactions)} lançamentos")


def test_bradesco_ignora_ultimos_lancamentos():
    from conversor.parsers.bradesco import parse
    sample = (
        ';Extrato de: Agência: 3045  Conta: 28679-6\n'
        'Data;Lançamento;Dcto.;Crédito (R$);Débito (R$);Saldo (R$)\n'
        '31/03/2026;SALDO ANTERIOR;;;;100,00\n'
        '01/04/2026;PIX RECEBIDO;123;50,00;;150,00\n'
        'Total;;;50,00;;150,00\n'
        '\n;Últimos Lançamentos\n\n'
        'Data;Lançamento;Dcto.;Crédito (R$);Débito (R$);Saldo (R$)\n'
        '31/07/2026;SALDO ANTERIOR;;;;200,00\n'
        '03/08/2026;PIX RECEBIDO;999;10,00;;210,00\n'
    ).encode('cp1252')
    result = parse(sample)
    assert len(result.transactions) == 2
    assert result.transactions[-1].date == '01/04/2026'
    assert all('/08/2026' not in t.date for t in result.transactions)
    assert any('Últimos Lançamentos' in w for w in result.warnings)
