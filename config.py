import os

# ── TELEGRAM ────────────────────────────────────────────────
TOKEN        = os.getenv("TELEGRAM_TOKEN", "")
CANAL_ID     = os.getenv("CANAL_ID", "@amznofertasbr")
GRUPO_ID     = os.getenv("GRUPO_ID", "")
ADMIN_IDS    = [7241393497]

# ── AMAZON AFILIADO ──────────────────────────────────────────
TAG = os.getenv("AMAZON_TAG", "linkfinderOf-20")

# ── REGRAS DE OFERTA ─────────────────────────────────────────
DESCONTO_MINIMO   = 15
PRECO_MAXIMO      = 5000.0
PRECO_MINIMO      = 20.0

# ── AGENDAMENTO ───────────────────────────────────────────────
INTERVALO_CANAL   = 30
INTERVALO_BUSCA   = 50

# ── CATEGORIAS PARA POSTAGEM AUTOMÁTICA ──────────────────────
CATEGORIAS = [
    # Tecnologia
    "smartphone",
    "headset gamer",
    "fone de ouvido bluetooth",
    "smartwatch",
    "tablet",
    "notebook",
    "monitor gamer",
    "teclado mecânico",
    "mouse sem fio",
    "SSD",
    "caixa de som bluetooth",
    "carregador rápido",
    "câmera de segurança",
    "impressora",
    # Casa
    "air fryer",
    "aspirador de pó",
    "panela elétrica",
    "ventilador torre",
    "cafeteira",
    "liquidificador",
    "ferro de passar",
    "micro-ondas",
    "purificador de água",
    "conjunto de cama",
    # Esportes
    "tênis esportivo",
    "whey protein",
    "suplemento alimentar",
    "bicicleta ergométrica",
    "halteres",
    "tapete de yoga",
    "mochila esportiva",
    "garrafa térmica",
    # Beleza
    "secador de cabelo",
    "prancha de cabelo",
    "perfume importado",
    "kit skincare",
    "barbeador elétrico",
    "escova elétrica dental",
    # Livros
    "livro autoajuda",
    "livro bestseller",
    "livro infantil",
    "mangá",
    # Bebês
    "carrinho de bebê",
    "berço",
    "fralda",
    "banheira de bebê",
    "monitor de bebê",
    "brinquedo bebê",
    "mamadeira",
]
