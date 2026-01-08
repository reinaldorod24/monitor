import streamlit as st
import socket
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_autorefresh import st_autorefresh

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
TIMEOUT = 3           # timeout de conexão em segundos
MAX_WORKERS = 30      # threads simultâneas
AUTO_REFRESH_MIN = 5  # atualizar automaticamente a cada 5 minutos

# ==========================
# AUTO-REFRESH LEVE
# ==========================
st_autorefresh(interval=AUTO_REFRESH_MIN * 60 * 1000, key="auto_refresh")

# ==========================
# FUNÇÕES
# ==========================
@st.cache_data
def carregar_gravadores():
    df = pd.read_excel(
        ARQUIVO_EXCEL,
        sheet_name=ABA_EXCEL,
        dtype={"ip": str, "nome": str, "porta": str, "ativo": int}
    )
    return df[df["ativo"] == 1].reset_index(drop=True)

def testar_conexao(gravador):
    ip = gravador["ip"]
    porta = gravador["porta"]
    nome = gravador["nome"]
    try:
        with socket.create_connection((ip, int(porta)), timeout=TIMEOUT):
            return {"Gravador": nome, "IP": ip, "Porta": porta, "Status": "ONLINE", "Horário": datetime.now().strftime("%H:%M:%S")}
    except Exception:
        return {"Gravador": nome, "IP": ip, "Porta": porta, "Status": "OFFLINE", "Horário": datetime.now().strftime("%H:%M:%S")}

def status_badge(status):
    return "🟢 ONLINE" if status == "ONLINE" else "🔴 OFFLINE"

# ==========================
# CARREGAR GRAVADORES
# ==========================
df_gravadores = carregar_gravadores()

# ==========================
# SESSION STATE PARA RESULTADOS
# ==========================
if "resultados" not in st.session_state:
    st.session_state.resultados = []

# Placeholder para tabela
placeholder = st.empty()

# ==========================
# SIDEBAR - FILTROS
# ==========================
st.sidebar.header("🔎 Filtros")
filtro_status = st.sidebar.selectbox("Status", ["Todos", "ONLINE", "OFFLINE"])
filtro_texto = st.sidebar.text_input("Buscar por nome ou IP", "")

# ==========================
# TÍTULO
# ==========================
st.title("📹 Monitoramento de Gravadores Automático")
st.caption(f"Atualização automática a cada {AUTO_REFRESH_MIN} minutos. Timeout de {TIMEOUT}s por gravador.")

# ==========================
# EXECUÇÃO DE TODOS OS GRAVADORES
# ==========================
if not st.session_state.resultados:
    st.info("Iniciando verificação dos gravadores...")

    resultados = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(testar_conexao, row): row for _, row in df_gravadores.iterrows()}
        for future in as_completed(futures):
            resultados.append(future.result())

    st.session_state.resultados = resultados
    st.success("✅ Todos os gravadores foram testados.")

# ==========================
# PREPARAR TABELA E DASHBOARD
# ==========================
df_res = pd.DataFrame(st.session_state.resultados)

# ==========================
# DASHBOARD - SOMENTE DEPOIS DE TODA VERIFICAÇÃO
# ==========================
col1, col2, col3 = st.columns(3)
col1.metric("📊 Total Gravadores", len(df_gravadores))
col2.metric("🟢 Online", (df_res["Status"] == "ONLINE").sum())
col3.metric("🔴 Offline", (df_res["Status"] == "OFFLINE").sum())

# ==========================
# APLICAR FILTROS
# ==========================
df_filtro = df_res.copy()
if filtro_status != "Todos":
    df_filtro = df_filtro[df_filtro["Status"] == filtro_status]
if filtro_texto:
    texto = filtro_texto.lower()
    df_filtro = df_filtro[
        df_filtro["Gravador"].str.lower().str.contains(texto) |
        df_filtro["IP"].str.lower().str.contains(texto)
    ]

# ==========================
# MOSTRAR TABELA FINAL
# ==========================
placeholder.dataframe(df_filtro, width="stretch", hide_index=True)