import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# ==========================
# CONFIGURAÇÃO
# ==========================
st.set_page_config(page_title="Monitor Básico de Gravadores", page_icon="📹", layout="wide")

TIMEOUT = 2.5                # timeout TCP (segundos)
MAX_SIMULTANEO = 30          # 30 por vez (threads)
AUTO_INTERVAL_MS = 2 * 60 * 1000  # 2 minutos


# ==========================
# LISTA DE GRAVADORES (cole seus 120 aqui)
# ==========================
GRAVADORES = [
    {"nome": "MG-VENO-VNO", "ip": "200.165.57.186", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "RJ-VITE-VITE", "ip": "200.202.197.102", "porta": 50000, "site": "SAO JOAO DE MERITI", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-BGU", "ip": "200.222.62.110", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-NLP-NLP", "ip": "187.12.208.162", "porta": 50000, "site": "NILOPOLIS", "cidade": "RJ", "ativo": True},
    {"nome": "MG-BHE-FLO", "ip": "200.222.56.22", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "ES-JAMC-JAMC", "ip": "200.216.113.2", "porta": 50000, "site": "CARIACICA", "cidade": "ES", "ativo": True},
    {"nome": "RJ-VRD-RETK", "ip": "200.222.73.242", "porta": 37777, "site": "VOLTA REDONDA", "cidade": "RJ", "ativo": True},
    {"nome": "MG-SLA-SLA", "ip": "200.165.58.50", "porta": 50000, "site": "SETE LAGOAS", "cidade": "MG", "ativo": True},
    {"nome": "RJ-RJO-RDB", "ip": "189.80.91.190", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-BERO-BERO", "ip": "200.222.73.102", "porta": 50000, "site": "BELFORD ROXO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-SGO-PDAL", "ip": "200.151.9.46", "porta": 37777, "site": "SAO GONCALO", "cidade": "RJ", "ativo": True},
    {"nome": "MG-BET-BET", "ip": "200.97.90.50", "porta": 37777, "site": "BETIM", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-GLO", "ip": "201.18.75.130", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "RJ-QUEA-QUEA", "ip": "200.202.197.74", "porta": 37777, "site": "QUEIMADOS", "cidade": "RJ", "ativo": True},
    {"nome": "MG-JFA-NEA", "ip": "200.216.241.26", "porta": 37777, "site": "JUIZ DE FORA", "cidade": "MG", "ativo": True},
    {"nome": "RJ-SMI-SMI", "ip": "200.202.229.86", "porta": 37777, "site": "SAO JOAO DE MERITI", "cidade": "RJ", "ativo": True},
    {"nome": "MG-UBA-SCW", "ip": "200.165.151.16", "porta": 37777, "site": "UBA", "cidade": "MG", "ativo": True},
    {"nome": "RJ-CRRS-CRRS", "ip": "200.149.2.118", "porta": 37777, "site": "PETROPOLIS", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-UNAR-UNAR", "ip": "189.80.240.2", "porta": 37777, "site": "CABO FRIO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-CVI", "ip": "201.32.212.150", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "MG-CEM-PET", "ip": "200.97.10.218", "porta": 50000, "site": "CONTAGEM", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-BEL", "ip": "200.199.8.224", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-PCS-FSA", "ip": "189.80.142.80", "porta": 37777, "site": "POCOS DE CALDAS", "cidade": "MG", "ativo": True},
    {"nome": "RJ-CPS-CPS", "ip": "200.223.200.90", "porta": 37777, "site": "CAMPOS DOS GOYTACAZES", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-TRL-VZA", "ip": "201.32.212.150", "porta": 37777, "site": "TERESOPOLIS", "cidade": "RJ", "ativo": True},
     {"nome": "MG-NLA-NLA", "ip": "187.76.241.210", "porta": 50000, "site": "NOVA LIMA", "cidade": "MG", "ativo": True},
    {"nome": "MG-VPN-VPN", "ip": "201.59.11.248", "porta": 37777, "site": "VESPASIANO", "cidade": "MG", "ativo": True},
    {"nome": "MG-BET-FDI", "ip": "200.216.252.8", "porta": 50000, "site": "BETIM", "cidade": "MG", "ativo": True},
    {"nome": "MG-BET-IRU", "ip": "200.202.243.240", "porta": 37777, "site": "BETIM", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-INC", "ip": "200.222.50.42", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BMO-BMO", "ip": "187.76.192.226", "porta": 50000, "site": "BRUMADINHO", "cidade": "MG", "ativo": True},
    {"nome": "MG-IIE-CAK", "ip": "187.76.216.194", "porta": 50000, "site": "IBIRITE", "cidade": "MG", "ativo": True},
    {"nome": "MG-IRP-IRP", "ip": "187.76.216.82", "porta": 50000, "site": "IGARAPE", "cidade": "MG", "ativo": True},
    {"nome": "MG-RNS-RNS", "ip": "200.149.101.176", "porta": 37777, "site": "RIBEIRAO DAS NEVES", "cidade": "MG", "ativo": True},
    {"nome": "MG-SRZE-SRZE", "ip": "200.97.16.2", "porta": 37777, "site": "SARZEDO", "cidade": "MG", "ativo": True},
    {"nome": "RJ-RJO-SLC", "ip": "200.202.197.86", "porta": 37777, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "DF-STMK-ETMS", "ip": "189.74.138.5", "porta": 50000, "site": "BRASILIA", "cidade": "DF", "ativo": True},
    {"nome": "DF-SOBD-ETSB", "ip": "201.41.66.78", "porta": 50000, "site": "BRASILIA", "cidade": "DF", "ativo": True},
    {"nome": "GO-GNA-MUT", "ip": "177.201.98.30", "porta": 50000, "site": "GOIANIA", "cidade": "GO", "ativo": True},
    {"nome": "RJ-IGI-IGI", "ip": "200.222.38.14", "porta": 50000, "site": "ITAGUAI", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-PNHE-PNHE", "ip": "200.164.236.106", "porta": 50000, "site": "PINHEIRAL", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-BAMC-BAMC", "ip": "200.222.142.250", "porta": 50000, "site": "MARICA", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-PPUC-PPUC", "ip": "200.165.139.102", "porta": 37777, "site": "CACHOEIRAS DE MACACU", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-PNB", "ip": "189.80.175.46", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "MG-SLU-SLU", "ip": "200.165.79.10", "porta": 50000, "site": "SANTA LUZIA", "cidade": "MG", "ativo": True},
    {"nome": "MG-IBA-IBA", "ip": "200.222.100.154", "porta": 50000, "site": "ITABIRA", "cidade": "MG", "ativo": True},
    {"nome": "MG-IIG-IIG", "ip": "200.216.246.102", "porta": 50000, "site": "IPATINGA", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-CLO", "ip": "200.195.46.50", "porta": 50000, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-DBO", "ip": "200.165.57.192", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-SAV", "ip": "200.149.128.8", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-CPO-CPO", "ip": "200.216.241.234", "porta": 50000, "site": "CAMPO BELO", "cidade": "MG", "ativo": True},
    {"nome": "MG-CUG-CUG", "ip": "200.97.9.174", "porta": 50000, "site": "CORDISBURGO", "cidade": "MG", "ativo": True},
    {"nome": "MG-FMA-FMA", "ip": "200.149.223.114", "porta": 50000, "site": "FORMIGA", "cidade": "MG", "ativo": True},
    {"nome": "MG-VENO-LET", "ip": "200.165.57.250", "porta": 50000, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-VENO-MHE", "ip": "200.151.82.130", "porta": 50000, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "RJ-INOA-INOA", "ip": "200.149.213.130", "porta": 50000, "site": "MARICA", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-IOY-IOY", "ip": "189.80.95.46", "porta": 50000, "site": "ITABORAI", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RBT-RBT", "ip": "189.80.74.38", "porta": 50000, "site": "RIO BONITO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-SALX-SALX", "ip": "200.149.2.142", "porta": 37777, "site": "MAGE", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-VAS-VAS", "ip": "201.18.31.130", "porta": 37777, "site": "VASSOURAS", "cidade": "RJ", "ativo": True},
    {"nome": "GO-ACG-CDL", "ip": "169.254.245.206", "porta": 50000, "site": "APARECIDA DE GOIANIA", "cidade": "GO", "ativo": True},
    {"nome": "GO-PIR-PIR", "ip": "169.254.245.206", "porta": 50000, "site": "PIRES DO RIO", "cidade": "GO", "ativo": True},
    {"nome": "DF-PLAA-ETPL", "ip": "177.202.157.18", "porta": 50000, "site": "BRASILIA", "cidade": "DF", "ativo": True},
    {"nome": "DF-GURX-ETGR", "ip": "179.255.254.206", "porta": 37777, "site": "BRASILIA", "cidade": "DF", "ativo": True},
    {"nome": "ES-JAIP-JAIP", "ip": "189.80.25.90", "porta": 50000, "site": "SERRA", "cidade": "ES", "ativo": True},
    {"nome": "DF-SAMB-ETSN", "ip": "187.52.102.2", "porta": 50000, "site": "BRASILIA", "cidade": "DF", "ativo": True},
    {"nome": "ES-JAMC-SFCO", "ip": "200.199.87.142", "porta": 50000, "site": "CARIACICA", "cidade": "ES", "ativo": True},
    {"nome": "ES-CCA-CCA", "ip": "200.165.57.154", "porta": 50000, "site": "CARIACICA", "cidade": "ES", "ativo": True},
    {"nome": "ES-VVA-NMEX", "ip": "200.216.111.82", "porta": 50000, "site": "VILA VELHA", "cidade": "ES", "ativo": True},
    {"nome": "MG-BHE-STE", "ip": "187.76.239.98", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-BCI", "ip": "200.216.236.58", "porta": 50000, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-ARI-ARI", "ip": "200.195.83.64", "porta": 37777, "site": "ARAGUARI", "cidade": "MG", "ativo": True},
    {"nome": "RJ-JACC-JACC", "ip": "200.222.90.218", "porta": 50000, "site": "ANGRA DOS REIS", "cidade": "RJ", "ativo": True},
    {"nome": "MG-LPD-LPD", "ip": "187.76.219.72", "porta": 37777, "site": "LEOPOLDINA", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-SCR", "ip": "201.32.16.8", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-SOBI-SOBI", "ip": "187.76.239.176", "porta": 37777, "site": "SANTA LUZIA", "cidade": "MG", "ativo": True},
    {"nome": "MG-SRS-SRS", "ip": "189.80.159.24", "porta": 37777, "site": "SANTA RITA DO SAPUCAI", "cidade": "MG", "ativo": True},
    {"nome": "MG-BET-NIT", "ip": "189.80.139.24", "porta": 37777, "site": "BETIM", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-CAZ", "ip": "201.59.6.216", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-ODA", "ip": "200.216.240.240", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-SMW", "ip": "200.216.163.186", "porta": 50000, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-CEM-IND", "ip": "201.18.22.217", "porta": 37777, "site": "CONTAGEM", "cidade": "MG", "ativo": True},
    {"nome": "MG-GVS-SLI", "ip": "200.202.243.233", "porta": 37777, "site": "GOVERNADOR VALADARES", "cidade": "MG", "ativo": True},
    {"nome": "MG-IAN-TAV", "ip": "187.76.239.32", "porta": 37777, "site": "ITAUNA", "cidade": "MG", "ativo": True},
    {"nome": "MG-IIE-IIE", "ip": "187.76.205.248", "porta": 37777, "site": "IBIRITE", "cidade": "MG", "ativo": True},
    {"nome": "MG-PSA-JAU", "ip": "200.223.164.248", "porta": 37777, "site": "POUSO ALEGRE", "cidade": "MG", "ativo": True},
    {"nome": "MG-SND-QFE", "ip": "189.80.149.80", "porta": 37777, "site": "SANTOS DUMONT", "cidade": "MG", "ativo": True},
    {"nome": "RJ-GUPM-GUPM", "ip": "200.149.96.254", "porta": 50000, "site": "GUAPIMIRIM", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-JPRI-JPRI", "ip": "200.222.107.250", "porta": 50000, "site": "JAPERI", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-JPRI-PT64", "ip": "201.18.85.210", "porta": 50000, "site": "JAPERI", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-PAT-PAT", "ip": "201.32.212.158", "porta": 50000, "site": "PARATY", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-JCP", "ip": "201.18.68.190", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-RJO-VGD", "ip": "200.164.148.122", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "MG-JUST-SLW", "ip": "187.76.219.232", "porta": 37777, "site": "RIBEIRAO DAS NEVES", "cidade": "MG", "ativo": True},
    {"nome": "MG-SBA-SBA", "ip": "200.97.11.232", "porta": 37777, "site": "SABARA", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-IND", "ip": "201.18.22.218", "porta": 50000, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-SAR", "ip": "201.18.117.16", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-TUP", "ip": "200.202.220.96", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-BHE-VJA", "ip": "200.165.57.176", "porta": 37777, "site": "BELO HORIZONTE", "cidade": "MG", "ativo": True},
    {"nome": "MG-LGT-SDU", "ip": "201.18.139.64", "porta": 37777, "site": "LAGOA SANTA", "cidade": "MG", "ativo": True},
    {"nome": "MG-MRPS-MRPS", "ip": "187.125.84.192", "porta": 37777, "site": "MARIO CAMPOS", "cidade": "MG", "ativo": True},
    {"nome": "MG-CEM-CON", "ip": "200.165.142.40", "porta": 37777, "site": "CONTAGEM", "cidade": "MG", "ativo": True},
    {"nome": "MG-DVL-CTDI", "ip": "187.76.11.72", "porta": 37777, "site": "DIVINOPOLIS", "cidade": "MG", "ativo": True},
    {"nome": "MG-MCL-CEN", "ip": "200.165.72.32", "porta": 37777, "site": "MONTES CLAROS", "cidade": "MG", "ativo": True},
    {"nome": "MG-JFA-RBR", "ip": "187.76.12.96", "porta": 37777, "site": "JUIZ DE FORA", "cidade": "MG", "ativo": True},
    {"nome": "SP-BRE-PTA", "ip": "200.141.233.144", "porta": 37777, "site": "BARUERI", "cidade": "SP", "ativo": True},
    {"nome": "SP-MCZ-MCZ", "ip": "201.32.38.184", "porta": 37777, "site": "MOGI DAS CRUZES", "cidade": "SP", "ativo": True},
    {"nome": "SP-ARQ-AAU", "ip": "201.18.27.168", "porta": 37777, "site": "ARARAQUARA", "cidade": "SP", "ativo": True},
    {"nome": "SP-LIS-LLU", "ip": "201.59.255.8", "porta": 37777, "site": "LINS", "cidade": "SP", "ativo": True},
    {"nome": "SP-SCL-JSP1", "ip": "200.195.56.80", "porta": 37777, "site": "SAO CARLOS", "cidade": "SP", "ativo": True},
    {"nome": "SP-JAU-JJU", "ip": "201.18.25.248", "porta": 37777, "site": "JAU", "cidade": "SP", "ativo": True},
    {"nome": "SP-ORN-PAF", "ip": "201.18.25.0", "porta": 37777, "site": "OURINHOS", "cidade": "SP", "ativo": True},
    # ... cole os demais até 120
]


# ==========================
# FUNÇÕES
# ==========================
def tcp_check(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def verificar_um(item: dict) -> dict:
    nome = str(item.get("nome", "")).strip()
    ip = str(item.get("ip", "")).strip()
    porta = int(item.get("porta", 0) or 0)
    site = str(item.get("site", "")).strip()
    cidade = str(item.get("cidade", "")).strip()
    ativo = bool(item.get("ativo", True))

    ok = False
    if ativo and ip and porta > 0:
        ok = tcp_check(ip, porta, TIMEOUT)

    return {
        "Nome": nome,
        "IP": ip,
        "Porta": porta,
        "Site": site,
        "Cidade": cidade,
        "Status": "ONLINE" if ok else "OFFLINE",
    }


def verificar_todos(gravadores: list[dict]) -> pd.DataFrame:
    total = len(gravadores)
    if total == 0:
        return pd.DataFrame(columns=["Nome", "IP", "Porta", "Site", "Cidade", "Status"])

    prog = st.progress(0, text=f"Verificando... (0/{total})")
    info = st.empty()

    results: list[dict] = []
    workers = min(MAX_SIMULTANEO, total)

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(verificar_um, g) for g in gravadores]
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            prog.progress(done / total, text=f"Verificando... ({done}/{total})")
            if done % 10 == 0 or done == total:
                info.write(f"Concluídos: {done}/{total}")

    prog.empty()
    info.empty()

    df = pd.DataFrame(results)
    # deixa consistente a ordenação inicial
    if not df.empty and "Nome" in df.columns:
        df = df.sort_values("Nome")
    return df


# ==========================
# ESTADO
# ==========================
if "modo" not in st.session_state:
    st.session_state.modo = "manual"  # "manual" ou "auto"
if "df" not in st.session_state:
    st.session_state.df = None
if "last_run" not in st.session_state:
    st.session_state.last_run = None


# ==========================
# UI - TOPO
# ==========================
st.title("📹 Monitor Básico de Gravadores")

cA, cB, cC = st.columns([1, 1, 3])

with cA:
    if st.button("🔁 Automático (2 min)", use_container_width=True):
        st.session_state.modo = "auto"

with cB:
    if st.button("🖱️ Manual", use_container_width=True):
        st.session_state.modo = "manual"

with cC:
    st.write(f"**Modo atual:** `{st.session_state.modo.upper()}`")
    if st.session_state.last_run:
        st.write(f"Última execução: **{st.session_state.last_run}**")


# ==========================
# AUTO-REFRESH (somente no modo automático)
# ==========================
if st.session_state.modo == "auto":
    st_autorefresh(interval=AUTO_INTERVAL_MS, key="auto_refresh_2min")


# ==========================
# EXECUÇÃO
# ==========================
executar_agora = False

if st.session_state.modo == "manual":
    executar_agora = st.button("▶️ Executar agora", type="primary")

# No automático: executa a cada rerun do autorefresh
if st.session_state.modo == "auto":
    executar_agora = True

if executar_agora:
    if not GRAVADORES:
        st.warning("Cole sua lista de gravadores na variável GRAVADORES.")
        st.stop()

    df = verificar_todos(GRAVADORES)
    st.session_state.df = df
    st.session_state.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==========================
# DASHBOARD + FILTRO + TABELA
# ==========================
if st.session_state.df is None:
    st.info("Selecione o modo e execute a verificação para carregar o dashboard.")
    st.stop()

df_all = st.session_state.df.copy()

# ---- filtro de status (vale para dashboard e tabela)
f_status = st.selectbox("Filtrar por Status", ["Todos", "ONLINE", "OFFLINE"], index=0)

if f_status != "Todos":
    df_view = df_all[df_all["Status"] == f_status].copy()
else:
    df_view = df_all.copy()

# ---- dashboard respeitando filtro
total = len(df_view)
online = int((df_view["Status"] == "ONLINE").sum()) if total else 0
offline = total - online

d1, d2, d3 = st.columns(3)
d1.metric("Total (filtrado)", total)
d2.metric("Online (filtrado)", online)
d3.metric("Offline (filtrado)", offline)

st.divider()

# ---- tabela (inclui Status)
st.dataframe(
    df_view[["Nome", "IP", "Porta", "Site", "Cidade", "Status"]],
    use_container_width=True,
    hide_index=True
)