# ============================================================
#   database.py — Controle de produtos postados + estatísticas
# ============================================================

import json
import os
import logging
from datetime import datetime, date

log = logging.getLogger(__name__)

POSTADOS_FILE  = "data/postados.json"
STATS_FILE     = "data/stats.json"

# ── Produtos postados ────────────────────────────────────────

def _load_postados() -> dict:
    if os.path.exists(POSTADOS_FILE):
        try:
            with open(POSTADOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"links": [], "total": 0}


def _save_postados(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(POSTADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ja_postado(link: str) -> bool:
    data = _load_postados()
    return link in data["links"]


def marcar_postado(link: str):
    data = _load_postados()
    if link not in data["links"]:
        data["links"].append(link)
        data["total"] += 1
        # Mantém só os últimos 1000
        data["links"] = data["links"][-1000:]
        _save_postados(data)


def total_postados() -> int:
    return _load_postados().get("total", 0)


# ── Estatísticas ─────────────────────────────────────────────

def _load_stats() -> dict:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "posts_total": 0,
        "posts_canal": 0,
        "buscas_manuais": 0,
        "por_categoria": {},
        "por_dia": {},
        "inicio": datetime.now().isoformat(),
    }


def _save_stats(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def registrar_post(canal: bool = True, keyword: str = ""):
    s = _load_stats()
    s["posts_total"] = s.get("posts_total", 0) + 1
    if canal:
        s["posts_canal"] = s.get("posts_canal", 0) + 1

    if keyword:
        cat = s.setdefault("por_categoria", {})
        cat[keyword] = cat.get(keyword, 0) + 1

    hoje = date.today().isoformat()
    dia = s.setdefault("por_dia", {})
    dia[hoje] = dia.get(hoje, 0) + 1

    _save_stats(s)


def registrar_busca():
    s = _load_stats()
    s["buscas_manuais"] = s.get("buscas_manuais", 0) + 1
    _save_stats(s)


def get_stats() -> dict:
    return _load_stats()
