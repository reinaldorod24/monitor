import streamlit as st
import socket
import time
from datetime import datetime

GRAVADORES = {
    "RJ-RJO-MAR": ("201.59.252.38", 80),
    "RJ-JDAR-JDAR": ("200.222.243.62", 80),
    "RJ-CHM-CHM": ("200.165.139.102", 80)
}

INTERVALO_ATUALIZACAO = 60
TIMEOUT = 3  # segundos

def esta_online(ip, porta):
    try:
        with socket.create_connection((ip, porta), timeout=TIMEOUT):
            return True
    except:
        return False

st.set_page_config(page_title="Monitor de Gravadores")

st.title("📹 Monitoramento de Gravadores")
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.divider()

for nome, (ip, porta) in GRAVADORES.items():
    online = esta_online(ip, porta)
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"**{nome}**")
        st.caption(f"{ip}:{porta}")

    with col2:
        if online:
            st.success("🟢 ONLINE")
        else:
            st.error("🔴 OFFLINE")

st.caption(f"Atualiza a cada {INTERVALO_ATUALIZACAO} segundos")

time.sleep(INTERVALO_ATUALIZACAO)
st.rerun()