import streamlit as st
import socket
import time
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================
# Configuração da página
# ==========================
st.set_page_config(
    page_title="Monitor de Gravadores",
    page_icon="📹",
    layout="wide"
)

# ==========================
# Dados dos gravadores
# ==========================
GRAVADORES = {
    "RJ-RJO-MAR": ("201.59.252.38", 50000),
    "RJ-JDAR-JDAR": ("200.222.243.62", 50000),
    "RJ-CHM-CHM": ("200.165.139.102", 37777),
    "RJ-VITE-VITE": ("200.202.197.102", 50000),
    "DF-STMK-ETMS": ("189.74.138.6", 50000),
    "DF-SOBD-ETSB": ("201.41.66.78", 50000),
    "ES-JAMC-SFCO": ("200.199.87.142", 50000),
    "GO-GNA-MUT": ("177.201.98.30", 50000),
    "MG-VENO-VNO": ("200.165.57.184", 50000),
    "PR-CTA-CTBV": ("201.89.63.142", 50000),
    "PR-SJP-SJRB": ("191.219.11.106", 50000),
    "RS-SLE-SLE": ("177.2.166.160", 50000),
    "RJ-RJO-FRE": ("200.216.55.46", 50000),
}

TIMEOUT_PADRAO = 10  # segundos

# ==========================
# Funções
# ==========================
def testar_conexao(ip: str, porta: int, timeout: float = TIMEOUT_PADRAO):
    inicio = time.perf_counter()
    try:
        with socket.create_connection((ip, porta), timeout=timeout):
            dur = (time.perf_counter() - inicio) * 1000
            return True, round(dur, 1)
    except Exception:
        return False, None

def medir_todos(gravadores: dict):
    resultados = []
    with ThreadPoolExecutor(max_workers=min(32, len(gravadores))) as executor:
        futures = {
            executor.submit(testar_conexao, ip, porta): (nome, ip, porta)
            for nome, (ip, porta) in gravadores.items()
        }

        for future in as_completed(futures):
            nome, ip, porta = futures[future]
            online, ms = future.result()
            resultados.append({
                "Gravador": nome,
                "IP": ip,
                "Porta": porta,
                "Status": "ONLINE" if online else "OFFLINE",
                "Tempo (ms)": ms if ms else ""
            })

    return pd.DataFrame(resultados)

def aplicar_filtros(df, busca, status):
    if busca:
        busca = busca.lower()
        df = df[
            df["Gravador"].str.lower().str.contains(busca) |
            df["IP"].str.lower().str.contains(busca)
        ]
    if status in ["ONLINE", "OFFLINE"]:
        df = df[df["Status"] == status]
    return df

def ordenar_df(df, ordenacao):
    if ordenacao == "Status (ONLINE primeiro)":
        df["ord"] = df["Status"].map({"ONLINE": 0, "OFFLINE": 1})
        df = df.sort_values(["ord", "Gravador"]).drop(columns="ord")
    else:  # Nome (A→Z)
        df = df.sort_values("Gravador")
    return df

def status_badge(status):
    return "🟢 ONLINE" if status == "ONLINE" else "🔴 OFFLINE"

# ==========================
# Sidebar
# ==========================
with st.sidebar:
    st.header("🔎 Filtros")

    BUSCA = st.text_input(
        "Buscar por nome ou IP",
        placeholder="Ex: RJ-RJO ou 201.59"
    )

    STATUS_SEL = st.selectbox(
        "Status",
        ["Todos", "ONLINE", "OFFLINE"]
    )

    ORDENACAO = st.selectbox(
        "Ordenar por",
        ["Status (ONLINE primeiro)", "Nome (A→Z)"]
    )

    if st.button("🔄 Verificar agora"):
        st.rerun()

# ==========================
# Header
# ==========================
st.title("📹 Monitoramento de Gravadores")
st.caption(f"Última verificação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.divider()

# ==========================
# Processamento
# ==========================
df = medir_todos(GRAVADORES)
df = aplicar_filtros(df, BUSCA, STATUS_SEL)
df = ordenar_df(df, ORDENACAO)

# ==========================
# Resumo
# ==========================
col1, col2, col3 = st.columns(3)
col1.metric("ONLINE", (df["Status"] == "ONLINE").sum())
col2.metric("OFFLINE", (df["Status"] == "OFFLINE").sum())
col3.metric("TOTAL", len(df))

st.divider()

# ==========================
# Tabela
# ==========================
df_show = df.copy()
df_show["Status"] = df_show["Status"].apply(status_badge)

st.dataframe(
    df_show,
    use_container_width=True,
    hide_index=True
)