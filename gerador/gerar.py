#!/usr/bin/env python3
"""Gerador estático de wilcatarinaartes.com.br. Uso: python gerador/gerar.py [--producao]
Saída em site/. Teste = noindex; --producao libera os buscadores."""
import json, shutil, sys, html, re
from pathlib import Path
from urllib.parse import quote
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "site"
PROD = "--producao" in sys.argv
S = json.loads((RAIZ / "dados/site.json").read_text(encoding="utf8"))
BLOG = json.loads((RAIZ / "dados/blog.json").read_text(encoding="utf8"))
DOM = S["dominio"]
e = html.escape

# ---------- imagens ----------
def webp(origem, nome, larguras, qualidade=80):
    im = Image.open(RAIZ / "fotos" / origem).convert("RGB")
    for w in larguras:
        if im.width < w and w != larguras[0]:
            continue
        c = im.copy()
        c.thumbnail((w, 99999))
        (SAIDA / "img").mkdir(parents=True, exist_ok=True)
        c.save(SAIDA / "img" / f"{nome}-{w}.webp", "WEBP", quality=qualidade, method=6)
    return im.size

def pic(nome, alt, w, h, tam=(480, 900, 1400), sizes="(min-width:800px) 560px, 100vw", prio=False, larg_max=None):
    ls = [t for t in tam if (SAIDA / "img" / f"{nome}-{t}.webp").exists()]
    ss = ", ".join(f"/img/{nome}-{t}.webp {t}w" for t in ls)
    attrs = 'fetchpriority="high"' if prio else 'loading="lazy" decoding="async"'
    return f'<img src="/img/{nome}-{ls[-1]}.webp" srcset="{ss}" sizes="{sizes}" width="{w}" height="{h}" alt="{e(alt)}" {attrs}>'

# ---------- util ----------
def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def wa(msg):
    return f"https://wa.me/{S['whatsapp']}?text={quote(msg)}"

def meses(d):
    a, m, dia = d.split("-")
    n = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    return f"{int(dia)} de {n[int(m)-1]} de {a}"

PESSOA_ID = DOM + "/#wil"
SITE_ID = DOM + "/#site"
SAME = [S["instagram"], S["facebook"]]

def pessoa():
    return {
        "@type": "Person", "@id": PESSOA_ID, "name": S["nome"],
        "jobTitle": "Artista visual e curadora", "url": DOM + "/sobre/",
        "image": DOM + "/img/wil-712.webp", "email": S["email"],
        "telephone": "+" + S["whatsapp"], "sameAs": SAME,
        "address": {"@type": "PostalAddress", "addressLocality": S["cidade"], "addressRegion": S["uf"], "addressCountry": "BR"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Universidade Federal Fluminense"},
        "knowsAbout": ["Artes visuais", "Pintura", "Escultura", "Curadoria de arte", "Arte contemporânea"],
    }

def jl(objs):
    g = {"@context": "https://schema.org", "@graph": objs}
    return '<script type="application/ld+json">' + json.dumps(g, ensure_ascii=False).replace("</", "<\\/") + "</script>"

def faq_ld(lista):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in lista]}

def crumb_ld(itens):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": DOM + u} for i, (n, u) in enumerate(itens)]}

def faq_html(lista):
    return "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in lista)

# ---------- layout ----------
NAV = [("Obras", "/obras/"), ("Sobre a artista", "/sobre/"), ("Blog", "/blog/"), ("Contato", "/contato/")]

def pagina(url, titulo, desc, corpo, ld, og="/img/og.jpg", ativo=None, tipo="website", extra_head=""):
    canon = DOM + url
    nav = "".join(f'<li><a href="{u}"{" aria-current=page" if u == ativo else ""}>{n}</a></li>' for n, u in NAV)
    robots = "index,follow,max-image-preview:large" if PROD else "noindex,nofollow"
    t = titulo if "Wil Catarina" in titulo else f"{titulo} | {S['nome_site']}"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(t)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#faf7f2">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="{tipo}"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="{S['nome_site']}">
<meta property="og:title" content="{e(t)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{DOM}{og}"><meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="/estilo.css">
{extra_head}{jl(ld)}
</head><body>
<a class="skip" href="#c">Ir para o conteúdo</a>
<header class="top"><div class="w bar">
<a class="logo" href="/">Wil Catarina<small>Artista visual · Niterói</small></a>
<nav aria-label="Principal"><ul>{nav}</ul></nav>
<a class="btn" href="{wa('Olá, Wil! Vi seu site e gostaria de conversar sobre suas obras.')}" rel="noopener">WhatsApp</a>
</div></header>
<main id="c">{corpo}</main>
<footer><div class="w fcols">
<div><strong>Wil Catarina</strong><br>Artista visual e curadora<br>{S['cidade']} · {S['uf']}</div>
<div><a href="{wa('Olá, Wil! Vi seu site.')}" rel="noopener">WhatsApp {S['whatsapp_exibir']}</a><br><a href="mailto:{S['email']}">{S['email']}</a><br><a href="{S['instagram']}" rel="me noopener">Instagram @wilcatarina</a> · <a href="{S['facebook']}" rel="me noopener">Facebook</a></div>
<div><a href="/obras/">Obras</a> · <a href="/sobre/">Sobre</a> · <a href="/blog/">Blog</a> · <a href="/contato/">Contato</a><br>© {S['nome_site']}. Todas as obras são de autoria de Wil Catarina.</div>
</div></footer>
<a class="btn flut" href="{wa('Olá, Wil! Vi seu site e gostaria de conversar sobre suas obras.')}" rel="noopener" aria-label="Falar no WhatsApp">Falar no WhatsApp</a>
</body></html>"""

def gravar(url, conteudo):
    p = SAIDA / url.strip("/") / "index.html" if url != "/" else SAIDA / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(conteudo, encoding="utf8")

# ---------- obras ----------
def ld_obra(o):
    url = f"{DOM}/obras/{o['slug']}/"
    d = {"@type": ["VisualArtwork", "Product"], "@id": url + "#obra", "name": o["titulo"], "description": o["descricao"],
         "image": f"{DOM}/img/{o['slug']}-1400.webp", "url": url, "creator": {"@id": PESSOA_ID},
         "artform": "Pintura" if o["tipo"] == "Tela" else "Escultura", "brand": {"@type": "Person", "name": S["nome"]}}
    if o["preco"]:
        d["offers"] = {"@type": "Offer", "price": f"{o['preco']:.2f}", "priceCurrency": "BRL", "availability": "https://schema.org/InStock",
                       "url": url, "seller": {"@id": PESSOA_ID}}
    return d

def card(o):
    preco = f'<span class="preco">{brl(o["preco"])}</span>' if o["preco"] else '<span class="cons">Valor sob consulta</span>'
    return f"""<article class="card"><a class="l" href="/obras/{o['slug']}/"><div class="im">{pic(o['slug'], o['titulo'] + ' — ' + o['resumo'], 480, 360, (480, 900), '(min-width:800px) 340px, 100vw')}</div>
<div class="cb"><h3>{e(o['titulo'])}</h3><p>{e(o['tipo'])} · Wil Catarina</p>{preco}</div></a>
<div class="cb" style="padding-top:0"><a class="btn" href="{wa('Olá, Wil! Tenho interesse na obra ' + o['titulo'] + '.')}" rel="noopener">Pedir pelo WhatsApp</a></div></article>"""

def pg_obra(o):
    url = f"/obras/{o['slug']}/"
    preco = f'<p class="preco" style="font-size:1.6rem">{brl(o["preco"])}</p>' if o["preco"] else '<p class="cons">Valor sob consulta. Peça pelo WhatsApp.</p>'
    outras = "".join(card(x) for x in S["obras"] if x["slug"] != o["slug"])
    corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › <a href="/obras/">Obras</a> › {e(o['titulo'])}</p>
<div class="prod"><div>{pic(o['slug'], o['titulo'] + ' — ' + o['resumo'], 1400, 785, sizes='(min-width:800px) 640px, 100vw', prio=True).replace('class=','class=') }</div>
<div><p class="kick">{e(o['tipo'])} · Wil Catarina</p><h1>{e(o['titulo'])}</h1>
<div class="resp"><strong>Resposta rápida:</strong> {e(o['titulo'])} é {'uma tela' if o['tipo']=='Tela' else 'uma escultura'} da artista visual Wil Catarina, de Niterói (RJ). {e(o['resumo'])} {'Valor: ' + brl(o['preco']) + '.' if o['preco'] else 'O valor é informado pelo WhatsApp.'}</div>
{preco}<p>{e(o['descricao'])}</p>
<p><a class="btn" href="{wa('Olá, Wil! Tenho interesse na obra ' + o['titulo'] + '. Pode me passar medidas, técnica e condições?')}" rel="noopener">Pedir pelo WhatsApp</a></p>
<p class="cons">Medidas, técnica e entrega combinadas direto com a artista.</p></div></div>
<h2>Outras obras</h2><div class="grade">{outras}</div></div>"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(), ld_obra(o),
          crumb_ld([("Início", "/"), ("Obras", "/obras/"), (o["titulo"], url)])]
    gravar(url, pagina(url, f"{o['titulo']} — {o['tipo']} de Wil Catarina", f"{o['titulo']}, {o['tipo'].lower()} de Wil Catarina, artista visual de Niterói. {o['resumo']} Peça pelo WhatsApp.", corpo, ld, og=f"/img/{o['slug']}-1400.webp", ativo="/obras/", tipo="product"))

def pg_obras():
    cards = "".join(card(o) for o in S["obras"])
    corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › Obras</p><h1>Obras de Wil Catarina</h1>
<div class="resp"><strong>Resposta rápida:</strong> aqui você vê telas e esculturas da artista visual Wil Catarina (Niterói, RJ). Clique na obra para ver os detalhes e peça pelo WhatsApp: a conversa vai direto para a artista.</div>
<div class="grade">{cards}</div>
<h2>Dúvidas frequentes</h2>{faq_html(S['faq'][:4])}</div>"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
          {"@type": "CollectionPage", "name": "Obras de Wil Catarina", "url": DOM + "/obras/", "about": {"@id": PESSOA_ID},
           "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{DOM}/obras/{o['slug']}/", "name": o["titulo"]} for i, o in enumerate(S["obras"])]}},
          faq_ld(S["faq"][:4]), crumb_ld([("Início", "/"), ("Obras", "/obras/")])]
    gravar("/obras/", pagina("/obras/", "Obras de Wil Catarina — telas e esculturas", "Telas e esculturas da artista visual Wil Catarina, de Niterói (RJ). Veja as obras e peça pelo WhatsApp.", corpo, ld, ativo="/obras/"))

# ---------- home ----------
def pg_home():
    cards = "".join(card(o) for o in S["obras"])
    posts = "".join(f'<li><a href="/blog/{p["slug"]}/">{e(p["titulo"])}</a></li>' for p in BLOG)
    corpo = f"""<div class="w"><section class="hero"><div><p class="kick">Artista visual · Niterói, RJ</p><h1>Telas e esculturas de Wil Catarina</h1>
<p class="lead">Arte inspirada na natureza, feita à mão em Niterói. Escolha uma obra e peça direto com a artista pelo WhatsApp.</p>
<p><a class="btn" href="/obras/">Ver as obras</a> <a class="btn o" href="{wa('Olá, Wil! Vi seu site e gostaria de conversar sobre suas obras.')}" rel="noopener">Falar no WhatsApp</a></p></div>
<div>{pic('tela-01', 'Tela 01, pintura abstrata amarela e laranja de Wil Catarina', 1400, 785, prio=True)}</div></section>
<div class="resp"><strong>Wil Catarina</strong> é artista visual e curadora de Niterói (RJ). Cria pinturas, desenhos e esculturas que incorporam elementos da natureza e já expôs no Museu de Arte Contemporânea (MAC), em galerias e em espaços culturais do Rio de Janeiro.</div>
<h2>Obras disponíveis</h2><div class="grade">{cards}</div>
<p><a href="/obras/">Ver todas as obras »</a></p></div>
<section class="faixa"><div class="w"><div class="hero" style="padding:0"><div class="ph-wrap">{pic('wil', 'Wil Catarina, artista visual, segurando uma pequena escultura', 712, 827, (480, 712), '(min-width:800px) 480px, 100vw').replace('<img ','<img class="ph" style="max-width:420px;width:100%" ')}</div>
<div><h2 style="margin-top:0">Sobre a artista</h2><p>“{e(S['frase'])}” A obra de Wil nasce do diálogo entre razão e sensibilidade, com olhar atento ao corpo, ao tempo e à matéria. É graduada em Artes pela UFF e faz oficinas e workshops para compartilhar seu processo.</p><p><a href="/sobre/">Conheça a trajetória »</a></p></div></div></div></section>
<div class="w"><h2>Do blog</h2><ul class="lista">{posts}</ul>
<h2>Dúvidas frequentes</h2>{faq_html(S['faq'])}</div>"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR", "publisher": {"@id": PESSOA_ID}},
          pessoa(), {"@type": "WebPage", "url": DOM + "/", "name": "Wil Catarina Artes", "about": {"@id": PESSOA_ID}, "isPartOf": {"@id": SITE_ID},
                     "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".resp", "h1"]}}, faq_ld(S["faq"])]
    gravar("/", pagina("/", "Wil Catarina — artista visual em Niterói | Telas e esculturas", S["descricao"], corpo, ld))

# ---------- sobre ----------
def pg_sobre():
    li = lambda l: "".join(f"<li>{e(x)}</li>" for x in l)
    corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › Sobre</p>
<div class="prod" style="grid-template-columns:1fr"><div style="display:grid;gap:28px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));align-items:start">
<div>{pic('wil', 'Wil Catarina, artista visual e curadora', 712, 827, (480, 712), '(min-width:800px) 420px, 100vw', prio=True).replace('<img ', '<img class="ph" ')}</div>
<div><p class="kick">Curadora e artista visual</p><h1>Wil Catarina</h1>
<div class="resp"><strong>Resposta rápida:</strong> Wil Catarina é artista visual e curadora de Niterói (RJ), graduada em Artes pela UFF. Faz pinturas, desenhos e esculturas inspirados na natureza e expõe desde o Museu de Arte Contemporânea (MAC) até galerias do Rio de Janeiro.</div>
<p>Minha arte nasce do diálogo entre razão e sensibilidade. Meu processo criativo é guiado pela observação atenta do corpo, do tempo e da matéria como expressões do existir. Em minhas obras, o olhar técnico se funde ao intuitivo, resultando em composições que atravessam o visível para revelar camadas sutis da experiência humana.</p>
<p>Entendo a criação como um ato de consciência e escuta, onde cada cor, traço ou textura traduz o que vibra entre o concreto e o simbólico. Minha pesquisa se move entre a ciência, a natureza e a espiritualidade, buscando compreender a arte como linguagem de conexão entre pessoas, territórios e percepções.</p>
<p><em>“{e(S['frase'])}”</em></p></div></div></div>
<h2>Formação e percurso</h2>
<ul class="lista"><li><strong>Formação técnica:</strong> Estruturas Navais (foco em desenho técnico) e Tecnólogo em Produção Publicitária (direção de arte, arte gráfica e imagens digitais).</li>
<li><strong>Artes visuais:</strong> graduação em Artes na Universidade Federal Fluminense (UFF), voltada para a arte contemporânea, complementada por cursos e workshops de cerâmica, aquarela, desenho e outros.</li>
<li><strong>Oficinas e workshops:</strong> compartilha sua paixão pela arte em experiências que aproximam o público das suas obras e técnicas.</li></ul>
<h2>Curadoria</h2><p>Como curadora, Wil Catarina seleciona obras e artistas com conceito claro e autenticidade, para que apreciadores e colecionadores tenham confiança no que adquirem.</p>
<h2>Exposições individuais</h2><ul class="lista">{li(S['exposicoes_individuais'])}</ul>
<h2>Exposições coletivas</h2><ul class="lista">{li(S['exposicoes_coletivas'])}</ul>
<p style="margin-top:28px"><a class="btn" href="{wa('Olá, Wil! Vi seu site e gostaria de conversar.')}" rel="noopener">Falar com a artista</a></p></div>"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"},
          {"@type": "AboutPage", "url": DOM + "/sobre/", "name": "Sobre Wil Catarina", "about": {"@id": PESSOA_ID}, "mainEntity": {"@id": PESSOA_ID}},
          pessoa(), crumb_ld([("Início", "/"), ("Sobre", "/sobre/")])]
    gravar("/sobre/", pagina("/sobre/", "Wil Catarina — artista visual e curadora de Niterói", "Conheça Wil Catarina, artista visual e curadora de Niterói (RJ): formação pela UFF, processo criativo e exposições no MAC e em galerias do Rio.", corpo, ld, og="/img/wil-712.webp", ativo="/sobre/", tipo="profile"))

# ---------- blog ----------
def pg_blog():
    itens = "".join(f"""<article class="card"><a class="l" href="/blog/{p['slug']}/"><div class="im">{pic(p['imagem'], p['titulo'], 480, 270, (480, 900), '(min-width:800px) 340px, 100vw')}</div><div class="cb"><h3>{e(p['titulo'])}</h3><p>{e(p['resumo'])}</p><span class="cons">{meses(p['data'])}</span></div></a></article>""" for p in BLOG)
    corpo = f'<div class="w"><p class="crumb"><a href="/">Início</a> › Blog</p><h1>Blog</h1><p>Textos sobre arte, curadoria e colecionismo, por Wil Catarina.</p><div class="grade">{itens}</div></div>'
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
          {"@type": "Blog", "url": DOM + "/blog/", "name": "Blog de Wil Catarina", "author": {"@id": PESSOA_ID}}, crumb_ld([("Início", "/"), ("Blog", "/blog/")])]
    gravar("/blog/", pagina("/blog/", "Blog — arte, curadoria e colecionismo", "Textos de Wil Catarina sobre curadoria, galeria de arte digital, termos do mercado de arte e molduras.", corpo, ld, ativo="/blog/"))
    for p in BLOG:
        url = f"/blog/{p['slug']}/"
        pars = "".join(f"<p>{x}</p>" for x in p["paragrafos"])
        corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › <a href="/blog/">Blog</a></p><article class="art"><h1>{e(p['titulo'])}</h1>
<p class="cons">Por Wil Catarina · {meses(p['data'])}</p>{pic(p['imagem'], p['titulo'], 1400, 785, sizes='(min-width:800px) 760px, 100vw', prio=True).replace('<img ', '<img class="ph" ')}
<div class="resp"><strong>Resposta rápida:</strong> {e(p['resumo'])}</div>{pars}
<p><a class="btn" href="{wa('Olá, Wil! Li seu texto no blog e gostaria de conversar.')}" rel="noopener">Conversar com a Wil</a> <a class="btn o" href="/obras/">Ver as obras</a></p></article></div>"""
        ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
              {"@type": "BlogPosting", "headline": p["titulo"], "description": p["resumo"], "datePublished": p["data"], "dateModified": p["data"], "inLanguage": "pt-BR",
               "image": f"{DOM}/img/{p['imagem']}-1400.webp", "mainEntityOfPage": DOM + url, "author": {"@id": PESSOA_ID}, "publisher": {"@id": PESSOA_ID},
               "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".resp", "h1"]}},
              crumb_ld([("Início", "/"), ("Blog", "/blog/"), (p["titulo"], url)])]
        gravar(url, pagina(url, p["titulo"], p["resumo"], corpo, ld, og=f"/img/{p['imagem']}-1400.webp", ativo="/blog/", tipo="article"))

# ---------- contato / 404 ----------
def pg_contato():
    corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › Contato</p><div class="art"><h1>Contato</h1>
<div class="resp"><strong>Resposta rápida:</strong> o jeito mais rápido de falar com a Wil Catarina é pelo WhatsApp {S['whatsapp_exibir']}. Também há e-mail e Instagram.</div>
<p><a class="btn" href="{wa('Olá, Wil! Vi seu site e gostaria de conversar sobre suas obras.')}" rel="noopener">Chamar no WhatsApp</a></p>
<ul class="lista"><li>WhatsApp: <a href="{wa('Olá, Wil!')}" rel="noopener">{S['whatsapp_exibir']}</a></li><li>E-mail: <a href="mailto:{S['email']}">{S['email']}</a></li>
<li>Instagram: <a href="{S['instagram']}" rel="me noopener">@wilcatarina</a></li><li>Facebook: <a href="{S['facebook']}" rel="me noopener">Wil Catarina</a></li><li>Local: {S['cidade']} · {S['uf']}</li></ul></div></div>"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
          {"@type": "ContactPage", "url": DOM + "/contato/", "name": "Contato", "about": {"@id": PESSOA_ID}}, crumb_ld([("Início", "/"), ("Contato", "/contato/")])]
    gravar("/contato/", pagina("/contato/", "Contato — fale com Wil Catarina", "Fale com a artista visual Wil Catarina pelo WhatsApp, e-mail ou Instagram. Niterói, RJ.", corpo, ld, ativo="/contato/"))

def pg_404():
    corpo = '<div class="w"><div class="art"><h1>Página não encontrada</h1><p>O endereço não existe ou mudou. Veja as <a href="/obras/">obras</a> ou volte ao <a href="/">início</a>.</p></div></div>'
    (SAIDA / "404.html").write_text(pagina("/404.html", "Página não encontrada", "Página não encontrada.", corpo, []).replace("index,follow", "noindex,follow").replace('<link rel="canonical" href="' + DOM + '/404.html">', ""), encoding="utf8")

# ---------- arquivos técnicos ----------
REDIR = """/galeria-digital  /obras/  301
/galeria-digital/  /obras/  301
/shop  /obras/  301
/shop/  /obras/  301
/home-shop/  /obras/  301
/produto/tela-01  /obras/tela-01/  301
/produto/tela-01/  /obras/tela-01/  301
/produto/*  /obras/  301
/wil-catarina-colunista/  /sobre/  301
/wil-catarina/  /sobre/  301
/sobre-nos/  /sobre/  301
/colunista-modelo/  /sobre/  301
/glossario-de-artes/  /blog/  301
/categoria/*  /obras/  301
/loja/*  /  301
/conectar-ideias-comunicacao/  /  301
/opcoes-de-anuncios/  /  301
/home/  /  301
/cart/  /obras/  301
/checkout/  /obras/  301
/my-account/  /  301
/wp-login.php  /  301
"""

def tecnicos(urls):
    redir = REDIR + "".join(f"/{p['slug']}/  /blog/{p['slug']}/  301\n/{p['slug']}  /blog/{p['slug']}/  301\n" for p in BLOG)
    (SAIDA / "_redirects").write_text(redir, encoding="utf8")
    (SAIDA / "_headers").write_text("/img/*\n  Cache-Control: public, max-age=31536000, immutable\n/estilo.css\n  Cache-Control: public, max-age=3600\n/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n", encoding="utf8")
    hoje = "2026-11-07"
    sm = "".join(f"<url><loc>{DOM}{u}</loc><lastmod>{hoje}</lastmod></url>" for u in urls)
    (SAIDA / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>', encoding="utf8")
    (SAIDA / "robots.txt").write_text(("User-agent: *\nAllow: /\n" if PROD else "User-agent: *\nDisallow: /\n") + f"\nSitemap: {DOM}/sitemap.xml\n", encoding="utf8")
    obras = "\n".join(f"- [{o['titulo']}]({DOM}/obras/{o['slug']}/): {o['resumo']}" for o in S["obras"])
    blog = "\n".join(f"- [{p['titulo']}]({DOM}/blog/{p['slug']}/)" for p in BLOG)
    (SAIDA / "llms.txt").write_text(f"# Wil Catarina Artes\n\n> {S['descricao']}\n\nWil Catarina é artista visual e curadora de Niterói (RJ), graduada em Artes pela UFF. As obras são vendidas pelo WhatsApp {S['whatsapp_exibir']}.\n\n## Obras\n{obras}\n\n## Páginas\n- [Sobre a artista]({DOM}/sobre/)\n- [Contato]({DOM}/contato/)\n\n## Blog\n{blog}\n", encoding="utf8")
    (SAIDA / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#8a5a12"/><text x="32" y="43" font-family="Georgia,serif" font-size="30" font-weight="700" fill="#faf7f2" text-anchor="middle">WC</text></svg>', encoding="utf8")
    shutil.copy(RAIZ / "estilo/estilo.css", SAIDA / "estilo.css")

def og():
    im = Image.open(RAIZ / "fotos/d64.jpg").convert("RGB")
    w, h = im.size
    nh = int(w * 630 / 1200)
    top = (h - nh) // 2
    im.crop((0, max(top, 0), w, max(top, 0) + min(nh, h))).resize((1200, 630)).save(SAIDA / "img/og.jpg", quality=82, optimize=True)

def main():
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir()
    tam = (480, 900, 1400)
    for o in S["obras"]:
        webp(o["foto"], o["slug"], tam)
    for p in BLOG:
        webp(p["imagem"] + ".png", p["imagem"], tam)
    webp("wil.jpg", "wil", (480, 712))
    og()
    pg_home(); pg_obras(); pg_sobre(); pg_blog(); pg_contato(); pg_404()
    for o in S["obras"]:
        pg_obra(o)
    urls = ["/", "/obras/", "/sobre/", "/blog/", "/contato/"] + [f"/obras/{o['slug']}/" for o in S["obras"]] + [f"/blog/{p['slug']}/" for p in BLOG]
    tecnicos(urls)
    print(("PRODUÇÃO" if PROD else "TESTE (noindex)"), "-", len(urls), "páginas")

main()
