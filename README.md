# 🛒 Bot de Ofertas Amazon → Telegram

Sistema completo para postar promoções da Amazon automaticamente em canal + grupo do Telegram com links de afiliado.

---

## 📁 Estrutura do Projeto

```
ofertasbot/
├── bot.py           ← Arquivo principal — rode este
├── config.py        ← Suas configurações (token, canal, etc)
├── scraper.py       ← Busca produtos na Amazon
├── database.py      ← Histórico de posts + estatísticas
├── formatter.py     ← Formata as mensagens
├── requirements.txt ← Dependências
├── data/
│   ├── postados.json    ← Gerado automaticamente
│   └── stats.json       ← Gerado automaticamente
└── logs/
    └── bot.log          ← Gerado automaticamente
```

---

## ⚙️ CONFIGURAÇÃO (3 passos)

### 1. Criar o Bot no Telegram
1. Abra o Telegram → pesquise **@BotFather**
2. Digite `/newbot` e siga as instruções
3. Copie o **TOKEN** gerado

### 2. Pegar seu ID de usuário
1. Abra **@userinfobot** no Telegram
2. Envie qualquer mensagem
3. Copie seu **ID numérico** (ex: `123456789`)

### 3. Editar o config.py
```python
TOKEN     = "SEU_TOKEN_AQUI"
CANAL_ID  = "@seu_canal"        # canal de ofertas
GRUPO_ID  = "@seu_grupo"        # grupo de suporte (opcional)
ADMIN_IDS = [123456789]         # seu ID numérico
TAG       = "sua_tag-20"        # tag de afiliado Amazon
```

> **Tag de afiliado:** Crie em [associados.amazon.com.br](https://associados.amazon.com.br)

---

## ▶️ COMO RODAR

### Instalar dependências:
```bash
pip install -r requirements.txt
```

### Iniciar o bot:
```bash
python bot.py
```

---

## 🤖 COMANDOS DO BOT

| Comando | Descrição |
|--------|-----------|
| `/start` | Menu principal com botões |
| `/buscar headset` | Busca produto específico |
| `/admin` | Painel de estatísticas (só admin) |

### Botões disponíveis:
- **🔥 Ver ofertas agora** — busca oferta aleatória
- **🔎 Pesquisar produto** — busca por texto
- **🗂️ Ver categorias** — escolhe categoria

### Admin:
- **📡 Postar agora no canal** — força post imediato
- **🔄 Atualizar stats** — atualiza o painel

---

## 📡 POSTAGEM AUTOMÁTICA

Com `CANAL_ID` configurado, o bot posta sozinho no canal a cada **15 minutos** (configurável em `INTERVALO_CANAL`).

Só posta produtos:
- Com desconto real (preço original vs atual)
- Acima do `DESCONTO_MINIMO` (padrão: 20%)
- Que ainda não foram postados

---

## 🖥️ RODAR 24H (VPS/Servidor)

Quando for migrar para VPS, use o `screen`:
```bash
screen -S bot
python bot.py
# Ctrl+A depois D para desanexar
```

Ou crie um serviço systemd:
```bash
# /etc/systemd/system/ofertasbot.service
[Unit]
Description=Bot Ofertas Amazon

[Service]
WorkingDirectory=/home/user/ofertasbot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
systemctl enable ofertasbot
systemctl start ofertasbot
```

---

## 📊 EXEMPLO DE MENSAGEM

```
🔥 OFERTA AMAZON

🎁 Headset Gamer XYZ Surround 7.1

💸 De R$ 299,00 por R$ 149,00
🏷️ 50% OFF
⭐ 4.5 de 5 estrelas

🛒 Corra, estoque limitado!

🛒 Comprar com desconto

📌 Link de afiliado Amazon
```
