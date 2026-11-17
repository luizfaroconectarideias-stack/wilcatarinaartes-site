#!/usr/bin/env python3
"""Importa as obras da pasta do Drive (baixada em _drive/) a partir de dados/obras_drive.json.
- Reduz as fotos para fotos/obras/ e fotos/expo/ (JPG até 1600 px).
- Gera migracoes/0003_obras_drive.sql para cadastrar as obras no banco D1.
Uso: python gerador/importar_obras.py"""
import json
from pathlib import Path
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
DRIVE = RAIZ / "_drive"
D = json.loads((RAIZ / "dados/obras_drive.json").read_text(encoding="utf8"))


def reduz(origem, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        return
    im = ImageOps.exif_transpose(Image.open(DRIVE / origem)).convert("RGB")
    im.thumbnail((1600, 1600))
    im.save(destino, "JPEG", quality=84, optimize=True)


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def texto(o):
    d = o["descricao"]
    if o.get("serie"):
        d += f" Da série {o['serie']}."
    return d


sql = ["-- Obras importadas do Google Drive da Wil em 17/11/2026 (dados/obras_drive.json)."]
for r in D["renomear"]:
    sql.append(f"UPDATE obras SET titulo={q(r['titulo'])}, descricao={q(texto(r))}, atualizado=datetime('now') WHERE id={r['id']};")
    for i, f in enumerate(r.get("fotos_extra", []), start=1):
        nome = f"o-id{r['id']}-{i}"
        reduz(f, RAIZ / "fotos/obras" / f"{nome}.jpg")
        sql.append(f"INSERT INTO fotos (obra_id,ordem,estatico) SELECT {r['id']},{i},{q(nome)} WHERE NOT EXISTS (SELECT 1 FROM fotos WHERE estatico={q(nome)});")

ordem = 200
for o in D["obras"]:
    sql.append("INSERT OR IGNORE INTO obras (slug,titulo,tipo,preco,tecnica,descricao,status,publicada,ordem) VALUES "
               f"({q(o['slug'])},{q(o['titulo'])},{q(o['tipo'])},NULL,{q(o.get('tecnica', ''))},{q(texto(o))},'disponivel',1,{ordem});")
    for i, f in enumerate(o["fotos"]):
        nome = f"o-{o['slug']}-{i + 1}"
        reduz(f, RAIZ / "fotos/obras" / f"{nome}.jpg")
        sql.append(f"INSERT INTO fotos (obra_id,ordem,estatico) SELECT id,{i},{q(nome)} FROM obras WHERE slug={q(o['slug'])} AND NOT EXISTS (SELECT 1 FROM fotos WHERE estatico={q(nome)});")
    ordem -= 1

for x in D["exposicoes"]:
    for i, f in enumerate(x["fotos"]):
        reduz(f, RAIZ / "fotos/expo" / f"x-{x['id']}-{i + 1}.jpg")

(RAIZ / "migracoes/0003_obras_drive.sql").write_text("\n".join(sql) + "\n", encoding="utf8")
print(len(D["obras"]), "obras;", len(sql), "linhas de SQL")
