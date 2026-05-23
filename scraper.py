import requests, random, re, time, logging
from config import TAG, DESCONTO_MINIMO, PRECO_MAXIMO, PRECO_MINIMO

log = logging.getLogger(__name__)
_session = requests.Session()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

def _headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def _link_afiliado(url):
    if "tag=" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}tag={TAG}"

def _preco_float(texto):
    if not texto:
        return None
    try:
        limpo = texto.replace("\xa0", "").replace("De:", "").replace("R$", "")
        limpo = re.sub(r"[^\d,]", "", limpo).replace(",", ".")
        partes = limpo.split(".")
        if len(partes) > 2:
            limpo = "".join(partes[:-1]) + "." + partes[-1]
        val = float(limpo)
        return val if val > 1 else None
    except:
        return None

def _desconto(atual, antigo):
    if atual and antigo and antigo > atual:
        return round((1 - atual / antigo) * 100)
    return 0

def _get(url):
    for i in range(2):
        try:
            time.sleep(random.uniform(0.5, 1.5))
            r = _session.get(url, headers=_headers(), timeout=10)
            if r.status_code == 200:
                return r.text
        except Exception as e:
            log.error(f"Erro GET tentativa {i+1}: {e}")
        time.sleep(1)
    return None

def buscar_produtos(keyword, desc_minimo=DESCONTO_MINIMO, limite=5):
    urls = [
        f"https://www.amazon.com.br/s?k={requests.utils.quote(keyword)}&deals-widget=1",
        f"https://www.amazon.com.br/s?k={requests.utils.quote(keyword)}+oferta+desconto",
    ]

    html = None
    for url in urls:
        log.info(f"Buscando: {url}")
        html = _get(url)
        if html:
            blocos = html.split('data-component-type="s-search-result"')
            if len(blocos) > 2:
                break

    if not html:
        return []

    blocos = html.split('data-component-type="s-search-result"')
    log.info(f"Blocos totais: {len(blocos)-1}")

    produtos = []

    for bloco in blocos[1:]:
        try:
            if "AdHolder" in bloco or '"adIndex"' in bloco:
                continue

            nome = None
            for sel in [
                'a-size-base-plus a-spacing-none a-color-base a-text-normal">',
                'a-size-medium a-color-base a-text-normal">',
                'a-size-base-plus a-color-base a-text-normal">',
                'a-size-base-plus a-color-base">',
            ]:
                if sel in bloco:
                    try:
                        nome = bloco.split(sel)[1].split("</span>")[0].strip()
                        nome = re.sub(r"<[^>]+>", "", nome).strip()
                        if len(nome) > 5:
                            break
                    except:
                        continue

            if not nome or len(nome) < 5:
                continue
            if any(x in nome for x in ["Ver informações", "Escolha da Amazon", "patrocinado"]):
                continue

            todos_precos = re.findall(r'a-offscreen">([^<]+)</span>', bloco)

            preco_atual_str = None
            preco_antigo_str = None

            for p in todos_precos:
                p_limpo = p.replace("\xa0", " ").strip()
                if p_limpo.startswith("De:"):
                    if preco_antigo_str is None:
                        preco_antigo_str = p_limpo
                else:
                    val = _preco_float(p_limpo)
                    if val and val > 50 and preco_atual_str is None:
                        preco_atual_str = p_limpo

            preco_float = _preco_float(preco_atual_str)
            preco_antigo_float = _preco_float(preco_antigo_str)
            desconto = _desconto(preco_float, preco_antigo_float)

            if desconto == 0:
                m = re.search(r'(\d+)%\s*de\s*desconto|[-–](\d+)%', bloco)
                if m:
                    desconto = int(next(x for x in m.groups() if x))
                    if preco_float and not preco_antigo_float:
                        preco_antigo_float = round(preco_float / (1 - desconto / 100), 2)
                        preco_antigo_str = f"R$ {preco_antigo_float:.2f}"

            if desconto < desc_minimo:
                continue

            if preco_float and (preco_float < PRECO_MINIMO or preco_float > PRECO_MAXIMO):
                continue

            hrefs = re.findall(r'href="(/dp/[A-Z0-9]{10}[^"]*)"', bloco)
            if not hrefs:
                hrefs = re.findall(r'href="(/[^"]*?/dp/[A-Z0-9]{10}[^"]*)"', bloco)
            if not hrefs:
                continue
            link = _link_afiliado("https://www.amazon.com.br" + hrefs[0].split("?")[0])

            imagem = ""
            m = re.search(r'src="(https://m\.media-amazon\.com/images/[^"]+)"', bloco)
            if m:
                imagem = m.group(1)

            rating = ""
            m = re.search(r'(\d[,.]\d)\s*de\s*5\s*estrelas', bloco)
            if m:
                rating = f"{m.group(1)} de 5 estrelas"

            produtos.append({
                "nome": nome,
                "link": link,
                "imagem": imagem,
                "preco_str": preco_atual_str or "",
                "preco_float": preco_float,
                "preco_antigo_str": preco_antigo_str or "",
                "preco_antigo_float": preco_antigo_float,
                "desconto": desconto,
                "rating": rating,
                "keyword": keyword,
            })

            log.info(f"✅ {nome[:40]} | {desconto}% | R${preco_float} | antes R${preco_antigo_float}")

            if len(produtos) >= limite:
                break

        except Exception as e:
            log.debug(f"Erro bloco: {e}")
            continue

    log.info(f"Total válidos: {len(produtos)}")
    return produtos

def buscar_ofertas_relampago(limite=5):
    return buscar_produtos("oferta relampago amazon", desc_minimo=0, limite=limite)
