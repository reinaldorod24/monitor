import streamlit as st
import socket
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

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
TIMEOUT = 3           # timeout de conexão em segundos
MAX_WORKERS = 30      # threads simultâneas
AUTO_REFRESH_MIN = 5  # atualizar automaticamente a cada 5 minutos

# ==========================
# LISTA FIXA (COLADA DA PLANILHA)
# ==========================
GRAVADORES = [
     {"nome": "MG-VENO-VNO", "ip": "200.165.57.186", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "RJ-RJO-BGU", "ip": "200.222.62.110", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-NLP-NLP", "ip": "187.12.208.162", "porta": 50000, "site": "NILOPOLIS", "cidade": "RJ", "ativo": True},
    {"nome": "MG-BHE-FLO", "ip": "200.222.56.22", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "ES-JAMC-JAMC", "ip": "200.216.113.2", "porta": 50000, "site": "CARIACICA", "cidade": "ES", "ativo": True},
    {"nome": "RJ-RJO-TRF", "ip": "187.12.208.94", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-CTB", "ip": "200.222.62.114", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-CTO", "ip": "200.222.62.115", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-CTE", "ip": "200.222.62.116", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-CTP", "ip": "200.222.62.117", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-CTR", "ip": "200.222.62.118", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-CTS", "ip": "200.222.62.119", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-CTZ", "ip": "200.222.62.120", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-GLO", "ip": "200.222.62.111", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-MAD", "ip": "200.222.62.112", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-MAR", "ip": "200.222.62.113", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-SGO-SGO", "ip": "187.12.208.170", "porta": 50000, "site": "SAO GONCALO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-SJM-SJM", "ip": "187.12.208.166", "porta": 50000, "site": "SAO JOAO DE MERITI", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TCM", "ip": "187.12.208.146", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TCR", "ip": "187.12.208.147", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TCT", "ip": "187.12.208.148", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TCV", "ip": "187.12.208.149", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TCW", "ip": "187.12.208.150", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TCX", "ip": "187.12.208.151", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TCY", "ip": "187.12.208.152", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TCZ", "ip": "187.12.208.153", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDA", "ip": "187.12.208.154", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDB", "ip": "187.12.208.155", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDC", "ip": "187.12.208.156", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDD", "ip": "187.12.208.157", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDE", "ip": "187.12.208.158", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDF", "ip": "187.12.208.159", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDG", "ip": "187.12.208.160", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDH", "ip": "187.12.208.161", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDI", "ip": "187.12.208.162", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDJ", "ip": "187.12.208.163", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDK", "ip": "187.12.208.164", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDL", "ip": "187.12.208.165", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDM", "ip": "187.12.208.166", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDN", "ip": "187.12.208.167", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDO", "ip": "187.12.208.168", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDP", "ip": "187.12.208.169", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDQ", "ip": "187.12.208.170", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDR", "ip": "187.12.208.171", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDS", "ip": "187.12.208.172", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDT", "ip": "187.12.208.173", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDU", "ip": "187.12.208.174", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDV", "ip": "187.12.208.175", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDW", "ip": "187.12.208.176", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDX", "ip": "187.12.208.177", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDY", "ip": "187.12.208.178", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TDZ", "ip": "187.12.208.179", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEA", "ip": "187.12.208.180", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEB", "ip": "187.12.208.181", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEC", "ip": "187.12.208.182", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TED", "ip": "187.12.208.183", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEE", "ip": "187.12.208.184", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEF", "ip": "187.12.208.185", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEG", "ip": "187.12.208.186", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEH", "ip": "187.12.208.187", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEI", "ip": "187.12.208.188", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEJ", "ip": "187.12.208.189", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEK", "ip": "187.12.208.190", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEL", "ip": "187.12.208.191", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEM", "ip": "187.12.208.192", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEN", "ip": "187.12.208.193", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEO", "ip": "187.12.208.194", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEP", "ip": "187.12.208.195", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEQ", "ip": "187.12.208.196", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TER", "ip": "187.12.208.197", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TES", "ip": "187.12.208.198", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TET", "ip": "187.12.208.199", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEU", "ip": "187.12.208.200", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEV", "ip": "187.12.208.201", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEW", "ip": "187.12.208.202", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEX", "ip": "187.12.208.203", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEY", "ip": "187.12.208.204", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TEZ", "ip": "187.12.208.205", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFA", "ip": "187.12.208.206", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFB", "ip": "187.12.208.207", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFC", "ip": "187.12.208.208", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFD", "ip": "187.12.208.209", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFE", "ip": "187.12.208.210", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFF", "ip": "187.12.208.211", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFG", "ip": "187.12.208.212", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFH", "ip": "187.12.208.213", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFI", "ip": "187.12.208.214", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFJ", "ip": "187.12.208.215", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFK", "ip": "187.12.208.216", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFL", "ip": "187.12.208.217", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFM", "ip": "187.12.208.218", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFN", "ip": "187.12.208.219", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFO", "ip": "187.12.208.220", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFP", "ip": "187.12.208.221", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFQ", "ip": "187.12.208.222", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFR", "ip": "187.12.208.223", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFS", "ip": "187.12.208.224", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFT", "ip": "187.12.208.225", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFU", "ip": "187.12.208.226", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFV", "ip": "187.12.208.227", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFW", "ip": "187.12.208.228", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFX", "ip": "187.12.208.229", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFY", "ip": "187.12.208.230", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-TFZ", "ip": "187.12.208.231", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "SP-BRU-BRU", "ip": "200.165.57.122", "porta": 37777, "site": "BARUERI", "cidade": "SP", "ativo": True},

]

# ==========================
# FUNÇÕES
# ==========================
def status_badge(status: str) -> str:
    return "🟢 ONLINE" if status == "ONLINE" else "🔴 OFFLINE"

def testar_conexao(g: dict) -> dict:
    nome = str(g.get("nome", "")).strip()
    ip = str(g.get("ip", "")).strip()
    site = str(g.get("site", "")).strip()
    cidade = str(g.get("cidade", "")).strip()
    porta_raw = g.get("porta", "")
    horario = datetime.now().strftime("%H:%M:%S")

    try:
        porta = int(porta_raw)
        with socket.create_connection((ip, porta), timeout=TIMEOUT):
            status = "ONLINE"
    except Exception:
        status = "OFFLINE"

    return {
        "🟢🔴": status_badge(status),
        "Gravador": nome,
        "IP": ip,
        "Porta": porta_raw,
        "Site": site,
        "Cidade": cidade,
        "Status": status,
        "Horário": horario,
    }

def rodar_verificacao(lista: list) -> pd.DataFrame:
    resultados = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(testar_conexao, g) for g in lista]
        for future in as_completed(futures):
            resultados.append(future.result())

    df = pd.DataFrame(resultados)
    # ordena só para ficar estável (opcional)
    if not df.empty and "Gravador" in df.columns:
        df = df.sort_values(by=["Status", "Gravador"], ascending=[True, True]).reset_index(drop=True)
    return df

# ==========================
# SIDEBAR - CONTROLES
# ==========================
st.sidebar.header("⚙️ Controles")

auto_on = st.sidebar.toggle("Auto-refresh", value=True)
st.sidebar.caption(f"Intervalo: {AUTO_REFRESH_MIN} min")

if st.sidebar.button("🔄 Atualizar agora", use_container_width=True):
    st.session_state.force_refresh = True
    st.rerun()

st.sidebar.divider()
st.sidebar.header("🔎 Filtros")
filtro_status = st.sidebar.selectbox("Status", ["Todos", "ONLINE", "OFFLINE"])
filtro_texto = st.sidebar.text_input("Buscar por nome, IP, site ou cidade", "")

st.sidebar.divider()
st.sidebar.header("↕️ Ordenação")
ordem_campo = st.sidebar.selectbox(
    "Ordenar por",
    ["Gravador", "Status", "Cidade", "Horário"],
    index=0
)
ordem_sentido = st.sidebar.radio("Sentido", ["Crescente", "Decrescente"], horizontal=True)
ordem_desc = (ordem_sentido == "Decrescente")

# ==========================
# TÍTULO
# ==========================
st.title("📹 Monitoramento de Gravadores")
st.caption(f"Timeout {TIMEOUT}s • Threads {MAX_WORKERS} • Auto-refresh {AUTO_REFRESH_MIN} min")

# ==========================
# LISTA ATIVA
# ==========================
gravadores_ativos = [g for g in GRAVADORES if bool(g.get("ativo", True))]
if not gravadores_ativos:
    st.warning("Nenhum gravador ativo configurado no código.")
    st.stop()

# ==========================
# STATE
# ==========================
if "df_res" not in st.session_state:
    st.session_state.df_res = None
if "last_run_ts" not in st.session_state:
    st.session_state.last_run_ts = 0.0
if "force_refresh" not in st.session_state:
    st.session_state.force_refresh = False

agora = time.time()
intervalo_seg = AUTO_REFRESH_MIN * 60
precisa_retestar = (
    st.session_state.df_res is None
    or st.session_state.force_refresh
    or (agora - st.session_state.last_run_ts) >= intervalo_seg
)

# ==========================
# EXECUÇÃO COMPLETA (DASHBOARD SÓ APÓS FINALIZAR)
# ==========================
if precisa_retestar:
    st.session_state.force_refresh = False

    status_box = st.empty()
    status_box.info("Iniciando verificação de todos os gravadores...")

    df_res = rodar_verificacao(gravadores_ativos)

    st.session_state.df_res = df_res
    st.session_state.last_run_ts = time.time()

    status_box.success("✅ Todos os gravadores foram testados.")

df_res = st.session_state.df_res

# ==========================
# DASHBOARD (SÓ DEPOIS)
# ==========================
online_count = int((df_res["Status"] == "ONLINE").sum()) if df_res is not None and not df_res.empty else 0
offline_count = int((df_res["Status"] == "OFFLINE").sum()) if df_res is not None and not df_res.empty else 0

c1, c2, c3 = st.columns(3)
c1.metric("📊 Total", len(gravadores_ativos))
c2.metric("🟢 Online", online_count)
c3.metric("🔴 Offline", offline_count)

# ==========================
# CONTADOR (CORPO + SIDEBAR)
# ==========================
if auto_on and st.session_state.last_run_ts > 0:
    elapsed = time.time() - st.session_state.last_run_ts
    faltam = max(0, int(intervalo_seg - elapsed))
    mm = faltam // 60
    ss = faltam % 60
    st.info(f"⏳ Próxima atualização automática em **{mm:02d}:{ss:02d}**")
    st.sidebar.caption(f"⏳ Próxima atualização em {mm:02d}:{ss:02d}")
elif auto_on:
    st.sidebar.caption("⏳ Próxima atualização em 00:00 (iniciando...)")

# ==========================
# FILTROS
# ==========================
df_filtro = df_res.copy()

if filtro_status != "Todos":
    df_filtro = df_filtro[df_filtro["Status"] == filtro_status]

if filtro_texto:
    t = filtro_texto.strip().lower()
    df_filtro = df_filtro[
        df_filtro["Gravador"].fillna("").str.lower().str.contains(t)
        | df_filtro["IP"].fillna("").str.lower().str.contains(t)
        | df_filtro["Site"].fillna("").str.lower().str.contains(t)
        | df_filtro["Cidade"].fillna("").str.lower().str.contains(t)
    ]

# ==========================
# ORDENAR (APÓS FILTROS)
# ==========================
df_ordenado = df_filtro.copy()

if ordem_campo == "Horário":
    df_ordenado["_horario_dt"] = pd.to_datetime(df_ordenado["Horário"], format="%H:%M:%S", errors="coerce")
    df_ordenado = df_ordenado.sort_values(by="_horario_dt", ascending=not ordem_desc, na_position="last")
    df_ordenado = df_ordenado.drop(columns=["_horario_dt"])
else:
    df_ordenado = df_ordenado.sort_values(by=ordem_campo, ascending=not ordem_desc, na_position="last")

# ==========================
# TABELA
# ==========================
st.dataframe(df_ordenado, width="stretch", hide_index=True)

# ==========================
# AUTO-REFRESH POR TEMPO (SEM BIBLIOTECA)
# ==========================
if auto_on:
    elapsed = time.time() - st.session_state.last_run_ts
    faltam = max(1, int(intervalo_seg - elapsed))

    mm = faltam // 60
    ss = faltam % 60
    st.caption(f"⏳ Próxima atualização automática em **{mm:02d}:{ss:02d}**")

    time.sleep(faltam)
    st.rerun()