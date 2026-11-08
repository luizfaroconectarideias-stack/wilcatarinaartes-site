"""Confere o site gerado: títulos, descrições, JSON-LD, H1 e links internos."""
import re, json, sys
from pathlib import Path
S = Path(__file__).resolve().parent.parent / "site"
paginas = {}
for f in S.rglob("index.html"):
    u = "/" + str(f.parent.relative_to(S)).replace("\\", "/") + "/"
    paginas[u.replace("/./", "/")] = f.read_text(encoding="utf8")
paginas["/"] = (S / "index.html").read_text(encoding="utf8")
erros = 0
def err(m):
    global erros; erros += 1; print("ERRO", m)
for u, h in sorted(paginas.items()):
    if u.startswith("/_tpl") or u.startswith("/painel"): continue
    t = re.search(r"<title>(.*?)</title>", h, re.S).group(1)
    d = re.search(r'<meta name="description" content="(.*?)"', h).group(1)
    if len(t) > 70: err(f"{u} título longo {len(t)}")
    if not 70 <= len(d) <= 165: print("aviso", u, "descrição", len(d))
    if h.count("<h1") != 1: err(f"{u} h1={h.count('<h1')}")
    for j in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try: json.loads(j)
        except Exception as ex:
            if "__ITEMS__" not in j: err(f"{u} json-ld inválido {ex}")
    for l in set(re.findall(r'href="(/[^"#?]*)"', h)):
        if l.startswith("/img/") or l in ("/estilo.css", "/favicon.svg", "/feed.xml", "/llms.txt", "/sitemap.xml"): continue
        if l not in paginas and not re.match(r"^/obras/[a-z0-9-]+/$", l) and l != "/painel/":
            err(f"{u} link quebrado {l}")
print(len(paginas), "páginas;", erros, "erros")
