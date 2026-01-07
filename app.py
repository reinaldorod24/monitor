
import streamlit as st
import socket
import time
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================
# Configurações da página
# ==========================

st.set_page_config(page_title="Monitor de Gravadores",page_icon="📹",layout="wide")

# ==========================
# Dados dos gravadores
# ==========================
GRAVADORES = {
    "RJ-RJO-MAR": ("201.59.252.38", 50000),
    "RJ-JDAR-JDAR": ("200.222.243.62", 50000),
    "RJ-CHM-CHM": ("200.165.139.102", 37777),
    "RJ-VITE-VITE": ("200.202.197.102", 50000),
    "RJ-VITE-VITE": ("200.202.197.102", 50000),
    "DF-STMK-ETMS": ("189.74.138.6", 50000),
    "DF-SOBD-ETSB": ("201.41.66.78", 50000),
    "ES-JAMC-SFCO": ("200.199.87.142", 50000),
    "GO-GNA-MUT": ("177.201.98.30", 50000),
    "MG-VENO-VNO": ("200.165.57.184", 50000),


    # Adicione aqui os demais até ~50...
    # "RJ-XXX-YYY": ("x.x.x.x", 50000),
}

# ==========================
# Funções utilitárias
# ==========================
def testar_conexao(ip: str, porta: int, timeout: float = 10.0):
    """
    Tenta abrir conexão TCP e retorna (online: bool, ms: float|None).
    """
    inicio = time.perf_counter()
    try:
        with socket.create_connection((ip, porta), timeout=timeout):
            dur = (time.perf_counter() - inicio) * 1000.0  # ms
            return True, round(dur, 1)
    except Exception:
        return False, None

def medir_todos(gravadores: dict[str, tuple[str, int]], timeout: float):
    """
    Medição concorrente para todos os gravadores.
    Retorna lista de dicts com: nome, ip, porta, status, tempo (ms).
    """
    results = []
    max_workers = min(32, len(gravadores)) or 1
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(testar_conexao, ip, porta, timeout): (nome, ip, porta)
            for nome, (ip, porta) in gravadores.items()
        }
        for fut in as_completed(futures):
            nome, ip, porta = futures[fut]
            try:
                online, ms = fut.result()
            except Exception:
                online, ms = False, None
            results.append({
                "Gravador": nome,
                "IP": ip,
                "Porta": porta,
                "Status": "ONLINE" if online else "OFFLINE",
                "Tempo (ms)": ms if ms is not None else ""
            })
    return results

def aplica_filtros(df: pd.DataFrame, busca: str, status_sel: str):
    """
    Filtra por texto (nome/IP) e por status (Todos/ONLINE/OFFLINE).
    """
    if busca:
        busca_low = busca.lower().strip()
        df = df[
            df["Gravador"].str.lower().str.contains(busca_low) |
            df["IP"].str.lower().str.contains(busca_low)
        ]
    if status_sel in ("ONLINE", "OFFLINE"):
        df = df[df["Status"] == status_sel]
    return df

def resumo(df: pd.DataFrame):
    online = int((df["Status"] == "ONLINE").sum())
    total = len(df)
    offline = total - online
    return online, offline, total

def status_badge(s: str):
    return "🟢 ONLINE" if s == "ONLINE" else "🔴 OFFLINE"

def ordenar_df(df: pd.DataFrame, modo: str) -> pd.DataFrame:
    """
    Ordena o DataFrame conforme modo escolhido pelo usuário.
    """
    if modo == "Status (ONLINE primeiro) + Nome":
        df["ord"] = df["Status"].map({"ONLINE": 0, "OFFLINE": 1})
        df = df.sort_values(["ord", "Gravador"]).drop(columns=["ord"])
    elif modo == "Tempo (ms) ↑":
        df["Tempo_num"] = pd.to_numeric(df["Tempo (ms)"], errors="coerce")
        df = df.sort_values(by="Tempo_num", ascending=True, na_position="last").drop(columns=["Tempo_num"])
    elif modo == "Tempo (ms) ↓":
        df["Tempo_num"] = pd.to_numeric(df["Tempo (ms)"], errors="coerce")
        df = df.sort_values(by="Tempo_num", ascending=False, na_position="last").drop(columns=["Tempo_num"])
    elif modo == "Nome (A→Z)":
        df = df.sort_values(by="Gravador", ascending=True)
    else:
        # fallback
        df = df.sort_values(by="Gravador", ascending=True)
    return df

# ==========================
# Sidebar (filtros e controles)
# ==========================
with st.sidebar:
    st.header("⚙️ Configurações")
    INTERVALO_ATUALIZACAO = st.slider(
        "Intervalo de atualização (segundos)",
        min_value=15, max_value=600, value=120, step=5
    )
    TIMEOUT = st.slider(
        "Timeout da conexão (segundos)",
        min_value=2, max_value=30, value=10, step=1
    )

    st.markdown("---")
    st.subheader("🔎 Filtros")
    BUSCA = st.text_input("Buscar por nome/IP", placeholder="Ex.: RJ-RJO ou 201.59...")
    STATUS_SEL = st.selectbox("Status", options=["Todos", "ONLINE", "OFFLINE"], index=0)

    st.markdown("---")
    MODE = st.radio("Modo de exibição", options=["Compacto (tabela)", "Cards compactos"], index=0)
    COLS = st.slider("Cards por linha (no modo cards)", min_value=3, max_value=6, value=6)
    ORDENACAO = st.selectbox(
        "Ordenar por",
        options=["Status (ONLINE primeiro) + Nome", "Tempo (ms) ↑", "Tempo (ms) ↓", "Nome (A→Z)"],
        index=0
    )

    st.markdown("---")
    if st.button("🔄 Verificar agora"):
        st.rerun()

    # Auto-atualização (opcional): instale o pacote e descomente abaixo
    # pip install streamlit-autorefresh
    # from streamlit_autorefresh import st_autorefresh
    # st_autorefresh(interval=INTERVALO_ATUALIZACAO * 1000, key="auto_refresh_key")

# ==========================
# Header
# ==========================
st.title("📹 Monitoramento de Gravadores")
st.caption(f"Última verificação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.divider()

# ==========================
# Medição + filtros + ordenação
# ==========================
linhas = medir_todos(GRAVADORES, TIMEOUT)
df = pd.DataFrame(linhas)

# Ordenação antes/apos filtros conforme necessidade:
df = ordenar_df(df, ORDENACAO)

# Aplica filtros
df_view = aplica_filtros(df, BUSCA, STATUS_SEL if STATUS_SEL != "Todos" else "")

# ==========================
# Resumo (totais)
# ==========================
on, off, tot = resumo(df_view)
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(label="ONLINE", value=on)
with c2:
    st.metric(label="OFFLINE", value=off)
with c3:
    st.metric(label="TOTAL (após filtros)", value=tot)

st.divider()

# ==========================
# Estilos compactos (opcional)
# ==========================

st.markdown("""
<style>
/* Títulos e linhas compactas (mantendo topo seguro) */
.card-title { font-size: 0.98rem; font-weight: 700; }
.card-sub { color: #9aa0a6; font-size: 0.82rem; }
.card-line { font-size: 0.9rem; }

/* Aumenta o topo para evitar corte do header */
.block-container { padding-top: 2rem; }

/* Opcional: um pequeno espaçamento abaixo do título principal */
h1, .stMarkdown h1 { margin-top: 0.5rem !important; }
</style>
""", unsafe_allow_html=True)


# ==========================
# Exibição (Tabela ou Cards)
# ==========================
if MODE == "Compacto (tabela)":
    # Tabela enxuta, ideal para ~50 gravadores
    df_show = df_view.copy()
    df_show["Status"] = df_show["Status"].apply(status_badge)

    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True
    )
    st.caption(f"Timeout: {TIMEOUT}s • Atualização automática (se habilitada): {INTERVALO_ATUALIZACAO}s")

else:
    # Cards compactos com grid responsivo
    cols = st.columns(COLS)

    # Fixar ordem de colunas para index por posição
    col_ordem = ["Gravador", "IP", "Porta", "Status", "Tempo (ms)"]
    df_cards = df_view[col_ordem].copy()

    for i, row in enumerate(df_cards.itertuples(index=False, name=None)):
        # row é uma tupla: (Gravador, IP, Porta, Status, TempoMS)
        gravador, ip, porta, status, tempo_ms = row
        tempo_txt = f"{tempo_ms} ms" if isinstance(tempo_ms, (int, float)) else "—"

        with cols[i % COLS]:
            st.container(border=True)
            st.markdown(f"<div class='card-title'>{gravador}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-sub'>IP: <code>{ip}</code> • Porta: <code>{porta}</code></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-line'>{status_badge(status)} &nbsp;|&nbsp; ⏱️ {tempo_txt}</div>", unsafe_allow_html=True)

    st.caption(f"Timeout: {TIMEOUT}s • Atualização automática (se habilitada): {INTERVALO_ATUALIZACAO}s")
