import streamlit as st
import subprocess
import time
import platform
import os
import random
from datetime import datetime

GRAVADORES = {
    "RJ-RJO-MAR": "201.59.252.38",
    "RJ-JDAR-JDAR": "200.222.243.62",
    "RJ-CHM-CHM": "200.165.139.102"
}

INTERVALO_ATUALIZACAO = 60
# --------------------------------------------- #

def rodando_na_nuvem():
    # Streamlit Cloud define essa variável
    return os.getenv("STREAMLIT_RUNTIME") is not None

def esta_online(ip):
    # 🌐 NUVEM → modo demo
    if rodando_na_nuvem():
        return random.choice([True, True, True, False])  # maioria online

    # 🏠 LOCAL → ping real
    sistema = platform.system().lower()
    if sistema == "windows":
        comando = ["ping", "-n", "1", ip]
    else:
        comando = ["ping", "-c", "1", ip]

    resposta = subprocess.run(
        comando,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return resposta.returncode == 0

# ---------------- DASHBOARD ---------------- #
st.set_page_config(page_title="Monitor de Gravadores")

st.title("📹 Monitoramento de Gravadores")

if rodando_na_nuvem():
    st.warning("⚠️ Modo DEMO ativo (ambiente de nuvem)")

st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.divider()

for nome, ip in GRAVADORES.items():
    online = esta_online(ip)
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"**{nome}**")
        st.caption(ip)

    with col2:
        if online:
            st.success("🟢 ONLINE")
        else:
            st.error("🔴 OFFLINE")

st.caption(f"Atualiza automaticamente a cada {INTERVALO_ATUALIZACAO} segundos")

time.sleep(INTERVALO_ATUALIZACAO)
st.rerun()