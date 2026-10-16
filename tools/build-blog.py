#!/usr/bin/env python3
"""Builds the Domegarde blog pages from plain text files.

    python3 tools/build-blog.py            (run from the website folder)
    python3 tools/build-blog.py --sitemap-out PATH   (also writes a complete sitemap.xml to PATH)

Reads  blog-src/<date>-<slug>.en.md  and  blog-src/<date>-<slug>.fr.md   (every post must exist in both languages)
Writes blog.html, blog-fr.html, blog-<slug>.html, blog-<slug>-fr.html, feed.xml and feed-fr.xml next to index.html.
Also reads blog-src/page-facts.<lang>.md and blog-src/page-changelog.<lang>.md and writes the "Domegarde in brief"
pages (facts.html, en-bref.html) and the "What's new" pages (whats-new.html, nouveautes.html).
The header and footer are copied from index.html / index-fr.html, so the blog always matches the rest of the site.
Standard library only. See blog-src/README.md for how to write a post.
"""
import argparse, datetime, glob, html, json, os, re, sys

HOST = "https://www.domegarde.com"
NOINDEX = True   # the whole site tells search engines to stay away until launch day; set to False when the site goes public
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECTIONS = {  # key -> label, blurb (per language); order = order on the blog page
    "building": {
        "en": ("Building Domegarde", "What's new in the product, and why."),
        "fr": ("Les coulisses de Domegarde", "Les nouveautés du produit, et pourquoi."),
    },
    "news": {
        "en": ("French property news", "Rule changes that matter to landlords, explained with their sources. Every post shows when we last checked it."),
        "fr": ("Actualités de l'immobilier en France", "Les changements de règles qui concernent les propriétaires, expliqués avec leurs sources. Chaque article indique la date de sa dernière vérification."),
    },
}
T = {
    "en": dict(
        blog="Blog", blog_title="Blog", all_posts="← All posts", draft="Draft", read="Read the post",
        min_read="min read", by="By", team="The Domegarde team", sources="Sources", checked="Last checked",
        h1="What we're building, and what's changing in French property.",
        sub="Short updates on Domegarde, and plain-English explainers on French rental rules, each with its sources. Information, not legal advice.",
        desc="Updates on what Domegarde is building, and explainers on changes to French rental rules, with their sources.",
        rss="RSS feed", rss_title="Domegarde blog",
        news_note="This article gives information, not legal advice. It was last checked on {date}; rules change, so please confirm anything that matters with the official sources above, or with a lawyer, notary or accountant. If you spot a mistake, <a href=\"about.html#contact\">tell us</a>.",
        draft_head="[BROUILLON — À VÉRIFIER AVANT PUBLICATION]", draft_text="This is a draft for the founders to review. To check before it goes out:",
        cta_eyebrow="Ready when you are", cta_h2="Ready to take control of your portfolio?", cta_a="Request early access", cta_b="Compare plans",
        empty="Nothing here yet.", months=["January","February","March","April","May","June","July","August","September","October","November","December"],
        datefmt=lambda d, m: f"{d.day} {m[d.month-1]} {d.year}",
        index="index.html", get_started="get-started.html", pricing="pricing.html", lang_label="EN",
        updated="Last updated", home_crumb="Home",
    ),
    "fr": dict(
        blog="Blog", blog_title="Blog", all_posts="← Tous les articles", draft="Brouillon", read="Lire l'article",
        min_read="min de lecture", by="Par", team="L'équipe Domegarde", sources="Sources", checked="Dernière vérification",
        h1="Ce que nous construisons, et ce qui change dans l'immobilier en France.",
        sub="De courtes nouvelles de Domegarde, et des explications claires sur les règles de la location en France, avec leurs sources. De l'information, pas un conseil juridique.",
        desc="Ce que Domegarde construit, et des explications sur les changements des règles de la location en France, avec leurs sources.",
        rss="Flux RSS", rss_title="Blog Domegarde",
        news_note="Cet article informe, il ne constitue pas un conseil juridique. Il a été vérifié pour la dernière fois le {date} ; les règles évoluent, merci de confirmer tout point important auprès des sources officielles ci-dessus, ou d'un avocat, d'un notaire ou d'un expert-comptable. Si vous voyez une erreur, <a href=\"about-fr.html#contact\">dites-le-nous</a>.",
        draft_head="[BROUILLON — À VÉRIFIER AVANT PUBLICATION]", draft_text="Ceci est un brouillon à relire par les fondateurs. À vérifier avant publication :",
        cta_eyebrow="Quand vous serez prêt", cta_h2="Prêt à prendre le contrôle de votre patrimoine ?", cta_a="Demander un accès anticipé", cta_b="Comparer les tarifs",
        empty="Rien ici pour l'instant.", months=["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"],
        datefmt=lambda d, m: ("1er" if d.day == 1 else str(d.day)) + f" {m[d.month-1]} {d.year}",
        index="index-fr.html", get_started="get-started-fr.html", pricing="pricing-fr.html", lang_label="FR",
        updated="Dernière mise à jour", home_crumb="Accueil",
    ),
}

PAGES = {  # simple pages written as text files: key -> output file per language, eyebrow per language
    "facts": {"files": {"en": "facts.html", "fr": "en-bref.html"}, "eyebrow": {"en": "Key facts", "fr": "L'essentiel"}},
    "changelog": {"files": {"en": "whats-new.html", "fr": "nouveautes.html"}, "eyebrow": {"en": "Changelog", "fr": "Journal des nouveautés"}},
}
ORG_ID = HOST + "/#organization"
def jsonld(*objs):
    """Structured data for search engines and AI systems. A data block, not a script, so the site's security rules allow it."""
    out = []
    for o in objs:
        txt = json.dumps(o, ensure_ascii=False, indent=2).replace("</", "<\\/")
        out.append('<script type="application/ld+json">\n' + txt + "\n</script>")
    return "\n".join(out) + "\n"
def org_object(lang):
    return {"@context": "https://schema.org", "@type": "Organization", "@id": ORG_ID, "name": "Domegarde", "url": HOST + "/",
            "logo": HOST + "/assets/logo-icon.png", "areaServed": "FR", "knowsLanguage": ["fr", "en"],
            "description": ("Software for independent landlords in France: which legal obligations apply, ranked by consequence, with the proof that satisfies each one."
                            if lang == "en" else
                            "Un logiciel pour les propriétaires bailleurs indépendants en France : quelles obligations légales s'appliquent, classées par conséquence, avec la preuve qui satisfait chacune.")}

# ------------------------------------------------------------------ text helpers
NB = " "
def fr_typo(s):
    """French spacing: a no-break space before : ; ? ! » and after «, and between a number and €."""
    s = re.sub(r"(?<=\S) ([:;?!»])", NB + r"\1", s)
    s = re.sub(r"(«) ", r"\1" + NB, s)
    s = re.sub(r"(\d) (€|%)", r"\1" + NB + r"\2", s)
    return s

def esc(s): return html.escape(s, quote=True)

def inline(s, lang):
    """Minimal markdown for one line of text: **bold**, *italic*, `code`, [text](url)."""
    if lang == "fr": s = fr_typo(s)
    s = esc(s)
    def link(m):
        text, url = m.group(1), html.unescape(m.group(2))
        ext = url.startswith("http")
        attrs = ' target="_blank" rel="noopener"' if ext else ""
        return f'<a href="{esc(url)}"{attrs}>{text}</a>'
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])", r"<em>\1</em>", s)
    return s

def slugify(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).lower()
    for a, b in (("é","e"),("è","e"),("ê","e"),("à","a"),("â","a"),("î","i"),("ô","o"),("ù","u"),("û","u"),("ç","c"),("’","'")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]

def markdown(body, lang):
    out, blocks = [], re.split(r"\n\s*\n", body.strip())
    for b in blocks:
        lines = [l.rstrip() for l in b.split("\n") if l.strip()]
        if not lines: continue
        if lines[0].startswith("## "):
            t = lines[0][3:].strip(); out.append(f'<h2 id="{slugify(t)}">{inline(t, lang)}</h2>')
            lines = lines[1:]
            if not lines: continue
        if lines[0].startswith("### "):
            out.append(f"<h3>{inline(lines[0][4:].strip(), lang)}</h3>"); lines = lines[1:]
            if not lines: continue
        if all(l.startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l[2:], lang)}</li>" for l in lines) + "</ul>")
        elif all(re.match(r"\d+\. ", l) for l in lines):
            items = [re.sub(r"^\d+\. ", "", l) for l in lines]
            out.append("<ol>" + "".join("<li>" + inline(i, lang) + "</li>" for i in items) + "</ol>")
        elif all(l.startswith("> ") for l in lines):
            out.append("<blockquote><p>" + inline(" ".join(l[2:] for l in lines), lang) + "</p></blockquote>")
        else:
            out.append("<p>" + inline(" ".join(lines), lang) + "</p>")
    return "\n".join(out)

def parse_front(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)\Z", raw, flags=re.S)
    assert m, f"{path}: missing front matter (--- ... ---)"
    meta, key = {}, None
    for line in m.group(1).split("\n"):
        if re.match(r"^- ", line) and key:
            meta.setdefault(key, []).append(line[2:].strip())
        elif ":" in line:
            key, _, val = line.partition(":"); key = key.strip(); val = val.strip()
            if val: meta[key] = val
            else: meta[key] = []
    meta["body"] = m.group(2)
    return meta

def parse_page(path):
    meta = parse_front(path)
    for req in ("title", "excerpt", "updated"):
        assert meta.get(req), f"{path}: front matter needs '{req}'"
    datetime.date.fromisoformat(meta["updated"])
    return meta

def parse_post(path):
    meta = parse_front(path)
    for req in ("title", "section", "excerpt"):
        assert meta.get(req), f"{path}: front matter needs '{req}'"
    assert meta["section"] in SECTIONS, f"{path}: section must be one of {list(SECTIONS)}"
    meta["status"] = meta.get("status", "published")
    assert meta["status"] in ("draft", "published"), f"{path}: status must be draft or published"
    return meta

# ------------------------------------------------------------------ page parts
def site_part(name, pattern):
    s = open(os.path.join(ROOT, name), encoding="utf-8").read()
    m = re.search(pattern, s, flags=re.S)
    assert m, f"{name}: could not find {pattern}"
    return m.group(0)

def header(lang, own_file, other_file, active_blog=True):
    h = site_part("index.html" if lang == "en" else "index-fr.html", r'<header class="site-header">.*?</header>')
    h = re.sub(r'<a href="(index(?:-fr)?\.html)" class="active" aria-current="page">', r'<a href="\1">', h)
    blog = "blog.html" if lang == "en" else "blog-fr.html"
    assert f'<a href="{blog}">' in h, "the header has no Blog link: add it to the site pages first"
    if active_blog:
        h = h.replace(f'<a href="{blog}">', f'<a href="{blog}" class="active" aria-current="page">', 1)
    sw = "index-fr.html" if lang == "en" else "index.html"
    assert h.count(f'<a href="{sw}" class="lang-switch"') == 1, "language switch not found in header"
    return h.replace(f'<a href="{sw}" class="lang-switch"', f'<a href="{other_file}" class="lang-switch"')

def footer(lang):
    return site_part("index.html" if lang == "en" else "index-fr.html", r'<footer class="site-footer">.*?</footer>')

def head(lang, title, desc, own, en_file, fr_file, kind="website", published=None, ld=""):
    t = T[lang]
    og_extra = f'\n<meta property="article:published_time" content="{published}">' if published else ""
    feed_en, feed_fr = "/feed.xml", "/feed-fr.xml"
    ROBOTS = '<meta name="robots" content="noindex, nofollow">\n' if NOINDEX else ""
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} — Domegarde</title>
<meta name="description" content="{esc(desc)}">
<link rel="preload" href="/assets/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/poppins-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
{ROBOTS}<link rel="canonical" href="{HOST}/{own}">
<link rel="alternate" hreflang="en" href="{HOST}/{en_file}">
<link rel="alternate" hreflang="fr" href="{HOST}/{fr_file}">
<link rel="alternate" hreflang="x-default" href="{HOST}/{fr_file}">
<link rel="alternate" type="application/rss+xml" title="{esc(T[lang]['rss_title'])}" href="{feed_en if lang == 'en' else feed_fr}">
<meta property="og:type" content="{kind}">
<meta property="og:site_name" content="Domegarde">
<meta property="og:title" content="{esc(title)} — Domegarde">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{HOST}/{own}">
<meta property="og:locale" content="{'en_GB' if lang == 'en' else 'fr_FR'}">
<meta property="og:locale:alternate" content="{'fr_FR' if lang == 'en' else 'en_GB'}">
<meta property="og:image" content="{HOST}/assets/social-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Domegarde">{og_extra}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F2F1EF">
<noscript><style>.reveal{{opacity:1;transform:none}}</style></noscript>
<link rel="stylesheet" href="/style.css">
{ld}</head>
<body>
<a class="skip-link" href="#main">{'Skip to main content' if lang == 'en' else 'Aller au contenu principal'}</a>

'''

def cta(lang):
    t = T[lang]
    return f'''  <section class="section-dark">
    <div class="wrap">
      <div class="cta-band reveal">
        <div>
          <div class="eyebrow">{t["cta_eyebrow"]}</div>
          <h2>{t["cta_h2"]}</h2>
        </div>
        <div style="display:flex; gap:14px; flex-wrap:wrap;">
          <a href="{t["get_started"]}" class="btn btn-gold btn-lg">{t["cta_a"]}</a>
          <a href="{t["pricing"]}" class="btn btn-ghost-light btn-lg">{t["cta_b"]}</a>
        </div>
      </div>
    </div>
  </section>
'''

def fmt_date(iso, lang):
    d = datetime.date.fromisoformat(iso); t = T[lang]
    out = t["datefmt"](d, t["months"])
    return out

def post_file(slug, lang): return f"blog-{slug}.html" if lang == "en" else f"blog-{slug}-fr.html"
def blog_file(lang): return "blog.html" if lang == "en" else "blog-fr.html"

# ------------------------------------------------------------------ pages
def render_post(slug, date, p, lang, other):
    t = T[lang]; sec_label = SECTIONS[p["section"]][lang][0]
    body = markdown(p["body"], lang)
    words = len(re.sub(r"<[^>]+>", " ", body).split()); mins = max(1, -(-words // 200))
    title = fr_typo(p["title"]) if lang == "fr" else p["title"]
    own, en_f, fr_f = post_file(slug, lang), post_file(slug, "en"), post_file(slug, "fr")
    draft = ""
    if p["status"] == "draft":
        notes = "".join(f"<li>{inline(n, lang)}</li>" for n in p.get("review", []))
        draft = f'''
      <div class="note-box draft-box">
        <p><mark class="todo">{t["draft_head"]}</mark></p>
        <p>{t["draft_text"]}</p>
        {f"<ul>{notes}</ul>" if notes else ""}
      </div>'''
    aside = ""
    if p["section"] == "news":
        assert p.get("checked"), f"{slug} ({lang}): news posts need a 'checked: YYYY-MM-DD' date"
        aside = f'''
      <aside class="note-box post-note">
        <p>{t["news_note"].format(date=fmt_date(p["checked"], lang))}</p>
      </aside>'''
    sources = ""
    if p.get("sources"):
        items = []
        for s in p["sources"]:
            name, _, url = s.rpartition("|"); name, url = name.strip(), url.strip()
            assert name and url.startswith("http"), f"{slug} ({lang}): bad source line {s!r} (use 'Title | https://...')"
            host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0])
            items.append(f'<li><a href="{esc(url)}" target="_blank" rel="noopener">{inline(name, lang)}</a> <span class="src-host">{esc(host)}</span></li>')
        sources = f'''
      <section class="post-sources" aria-labelledby="sources-h">
        <h2 id="sources-h">{t["sources"]}</h2>
        <ol>{"".join(items)}</ol>
      </section>'''
    author = p.get("author", t["team"])
    meta_line = f'<time datetime="{date}">{fmt_date(date, lang)}</time> · {t["by"]} {esc(author)} · {mins} {t["min_read"]}'
    if p.get("checked"): meta_line += f' · {t["checked"]}{NB if lang == "fr" else ""}: {fmt_date(p["checked"], lang)}'
    ld = jsonld({"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": p["excerpt"],
                 "inLanguage": lang, "datePublished": date, "dateModified": p.get("checked", date),
                 "author": {"@type": "Organization", "@id": ORG_ID, "name": "Domegarde"}, "publisher": {"@id": ORG_ID},
                 "mainEntityOfPage": f"{HOST}/{own}", "image": HOST + "/assets/social-card.png"},
                {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": t["home_crumb"], "item": HOST + "/" + ("" if lang == "en" else "index-fr.html")},
                    {"@type": "ListItem", "position": 2, "name": t["blog"], "item": f"{HOST}/{blog_file(lang)}"},
                    {"@type": "ListItem", "position": 3, "name": p["title"], "item": f"{HOST}/{own}"}]})
    page = head(lang, title, p["excerpt"], own, en_f, fr_f, kind="article", published=date, ld=ld)
    page += header(lang, own, post_file(slug, other)) + "\n\n<main id=\"main\">\n"
    page += f'''  <article class="post">
    <div class="wrap post-wrap">
      <p class="post-back"><a href="{blog_file(lang)}">{t["all_posts"]}</a></p>
      <div class="eyebrow">{esc(sec_label)}</div>
      <h1>{esc(title)}</h1>
      <p class="post-meta">{meta_line}</p>{draft}
      <div class="post-body">
{body}
      </div>{aside}{sources}
    </div>
  </article>

{cta(lang)}</main>

'''
    page += footer(lang) + '\n\n<script src="/main.js"></script>\n</body>\n</html>\n'
    return page

def render_index(posts, lang, other):
    t = T[lang]; own = blog_file(lang)
    page = head(lang, t["blog_title"], t["desc"], own, blog_file("en"), blog_file("fr"))
    page += header(lang, own, blog_file(other)) + "\n\n<main id=\"main\">\n"
    page += f'''  <section class="hero" style="padding-bottom: 24px;">
    <div class="wrap" style="max-width: 860px;">
      <div class="eyebrow">{t["blog"]}</div>
      <h1 style="font-size: clamp(2.2rem, 4.2vw, 3.3rem);">{esc(t["h1"])}</h1>
      <p class="hero-sub" style="max-width: 60ch; font-size: 1.15rem;">{esc(t["sub"])}</p>
      <p class="rss-link"><a href="{'feed.xml' if lang == 'en' else 'feed-fr.xml'}">{t["rss"]}</a></p>
    </div>
  </section>
'''
    for key in SECTIONS:
        label, blurb = SECTIONS[key][lang]
        cards = []
        for slug, date, posts_by_lang in posts:
            p = posts_by_lang[lang]
            if p["section"] != key: continue
            draft = f' <mark class="todo">{t["draft"]}</mark>' if p["status"] == "draft" else ""
            title = fr_typo(p["title"]) if lang == "fr" else p["title"]
            cards.append(f'''        <article class="post-card reveal">
          <p class="post-card-meta"><time datetime="{date}">{fmt_date(date, lang)}</time>{draft}</p>
          <h3><a href="{post_file(slug, lang)}">{esc(title)}</a></h3>
          <p>{inline(p["excerpt"], lang)}</p>
          <p class="post-more"><a href="{post_file(slug, lang)}">{t["read"]} <span aria-hidden="true">→</span><span class="sr-only">: {esc(title)}</span></a></p>
        </article>''')
        listing = "\n".join(cards) if cards else '        <p class="section-blurb">' + t["empty"] + '</p>'
        page += f'''  <section id="{key}" style="padding-top: 0;">
    <div class="wrap" style="max-width: 860px;">
      <div class="status-group reveal" style="margin-top: 40px;">
        <h2>{esc(label)}</h2>
        <p class="section-blurb">{esc(blurb)}</p>
      </div>
      <div class="post-list">
{listing}
      </div>
    </div>
  </section>
'''
    page += "\n" + cta(lang) + "</main>\n\n" + footer(lang) + '\n\n<script src="/main.js"></script>\n</body>\n</html>\n'
    return page

def changelog_html(body, lang):
    """Entries are '## 2026-10-14 | Title | Tag' followed by a short text or bullet list, newest first."""
    out = []
    for e in [x for x in re.split(r"(?m)^## ", body.strip()) if x.strip()]:
        head_line, _, rest = e.partition("\n")
        m = re.match(r"(\d{4}-\d{2}-\d{2}) \| (.+?) \| (.+)$", head_line.strip())
        assert m, f"changelog entry heading must look like '## 2026-10-14 | Title | Tag', got: {head_line!r}"
        date, title, tag = m.groups(); datetime.date.fromisoformat(date)
        out.append(f'''<article class="log-entry" id="d-{date}-{slugify(title)}">
<p class="log-meta"><time datetime="{date}">{fmt_date(date, lang)}</time> <span class="log-tag">{esc(tag)}</span></p>
<h2>{inline(title, lang)}</h2>
{markdown(rest, lang)}
</article>''')
    return "\n".join(out)

def render_page(key, p, lang, other):
    t = T[lang]; files = PAGES[key]["files"]; own = files[lang]
    title = fr_typo(p["title"]) if lang == "fr" else p["title"]
    body = changelog_html(p["body"], lang) if key == "changelog" else markdown(p["body"], lang)
    ld_objs = []
    if key == "facts":
        ld_objs += [org_object(lang), {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Domegarde", "url": HOST + "/",
                    "applicationCategory": "BusinessApplication", "operatingSystem": "Web", "inLanguage": ["fr", "en"],
                    "description": p["excerpt"], "provider": {"@id": ORG_ID}, "featureList": p.get("features", [])}]
    ld_objs.append({"@context": "https://schema.org", "@type": "WebPage", "name": p["title"], "description": p["excerpt"], "inLanguage": lang,
                    "url": f"{HOST}/{own}", "dateModified": p["updated"], "isPartOf": {"@id": ORG_ID}})
    page = head(lang, title, p["excerpt"], own, files["en"], files["fr"], ld=jsonld(*ld_objs))
    page += header(lang, own, files[other], active_blog=False) + "\n\n<main id=\"main\">\n"
    page += f'''  <section class="hero" style="padding-bottom: 24px;">
    <div class="wrap" style="max-width: 760px;">
      <div class="eyebrow">{esc(PAGES[key]["eyebrow"][lang])}</div>
      <h1 style="font-size: clamp(2.2rem, 4.2vw, 3.3rem);">{esc(title)}</h1>
      <p class="hero-sub" style="max-width: 62ch; font-size: 1.15rem;">{inline(p["excerpt"], lang)}</p>
      <p class="post-meta" style="margin: 18px 0 0;">{t["updated"]}{NB if lang == "fr" else ""}: <time datetime="{p["updated"]}">{fmt_date(p["updated"], lang)}</time></p>
    </div>
  </section>
  <section style="padding-top: 0;">
    <div class="wrap post-wrap">
      <div class="post-body">
{body}
      </div>
    </div>
  </section>

{cta(lang)}</main>

'''
    page += footer(lang) + '\n\n<script src="/main.js"></script>\n</body>\n</html>\n'
    return page

def rfc822(iso):
    d = datetime.datetime.fromisoformat(iso + "T09:00:00+00:00")
    return d.strftime("%a, %d %b %Y %H:%M:%S +0000")

def render_feed(posts, lang):
    t = T[lang]
    items = []
    for slug, date, by_lang in posts:
        p = by_lang[lang]
        if p["status"] != "published": continue
        link = f"{HOST}/{post_file(slug, lang)}"
        items.append(f"""    <item>
      <title>{esc(p['title'])}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <pubDate>{rfc822(date)}</pubDate>
      <description>{esc(p['excerpt'])}</description>
    </item>""")
    own = "feed.xml" if lang == "en" else "feed-fr.xml"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{esc(t['rss_title'])}</title>
    <link>{HOST}/{blog_file(lang)}</link>
    <atom:link href="{HOST}/{own}" rel="self" type="application/rss+xml"/>
    <description>{esc(t['desc'])}</description>
    <language>{lang}</language>
{chr(10).join(items)}
  </channel>
</rss>
"""

def render_sitemap(posts):
    pairs = [("index.html","index-fr.html"),("about.html","about-fr.html"),("pricing.html","pricing-fr.html"),
             ("get-started.html","get-started-fr.html"),("terms.html","terms-fr.html"),("privacy.html","privacy-fr.html"),
             ("legal-notice.html","mentions-legales.html"),("whats-coming.html","ce-qui-arrive.html"),
             ("expat-landlords.html","proprietaires-non-residents.html"),("blog.html","blog-fr.html"),
             ("facts.html","en-bref.html"),("whats-new.html","nouveautes.html")]
    for slug, date, by_lang in posts:
        if by_lang["en"]["status"] == "published" and by_lang["fr"]["status"] == "published":
            pairs.append((post_file(slug, "en"), post_file(slug, "fr")))
    def u(f): return HOST + "/" if f == "index.html" else f"{HOST}/{f}"
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for en, fr in pairs:
        for f in (en, fr):
            out += ["  <url>", f"    <loc>{u(f)}</loc>",
                    f'    <xhtml:link rel="alternate" hreflang="en" href="{u(en)}"/>',
                    f'    <xhtml:link rel="alternate" hreflang="fr" href="{u(fr)}"/>',
                    f'    <xhtml:link rel="alternate" hreflang="x-default" href="{u(fr)}"/>', "  </url>"]
    out.append("</urlset>")
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sitemap-out"); args = ap.parse_args()
    found = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "blog-src", "*.md"))):
        name = os.path.basename(path)
        if name.lower() == "readme.md" or name.startswith("page-"): continue
        m = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)\.(en|fr)\.md$", name)
        assert m, f"blog-src/{name}: name must look like 2026-10-16-my-slug.en.md (or .fr.md)"
        date, slug, lang = m.groups()
        datetime.date.fromisoformat(date)
        found.setdefault((date, slug), {})[lang] = parse_post(path)
    posts = []
    for (date, slug), by_lang in sorted(found.items(), reverse=True):
        assert set(by_lang) == {"en", "fr"}, f"{date}-{slug}: needs both an .en.md and a .fr.md file (missing: {({'en','fr'} - set(by_lang))})"
        assert by_lang["en"]["section"] == by_lang["fr"]["section"], f"{slug}: section differs between languages"
        assert by_lang["en"]["status"] == by_lang["fr"]["status"], f"{slug}: status differs between languages"
        posts.append((slug, date, by_lang))
    wrote = []
    def w(name, s): open(os.path.join(ROOT, name), "w", encoding="utf-8").write(s); wrote.append(name)
    for lang, other in (("en", "fr"), ("fr", "en")):
        w(blog_file(lang), render_index(posts, lang, other))
        w("feed.xml" if lang == "en" else "feed-fr.xml", render_feed(posts, lang))
        for slug, date, by_lang in posts:
            w(post_file(slug, lang), render_post(slug, date, by_lang[lang], lang, other))
    for key in PAGES:
        srcs = {}
        for lang in ("en", "fr"):
            path = os.path.join(ROOT, "blog-src", f"page-{key}.{lang}.md")
            assert os.path.exists(path), f"blog-src/page-{key}.{lang}.md is missing (every page needs both languages)"
            srcs[lang] = parse_page(path)
        for lang, other in (("en", "fr"), ("fr", "en")):
            w(PAGES[key]["files"][lang], render_page(key, srcs[lang], lang, other))
    if args.sitemap_out:
        open(args.sitemap_out, "w", encoding="utf-8").write(render_sitemap(posts))
    pub = [f"{HOST}/{post_file(s, l)}" for s, d, b in posts if b['en']['status'] == 'published' for l in ('en', 'fr')]
    print(f"blog: {len(posts)} post(s) and {len(PAGES)} pages in two languages; {len(wrote)} files written; {len(pub)//2} published")
    for n in wrote: print("  ", n)

if __name__ == "__main__":
    main()
