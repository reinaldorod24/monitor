import streamlit as st
import socket
import time
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================
# CONFIGURAÇÃO DA PÁGINA
# ==========================
st.set_page_config(
    page_title="Monitor de Gravadores",
    page_icon="📹",
    layout="wide"
)

# ==========================
# CONSTANTES
# ==========================
ARQUIVO_EXCEL = "gravadores.xlsx"
ABA_EXCEL = "gravadores"
TIMEOUT_PADRAO = 3
MAX_WORKERS = 20

# ==========================
# CARREGAMENTO DOS GRAVADORES
# ==========================
@st.cache_data
def carregar_gravadores():
    df = pd.read_excel(
        ARQUIVO_EXCEL,
        sheet_name=ABA_EXCEL,
        dtype={"ip": str, "nome": str}
    )
    return df[df["ativo"] == 1]

# ==========================
# FUNÇÕES DE REDE
# ==========================
def testar_conexao(ip: str, porta: int, timeout: float = TIMEOUT_PADRAO):
    inicio = time.perf_counter()
    try:
        with socket.create_connection((ip, porta), timeout=timeout):
            dur = (time.perf_counter() - inicio) * 1000
            return True, round(dur, 1)
    except Exception:
        return False, None

def medir_todos(df: pd.DataFrame):
    resultados = []

    if df.empty:
        return pd.DataFrame()

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(df))) as executor:
        futures = {
            executor.submit(testar_conexao, row["ip"], int(row["porta"])): row
            for _, row in df.iterrows()
        }

        for future in as_completed(futures):
            row = futures[future]
            online, ms = future.result()

            resultados.append({
                "Gravador": row["nome"],
                "IP": row["ip"],
                "Porta": row["porta"],
                "Status": "ONLINE" if online else "OFFLINE",
                "Tempo (ms)": ms if ms else ""
            })

    return pd.DataFrame(resultados)

# ==========================
# FILTROS E ORDENAÇÃO
# ==========================
def aplicar_filtros(df, busca, status):
    if busca:
        busca = busca.lower().strip()
        df = df[
            df["Gravador"].str.lower().str.contains(busca) |
            df["IP"].str.lower().str.contains(busca)
        ]

    if status in ("ONLINE", "OFFLINE"):
        df = df[df["Status"] == status]

    return df

def ordenar_df(df, ordenacao):
    if ordenacao == "Status (ONLINE primeiro)":
        df["ord"] = df["Status"].map({"ONLINE": 0, "OFFLINE": 1})
        df = df.sort_values(["ord", "Gravador"]).drop(columns="ord")
    else:
        df = df.sort_values("Gravador")
    return df

def status_badge(status):
    return "🟢 ONLINE" if status == "ONLINE" else "🔴 OFFLINE"

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.header("🔎 Filtros")

    BUSCA = st.text_input("Buscar por nome ou IP")
    STATUS_SEL = st.selectbox("Status", ["Todos", "ONLINE", "OFFLINE"])
    ORDENACAO = st.selectbox(
        "Ordenar por",
        ["Status (ONLINE primeiro)", "Nome (A→Z)"]
    )

    st.divider()
    EXECUTAR = st.button("▶️ Verificar gravadores")

# ==========================
# HEADER
# ==========================
st.title("📹 Monitoramento de Gravadores")
st.caption("Clique no botão para iniciar a verificação")
st.divider()

# ==========================
# SESSION STATE
# ==========================
if "resultado" not in st.session_state:
    st.session_state["resultado"] = pd.DataFrame()

if "ultima_execucao" not in st.session_state:
    st.session_state["ultima_execucao"] = None

# ==========================
# EXECUÇÃO MANUAL
# ==========================
if EXECUTAR:
    df_gravadores = carregar_gravadores()

    with st.spinner("🔍 Verificando gravadores..."):
        st.session_state["resultado"] = medir_todos(df_gravadores)
        st.session_state["ultima_execucao"] = datetime.now()

# ==========================
# EXIBIÇÃO
# ==========================
df_resultado = st.session_state["resultado"]

if df_resultado.empty:
    st.info("👉 Clique em **Verificar gravadores** para iniciar.")
    st.stop()

# ==========================
# FILTROS
# ==========================
df_resultado = aplicar_filtros(
    df_resultado,
    BUSCA,
    STATUS_SEL if STATUS_SEL != "Todos" else ""
)
df_resultado = ordenar_df(df_resultado, ORDENACAO)

# ==========================
# RESUMO
# ==========================
col1, col2, col3 = st.columns(3)
col1.metric("🟢 ONLINE", (df_resultado["Status"] == "ONLINE").sum())
col2.metric("🔴 OFFLINE", (df_resultado["Status"] == "OFFLINE").sum())
col3.metric("📊 TOTAL", len(df_resultado))

if st.session_state["ultima_execucao"]:
    st.caption(
        f"Última verificação: "
        f"{st.session_state['ultima_execucao'].strftime('%d/%m/%Y %H:%M:%S')}"
    )

st.divider()

# ==========================
# TABELA
# ==========================
df_show = df_resultado.copy()
df_show["Status"] = df_show["Status"].apply(status_badge)

st.dataframe(
    df_show,
    use_container_width=True,
    hide_index=True
)