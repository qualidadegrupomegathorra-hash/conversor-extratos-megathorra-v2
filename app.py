from decimal import Decimal
from datetime import datetime
import hashlib

import streamlit as st

from conversor.parsers import PARSERS
from conversor.exporter import to_csv_bytes

APP_VERSION = "2.2"
SUPPORTED_TYPES = ["xlsx", "xlsm", "csv", "pdf"]
BANK_FORMAT = {
    "Santander": "Excel (.xlsx/.xlsm)",
    "Bradesco": "CSV (.csv)",
    "Itau": "Excel (.xlsx/.xlsm)",
    "Caixa": "PDF (.pdf)",
    "Banco Brasil Corrente": "PDF (.pdf)",
    "Banco Brasil Poupanca": "PDF (.pdf)",
}


def _start_new_conversion() -> None:
    st.session_state["conversion_seq"] = st.session_state.get("conversion_seq", 0) + 1
    st.session_state.pop("processed_context", None)


def _fmt_brl(value: Decimal) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _date_key(s: str):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def _period_label(transactions) -> str:
    dates = [_date_key(t.date) for t in transactions]
    dates = [d for d in dates if d]
    if not dates:
        return "Não identificado"
    return f"{min(dates).strftime('%d/%m/%Y')} a {max(dates).strftime('%d/%m/%Y')}"


def _signed_total(transactions) -> Decimal:
    total = Decimal("0")
    for t in transactions:
        total += abs(t.value) if t.dc == "C" else -abs(t.value)
    return total


st.set_page_config(
    page_title="Conversor de Extratos | MegaThorra",
    page_icon="assets/logo_megathorra.jpg",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background: #0d1017; }
    [data-testid="stSidebar"] { background: #171b25; border-right: 1px solid #2b3140; }
    .block-container { max-width: 1450px; padding-top: 2rem; padding-bottom: 4rem; }
    .mega-logo { width:118px; height:118px; object-fit:contain; border-radius:50%; margin-bottom:14px; }
    .mega-eyebrow { color:#aeb6c8; font-size:.78rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.35rem; }
    .mega-title { font-size:2.35rem; line-height:1.05; font-weight:800; margin:0; color:#f7f8fb; }
    .mega-sub { color:#9ca6b9; margin-top:.65rem; font-size:1rem; }
    .stepbar { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:1.35rem 0 1.6rem; }
    .step { border:1px solid #303746; background:#151923; border-radius:12px; padding:12px 14px; color:#929caf; font-size:.85rem; }
    .step b { display:block; color:#eef1f7; font-size:.92rem; margin-bottom:2px; }
    .card { border:1px solid #2d3443; background:#141922; border-radius:16px; padding:18px 20px; margin-bottom:14px; }
    .okbox { border:1px solid rgba(53,199,122,.38); background:rgba(53,199,122,.08); border-radius:12px; padding:12px 14px; color:#d9f5e6; }
    .soft { color:#9ba5b7; font-size:.88rem; }
    .bank-badge { display:inline-block; padding:5px 9px; border-radius:999px; border:1px solid #384052; color:#d7dce7; font-size:.78rem; margin-right:6px; }
    div[data-testid="stMetric"] { border:1px solid #2d3443; background:#141922; border-radius:14px; padding:14px 16px; }
    div[data-testid="stMetricLabel"] { color:#9ca6b9; }
    .stDownloadButton > button { min-height:48px; font-weight:700; }
</style>
""",
    unsafe_allow_html=True,
)

st.session_state.setdefault("conversion_seq", 0)
st.session_state.setdefault("selected_bank", list(PARSERS.keys())[0])

with st.sidebar:
    st.image("assets/logo_megathorra.jpg", width=118)
    st.markdown("### Conversor CIGAM")
    st.caption(f"MegaThorra • Conciliação Bancária • v{APP_VERSION}")
    st.divider()
    st.markdown("**Origem do arquivo**")
    bank = st.selectbox(
        "Banco",
        list(PARSERS.keys()),
        key="selected_bank",
        on_change=_start_new_conversion,
        label_visibility="visible",
    )
    st.caption(f"Formato homologado: {BANK_FORMAT.get(bank, 'Conforme layout validado')}")
    st.info("Agência, conta, dígito e operação são lidos do próprio extrato. Nenhuma conta fica fixa no sistema.")
    if st.button("↻ Nova conversão", use_container_width=True):
        _start_new_conversion()
        st.rerun()
    st.divider()
    st.markdown("**Bancos homologados**")
    for item in PARSERS.keys():
        st.caption(f"✓ {item}")

h1, h2 = st.columns([0.12, 0.88], vertical_alignment="center")
with h1:
    st.image("assets/logo_megathorra.jpg", width=105)
with h2:
    st.markdown('<div class="mega-eyebrow">MegaThorra • Administrativo Financeiro</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="mega-title">Conversor de Extratos para CIGAM</h1>', unsafe_allow_html=True)
    st.markdown('<div class="mega-sub">Converta extratos bancários para o layout homologado de importação, com conferência antes do download.</div>', unsafe_allow_html=True)
st.markdown(
    """
<div class="stepbar">
  <div class="step"><b>1. Origem</b>Banco e arquivo</div>
  <div class="step"><b>2. Conferência</b>Conta e período</div>
  <div class="step"><b>3. Validação</b>Lançamentos e totais</div>
  <div class="step"><b>4. Exportação</b>CSV para o CIGAM</div>
</div>
""",
    unsafe_allow_html=True,
)

upload_key = f"source_file_{bank}_{st.session_state['conversion_seq']}"
uploaded = st.file_uploader(
    f"Envie o extrato do {bank}",
    type=SUPPORTED_TYPES,
    key=upload_key,
    help="O arquivo é processado somente para gerar a conversão desta sessão.",
)

if not uploaded:
    st.markdown(
        f"""
<div class="card">
  <div class="soft">Banco selecionado</div>
  <div style="font-size:1.25rem;font-weight:750;margin-top:4px">{bank}</div>
  <div class="soft" style="margin-top:8px">Formato homologado: {BANK_FORMAT.get(bank, '')}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("Selecione o banco na lateral e envie um extrato para iniciar. Ao trocar de banco, a conversão anterior é invalidada automaticamente.")
    st.stop()

try:
    raw = uploaded.getvalue()
    source_hash = hashlib.sha256(raw).hexdigest()

    with st.spinner("Lendo o extrato e aplicando as regras homologadas..."):
        result = PARSERS[bank](raw)

    if result.meta.bank != bank:
        st.error("Conversão bloqueada: o resultado processado não corresponde ao banco selecionado.")
        st.stop()

    current_context = {
        "bank": bank,
        "filename": uploaded.name,
        "sha256": source_hash,
        "seq": st.session_state["conversion_seq"],
    }
    st.session_state["processed_context"] = current_context

    st.markdown(f'<div class="okbox">✓ Arquivo processado com sucesso: <b>{uploaded.name}</b> • {len(result.transactions)} lançamentos reconhecidos.</div>', unsafe_allow_html=True)
    st.write("")

    st.subheader("Conferência da conta")
    c1, c2, c3, c4 = st.columns(4)
    result.meta.agency = c1.text_input("Agência", result.meta.agency, key=f"agency_{source_hash}_{bank}")
    if bank == "Caixa":
        result.meta.operation = c2.text_input("Operação", result.meta.operation, key=f"operation_{source_hash}_{bank}")
    else:
        c2.text_input("Operação", "Não se aplica", disabled=True, key=f"operation_na_{source_hash}_{bank}")
    result.meta.account = c3.text_input("Conta", result.meta.account, key=f"account_{source_hash}_{bank}")
    result.meta.digit = c4.text_input("Dígito", result.meta.digit, key=f"digit_{source_hash}_{bank}")

    warnings = result.meta.warnings + result.warnings
    for warning in warnings:
        st.warning(warning)

    credits = sum((abs(t.value) for t in result.transactions if t.dc == "C"), Decimal("0"))
    debits = sum((abs(t.value) for t in result.transactions if t.dc == "D"), Decimal("0"))
    movement = _signed_total(result.transactions)

    st.subheader("Validação do extrato")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Lançamentos", f"{len(result.transactions):,}".replace(",", "."))
    k2.metric("Créditos", _fmt_brl(credits))
    k3.metric("Débitos", _fmt_brl(debits))
    k4.metric("Movimento líquido", _fmt_brl(movement))
    k5.metric("Período", _period_label(result.transactions))

    st.subheader("Pré-visualização")
    preview = []
    for t in result.transactions[:500]:
        preview.append({
            "Data": t.date,
            "Histórico": t.description,
            "Documento": t.document,
            "C/D": t.dc,
            "Valor (R$)": float(t.value),
            "Saldo (R$)": None if t.balance is None else float(t.balance),
        })

    st.dataframe(
        preview,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Valor (R$)": st.column_config.NumberColumn(format="%.2f"),
            "Saldo (R$)": st.column_config.NumberColumn(format="%.2f"),
        },
        height=420,
    )
    if len(result.transactions) > 500:
        st.caption(f"Prévia exibindo 500 de {len(result.transactions)} lançamentos. O CSV contém todos os registros.")

    st.subheader("Arquivo para importação")
    missing = []
    if not result.meta.agency:
        missing.append("Agência")
    if not result.meta.account:
        missing.append("Conta")
    if not result.meta.digit:
        missing.append("Dígito")
    if bank == "Caixa" and not result.meta.operation:
        missing.append("Operação")
    if not result.transactions:
        missing.append("Lançamentos")

    context = st.session_state.get("processed_context")
    context_ok = bool(
        context
        and context.get("bank") == bank
        and context.get("filename") == uploaded.name
        and context.get("sha256") == source_hash
        and context.get("seq") == st.session_state["conversion_seq"]
    )

    if missing:
        st.error("Arquivo bloqueado. Preencha/valide: " + ", ".join(missing))
    elif not context_ok:
        st.error("Arquivo bloqueado porque o banco ou upload atual não corresponde ao processamento corrente. Inicie uma nova conversão.")
    else:
        output = to_csv_bytes(result)
        safe_bank = bank.replace(" ", "_")
        name = f"CIGAM_{safe_bank}_{result.meta.agency}_{result.meta.account}.csv"

        a, b = st.columns([1.25, .75])
        with a:
            st.markdown(
                f"""
<div class="card">
  <div class="soft">Pronto para exportar</div>
  <div style="font-size:1.15rem;font-weight:750;margin:5px 0 10px">{name}</div>
  <span class="bank-badge">{bank}</span>
  <span class="bank-badge">Ag. {result.meta.agency}</span>
  <span class="bank-badge">Conta {result.meta.account}-{result.meta.digit}</span>
  <div class="soft" style="margin-top:12px">Origem: {uploaded.name}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with b:
            st.write("")
            st.download_button(
                "Baixar CSV para o CIGAM",
                output,
                name,
                "text/csv",
                type="primary",
                use_container_width=True,
                key=f"download_{source_hash}_{bank}",
            )
            st.caption("UTF-8 com BOM • Separador ; • Layout homologado por banco")

except Exception as exc:
    st.error("Não foi possível processar este extrato.")
    st.caption(f"Detalhe técnico: {exc}")
    st.info("Nenhum CSV foi gerado. Verifique se o banco selecionado e o formato do arquivo estão corretos e tente novamente.")
