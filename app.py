import socket
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st


# ==========================
# CONFIG DA PÁGINA
# ==========================
st.set_page_config(page_title="Monitor de Gravadores", page_icon="📹", layout="wide")


# ==========================
# AJUSTES PRINCIPAIS
# ==========================
AUTO_REFRESH_MIN = 5  # atualizar automaticamente a cada 5 minutos

# Fase A: varredura rápida
PHASE_A_TIMEOUT = 1.5
PHASE_A_WORKERS_START = 50
PHASE_A_WORKERS_MIN = 20
PHASE_A_WORKERS_MAX = 80

# Fase B: confirmação só dos OFFLINE da fase A
PHASE_B_TIMEOUT = 3.0
PHASE_B_WORKERS_START = 30
PHASE_B_WORKERS_MIN = 10
PHASE_B_WORKERS_MAX = 50

# Adaptação de concorrência (baseado em taxa de erros/timeouts)
ERROR_RATE_UPPER = 0.12  # acima disso, reduz workers
ERROR_RATE_LOWER = 0.03  # abaixo disso, pode aumentar workers
WORKERS_STEP = 10        # quanto sobe/desce por rodada


# ==========================
# LISTA FIXA (COLE AQUI)
# ==========================
GRAVADORES = [  {"nome": "RJ-RJO-MAR", "ip": "201.59.252.38", "porta": 37777, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    {"nome": "RJ-JDAR-JDAR", "ip": "200.222.243.62", "porta": 50000, "site": "RIO DE JANEIRO", "cidade": "RJ", "ativo": True},
    
]


# ==========================
# TELEMETRIA
# ==========================
@dataclass
class RoundStats:
    total: int
    online: int
    offline: int
    errors: int
    avg_ms: int
    p95_ms: int
    phase: str
    timeout: float
    workers_used: int


# ==========================
# TCP CHECK (stdlib)
# ==========================
def testar_conexao_tcp(ip: str, porta: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, porta), timeout=timeout):
            return True
    except OSError:
        return False


def _verificar_item(item: dict, timeout: float) -> dict:
    nome = item.get("nome", "")
    ip = item.get("ip", "")
    porta = int(item.get("porta", 0))
    site = item.get("site", "")
    cidade = item.get("cidade", "")
    ativo = bool(item.get("ativo", True))

    inicio = time.perf_counter()
    ok = False
    error = False

    if ativo and ip and porta:
        try:
            ok = testar_conexao_tcp(ip, porta, timeout=timeout)
        except OSError:
            ok = False
            error = True
    else:
        ok = False

    dur_ms = int((time.perf_counter() - inicio) * 1000)

    return {
        "Nome": nome,
        "IP": ip,
        "Porta": porta,
        "Site": site,
        "Cidade": cidade,
        "Ativo": ativo,
        "Status": "ONLINE" if ok else "OFFLINE",
        "Latência (ms)": dur_ms if ok else None,
        "_dur_ms": dur_ms,
        "_error": bool(error) if not ok else False,
        "Última verificação": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _rodar_fase(
    gravadores: list[dict],
    timeout: float,
    workers: int,
    phase_name: str,
) -> tuple[pd.DataFrame, RoundStats]:
    total = len(gravadores)
    if total == 0:
        df_empty = pd.DataFrame(
            columns=[
                "Nome", "IP", "Porta", "Site", "Cidade", "Ativo",
                "Status", "Latência (ms)", "Última verificação"
            ]
        )
        stats = RoundStats(0, 0, 0, 0, 0, 0, phase_name, timeout, workers)
        return df_empty, stats

    prog = st.progress(0, text=f"{phase_name}: verificando... (0/{total})")
    info = st.empty()

    results: list[dict] = []
    workers_used = max(1, min(int(workers), total))

    done = 0
    with ThreadPoolExecutor(max_workers=workers_used) as ex:
        futures = [ex.submit(_verificar_item, g, timeout) for g in gravadores]
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            prog.progress(done / total, text=f"{phase_name}: verificando... ({done}/{total})")
            if done % 10 == 0 or done == total:
                info.write(f"{phase_name}: {done}/{total} concluídos")

    prog.empty()
    info.empty()

    df = pd.DataFrame(results)

    online = int((df["Status"] == "ONLINE").sum()) if not df.empty else 0
    offline = total - online
    errors = int(df["_error"].sum()) if not df.empty else 0

    durs = df["_dur_ms"].tolist() if not df.empty else []
    avg_ms = int(sum(durs) / len(durs)) if durs else 0
    if durs:
        durs_sorted = sorted(durs)
        p95 = durs_sorted[min(len(durs_sorted) - 1, int(len(durs_sorted) * 0.95))]
    else:
        p95 = 0

    stats = RoundStats(
        total=total,
        online=online,
        offline=offline,
        errors=errors,
        avg_ms=avg_ms,
        p95_ms=int(p95),
        phase=phase_name,
        timeout=timeout,
        workers_used=workers_used,
    )
    return df, stats


def _adapt_workers(current: int, error_rate: float, wmin: int, wmax: int) -> int:
    nxt = int(current)
    if error_rate > ERROR_RATE_UPPER:
        nxt = max(wmin, nxt - WORKERS_STEP)
    elif error_rate < ERROR_RATE_LOWER:
        nxt = min(wmax, nxt + WORKERS_STEP)
    return nxt


def verificar_todos_duas_fases(gravadores: list[dict]) -> tuple[pd.DataFrame, dict]:
    # Persistência entre reruns
    if "workers_a" not in st.session_state:
        st.session_state.workers_a = PHASE_A_WORKERS_START
    if "workers_b" not in st.session_state:
        st.session_state.workers_b = PHASE_B_WORKERS_START

    # Fase A
    df_a, stats_a = _rodar_fase(
        gravadores,
        timeout=PHASE_A_TIMEOUT,
        workers=int(st.session_state.workers_a),
        phase_name="Fase A (rápida)",
    )

    err_rate_a = (stats_a.errors / stats_a.total) if stats_a.total else 0.0
    st.session_state.workers_a = _adapt_workers(
        current=int(st.session_state.workers_a),
        error_rate=err_rate_a,
        wmin=PHASE_A_WORKERS_MIN,
        wmax=PHASE_A_WORKERS_MAX,
    )

    # Offline para confirmar
    offline_items: list[dict] = []
    if not df_a.empty:
        offline_rows = df_a[df_a["Status"] == "OFFLINE"]
        offline_keys = set(zip(offline_rows["IP"].astype(str), offline_rows["Porta"].astype(int)))

        for g in gravadores:
            k = (str(g.get("ip", "")), int(g.get("porta", 0)))
            if k in offline_keys:
                offline_items.append(g)

    # Fase B (apenas offline)
    df_b, stats_b = _rodar_fase(
        offline_items,
        timeout=PHASE_B_TIMEOUT,
        workers=int(st.session_state.workers_b),
        phase_name="Fase B (confirmação)",
    )

    err_rate_b = (stats_b.errors / stats_b.total) if stats_b.total else 0.0
    st.session_state.workers_b = _adapt_workers(
        current=int(st.session_state.workers_b),
        error_rate=err_rate_b,
        wmin=PHASE_B_WORKERS_MIN,
        wmax=PHASE_B_WORKERS_MAX,
    )

    # Merge: B sobrescreve OFFLINE da A
    if df_a.empty:
        df_final = df_b
    elif df_b.empty:
        df_final = df_a
    else:
        key_cols = ["IP", "Porta"]
        a = df_a.set_index(key_cols, drop=False)
        b = df_b.set_index(key_cols, drop=False)
        a.update(b)
        df_final = a.reset_index(drop=True)

    # Limpa colunas internas + bolinha
    if not df_final.empty:
        for c in ("_dur_ms", "_error"):
            if c in df_final.columns:
                df_final = df_final.drop(columns=[c])

        if "●" not in df_final.columns:
            df_final.insert(0, "●", df_final["Status"].map({"ONLINE": "🟢", "OFFLINE": "🔴"}))

    meta = {
        "stats_a": stats_a.__dict__,
        "stats_b": stats_b.__dict__,
        "workers_next_a": int(st.session_state.workers_a),
        "workers_next_b": int(st.session_state.workers_b),
    }
    return df_final, meta


# ==========================
# ESTADO / UTILITÁRIOS UI
# ==========================
def _ensure_state():
    st.session_state.setdefault("df", None)
    st.session_state.setdefault("meta", None)
    st.session_state.setdefault("last_check_at", None)
    st.session_state.setdefault("next_check_at", None)
    st.session_state.setdefault("is_checking", False)


def _seconds_left() -> int:
    nxt = st.session_state.get("next_check_at")
    if not nxt:
        return 0
    return max(0, int((nxt - datetime.now()).total_seconds()))


def _format_mmss(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"


# ==========================
# APP
# ==========================
st.title("📹 Monitor de Gravadores")
_ensure_state()

if not GRAVADORES:
    st.warning("Cole sua lista GRAVADORES no topo do arquivo app.py.")
    st.stop()

# Atualiza contador a cada 1s sem refazer testes (se disponível)
try:
    st.autorefresh(interval=1000, key="countdown_tick")
except Exception:
    pass

# Primeira vez: agenda agora
if st.session_state.next_check_at is None:
    st.session_state.next_check_at = datetime.now()

# Quando chega a hora (e não está verificando), executa verificação completa
if (datetime.now() >= st.session_state.next_check_at) and (not st.session_state.is_checking):
    st.session_state.is_checking = True

    df, meta = verificar_todos_duas_fases(GRAVADORES)

    st.session_state.df = df
    st.session_state.meta = meta
    st.session_state.last_check_at = datetime.now()
    st.session_state.next_check_at = st.session_state.last_check_at + timedelta(minutes=AUTO_REFRESH_MIN)

    st.session_state.is_checking = False
    st.rerun()

# Não renderiza dashboard enquanto ainda está “montando” a rodada
if st.session_state.is_checking or st.session_state.df is None:
    st.info("Executando verificação inicial... aguarde.")
    st.stop()

df = st.session_state.df.copy()

# ==========================
# DASHBOARD (após verificação completa)
# ==========================
total = len(df)
online = int((df["Status"] == "ONLINE").sum())
offline = total - online

cols = st.columns([1, 1, 1, 2])
cols[0].metric("Total", total)
cols[1].metric("Online", online)
cols[2].metric("Offline", offline)
cols[3].metric("Próxima atualização em", _format_mmss(_seconds_left()))

st.divider()

# ==========================
# CONTROLES (filtros/ordem)
# ==========================
c1, c2, c3, c4 = st.columns([1.2, 1.2, 3, 1.2])

f_status = c1.selectbox("Mostrar", ["Todos", "Somente Online", "Somente Offline"], index=0)
ordem = c2.selectbox("Ordenar por", ["Nome", "Status", "Cidade", "Última verificação"], index=0)
texto = c3.text_input("Filtro por texto (Nome, IP, Site, Cidade)", value="").strip().lower()
show_meta = c4.checkbox("Métricas", value=False)

# Aplica filtro status
if f_status == "Somente Online":
    df = df[df["Status"] == "ONLINE"]
elif f_status == "Somente Offline":
    df = df[df["Status"] == "OFFLINE"]

# Aplica filtro texto
if texto:
    mask = (
        df["Nome"].astype(str).str.lower().str.contains(texto, na=False)
        | df["IP"].astype(str).str.lower().str.contains(texto, na=False)
        | df["Site"].astype(str).str.lower().str.contains(texto, na=False)
        | df["Cidade"].astype(str).str.lower().str.contains(texto, na=False)
    )
    df = df[mask]

# Ordenação (Status: ONLINE primeiro)
if ordem == "Status":
    df["_ord"] = df["Status"].map({"ONLINE": 0, "OFFLINE": 1}).fillna(2).astype(int)
    df = df.sort_values(["_ord", "Nome"], ascending=[True, True]).drop(columns=["_ord"])
else:
    df = df.sort_values(ordem, ascending=True)

# ==========================
# TABELA
# ==========================
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Ativo": st.column_config.CheckboxColumn("Ativo"),
        "Latência (ms)": st.column_config.NumberColumn("Latência (ms)", format="%d"),
    },
)

# ==========================
# MÉTRICAS (opcional)
# ==========================
if show_meta and st.session_state.meta:
    with st.expander("Detalhes da rodada (Fase A / Fase B)"):
        st.json(st.session_state.meta)