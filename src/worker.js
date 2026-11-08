// Worker do site Wil Catarina Artes.
// - Páginas estáticas vêm de /site (assets).
// - Início, /obras/ e /obras/<slug>/ são montadas com as obras do banco (D1).
// - /api/* é o painel da artista (login por senha, cadastro de obras e fotos).
// - /f/<id>-p.webp|g.webp serve as fotos enviadas pelo painel.

const TIPOS = ["Tela", "Escultura", "Desenho", "Gravura", "Fotografia", "Outro"];
let CFG = null, MOLDURA = null;

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const brl = (v) => "R$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const json = (o, status = 200, extra = {}) => new Response(JSON.stringify(o), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra } });

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const p = url.pathname;
    try {
      if (p.startsWith("/api/")) return await api(req, env, url);
      if (p.startsWith("/f/")) return await foto(env, p);
      if (p.startsWith("/_tpl/")) return new Response("Não encontrado", { status: 404 });
      if (p === "/sitemap.xml") return await sitemap(env, url);
      if (p === "/") return await paginaMarcada(env, url, true);
      if (p === "/obras" ) return Response.redirect(url.origin + "/obras/", 301);
      if (p === "/obras/") return await paginaMarcada(env, url, false);
      const m = p.match(/^\/obras\/([a-z0-9-]+)\/?$/);
      if (m) return await paginaObra(env, url, m[1]);
    } catch (e) {
      console.error("erro", p, e && e.stack || e);
      return env.ASSETS.fetch(req); // cai para a versão estática
    }
    return env.ASSETS.fetch(req);
  },
};

// ---------- dados ----------
async function carregarModelos(env, url) {
  if (!CFG) CFG = await (await env.ASSETS.fetch(new Request(url.origin + "/_tpl/config.json"))).json();
  if (!MOLDURA) MOLDURA = await (await env.ASSETS.fetch(new Request(url.origin + "/_tpl/moldura.html"))).text();
}

async function listar(env, soPublicas) {
  const o = await env.DB.prepare(`SELECT id,slug,titulo,tipo,preco,medidas,tecnica,ano,descricao,status,publicada,ordem,atualizado FROM obras ${soPublicas ? "WHERE publicada=1" : ""} ORDER BY ordem DESC, id DESC`).all();
  const f = await env.DB.prepare("SELECT id,obra_id,estatico FROM fotos ORDER BY obra_id, ordem, id").all();
  const por = {};
  for (const x of f.results) (por[x.obra_id] ||= []).push({ id: x.id, estatico: x.estatico });
  return o.results.map((r) => ({ ...r, fotos: por[r.id] || [] }));
}

function imgs(foto) {
  if (!foto) return null;
  if (foto.estatico) return { p: `/img/${foto.estatico}-480.webp`, g: `/img/${foto.estatico}-1400.webp`, srcsetP: `/img/${foto.estatico}-480.webp 480w, /img/${foto.estatico}-900.webp 900w`, srcsetG: `/img/${foto.estatico}-480.webp 480w, /img/${foto.estatico}-900.webp 900w, /img/${foto.estatico}-1400.webp 1400w` };
  return { p: `/f/${foto.id}-p.webp`, g: `/f/${foto.id}-g.webp`, srcsetP: `/f/${foto.id}-p.webp 640w, /f/${foto.id}-g.webp 1400w`, srcsetG: `/f/${foto.id}-p.webp 640w, /f/${foto.id}-g.webp 1400w` };
}

const wa = (cfg, msg) => `https://wa.me/${cfg.whatsapp}?text=${encodeURIComponent(msg)}`;
const alt = (o) => `${o.titulo}, ${o.tipo.toLowerCase()} de Wil Catarina`;

// ---------- páginas ----------
function precoHtml(o, grande) {
  if (o.status === "vendida") return `<span class="preco">Vendida</span>`;
  if (o.preco) return `<span class="preco"${grande ? ' style="font-size:1.6rem"' : ""}>${brl(o.preco)}</span>`;
  return `<span class="cons">Valor sob consulta</span>`;
}

function card(cfg, o) {
  const im = imgs(o.fotos[0]);
  const img = im ? `<img src="${im.p}" srcset="${im.srcsetP}" sizes="(min-width:800px) 340px, 100vw" width="480" height="360" alt="${esc(alt(o))}" loading="lazy" decoding="async">` : "";
  const btn = o.status === "vendida"
    ? `<a class="btn o" href="/obras/${o.slug}/">Ver detalhes</a>`
    : `<a class="btn" href="${wa(cfg, "Olá, Wil! Tenho interesse na obra " + o.titulo + ".")}" rel="noopener">Pedir pelo WhatsApp</a>`;
  return `<article class="card"><a class="l" href="/obras/${o.slug}/"><div class="im">${img}</div><div class="cb"><h3>${esc(o.titulo)}</h3><p>${esc(o.tipo)} · Wil Catarina</p>${precoHtml(o)}</div></a><div class="cb" style="padding-top:0">${btn}</div></article>`;
}

async function paginaMarcada(env, url, home) {
  await carregarModelos(env, url);
  const [res, obras] = await Promise.all([env.ASSETS.fetch(new Request(url.origin + url.pathname)), listar(env, true)]);
  let html = await res.text();
  const lista = home ? obras.slice(0, 6) : obras;
  const cards = lista.length ? lista.map((o) => card(CFG, o)).join("") : `<p>Em breve, novas obras. Fale com a artista pelo WhatsApp.</p>`;
  html = html.replace(/<!--OBRAS-->[\s\S]*?<!--\/OBRAS-->/, () => `<!--OBRAS-->${cards}<!--/OBRAS-->`);
  const itens = obras.map((o, i) => ({ "@type": "ListItem", position: i + 1, url: `${CFG.dominio}/obras/${o.slug}/`, name: o.titulo }));
  html = html.replace('"__ITEMS__"', () => JSON.stringify(itens));
  return new Response(html, { status: res.status, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=60" } });
}

function paragrafos(texto) {
  return String(texto || "").split(/\n{2,}/).map((t) => t.trim()).filter(Boolean).map((t) => `<p>${esc(t).replace(/\n/g, "<br>")}</p>`).join("");
}

async function paginaObra(env, url, slug) {
  await carregarModelos(env, url);
  const todas = await listar(env, true);
  const o = todas.find((x) => x.slug === slug);
  if (!o) {
    const r = await env.ASSETS.fetch(new Request(url.origin + "/404.html"));
    return new Response(await r.text(), { status: 404, headers: { "content-type": "text/html; charset=utf-8" } });
  }
  const cfg = CFG, im = imgs(o.fotos[0]);
  const vendida = o.status === "vendida";
  const artigo = o.tipo === "Tela" ? "uma tela" : o.tipo === "Escultura" ? "uma escultura" : o.tipo === "Desenho" ? "um desenho" : o.tipo === "Gravura" ? "uma gravura" : o.tipo === "Fotografia" ? "uma fotografia" : "uma obra";
  const ficha = [["Tipo", o.tipo], ["Técnica", o.tecnica], ["Medidas", o.medidas], ["Ano", o.ano]].filter((x) => x[1]).map((x) => `<li><strong>${x[0]}:</strong> ${esc(x[1])}</li>`).join("");
  const resumoPreco = vendida ? "Esta obra já foi vendida." : o.preco ? `Valor: ${brl(o.preco)}.` : "O valor é informado pelo WhatsApp.";
  const detalhes = [o.tecnica, o.medidas].filter(Boolean).join(", ");
  const resposta = `${o.titulo} é ${artigo} da artista visual Wil Catarina, de Niterói (RJ).${detalhes ? " " + detalhes + "." : ""} ${resumoPreco}`;
  const desc = (o.descricao || resposta).slice(0, 300);
  const fotos = o.fotos.map(imgs);
  const galeria = fotos.slice(1).map((f) => `<img class="ph" src="${f.g}" srcset="${f.srcsetG}" sizes="(min-width:800px) 640px, 100vw" alt="${esc(alt(o))}, outro ângulo" loading="lazy" decoding="async" style="margin-top:14px;width:100%">`).join("");
  const outras = todas.filter((x) => x.slug !== slug).slice(0, 3).map((x) => card(cfg, x)).join("");
  const botao = vendida
    ? `<p><a class="btn o" href="${wa(cfg, "Olá, Wil! Vi que a obra " + o.titulo + " foi vendida. Você faz algo parecido?")}" rel="noopener">Pedir algo parecido</a></p>`
    : `<p><a class="btn" href="${wa(cfg, "Olá, Wil! Tenho interesse na obra " + o.titulo + ". Pode me passar medidas, técnica e condições?")}" rel="noopener">Pedir pelo WhatsApp</a></p><p class="cons">Medidas, técnica e entrega combinadas direto com a artista.</p>`;
  const corpo = `<div class="w"><p class="crumb"><a href="/">Início</a> › <a href="/obras/">Obras</a> › ${esc(o.titulo)}</p>
<div class="prod"><div>${im ? `<img class="ph" src="${im.g}" srcset="${im.srcsetG}" sizes="(min-width:800px) 640px, 100vw" width="1400" height="1000" alt="${esc(alt(o))}" fetchpriority="high">` : ""}${galeria}</div>
<div><p class="kick">${esc(o.tipo)} · Wil Catarina</p><h1>${esc(o.titulo)}</h1>
<div class="resp"><strong>Resposta rápida:</strong> ${esc(resposta)}</div>
<p>${precoHtml(o, true)}</p>${paragrafos(o.descricao)}${ficha ? `<ul class="lista">${ficha}</ul>` : ""}${botao}</div></div>
${outras ? `<h2>Outras obras</h2><div class="grade">${outras}</div>` : ""}</div>`;
  const pagUrl = `${cfg.dominio}/obras/${o.slug}/`;
  const ogImg = im ? cfg.dominio + im.g : cfg.dominio + "/img/og.jpg";
  const obra = { "@type": ["VisualArtwork", "Product"], "@id": pagUrl + "#obra", name: o.titulo, description: desc, image: ogImg, url: pagUrl, creator: { "@id": cfg.pessoa_id }, artform: o.tipo, brand: { "@type": "Person", name: cfg.nome } };
  if (o.tecnica) obra.artMedium = o.tecnica;
  if (o.ano) obra.dateCreated = o.ano;
  if (o.preco && !vendida) obra.offers = { "@type": "Offer", price: Number(o.preco).toFixed(2), priceCurrency: "BRL", availability: "https://schema.org/InStock", url: pagUrl, seller: { "@id": cfg.pessoa_id } };
  if (vendida) obra.offers = { "@type": "Offer", priceCurrency: "BRL", availability: "https://schema.org/SoldOut", url: pagUrl, ...(o.preco ? { price: Number(o.preco).toFixed(2) } : {}) };
  const crumb = { "@type": "BreadcrumbList", itemListElement: [["Início", "/"], ["Obras", "/obras/"], [o.titulo, `/obras/${o.slug}/`]].map((x, i) => ({ "@type": "ListItem", position: i + 1, name: x[0], item: cfg.dominio + x[1] })) };
  const ld = `<script type="application/ld+json">${JSON.stringify({ "@context": "https://schema.org", "@graph": [{ "@type": "WebSite", "@id": cfg.site_id, url: cfg.dominio + "/", name: cfg.nome_site, inLanguage: "pt-BR" }, cfg.pessoa, obra, crumb] }).replace(/</g, "\\u003c")}</script>`;
  const titulo = `${o.titulo} — ${o.tipo} de Wil Catarina | ${cfg.nome_site}`;
  const html = MOLDURA.replaceAll("{{TITLE}}", () => esc(titulo)).replaceAll("{{DESC}}", () => esc(desc)).replaceAll("{{URL}}", () => pagUrl).replaceAll("{{OG}}", () => ogImg).replace("{{LD}}", () => ld).replace("{{BODY}}", () => corpo);
  return new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=60" } });
}

async function sitemap(env, url) {
  const res = await env.ASSETS.fetch(new Request(url.origin + "/sitemap.xml"));
  let xml = await res.text();
  const obras = await listar(env, true);
  const extra = obras.map((o) => `<url><loc>${(CFG ? CFG.dominio : url.origin)}/obras/${o.slug}/</loc><lastmod>${String(o.atualizado).slice(0, 10)}</lastmod></url>`).join("");
  xml = xml.replace("</urlset>", () => extra + "</urlset>");
  return new Response(xml, { headers: { "content-type": "application/xml; charset=utf-8", "cache-control": "public, max-age=300" } });
}

async function foto(env, p) {
  const m = p.match(/^\/f\/(\d+)-(p|g)\.webp$/);
  if (!m) return new Response("Não encontrado", { status: 404 });
  const col = m[2];
  const r = await env.DB.prepare(`SELECT ${col} AS b FROM fotos WHERE id=? AND ${col} IS NOT NULL`).bind(Number(m[1])).first();
  if (!r) return new Response("Não encontrado", { status: 404 });
  const bytes = r.b instanceof ArrayBuffer ? new Uint8Array(r.b) : Uint8Array.from(r.b);
  return new Response(bytes, { headers: { "content-type": "image/webp", "cache-control": "public, max-age=31536000, immutable" } });
}

// ---------- autenticação ----------
const enc = new TextEncoder();
async function hmac(chave, texto) {
  const k = await crypto.subtle.importKey("raw", enc.encode(chave), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const s = await crypto.subtle.sign("HMAC", k, enc.encode(texto));
  return [...new Uint8Array(s)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
function igual(a, b) {
  const x = enc.encode(a), y = enc.encode(b);
  let d = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) d |= (x[i] || 0) ^ (y[i] || 0);
  return d === 0;
}
async function sessaoValida(req, env) {
  const c = (req.headers.get("cookie") || "").match(/(?:^|;\s*)sid=([0-9]+)\.([0-9a-f]+)/);
  if (!c || Number(c[1]) < Date.now()) return false;
  return igual(c[2], await hmac(env.SESSION_SECRET, c[1]));
}

// ---------- API ----------
const limpa = (v, n) => String(v ?? "").replace(/\s+$/g, "").slice(0, n);
const ACENTOS = new RegExp("[" + String.fromCharCode(0x300) + "-" + String.fromCharCode(0x36f) + "]", "g");
function slugDe(t) {
  return String(t).normalize("NFD").replace(ACENTOS, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "obra";
}
async function slugUnico(env, titulo, ignorarId) {
  const base = slugDe(titulo);
  let s = base, i = 2;
  for (;;) {
    const r = await env.DB.prepare("SELECT id FROM obras WHERE slug=?").bind(s).first();
    if (!r || r.id === ignorarId) return s;
    s = `${base}-${i++}`;
  }
}
function dadosObra(b) {
  const titulo = limpa(b.titulo, 120).trim();
  if (!titulo) throw new Erro("Escreva o título da obra.");
  const tipo = TIPOS.includes(b.tipo) ? b.tipo : "Tela";
  let preco = null;
  if (b.preco !== null && b.preco !== undefined && String(b.preco).trim() !== "") {
    preco = Number(String(b.preco).replace(/\./g, "").replace(",", "."));
    if (!isFinite(preco) || preco < 0 || preco > 100000000) throw new Erro("Preço inválido. Use só números, por exemplo 1500 ou 1500,50.");
    if (preco === 0) preco = null;
  }
  return { titulo, tipo, preco, medidas: limpa(b.medidas, 80), tecnica: limpa(b.tecnica, 120), ano: limpa(b.ano, 20), descricao: limpa(b.descricao, 3000), status: b.status === "vendida" ? "vendida" : "disponivel", publicada: b.publicada ? 1 : 0 };
}
class Erro extends Error {}

async function api(req, env, url) {
  const p = url.pathname, met = req.method;
  const origem = req.headers.get("origin");
  if (met !== "GET" && origem && new URL(origem).host !== url.host) return json({ erro: "Origem não permitida." }, 403);

  if (p === "/api/login" && met === "POST") {
    const ip = req.headers.get("cf-connecting-ip") || "?";
    const agora = Date.now();
    await env.DB.prepare("DELETE FROM login_falhas WHERE ts < ?").bind(agora - 900000).run();
    const n = await env.DB.prepare("SELECT COUNT(*) AS n FROM login_falhas WHERE ip=?").bind(ip).first();
    if (n.n >= 8) return json({ erro: "Muitas tentativas. Espere 15 minutos." }, 429);
    const b = await req.json().catch(() => ({}));
    if (!env.SENHA_PAINEL || !igual(String(b.senha || "").trim(), String(env.SENHA_PAINEL).trim())) {
      await env.DB.prepare("INSERT INTO login_falhas (ip, ts) VALUES (?,?)").bind(ip, agora).run();
      return json({ erro: "Senha incorreta." }, 401);
    }
    const exp = String(agora + 30 * 86400000);
    const sid = `${exp}.${await hmac(env.SESSION_SECRET, exp)}`;
    return json({ ok: true }, 200, { "set-cookie": `sid=${sid}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Strict` });
  }
  if (p === "/api/logout" && met === "POST") return json({ ok: true }, 200, { "set-cookie": "sid=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict" });

  if (!(await sessaoValida(req, env))) return json({ erro: "Entre com a senha." }, 401);

  try {
    if (p === "/api/obras" && met === "GET") return json({ obras: await listar(env, false), tipos: TIPOS });
    if (p === "/api/obras" && met === "POST") {
      const d = dadosObra(await req.json());
      const slug = await slugUnico(env, d.titulo, 0);
      const mx = await env.DB.prepare("SELECT COALESCE(MAX(ordem),0) AS m FROM obras").first();
      const r = await env.DB.prepare("INSERT INTO obras (slug,titulo,tipo,preco,medidas,tecnica,ano,descricao,status,publicada,ordem) VALUES (?,?,?,?,?,?,?,?,?,?,?)")
        .bind(slug, d.titulo, d.tipo, d.preco, d.medidas, d.tecnica, d.ano, d.descricao, d.status, d.publicada, mx.m + 1).run();
      return json({ ok: true, id: r.meta.last_row_id, slug });
    }
    let m = p.match(/^\/api\/obras\/(\d+)$/);
    if (m && met === "PUT") {
      const id = Number(m[1]);
      const d = dadosObra(await req.json());
      const slug = await slugUnico(env, d.titulo, id);
      await env.DB.prepare("UPDATE obras SET slug=?,titulo=?,tipo=?,preco=?,medidas=?,tecnica=?,ano=?,descricao=?,status=?,publicada=?,atualizado=datetime('now') WHERE id=?")
        .bind(slug, d.titulo, d.tipo, d.preco, d.medidas, d.tecnica, d.ano, d.descricao, d.status, d.publicada, id).run();
      return json({ ok: true, slug });
    }
    if (m && met === "DELETE") {
      const id = Number(m[1]);
      await env.DB.prepare("DELETE FROM fotos WHERE obra_id=?").bind(id).run();
      await env.DB.prepare("DELETE FROM obras WHERE id=?").bind(id).run();
      return json({ ok: true });
    }
    m = p.match(/^\/api\/obras\/(\d+)\/fotos$/);
    if (m && met === "POST") {
      const id = Number(m[1]);
      const ob = await env.DB.prepare("SELECT id FROM obras WHERE id=?").bind(id).first();
      if (!ob) return json({ erro: "Obra não encontrada." }, 404);
      const qt = await env.DB.prepare("SELECT COUNT(*) AS n, COALESCE(MAX(ordem),0) AS m FROM fotos WHERE obra_id=?").bind(id).first();
      if (qt.n >= 6) return json({ erro: "No máximo 6 fotos por obra." }, 400);
      const f = await req.formData();
      const pq = f.get("p"), g = f.get("g");
      if (!pq || !g || typeof pq === "string" || typeof g === "string") return json({ erro: "Foto inválida." }, 400);
      if (pq.size > 250000 || g.size > 1000000) return json({ erro: "Foto muito grande." }, 413);
      const bp = await pq.arrayBuffer(), bg = await g.arrayBuffer();
      const ok = (b) => { const u = new Uint8Array(b); return u.length > 12 && String.fromCharCode(...u.slice(0, 4)) === "RIFF" && String.fromCharCode(...u.slice(8, 12)) === "WEBP"; };
      if (!ok(bp) || !ok(bg)) return json({ erro: "Formato de foto inválido." }, 400);
      const r = await env.DB.prepare("INSERT INTO fotos (obra_id,ordem,p,g) VALUES (?,?,?,?)").bind(id, qt.m + 1, bp, bg).run();
      await env.DB.prepare("UPDATE obras SET atualizado=datetime('now') WHERE id=?").bind(id).run();
      return json({ ok: true, id: r.meta.last_row_id });
    }
    m = p.match(/^\/api\/fotos\/(\d+)$/);
    if (m && met === "DELETE") {
      const f = await env.DB.prepare("SELECT obra_id FROM fotos WHERE id=?").bind(Number(m[1])).first();
      await env.DB.prepare("DELETE FROM fotos WHERE id=?").bind(Number(m[1])).run();
      if (f) await env.DB.prepare("UPDATE obras SET atualizado=datetime('now') WHERE id=?").bind(f.obra_id).run();
      return json({ ok: true });
    }
    m = p.match(/^\/api\/fotos\/(\d+)\/capa$/);
    if (m && met === "POST") {
      const f = await env.DB.prepare("SELECT obra_id FROM fotos WHERE id=?").bind(Number(m[1])).first();
      if (!f) return json({ erro: "Foto não encontrada." }, 404);
      const mn = await env.DB.prepare("SELECT COALESCE(MIN(ordem),0) AS m FROM fotos WHERE obra_id=?").bind(f.obra_id).first();
      await env.DB.prepare("UPDATE fotos SET ordem=? WHERE id=?").bind(mn.m - 1, Number(m[1])).run();
      await env.DB.prepare("UPDATE obras SET atualizado=datetime('now') WHERE id=?").bind(f.obra_id).run();
      return json({ ok: true });
    }
  } catch (e) {
    if (e instanceof Erro) return json({ erro: e.message }, 400);
    console.error(e && e.stack || e);
    return json({ erro: "Erro no servidor. Tente de novo." }, 500);
  }
  return json({ erro: "Não encontrado." }, 404);
}
