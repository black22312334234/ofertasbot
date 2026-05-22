# ============================================================
#   formatter.py — Formata as mensagens para o Telegram
# ============================================================

import random

EMOJIS = ["🔥", "⚡", "💥", "🚨", "🎯", "🤑", "💣", "🏆"]

CTAS = [
    "👆 Garanta antes de acabar!",
    "🛒 Corra, estoque limitado!",
    "⏰ Oferta por tempo limitado!",
    "✅ Clique e aproveite o desconto!",
    "💨 Voando dos estoques!",
    "🔔 Não perca essa oportunidade!",
    "💸 Economize agora!",
]


def formatar_oferta(p: dict, canal: bool = True) -> str:
    """
    Formata mensagem de produto.
    canal=True → mensagem para o canal (mais enxuta)
    canal=False → resposta no grupo (pode ter mais info)
    """
    emoji = random.choice(EMOJIS)
    cta   = random.choice(CTAS)

    nome = p["nome"]
    if len(nome) > 65:
        nome = nome[:65] + "…"

    # Linha de preço
    atual  = p.get("preco_float")
    antigo = p.get("preco_antigo_float")
    desc   = p.get("desconto", 0)

    if atual and antigo and desc > 0:
        linha_preco = (
            f"💸 De <s>R$ {antigo:.2f}</s> "
            f"por <b>R$ {atual:.2f}</b>\n"
            f"🏷️ <b>{desc}% OFF</b>"
        )
    elif atual:
        linha_preco = f"💸 <b>R$ {atual:.2f}</b>"
    else:
        linha_preco = f"💸 <b>R$ {p.get('preco_str', 'Ver na Amazon')}</b>"

    # Rating
    rating_linha = ""
    if p.get("rating"):
        rating_linha = f"\n⭐ {p['rating']}"

    link = p["link"]

    msg = (
        f"{emoji} <b>OFERTA AMAZON</b>\n\n"
        f"🎁 <b>{nome}</b>\n\n"
        f"{linha_preco}"
        f"{rating_linha}\n\n"
        f"{cta}\n\n"
        f"🛒 <a href='{link}'>Comprar com desconto</a>\n\n"
        f"<i>📌 Link de afiliado Amazon</i>"
    )
    return msg.strip()


def formatar_stats(s: dict) -> str:
    from datetime import datetime

    inicio = s.get("inicio", "")
    try:
        inicio_dt = datetime.fromisoformat(inicio)
        dias = (datetime.now() - inicio_dt).days
        inicio_fmt = inicio_dt.strftime("%d/%m/%Y")
    except Exception:
        dias = 0
        inicio_fmt = "?"

    # Top 3 categorias
    cats = s.get("por_categoria", {})
    top_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:3]
    cats_txt = "\n".join(f"  • {k}: {v}x" for k, v in top_cats) or "  (nenhuma ainda)"

    # Posts dos últimos 7 dias
    from datetime import date, timedelta
    hoje = date.today()
    dias_recentes = []
    for i in range(6, -1, -1):
        d = (hoje - timedelta(days=i)).isoformat()
        n = s.get("por_dia", {}).get(d, 0)
        dias_recentes.append(f"  {d[5:]}: {n} post{'s' if n != 1 else ''}")
    dias_txt = "\n".join(dias_recentes)

    return (
        f"📊 <b>PAINEL DE ESTATÍSTICAS</b>\n\n"
        f"🚀 Bot ativo desde: {inicio_fmt} ({dias} dia{'s' if dias != 1 else ''})\n\n"
        f"📦 Posts totais: <b>{s.get('posts_total', 0)}</b>\n"
        f"📡 Posts no canal: <b>{s.get('posts_canal', 0)}</b>\n"
        f"🔎 Buscas manuais: <b>{s.get('buscas_manuais', 0)}</b>\n\n"
        f"🏆 Top categorias:\n{cats_txt}\n\n"
        f"📅 Últimos 7 dias:\n{dias_txt}"
    )
