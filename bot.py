# ============================================================
#   bot.py — Bot principal com todos os handlers
# ============================================================

import logging
import random
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

import config
from scraper import buscar_produtos
from database import (
    ja_postado, marcar_postado, registrar_post,
    registrar_busca, get_stats, total_postados,
)
from formatter import formatar_oferta, formatar_stats

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        
    ],
)
log = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def menu_principal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Ver ofertas agora",    callback_data="cb_ofertas")],
        [InlineKeyboardButton("🔎 Pesquisar produto",    callback_data="cb_pesquisar")],
        [InlineKeyboardButton("🗂️ Ver categorias",       callback_data="cb_categorias")],
    ])


GRUPOS = {
    "📱 Tecnologia": ["smartphone", "headset gamer", "fone de ouvido bluetooth", "smartwatch", "tablet", "notebook", "monitor gamer", "teclado mecânico", "mouse sem fio", "SSD"],
    "🏠 Casa": ["air fryer", "aspirador de pó", "panela elétrica", "ventilador torre", "cafeteira", "liquidificador", "micro-ondas"],
    "💪 Esportes": ["tênis esportivo", "whey protein", "suplemento alimentar", "bicicleta ergométrica", "halteres", "tapete de yoga"],
    "💄 Beleza": ["secador de cabelo", "prancha de cabelo", "perfume importado", "kit skincare", "barbeador elétrico"],
    "📚 Livros": ["livro autoajuda", "livro bestseller", "livro infantil", "mangá"],
    "👶 Bebês": ["carrinho de bebê", "berço", "fralda", "banheira de bebê", "brinquedo bebê"],
}

def menu_categorias():
    botoes = []
    for nome in GRUPOS:
        botoes.append([InlineKeyboardButton(nome, callback_data=f"grupo_{nome}")])
    botoes.append([InlineKeyboardButton("⬅️ Voltar", callback_data="cb_menu")])
    return InlineKeyboardMarkup(botoes)


async def enviar_produto(produto: dict, chat_id, bot, canal: bool = False):
    """Envia produto com foto. Fallback para texto se foto falhar."""
    texto = formatar_oferta(produto, canal=canal)
    imagem = produto.get("imagem", "")

    try:
        if imagem:
            await bot.send_photo(
                chat_id=chat_id,
                photo=imagem,
                caption=texto,
                parse_mode=ParseMode.HTML,
            )
        else:
            raise ValueError("Sem imagem")
    except Exception:
        # Fallback: só texto com preview do link
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=texto,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
        except TelegramError as e:
            log.error(f"Erro ao enviar produto: {e}")


# ── /start ───────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.effective_user.first_name or "você"
    await update.message.reply_text(
        f"👋 Olá, <b>{nome}</b>!\n\n"
        f"🛒 Sou o bot de ofertas da Amazon.\n"
        f"Encontro os melhores descontos e aviso você!\n\n"
        f"Use o menu abaixo para começar:",
        parse_mode=ParseMode.HTML,
        reply_markup=menu_principal(),
    )


# ── /admin ───────────────────────────────────────────────────

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⛔ Acesso restrito.")
        return

    s = get_stats()
    texto = formatar_stats(s)

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 Postar agora no canal", callback_data="adm_postar_canal")],
        [InlineKeyboardButton("🔄 Atualizar stats",       callback_data="adm_stats")],
    ])

    await update.message.reply_text(texto, parse_mode=ParseMode.HTML, reply_markup=teclado)


# ── /buscar ──────────────────────────────────────────────────

async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    termo = " ".join(context.args)
    if not termo:
        await update.message.reply_text(
            "🔎 Use assim:\n/buscar <b>nome do produto</b>\n\nEx: /buscar headset gamer",
            parse_mode=ParseMode.HTML,
        )
        return

    await _executar_busca(update.message, context.bot, termo, usuario=True)


# ── Callbacks ─────────────────────────────────────────────────

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Menu
    if data == "cb_menu":
        await query.message.reply_text(
            "📋 Menu principal:", reply_markup=menu_principal()
        )

    # Ofertas gerais
    elif data == "cb_ofertas":
        await query.message.reply_text("🔍 Buscando ofertas, aguarde um instante...")
        keyword = random.choice(config.CATEGORIAS)
        await _executar_busca(query.message, context.bot, keyword, usuario=True)

    # Pedir pesquisa
    elif data == "cb_pesquisar":
        context.user_data["aguardando_busca"] = True
        await query.message.reply_text(
            "🔎 Me diga o produto que você quer buscar:\n\n"
            "(ou use /buscar <b>produto</b> a qualquer momento)",
            parse_mode=ParseMode.HTML,
        )

    # Categorias
    elif data == "cb_categorias":
        await query.message.reply_text(
            "🗂️ Escolha uma categoria:", reply_markup=menu_categorias()
        )

    elif data.startswith("grupo_"):
        keyword = random.choice(GRUPOS.get(data[6:], config.CATEGORIAS))
        await query.message.reply_text(f"🔍 Buscando em <b>{data[6:]}</b>...", parse_mode=ParseMode.HTML)
        await _executar_busca(query.message, context.bot, keyword, usuario=True)

    elif data.startswith("cat_"):
        keyword = data[4:]
        await query.message.reply_text(f"🔍 Buscando <b>{keyword}</b>...", parse_mode=ParseMode.HTML)
        await _executar_busca(query.message, context.bot, keyword, usuario=True)

    # Admin: postar no canal agora
    elif data == "adm_postar_canal":
        uid = update.effective_user.id
        if not is_admin(uid):
            return
        await query.message.reply_text("📡 Postando no canal...")
        ok = await _postar_no_canal(context.bot)
        msg = "✅ Postado no canal!" if ok else "😕 Nenhum produto novo encontrado."
        await query.message.reply_text(msg)

    # Admin: atualizar stats
    elif data == "adm_stats":
        uid = update.effective_user.id
        if not is_admin(uid):
            return
        s = get_stats()
        await query.message.edit_text(
            formatar_stats(s),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📡 Postar agora no canal", callback_data="adm_postar_canal")],
                [InlineKeyboardButton("🔄 Atualizar stats",       callback_data="adm_stats")],
            ]),
        )


# ── Receber texto (busca manual por mensagem) ─────────────────

async def receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("aguardando_busca"):
        return

    keyword = update.message.text.strip()
    context.user_data["aguardando_busca"] = False

    await update.message.reply_text(
        f"🔍 Buscando <b>{keyword}</b>...", parse_mode=ParseMode.HTML
    )
    await _executar_busca(update.message, context.bot, keyword, usuario=True)


# ── Core: executar busca e enviar resultados ──────────────────

async def _executar_busca(message, bot, keyword: str, usuario: bool = True):
    """Busca produtos e envia para o chat onde veio a mensagem."""
    desc_min = 0 if usuario else config.DESCONTO_MINIMO  # manual aceita qualquer

    produtos = buscar_produtos(keyword, desc_minimo=desc_min, limite=3)
    novos = [p for p in produtos if not ja_postado(p["link"])]

    if not novos:
        await message.reply_text(
            "😕 Nenhuma oferta nova encontrada para esse produto agora.\n"
            "Tente outro termo ou aguarde alguns minutos!",
        )
        return

    chat_id = message.chat_id
    for p in novos:
        await enviar_produto(p, chat_id, bot, canal=False)
        marcar_postado(p["link"])
        registrar_post(canal=False, keyword=keyword)
        await asyncio.sleep(1.5)

    if usuario:
        registrar_busca()

    await message.reply_text(
        f"✅ {len(novos)} oferta(s) encontrada(s)!\n\n"
        f"Use /buscar <b>produto</b> para pesquisar qualquer coisa.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Mais ofertas",      callback_data="cb_ofertas")],
            [InlineKeyboardButton("🗂️ Ver categorias",    callback_data="cb_categorias")],
        ]),
    )


async def _postar_no_canal(bot) -> bool:
    """Busca uma oferta nova e posta no canal. Retorna True se postou."""
    if not config.CANAL_ID:
        log.warning("CANAL_ID não configurado!")
        return False

    keyword = random.choice(config.CATEGORIAS)
    produtos = buscar_produtos(keyword, desc_minimo=config.DESCONTO_MINIMO, limite=5)
    novos = [p for p in produtos if not ja_postado(p["link"])]

    if not novos:
        log.info(f"[CANAL] Sem produtos novos para '{keyword}'")
        return False

    p = novos[0]
    await enviar_produto(p, config.CANAL_ID, bot, canal=True)
    marcar_postado(p["link"])
    registrar_post(canal=True, keyword=keyword)
    log.info(f"[CANAL] Postado: {p['nome'][:50]} | {p['desconto']}% OFF")
    return True


# ── Job: postagem automática ──────────────────────────────────

async def job_canal(context: ContextTypes.DEFAULT_TYPE):
    log.info("[JOB] Iniciando postagem automática no canal...")
    await _postar_no_canal(context.bot)


# ── Main ──────────────────────────────────────────────────────

def main():
    import os
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    app = ApplicationBuilder().token(config.TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("admin",  cmd_admin))
    app.add_handler(CommandHandler("buscar", cmd_buscar))

    # Callbacks dos botões
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Mensagens de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_texto))

    # Job: posta no canal automaticamente
    if config.CANAL_ID:
        app.job_queue.run_repeating(
            job_canal,
            interval=config.INTERVALO_CANAL,
            first=15,  # começa 15s após iniciar
        )
        log.info(f"[JOB] Postagem automática: a cada {config.INTERVALO_CANAL}s no canal {config.CANAL_ID}")

    log.info("🚀 BOT AMAZON OFERTAS INICIADO!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
