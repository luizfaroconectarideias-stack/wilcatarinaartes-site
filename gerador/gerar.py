#!/usr/bin/env python3
"""Gerador estático de wilcatarinaartes.com.br. Uso: python gerador/gerar.py [--producao]
Saída em site/. Teste = noindex; --producao libera os buscadores."""
import json, shutil, sys, html, re
import markdown
from pathlib import Path
from urllib.parse import quote
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "site"
PROD = "--producao" in sys.argv
S = json.loads((RAIZ / "dados/site.json").read_text(encoding="utf8"))
BLOG = json.loads((RAIZ / "dados/blog.json").read_text(encoding="utf8"))
DOM = S["dominio"]
HOJE = "2026-11-07"
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
        "description": "Artista visual e curadora de Niterói (RJ). Cria pinturas, desenhos e esculturas inspirados na natureza e expõe em museus, galerias e espaços culturais do Rio de Janeiro.",
        "workLocation": {"@type": "Place", "name": "Niterói, RJ"},
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
NAV = [("Obras", "/obras/"), ("Sobre a artista", "/sobre/"), ("Glossário", "/glossario/"), ("Onde expor", "/onde-expor-arte-rj/"), ("Blog", "/blog/"), ("Contato", "/contato/")]
CSS = re.sub(r"\s+", " ", re.sub(r"/\*.*?\*/", "", (RAIZ / "estilo/estilo.css").read_text(encoding="utf8"), flags=re.S)).replace(" {", "{").replace("{ ", "{").replace("; ", ";").replace(": ", ":")

def meta_desc(t, n=158):
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",;:.") + "…"

def pagina(url, titulo, desc, corpo, ld, og="/img/og.jpg", ativo=None, tipo="website", extra_head="", raw_title=False):
    canon = DOM + url
    nav = "".join(f'<li><a href="{u}"{" aria-current=page" if u == ativo else ""}>{n}</a></li>' for n, u in NAV)
    robots = "index,follow,max-image-preview:large" if PROD else "noindex,nofollow"
    if raw_title or "Wil Catarina" in titulo:
        t = titulo
    else:
        t = f"{titulo} | {S['nome_site']}"
        if len(t) > 66:
            t = titulo
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(t)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="{tipo}"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="{S['nome_site']}">
<meta property="og:title" content="{e(t)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{DOM}{og}"><meta name="twitter:card" content="summary_large_image">
<meta name="author" content="Wil Catarina">
<link rel="alternate" type="application/rss+xml" title="Blog de Wil Catarina" href="/feed.xml">
<meta property="og:image:alt" content="{e(t)}">
<link rel="preload" href="/img/j400.woff2" as="font" type="font/woff2" crossorigin>
<style>{CSS}</style>
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
<div><a href="/obras/">Obras</a> · <a href="/sobre/">Sobre</a> · <a href="/glossario/">Glossário</a> · <a href="/onde-expor-arte-rj/">Onde expor</a> · <a href="/blog/">Blog</a> · <a href="/contato/">Contato</a><br><a href="/politica-de-privacidade/">Privacidade</a> · <a href="/termos-de-uso/">Termos de uso</a> · <a href="/acessibilidade/">Acessibilidade</a><br>© {S['nome_site']}. Todas as obras são de autoria de Wil Catarina.</div>
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
<div class="grade"><!--OBRAS-->{cards}<!--/OBRAS--></div>
<h2>Dúvidas frequentes</h2>{faq_html(S['faq'][:4])}</div>"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
          {"@type": "CollectionPage", "name": "Obras de Wil Catarina", "url": DOM + "/obras/", "about": {"@id": PESSOA_ID},
           "mainEntity": {"@type": "ItemList", "itemListElement": "__ITEMS__"}},
          faq_ld(S["faq"][:4]), crumb_ld([("Início", "/"), ("Obras", "/obras/")])]
    gravar("/obras/", pagina("/obras/", "Obras de Wil Catarina — telas e esculturas", "Telas e esculturas da artista visual Wil Catarina, de Niterói (RJ). Veja as obras e peça pelo WhatsApp.", corpo, ld, ativo="/obras/"))

# ---------- home ----------
def pg_home():
    gl_cards = "".join(f'<li><a href="{t["url"]}">{e(t["termo"].capitalize())}</a>: {e(t["resumo"].split(". ")[0].rstrip("."))}.</li>' for t in TERMOS[:6])
    cards = "".join(card(o) for o in S["obras"])
    posts = "".join(f'<li><a href="/blog/{p["slug"]}/">{e(p["titulo"])}</a></li>' for p in BLOG)
    corpo = f"""<section class="banda"><div class="w hero"><div><p class="kick">Artista visual · Niterói, RJ</p><h1>Telas e esculturas de Wil Catarina</h1>
<p class="lead">Arte inspirada na natureza, feita à mão em Niterói. Escolha uma obra e peça direto com a artista pelo WhatsApp.</p>
<p><a class="btn" href="/obras/">Ver as obras</a> <a class="btn o" href="{wa('Olá, Wil! Vi seu site e gostaria de conversar sobre suas obras.')}" rel="noopener">Falar no WhatsApp</a></p></div>
<div>{pic('tela-01', 'Tela 01, pintura abstrata amarela e laranja de Wil Catarina', 1400, 785, prio=True)}</div></div></section>
<div class="w"><div class="resp"><strong>Wil Catarina</strong> é artista visual e curadora de Niterói (RJ). Cria pinturas, desenhos e esculturas que incorporam elementos da natureza e já expôs no Museu de Arte Contemporânea (MAC), em galerias e em espaços culturais do Rio de Janeiro.</div>
<h2>Obras disponíveis</h2><div class="grade"><!--OBRAS-->{cards}<!--/OBRAS--></div>
<p><a href="/obras/">Ver todas as obras »</a></p></div>
<section class="faixa"><div class="w"><div class="hero" style="padding-block:0"><div class="ph-wrap">{pic('wil', 'Wil Catarina, artista visual, segurando uma pequena escultura', 712, 827, (480, 712), '(min-width:800px) 480px, 100vw').replace('<img ','<img class="ph" style="max-width:420px;width:100%" ')}</div>
<div><h2 style="margin-top:0">Sobre a artista</h2><p>“{e(S['frase'])}” A obra de Wil nasce do diálogo entre razão e sensibilidade, com olhar atento ao corpo, ao tempo e à matéria. É graduada em Artes pela UFF e faz oficinas e workshops para compartilhar seu processo.</p><p><a href="/sobre/">Conheça a trajetória »</a></p></div></div></div></section>
<div class="w"><h2>Glossário de arte</h2><ul class="lista">{gl_cards}</ul><p><a href="/glossario/">Ver os 20 termos do glossário »</a></p><h2>Onde expor arte no Rio de Janeiro</h2><p>Museus, galerias e centros culturais do estado, organizados por cidade. <a href="/onde-expor-arte-rj/">Ver locais de exposição »</a></p><h2>Do blog</h2><ul class="lista">{posts}</ul>
<h2>Dúvidas frequentes</h2>{faq_html(S['faq'])}</div>"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR", "publisher": {"@id": PESSOA_ID}},
          pessoa(), {"@type": "WebPage", "url": DOM + "/", "name": "Wil Catarina Artes", "about": {"@id": PESSOA_ID}, "isPartOf": {"@id": SITE_ID},
                     "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".resp", "h1"]}}, faq_ld(S["faq"])]
    pre = '<link rel="preload" as="image" href="/img/tela-01-1400.webp" imagesrcset="/img/tela-01-480.webp 480w, /img/tela-01-900.webp 900w, /img/tela-01-1400.webp 1400w" imagesizes="(min-width:800px) 560px, 100vw" fetchpriority="high">'
    gravar("/", pagina("/", "Wil Catarina — artista visual em Niterói | Telas e esculturas", S["descricao"], corpo, ld, extra_head=pre))

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
<p class="cons">Por <a href="/sobre/">Wil Catarina</a>, artista visual e curadora · Publicado em {meses(p['data'])}</p>{pic(p['imagem'], p['titulo'], 1400, 785, sizes='(min-width:800px) 760px, 100vw', prio=True).replace('<img ', '<img class="ph" ')}
<div class="resp"><strong>Resposta rápida:</strong> {e(p['resumo'])}</div>{pars}
{termos_do_post(p["slug"])}<p><a class="btn" href="{wa('Olá, Wil! Li seu texto no blog e gostaria de conversar.')}" rel="noopener">Conversar com a Wil</a> <a class="btn o" href="/obras/">Ver as obras</a></p></article></div>"""
        ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
              {"@type": "BlogPosting", "headline": p["titulo"], "description": p["resumo"], "datePublished": p["data"], "dateModified": p["data"], "inLanguage": "pt-BR",
               "image": f"{DOM}/img/{p['imagem']}-1400.webp", "mainEntityOfPage": DOM + url, "author": {"@id": PESSOA_ID}, "publisher": {"@id": PESSOA_ID},
               "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".resp", "h1"]}},
              crumb_ld([("Início", "/"), ("Blog", "/blog/"), (p["titulo"], url)])]
        gravar(url, pagina(url, p.get("titulo_seo", p["titulo"]), meta_desc(p["resumo"]), corpo, ld, og=f"/img/{p['imagem']}-1400.webp", ativo="/blog/", tipo="article"))

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
    (SAIDA / "robots.txt").write_text(("User-agent: *\nAllow: /\nDisallow: /painel/\nDisallow: /api/\n\n" + "".join(f"User-agent: {b}\nAllow: /\nDisallow: /painel/\nDisallow: /api/\n\n" for b in ("GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot")) if PROD else "User-agent: *\nDisallow: /\n") + f"\nSitemap: {DOM}/sitemap.xml\n", encoding="utf8")
    obras = "\n".join(f"- [{o['titulo']}]({DOM}/obras/{o['slug']}/): {o['resumo']}" for o in S["obras"])
    blog = "\n".join(f"- [{p['titulo']}]({DOM}/blog/{p['slug']}/)" for p in BLOG)
    gl = "\n".join(f"- [{t['termo']}]({DOM}{t['url']}): {t['resumo']}" for t in TERMOS)
    (SAIDA / "llms.txt").write_text(f"# Wil Catarina Artes\n\n> {S['descricao']}\n\nWil Catarina é artista visual e curadora de Niterói (RJ), graduada em Artes pela UFF. As obras são vendidas pelo WhatsApp {S['whatsapp_exibir']}.\n\n## Obras\n{obras}\n\n## Páginas\n- [Sobre a artista]({DOM}/sobre/)\n- [Contato]({DOM}/contato/)\n\n## Glossário de arte\n{gl}\n\n## Blog\n{blog}\n\nVersão completa em texto: {DOM}/llms-full.txt\n", encoding="utf8")
    (SAIDA / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1d6b6b"/><text x="32" y="43" font-family="Georgia,serif" font-size="30" font-weight="700" fill="#ffffff" text-anchor="middle">WC</text></svg>', encoding="utf8")
    shutil.copy(RAIZ / "estilo/estilo.css", SAIDA / "estilo.css")
    for f in (RAIZ / "estilo/fontes").glob("*.woff2"):
        shutil.copy(f, SAIDA / "img" / f.name)

def og():
    im = Image.open(RAIZ / "fotos/d64.jpg").convert("RGB")
    w, h = im.size
    nh = int(w * 630 / 1200)
    top = (h - nh) // 2
    im.crop((0, max(top, 0), w, max(top, 0) + min(nh, h))).resize((1200, 630)).save(SAIDA / "img/og.jpg", quality=82, optimize=True)

def modelos():
    """Moldura (cabecalho/rodape) e dados para o Worker montar as paginas das obras."""
    d = SAIDA / "_tpl"
    d.mkdir(parents=True, exist_ok=True)
    shell = pagina("{{URL}}", "{{TITLE}}", "{{DESC}}", "{{BODY}}", [], og="{{OG}}", ativo="/obras/", tipo="product", raw_title=True)
    shell = re.sub(r'<script type="application/ld[+]json">.*?</script>', "{{LD}}", shell, flags=re.S)
    shell = shell.replace(DOM + "{{OG}}", "{{OG}}").replace(DOM + "{{URL}}", "{{URL}}")
    (d / "moldura.html").write_text(shell, encoding="utf8")
    cfg = {"dominio": DOM, "whatsapp": S["whatsapp"], "nome": S["nome"], "nome_site": S["nome_site"], "pessoa": pessoa(),
           "site_id": SITE_ID, "pessoa_id": PESSOA_ID}
    (d / "config.json").write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf8")

def painel():
    d = SAIDA / "painel"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(RAIZ / "painel/index.html", d / "index.html")


# ---------- glossário e páginas institucionais ----------
def ler_md(arq):
    txt = arq.read_text(encoding="utf8")
    _, fm, corpo = txt.split("---", 2)
    meta = {}
    for ln in fm.strip().splitlines():
        k, _, v = ln.partition(":")
        meta[k.strip()] = v.strip()
    return meta, corpo.strip()

def md(t):
    return markdown.markdown(t, extensions=["tables", "sane_lists", "toc"])

def fontes_lista(txt):
    out = []
    for f in [x.strip() for x in txt.split(" ; " if " ; " in txt else ";") if x.strip()]:
        nome, _, u = f.rpartition("|")
        out.append((nome.strip(), u.strip()))
    return out

TERMOS = []
def carregar_termos():
    for arq in sorted((RAIZ / "dados/glossario").glob("*.md")):
        m, corpo = ler_md(arq)
        corpo_md, _, faq_md = corpo.partition("## Perguntas frequentes")
        faq = []
        for bloco in faq_md.split("### ")[1:]:
            q, _, a = bloco.partition("\n")
            faq.append((q.strip(), " ".join(a.split())))
        slug = "o-que-e-" + arq.stem
        TERMOS.append(dict(meta=m, arq=arq.stem, slug=slug, url=f"/glossario/{slug}/", termo=m["termo"], titulo_seo=m["titulo_seo"], resumo=m["resumo"],
                           sin=[x.strip() for x in m.get("sinonimos", "").split(",") if x.strip()], rel=[x.strip() for x in m.get("relacionados", "").split(",") if x.strip()],
                           fontes=fontes_lista(m.get("fontes", "")) if m.get("fontes") else [], blog=m.get("blog", ""), atualizado=m["atualizado"],
                           html=md(corpo_md), faq=faq))
    TERMOS.sort(key=lambda t: t["termo"].lower().replace("á", "a").replace("é", "e").replace("ê", "e").replace("í", "i").replace("ó", "o").replace("ç", "c").replace("ú", "u"))

def termo_por_arq(a):
    return next((t for t in TERMOS if t["arq"] == a), None)

def termos_do_post(slug):
    ts = [t for t in TERMOS if t["blog"] == slug]
    if not ts:
        return ""
    return '<h2>Termos de arte neste texto</h2><ul class="lista">' + "".join(f'<li><a href="{t["url"]}">{e(t["termo"].capitalize())}</a>: {e(t["resumo"].split(". ")[0].rstrip("."))}.</li>' for t in ts) + "</ul>"

def nome_termo(t):
    return t["termo"].split(" (")[0]

def inicial(t):
    return slug_de(nome_termo(t))[0].upper()

def cartao_termo(t):
    return f'<a class="tcard" href="{t["url"]}" data-n="{e(slug_de(nome_termo(t)).replace("-", " "))}"><strong>{e(nome_termo(t).capitalize())}</strong><span>{e(t["resumo"])}</span></a>'

def barra_az(ativa=None):
    letras = {inicial(t) for t in TERMOS}
    itens = ""
    for L in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if L in letras:
            itens += f'<a href="/glossario/letra-{L.lower()}/"{" aria-current=page" if L == ativa else ""}>{L}</a>'
        else:
            itens += f'<span aria-hidden="true">{L}</span>'
    return f'<nav class="az" aria-label="Filtrar por letra">{itens}</nav>'

SCRIPT_BUSCA = """<script>(function(){var f=document.getElementById('bf'),q=document.getElementById('bq');if(!f)return;function ap(){var v=q.value.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').trim(),n=0;document.querySelectorAll('.tcard').forEach(function(c){var ok=!v||c.getAttribute('data-n').indexOf(v)>-1||c.textContent.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').indexOf(v)>-1;c.style.display=ok?'':'none';if(ok)n++});document.getElementById('bn').textContent=n?'':'Nenhum termo encontrado.'}q.addEventListener('input',ap);f.addEventListener('submit',function(ev){ev.preventDefault();ap()})})();</script>"""

def pg_glossario():
    cards = "".join(cartao_termo(t) for t in TERMOS)
    corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › Glossário</p><div class="glos"><h1>Glossário de arte, curadoria e colecionismo</h1>
<p class="lead">Significado de termos de arte explicados de forma direta, com perguntas frequentes.</p>
<form id="bf" class="busca" role="search"><label for="bq">Buscar um termo</label><div><input id="bq" type="search" placeholder="Ex.: vernissage, curadoria, passe-partout" autocomplete="off"><button class="btn" type="submit">Buscar</button></div></form>
{barra_az()}<p id="bn" role="status" class="cons"></p>
<div class="tlista">{cards}</div>
<p>Quer ver arte de perto? Conheça as <a href="/obras/">obras de Wil Catarina</a> ou descubra <a href="/onde-expor-arte-rj/">onde ver e expor arte no Rio de Janeiro</a>.</p></div></div>{SCRIPT_BUSCA}"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
          {"@type": "DefinedTermSet", "@id": DOM + "/glossario/#set", "name": "Glossário de arte", "url": DOM + "/glossario/", "inLanguage": "pt-BR",
           "hasDefinedTerm": [{"@type": "DefinedTerm", "name": nome_termo(t), "description": t["resumo"], "url": DOM + t["url"]} for t in TERMOS]},
          {"@type": "CollectionPage", "name": "Glossário de arte", "url": DOM + "/glossario/", "about": {"@id": DOM + "/glossario/#set"}, "publisher": {"@id": PESSOA_ID},
           "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".lead", "h1"]}}, crumb_ld([("Início", "/"), ("Glossário", "/glossario/")])]
    gravar("/glossario/", pagina("/glossario/", "Glossário de arte: 20 termos explicados de forma simples", f"{len(TERMOS)} termos de arte explicados em linguagem simples: curadoria, vernissage, proveniência, fine art, técnica mista, moldura de conservação e mais.", corpo, ld, ativo="/glossario/"))
    # páginas por letra
    for L in sorted({inicial(t) for t in TERMOS}):
        ts = [t for t in TERMOS if inicial(t) == L]
        url = f"/glossario/letra-{L.lower()}/"
        nomes = ", ".join(nome_termo(t) for t in ts)
        corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › <a href="/glossario/">Glossário</a> › Letra {L}</p><div class="glos"><h1>Glossário de arte: letra {L}</h1>
<p class="lead">Termos de arte que começam com {L}: {e(nomes)}.</p>{barra_az(L)}<div class="tlista">{"".join(cartao_termo(t) for t in ts)}</div>
<p><a href="/glossario/">Ver todos os termos</a></p></div></div>"""
        ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
              {"@type": "CollectionPage", "name": f"Glossário de arte: letra {L}", "url": DOM + url, "isPartOf": {"@id": DOM + "/glossario/#set"}, "publisher": {"@id": PESSOA_ID}},
              crumb_ld([("Início", "/"), ("Glossário", "/glossario/"), (f"Letra {L}", url)])]
        gravar(url, pagina(url, f"Glossário de arte: termos com a letra {L}", meta_desc(f"Termos de arte que começam com {L}: {nomes}. Veja o significado de cada um."), corpo, ld, ativo="/glossario/").replace("index,follow,max-image-preview:large", "noindex,follow"))
    for t in TERMOS:
        L = inicial(t)
        rel = [termo_por_arq(a) for a in t["rel"]]
        rel = [r for r in rel if r]
        faq = faq_html(t["faq"])
        fontes = ""
        if t["fontes"]:
            fontes = '<h2 id="fontes">Fontes</h2><ul class="lista">' + "".join(f'<li><a href="{u}" rel="noopener">{e(n)}</a></li>' for n, u in t["fontes"]) + "</ul>"
        veja = '<h2 id="veja-tambem">Veja também</h2><ul class="lista">' + "".join(f'<li><a href="{r["url"]}">{e(nome_termo(r).capitalize())}</a>: {e(r["resumo"].split(". ")[0].rstrip("."))}.</li>' for r in rel) + "</ul>" if rel else ""
        blogl = ""
        if t["blog"]:
            bp = next((p for p in BLOG if p["slug"] == t["blog"]), None)
            if bp:
                blogl = f'<p>Leia também no blog: <a href="/blog/{bp["slug"]}/">{e(bp["titulo"])}</a>.</p>'
        h1 = "O que é " + nome_termo(t) + "?"
        h2s = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', t["html"])
        toc_itens = [(i, x) for i, x in h2s] + [("faq", "Perguntas frequentes")] + ([("veja-tambem", "Veja também")] if rel else []) + ([("fontes", "Fontes")] if t["fontes"] else [])
        toc = '<nav class="toc" aria-label="Neste artigo"><strong>Neste artigo</strong><ol>' + "".join(f'<li><a href="#{i}">{x}</a></li>' for i, x in toc_itens) + "</ol></nav>"
        tambem = f'<p class="cons"><strong>Também chamado de:</strong> {e(", ".join(t["sin"]))}</p>' if t["sin"] else ""
        corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › <a href="/glossario/">Glossário</a> › <a href="/glossario/letra-{L.lower()}/">Letra {L}</a> › {e(nome_termo(t).capitalize())}</p><article class="art"><p class="kick">Glossário · Letra {L}</p><h1>{e(h1)}</h1>
<div class="resumo"><span class="kick">Em resumo</span><p>{e(t['resumo'])}</p></div>{tambem}
<p class="cons">Redação <a href="/sobre/">Wil Catarina Artes</a> · atualizado em {meses(t['atualizado'])}</p>{toc}
{t['html']}{blogl}<h2 id="faq">Perguntas frequentes</h2>{faq}{veja}{fontes}
<p><a class="btn o" href="/glossario/">Voltar ao glossário</a> <a class="btn" href="/obras/">Ver as obras</a></p></article></div>"""
        ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
              {"@type": "DefinedTerm", "@id": DOM + t["url"] + "#termo", "name": nome_termo(t), "description": t["resumo"], "url": DOM + t["url"], "inDefinedTermSet": DOM + "/glossario/#set",
               **({"alternateName": t["sin"]} if t["sin"] else {})},
              {"@type": "WebPage", "@id": DOM + t["url"], "name": h1, "url": DOM + t["url"], "inLanguage": "pt-BR", "datePublished": t["atualizado"], "dateModified": t["atualizado"],
               "isPartOf": {"@id": SITE_ID}, "publisher": {"@id": PESSOA_ID}, "mainEntity": {"@id": DOM + t["url"] + "#termo"},
               "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".resumo", "h1"]},
               **({"citation": [{"@type": "CreativeWork", "name": n, "url": u} for n, u in t["fontes"]]} if t["fontes"] else {})},
              faq_ld(t["faq"]), crumb_ld([("Início", "/"), ("Glossário", "/glossario/"), (f"Letra {L}", f"/glossario/letra-{L.lower()}/"), (nome_termo(t).capitalize(), t["url"])])]
        gravar(t["url"], pagina(t["url"], t["titulo_seo"], meta_desc(t["resumo"]), corpo, ld, ativo="/glossario/", tipo="article"))

PAGINAS_LEGAIS = [("politica-de-privacidade", "Política de Privacidade"), ("termos-de-uso", "Termos de Uso"), ("acessibilidade", "Acessibilidade")]
def pgs_legais():
    for slug, nome in PAGINAS_LEGAIS:
        m, corpo = ler_md(RAIZ / f"dados/paginas/{slug}.md")
        url = f"/{slug}/"
        c = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › {e(m['titulo'])}</p><article class="art"><h1>{e(m['titulo'])}</h1>
<p class="cons">Atualizado em {meses(m['atualizado'])}</p><div class="resp">{e(m['resumo'])}</div>{md(corpo)}</article></div>"""
        ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
              {"@type": "WebPage", "name": m["titulo"], "url": DOM + url, "inLanguage": "pt-BR", "dateModified": m["atualizado"], "isPartOf": {"@id": SITE_ID}},
              crumb_ld([("Início", "/"), (m["titulo"], url)])]
        gravar(url, pagina(url, m["titulo_seo"], meta_desc(m["resumo"]), c, ld, raw_title=True))

def feed():
    itens = "".join(f"<item><title>{e(p['titulo'])}</title><link>{DOM}/blog/{p['slug']}/</link><guid>{DOM}/blog/{p['slug']}/</guid><pubDate>Fri, 29 May 2026 12:00:00 +0000</pubDate><description>{e(p['resumo'])}</description></item>" for p in BLOG)
    (SAIDA / "feed.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Blog de Wil Catarina</title><link>{DOM}/blog/</link><description>Textos sobre arte, curadoria e colecionismo.</description><language>pt-BR</language>{itens}</channel></rss>', encoding="utf8")

def llms_full():
    partes = [f"# Wil Catarina Artes — conteúdo completo\n\n> {S['descricao']}\n\nSite: {DOM}\nArtista: Wil Catarina, artista visual e curadora de Niterói (RJ). Contato: {S['email']} · WhatsApp {S['whatsapp_exibir']}\n"]
    partes.append("## Perguntas frequentes\n" + "\n".join(f"- **{q}** {a}" for q, a in S["faq"]))
    partes.append("## Glossário de arte")
    for t in TERMOS:
        partes.append(f"### {t['termo']}\nURL: {DOM}{t['url']}\n{t['resumo']}\n" + "\n".join(f"- **{q}** {a}" for q, a in t["faq"]))
    partes.append("## Blog")
    for p in BLOG:
        partes.append(f"### {p['titulo']}\nURL: {DOM}/blog/{p['slug']}/\n{p['resumo']}")
    (SAIDA / "llms-full.txt").write_text("\n\n".join(partes) + "\n", encoding="utf8")


# ---------- onde expor arte: página-mãe e páginas por cidade ----------
SEM_ACENTO = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçñ", "aaaaaeeeeiiiiooooouuuucn")
def slug_de(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower().translate(SEM_ACENTO)).strip("-")

TIPO_ORDEM = ["Museu", "Galeria de arte", "Centro de arte", "Centro cultural", "Espaço cultural"]
LOCAIS = []
def carregar_locais():
    f = RAIZ / "dados/locais_bruto.json"
    if not f.exists():
        return
    vistos = set()
    ajustes = {}
    fa = RAIZ / "dados/locais_ajustes.json"
    if fa.exists():
        ajustes = json.loads(fa.read_text(encoding="utf8"))
    for x in json.loads(f.read_text(encoding="utf8")):
        chave = x.get("feature_id") or (x["nome"], x["endereco"])
        if chave in vistos or x["nome"] in ajustes.get("excluir", []):
            continue
        vistos.add(chave)
        x["tipo"] = ajustes.get("tipo", {}).get(x["nome"], x["tipo"])
        LOCAIS.append(x)

def locais_por_cidade():
    d = {}
    for x in LOCAIS:
        d.setdefault(x["cidade"], []).append(x)
    for c in d:
        d[c].sort(key=lambda v: (TIPO_ORDEM.index(v["tipo"]) if v["tipo"] in TIPO_ORDEM else 9, -(v.get("avaliacoes") or 0)))
    return d

MIN_CIDADE = 4
BASE_EXPOR = "/onde-expor-arte-rj/"

def local_ld(v):
    tipo = {"Museu": "Museum", "Galeria de arte": "ArtGallery"}.get(v["tipo"], "Place")
    d = {"@type": tipo, "name": v["nome"], "address": {"@type": "PostalAddress", "streetAddress": v["endereco"], "addressLocality": v["cidade"], "addressRegion": "RJ", "addressCountry": "BR"}}
    if v.get("lat") is not None:
        d["geo"] = {"@type": "GeoCoordinates", "latitude": v["lat"], "longitude": v["lng"]}
    if v.get("telefone"):
        d["telephone"] = v["telefone"]
    if v.get("site"):
        d["url"] = v["site"]
    d["hasMap"] = mapa(v)
    return d

def mapa(v):
    from urllib.parse import quote
    return "https://www.google.com/maps/search/?api=1&query=" + quote(f"{v['nome']}, {v['endereco']}")

def ficha_local(v):
    partes = [f'<h3>{e(v["nome"])}</h3>', f'<p class="cons">{e(v["tipo"])}{" · " + e(v["bairro"]) if v.get("bairro") else ""}</p>', f'<p>{e(v["endereco"])}</p>']
    li = []
    if v.get("telefone"):
        li.append(f'Telefone: <a href="tel:{re.sub(r"[^0-9+]", "", v["telefone"])}">{e(v["telefone"])}</a>')
    if v.get("site"):
        rotulo = "Instagram" if "instagram.com" in v["site"] else "Facebook" if "facebook.com" in v["site"] else "Site"
        li.append(f'{rotulo}: <a href="{e(v["site"])}" rel="nofollow noopener" target="_blank">{e(re.sub(r"^https?://(www[.])?", "", v["site"]).split("?")[0].rstrip("/")[:50])}</a>')
    li.append(f'<a href="{e(mapa(v))}" rel="nofollow noopener" target="_blank">Ver no Google Maps</a>')
    if li:
        partes.append("<ul class=\"lista\">" + "".join(f"<li>{x}</li>" for x in li) + "</ul>")
    return '<div class="ficha">' + "".join(partes) + "</div>"

DICAS_EXPOR = """<h2>Como propor uma exposição a um museu, galeria ou centro cultural?</h2>
<ol>
<li><strong>Pesquise o espaço:</strong> veja as exposições anteriores e se o perfil combina com o seu trabalho.</li>
<li><strong>Procure o canal certo:</strong> muitos espaços têm e-mail de curadoria, editais ou formulário de inscrição. Se não houver, ligue ou mande mensagem para perguntar.</li>
<li><strong>Prepare o material:</strong> portfólio com fotos boas das obras, currículo, texto sobre sua pesquisa e, se possível, uma proposta de montagem.</li>
<li><strong>Informe o essencial:</strong> título, técnica, medidas e quantidade de obras, além de necessidades de montagem e seguro.</li>
<li><strong>Combine por escrito:</strong> datas, responsabilidades, transporte, divulgação e eventual venda das obras.</li>
</ol>
<p>Termos úteis: <a href="/glossario/o-que-e-curadoria/">curadoria</a>, <a href="/glossario/o-que-e-vernissage/">vernissage</a>, <a href="/glossario/o-que-e-galeria-de-arte/">galeria de arte</a> e <a href="/glossario/o-que-e-acervo/">acervo</a>.</p>"""

def titulo_cidade(c):
    t = f"Museus e galerias de arte em {c} (RJ): endereços e contatos"
    return t if len(t) <= 66 else f"Museus e galerias em {c} (RJ): endereços"

def pgs_locais():
    if not LOCAIS:
        return []
    por = locais_por_cidade()
    cidades = sorted(por, key=lambda c: (-len(por[c]), c))
    grandes = [c for c in cidades if len(por[c]) >= MIN_CIDADE]
    pequenas = [c for c in cidades if len(por[c]) < MIN_CIDADE]
    ar = "Rio de Janeiro"
    urls = [BASE_EXPOR]
    total = len(LOCAIS)
    # --- páginas por cidade
    for c in grandes:
        vs = por[c]
        url = f"{BASE_EXPOR}{slug_de(c)}/"
        urls.append(url)
        nomes = [v["nome"] for v in vs[:3]]
        resp = f"{c} tem {len(vs)} locais de exposição de arte listados aqui, entre museus, galerias e espaços culturais, como {', '.join(nomes[:-1])} e {nomes[-1]}." if len(nomes) > 1 else f"{c} tem {len(vs)} local de exposição de arte listado aqui: {nomes[0]}."
        grupos = ""
        for tp in TIPO_ORDEM:
            g = [v for v in vs if v["tipo"] == tp]
            if g:
                plural = {"Museu": "Museus", "Galeria de arte": "Galerias de arte", "Centro de arte": "Centros de arte", "Centro cultural": "Centros culturais", "Espaço cultural": "Espaços culturais"}[tp]
                grupos += f"<h2>{plural} em {e(c)}</h2>" + "".join(ficha_local(v) for v in g)
        faq = [(f"Quais museus e galerias de arte existem em {c}?", f"Entre os locais listados nesta página estão {', '.join(v['nome'] for v in vs[:6])}. A lista traz endereço, telefone e site quando disponíveis."),
               (f"Como expor minha arte em {c}?", "Pesquise o perfil do espaço, procure o canal de curadoria ou os editais, envie portfólio e currículo e combine tudo por escrito. Cada espaço tem suas regras."),
               ("As informações desta página estão atualizadas?", "Os dados foram coletados em 7 de novembro de 2026. Horários, endereços e programação mudam, por isso confirme com o espaço antes de ir ou de enviar uma proposta.")]
        outras = "".join(f'<li><a href="{BASE_EXPOR}{slug_de(x)}/">{e(x)}</a> ({len(por[x])})</li>' for x in grandes if x != c)
        corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › <a href="{BASE_EXPOR}">Onde expor arte no RJ</a> › {e(c)}</p><article class="art" style="max-width:860px"><h1>Museus, galerias e espaços culturais em {e(c)} (RJ)</h1>
<p class="cons">Atualizado em {meses(HOJE)} · <a href="/sobre/">Wil Catarina Artes</a></p>
<div class="resp"><strong>Resposta rápida:</strong> {e(resp)}</div>
{grupos}{DICAS_EXPOR}<h2>Perguntas frequentes</h2>{faq_html(faq)}
<h2>Outras cidades do estado do Rio</h2><ul class="lista">{outras}</ul>
<p>Veja também a <a href="{BASE_EXPOR}">lista de todas as cidades</a> e conheça as <a href="/obras/">obras de Wil Catarina</a>.</p>
<p class="cons">Dados coletados do Google Maps em {meses(HOJE)}. Confirme horários e programação diretamente com cada espaço.</p></article></div>"""
        ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
              {"@type": "CollectionPage", "name": f"Museus e galerias de arte em {c} (RJ)", "url": DOM + url, "inLanguage": "pt-BR", "dateModified": HOJE, "isPartOf": {"@id": SITE_ID}, "publisher": {"@id": PESSOA_ID},
               "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".resp", "h1"]},
               "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": local_ld(v)} for i, v in enumerate(vs)]}},
              faq_ld(faq), crumb_ld([("Início", "/"), ("Onde expor arte no RJ", BASE_EXPOR), (c, url)])]
        gravar(url, pagina(url, titulo_cidade(c), meta_desc(f"{resp} Endereços, telefones e sites para visitar ou propor uma exposição."), corpo, ld, ativo=BASE_EXPOR))
    # --- página-mãe
    lista_cid = "".join(f'<li><a href="{BASE_EXPOR}{slug_de(c)}/"><strong>{e(c)}</strong></a>: {len(por[c])} locais ({e(", ".join(v["nome"] for v in por[c][:3]))}…)</li>' for c in grandes)
    outras_html = ""
    if pequenas:
        outras_html = "<h2>Outras cidades com locais de arte</h2>" + "".join(
            f'<h3>{e(c)}</h3><ul class="lista">' + "".join(f'<li><strong>{e(v["nome"])}</strong> ({e(v["tipo"].lower())}) — {e(v["endereco"])}' + (f' · <a href="{e(v["site"])}" rel="nofollow noopener" target="_blank">site</a>' if v.get("site") else "") + "</li>" for v in por[c]) + "</ul>"
            for c in pequenas)
    faq = [("Onde expor arte no estado do Rio de Janeiro?", f"Esta página reúne {total} museus, galerias e espaços culturais em {len(por)} cidades do estado do Rio, com endereço e contato. As maiores concentrações estão em " + ", ".join(grandes[:3]) + "."),
           ("Como propor uma exposição?", "Pesquise o espaço, procure o canal de curadoria ou o edital, envie portfólio, currículo e texto sobre sua pesquisa e combine datas, montagem e divulgação por escrito."),
           ("Preciso pagar para expor?", "Depende do espaço. Alguns são públicos e selecionam por edital ou curadoria, outros são galerias que cobram taxa ou comissão sobre vendas. Pergunte e combine por escrito antes de aceitar."),
           ("As informações estão atualizadas?", "Os dados foram coletados em 7 de novembro de 2026. Confirme horários, endereços e programação com cada espaço antes de ir.")]
    corpo = f"""<div class="w"><p class="crumb"><a href="/">Início</a> › Onde expor arte no RJ</p><article class="art" style="max-width:860px"><h1>Onde expor arte no Rio de Janeiro: museus, galerias e espaços culturais</h1>
<p class="cons">Atualizado em {meses(HOJE)} · <a href="/sobre/">Wil Catarina Artes</a></p>
<div class="resp"><strong>Resposta rápida:</strong> reunimos {total} museus, galerias de arte, centros culturais e espaços de exposição em {len(por)} cidades do estado do Rio de Janeiro, com endereço, telefone e site. Escolha a cidade, veja os locais e entre em contato para propor sua exposição ou planejar uma visita.</div>
<h2>Locais de exposição por cidade</h2><ul class="lista">{lista_cid}</ul>
{outras_html}{DICAS_EXPOR}<h2>Perguntas frequentes</h2>{faq_html(faq)}
<p>Wil Catarina é artista visual e curadora de Niterói e já expôs em museus, galerias e espaços culturais do Rio. <a href="/sobre/">Conheça a trajetória</a> e veja as <a href="/obras/">obras</a>.</p>
<p class="cons">Dados coletados do Google Maps em {meses(HOJE)}. Confirme horários e programação diretamente com cada espaço.</p></article></div>"""
    ld = [{"@type": "WebSite", "@id": SITE_ID, "url": DOM + "/", "name": S["nome_site"], "inLanguage": "pt-BR"}, pessoa(),
          {"@type": "CollectionPage", "name": "Onde expor arte no Rio de Janeiro", "url": DOM + BASE_EXPOR, "inLanguage": "pt-BR", "dateModified": HOJE, "isPartOf": {"@id": SITE_ID}, "publisher": {"@id": PESSOA_ID},
           "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".resp", "h1"]},
           "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f"Museus e galerias de arte em {c}", "url": f"{DOM}{BASE_EXPOR}{slug_de(c)}/"} for i, c in enumerate(grandes)]}},
          faq_ld(faq), crumb_ld([("Início", "/"), ("Onde expor arte no RJ", BASE_EXPOR)])]
    gravar(BASE_EXPOR, pagina(BASE_EXPOR, "Onde expor arte no Rio de Janeiro: museus, galerias e espaços", f"{total} museus, galerias e centros culturais do estado do Rio de Janeiro, por cidade, com endereço, telefone e site. Veja como propor uma exposição.", corpo, ld, ativo=BASE_EXPOR))
    return urls

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
    carregar_termos()
    carregar_locais()
    modelos(); painel(); pg_home(); pg_obras(); pg_sobre(); pg_blog(); pg_contato(); pg_404(); pg_glossario(); pgs_legais(); feed(); llms_full(); urls_locais = pgs_locais()
    for o in S["obras"]:
        pg_obra(o)
    urls = ["/", "/obras/", "/sobre/", "/glossario/"] + ["/blog/", "/contato/", "/politica-de-privacidade/", "/termos-de-uso/", "/acessibilidade/"] + [t["url"] for t in TERMOS] + [f"/blog/{p['slug']}/" for p in BLOG] + urls_locais
    tecnicos(urls)
    print(("PRODUÇÃO" if PROD else "TESTE (noindex)"), "-", len(urls), "páginas")

main()
