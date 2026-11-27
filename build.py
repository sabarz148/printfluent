#!/usr/bin/env python3
"""PrintFluent static site generator.  python3 build.py  ->  dist/
Reads config/site.json + data/products.json, writes plain HTML (no framework, no runtime deps)."""
import html, json, shutil, pathlib, datetime, re
from content import CAT_SEO, GUIDES

ROOT = pathlib.Path(__file__).resolve().parent
SRC, DIST = ROOT / "src", ROOT / "dist"
CFG = json.loads((ROOT / "config/site.json").read_text())
DATA = json.loads((ROOT / "data/products.json").read_text())
BUNDLES = json.loads((ROOT / "data/bundles.json").read_text())["bundles"] if (ROOT / "data/bundles.json").exists() else []
PRODUCTS = sorted([p for p in DATA["products"] if not p.get("hidden")] + BUNDLES, key=lambda p: p["order"])
def _links():
    import csv
    f = ROOT / "data/checkout_links.csv"
    out = {}
    if f.exists():
        for r in csv.DictReader(f.open()):
            u = (r.get("checkout_url") or "").strip()
            if u: out[r["etsy_id"]] = u
    return out
LINKS = _links()
for _p in PRODUCTS: _p["checkout"] = LINKS.get(_p["id"], "")
HAS_LS = bool(LINKS)
CATS = {c["slug"]: c for c in CFG["categories"]}
BASE = CFG["url"].rstrip("/")
e = html.escape
DEFAULT_OG = BASE + "/assets/img/og.jpg"

ICON = {
 "tumbler-wraps": '<path d="M8 3h8l-1 18H9z M7 7h10" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>',
 "planners-trackers": '<rect x="4" y="5" width="16" height="15" rx="2" fill="none" stroke="#fff" stroke-width="1.6"/><path d="M4 10h16M9 3v4M15 3v4M8 14h3M13 14h3" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round"/>',
 "t-shirt-designs": '<path d="M8 3l-5 3 2 4 3-1v11h8V9l3 1 2-4-5-3c-1 2-3 2-4 2s-3 0-4-2z" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>',
 "teacher-resources": '<path d="M4 5h7a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H4zM20 5h-7v15a2 2 0 0 1 2-2h5z" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>',
 "bundles": '<path d="M12 3l9 4.5-9 4.5-9-4.5zM3 12l9 4.5 9-4.5M3 16.500l9 4.500 9-4.500" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>',
 "sympathy-cards": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.600-7 10-7 10z" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>',
 "kids-activities": '<circle cx="12" cy="12" r="8" fill="none" stroke="#fff" stroke-width="1.6"/><path d="M8.500 14c1 1.500 2 2 3.500 2s2.500-.5 3.500-2M9 10h.01M15 10h.01" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/>',
 "birthday-cards": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.600-7 10-7 10z" fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>',
}
CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M8 12.500l3 3 5-6"/></svg>'


def money(x): return f"${x:,.2f}"


def img_for(p, full=False, eager=False):
    """Real image if present in src/assets/products/<id>.jpg, otherwise a branded colour card."""
    c = CATS[p["category"]]["color"]
    t = {"blush": "t-blush", "sage": "t-sage", "coral": "t-coral", "teal": "t-teal", "purple": "t-purple", "mustard": "t-mustard"}[c]
    f = SRC / "assets/products" / f"{p['id']}.jpg"
    if f.exists():
        src = f"/assets/products/{p['id']}.jpg" if full else f"/assets/products/t/{p['id']}.jpg"
        w = 900 if full else 480
        load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
        return f'<img class="thumb" src="{src}" alt="{e(p["title"])} - digital download by PrintFluent" {load} width="{w}" height="{w}">'
    return f'<div class="card-art {t}" role="img" aria-label="{e(CATS[p["category"]]["name"])}"><svg viewBox="0 0 24 24" aria-hidden="true">{ICON[p["category"]]}</svg></div>'


def card(p):
    cat = CATS[p["category"]]
    badge = '<span class="badge">Featured</span>' if p.get("featured") else ""
    return (f'<article class="card" data-cat="{p["category"]}" data-price="{p["price"]}" data-order="{p["order"]}" '
            f'data-title="{e(p["title"].lower())}">'
            f'<a class="media" href="/product/{p["slug"]}/" aria-label="{e(p["title"])}">{badge}{img_for(p)}</a>'
            f'<div class="card-body"><span class="cat">{e(cat["name"])}</span>'
            f'<h3><a href="/product/{p["slug"]}/">{e(p["title"])}</a></h3>'
            f'<div class="card-foot"><span class="price">{money(p["price"])}</span>' +
            (f'<a class="btn sm" href="/product/{p["slug"]}/">{"View pack" if p.get("bundle") else "Buy now"}</a>' if (p["checkout"] or p.get("bundle")) else f'<a class="btn etsy sm" href="{p["etsy_url"]}" target="_blank" rel="noopener">Get on Etsy</a>') + '</div></div></article>')


def inc_list(p):
    if not p.get("includes"): return ""
    return '<h3>What\'s in the pack</h3><ul class="inc">' + "".join(f"<li>{e(t)}</li>" for t in p["includes"]) + "</ul>"


def buy_buttons(p):
    if p.get("bundle"):
        if p["checkout"]: return f'<a class="btn" href="{p["checkout"]}" target="_blank" rel="noopener">Buy now · {money(p["price"])}</a>'
        return '<span class="btn ghost" aria-disabled="true">Coming soon</span>'
    etsy = f'<a class="btn ghost" href="{p["etsy_url"]}" target="_blank" rel="noopener">Buy on Etsy</a>'
    if not p["checkout"]: return f'<a class="btn etsy" href="{p["etsy_url"]}" target="_blank" rel="noopener">Buy on Etsy</a>'
    return f'<div class="hero-actions"><a class="btn" href="{p["checkout"]}" target="_blank" rel="noopener">Buy now · {money(p["price"])}</a>{etsy}</div>'


def facts(p):
    t = p["title"].lower()
    if p.get("bundle"):
        return [f"{p['count']} designs in one pack (worth {money(p['worth'])} bought one by one)." if p["worth"] else f"{p['count']} planner versions in one pack.",
                "Instant digital download. Nothing is shipped.", "Sold direct by PrintFluent. Not available on Etsy as a pack.", "Original artwork only."]
    out = ["Instant digital download from Etsy. Nothing is shipped."]
    c = p["category"]
    if c == "tumbler-wraps":
        out += ["1 high-resolution PNG, 300 DPI.", "Sized 9.3 × 8.1 in for 20oz skinny straight tumbler blanks.", "For personal and small-batch sublimation. See the Etsy listing for licence terms."]
    elif c == "t-shirt-designs":
        out += ["High-resolution PNG design file for shirt sublimation and similar transfers.", "100% original artwork by PrintFluent."]
    elif c == "planners-trackers":
        if "spreadsheet" in t:
            out += ["Works in Excel and Google Sheets.", "Budget, guest list, timeline and more in one workbook."]
        else:
            out += ["Printable PDF. Print at home or at a print shop.", "Open the Etsy listing for page counts and sizes."]
    elif c == "teacher-resources":
        out += ["Printable PDF for the classroom or the family fridge."]
    elif c == "kids-activities":
        out += ["Printable PDF workbook. Print at home on US Letter or A4."]
    else:
        out += ["Printable card file. Print at home or at a print shop."]
    return out


def head(title, desc, path, extra="", og_img="", og_type="website"):
    ga = ""
    if CFG["ga4_measurement_id"]:
        g = CFG["ga4_measurement_id"]
        ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={g}"></script>'
              f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{g}');</script>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE}{path}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
{f'<meta name="google-site-verification" content="{CFG["google_site_verification"]}">' if CFG.get("google_site_verification") else ''}{f'<meta name="msvalidate.01" content="{CFG["bing_site_verification"]}">' if CFG.get("bing_site_verification") else ''}
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{CFG['name']}"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{BASE}{path}"><meta property="og:image" content="{og_img or DEFAULT_OG}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{og_img or DEFAULT_OG}">
<meta name="theme-color" content="#2b2b2f">
<link rel="icon" href="/assets/img/logo.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/style.css">{extra}{ga}</head>"""


NAV = [("/", "Home"), ("/shop/", "Shop"), ("/guides/", "Guides"), ("/about/", "About"), ("/contact/", "Contact")]


def header(path):
    links = "".join(f'<li><a href="{h}"{" aria-current=page" if (h == path or (h != "/" and path.startswith(h))) else ""}>{n}</a></li>' for h, n in NAV)
    return f"""<body><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap nav">
<a class="brand" href="/"><img src="/assets/img/logo.svg" alt="" width="42" height="42"><span>{CFG['name']}</span></a>
<button class="menu-btn" aria-expanded="false" aria-label="Menu">Menu</button>
<ul>{links}</ul>
<a class="btn etsy sm nav-cta" href="{CFG['etsy_shop_url']}" target="_blank" rel="noopener">Etsy shop</a>
</div></header><main id="main">"""


def footer():
    soc = "".join(f'<li><a href="{u}" target="_blank" rel="noopener">{n}</a></li>' for n, u in CFG["socials"].items())
    cats = "".join(f'<li><a href="/categories/{c["slug"]}/">{e(c["name"])}</a></li>' for c in CFG["categories"])
    year = datetime.date.today().year
    ls = ""
    return f"""</main><footer class="site-footer"><div class="wrap"><div class="foot">
<div><h4>{CFG['name']}</h4><p>{e(CFG['tagline'])}</p><p>Secure checkout. Orders on Etsy are handled by Etsy.</p></div>
<div><h4>Shop</h4><ul>{cats}</ul></div>
<div><h4>Company</h4><ul><li><a href="/guides/">Guides</a></li><li><a href="/about/">About</a></li><li><a href="/contact/">Contact</a></li><li><a href="{CFG['etsy_shop_url']}" target="_blank" rel="noopener">Etsy shop</a></li></ul></div>
<div><h4>Follow</h4><ul>{soc}</ul></div></div>
<div class="legal"><span>© {year} {CFG['name']}. All rights reserved.</span><span>Digital downloads only. No physical item ships.</span></div></div></footer>
{ls}<script src="/assets/js/app.js" defer></script></body></html>"""


def page(path, title, desc, body, extra="", og_img="", og_type="website"):
    out = DIST / path.strip("/") / "index.html" if path != "/" else DIST / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, path, extra, og_img, og_type) + header(path) + body + footer(), encoding="utf-8")


def cat_tiles():
    n = {s: sum(1 for p in PRODUCTS if p["category"] == s) for s in CATS}
    return "".join(f'<a class="cat-tile tint-{c["color"]}" href="/categories/{c["slug"]}/"><span class="count">{n[c["slug"]]}</span>'
                   f'<h3>{e(c["name"])}</h3><p>{e(c["blurb"])}</p></a>' for c in CFG["categories"])


def about_text(p):
    c = p["category"]
    t = e(p["title"])
    if p.get("bundle"):
        n = p["count"]
        return (f"<p>{t} gives you {n} original designs in one ZIP download, sold direct by PrintFluent. A short README lists every file.</p>"
                f"<p>Browse more in <a href=\"/categories/bundles/\">Bundles &amp; Packs</a>.</p>")
    if c == "tumbler-wraps":
        return (f"<p>{t} is a high-resolution PNG (300 DPI, 9.3 × 8.1 in) made for 20oz skinny straight sublimation tumblers. Print it mirrored on sublimation paper, wrap it around a coated blank and press it with heat.</p>"
                "<p>New to sublimation? Read the <a href=\"/guides/how-to-use-sublimation-tumbler-wraps/\">beginner guide to tumbler wraps</a>, or see more <a href=\"/categories/tumbler-wraps/\">tumbler wrap designs</a>.</p>")
    if c == "t-shirt-designs":
        return (f"<p>{t} is an original PNG shirt design for sublimation, DTF and other transfer methods. Sublimation suits light polyester, and DTF also works on cotton and dark garments.</p>"
                "<p>Not sure which method to use? Read <a href=\"/guides/sublimation-vs-dtf-shirt-designs/\">sublimation vs DTF</a>, or browse more <a href=\"/categories/t-shirt-designs/\">t-shirt designs</a>.</p>")
    if c == "planners-trackers":
        return (f"<p>{t} is a printable planner delivered as an instant digital download. Print it at home or at a print shop, or fill it in on screen where the file is fillable.</p>"
                "<p>Planning a party? Use the <a href=\"/guides/birthday-party-planning-checklist/\">birthday party planning checklist</a> alongside it, or see more <a href=\"/categories/planners-trackers/\">planners</a>.</p>")
    if c == "birthday-cards":
        return (f"<p>{t} is a printable card delivered as an instant digital download. Print it at home or at a print shop, fold and sign.</p>"
                "<p>See more <a href=\"/categories/birthday-cards/\">printable birthday cards</a>.</p>")
    if c == "sympathy-cards":
        return (f"<p>{t} is a printable sympathy card delivered as an instant digital download. Print it at home or at a print shop, fold and write your message inside.</p>"
                "<p>See more <a href=\"/categories/sympathy-cards/\">printable sympathy cards</a>.</p>")
    if c == "kids-activities":
        return (f"<p>{t} is a printable kids activity delivered as an instant digital download. Print the pages at home and use them with children.</p>"
                "<p>See more <a href=\"/categories/kids-activities/\">kids activities</a>.</p>")
    return (f"<p>{t} is a printable teacher resource delivered as an instant digital download.</p>"
            "<p>See more <a href=\"/categories/teacher-resources/\">teacher resources</a>.</p>")


def gallery_html(p):
    n = int(p.get("gallery") or 0)
    if n < 2 and not p.get("video"):
        return img_for(p, full=True, eager=True)
    pid = p["id"]; alt = e(p["title"])
    main = f'<img id="gmain" class="thumb" src="/assets/products/{pid}/1.jpg" alt="{alt} - digital download by PrintFluent" fetchpriority="high" width="900" height="900">'
    thumbs = "".join(
        f'<button type="button" class="gt" data-src="/assets/products/{pid}/{k}.jpg" aria-label="Photo {k}"><img src="/assets/products/{pid}/t{k}.jpg" alt="{alt} photo {k}" loading="lazy" width="96" height="96"></button>'
        for k in range(1, n + 1))
    vid = ""
    if p.get("video"):
        poster = f'/assets/products/{pid}/poster.jpg'
        vid = (f'<button type="button" class="gt gv" data-video="/assets/products/{pid}/video.mp4" data-poster="{poster}" aria-label="Play video">'
               f'<span>&#9654; Video</span></button>')
    return (f'<div class="gallery"><div class="gstage">{main}</div><div class="gthumbs">{vid}{thumbs}</div></div>')


def desc_html(p):
    d = (p.get("description") or "").strip()
    if not d: return ""
    out, bullets = [], []
    def flush():
        if bullets: out.append("<ul>" + "".join(f"<li>{e(b)}</li>" for b in bullets) + "</ul>"); bullets.clear()
    for line in d.replace("\r", "").split("\n"):
        t = line.strip()
        if not t: flush(); continue
        if t[:1] in "•-*" and len(t) > 2: bullets.append(t.lstrip("•-* ").strip()); continue
        flush()
        out.append(f"<h3>{e(t.capitalize())}</h3>" if (t.isupper() and len(t) < 40) else f"<p>{e(t)}</p>")
    flush()
    return '<section class="block"><div class="prose"><h2>Full details</h2>' + "".join(out) + '</div></section>'


def build():
    if DIST.exists(): shutil.rmtree(DIST)
    shutil.copytree(SRC / "assets", DIST / "assets")
    try:
        from PIL import Image
        (DIST / "assets/products/t").mkdir(parents=True, exist_ok=True)
        for f in (SRC / "assets/products").glob("*.jpg"):
            im = Image.open(f).convert("RGB")
            im.thumbnail((480, 480), Image.LANCZOS)
            im.save(DIST / "assets/products/t" / f.name, "JPEG", quality=80, optimize=True, progressive=True)
        for f in (SRC / "assets/products").glob("*/[0-9]*.jpg"):
            im = Image.open(f).convert("RGB"); im.thumbnail((192, 192), Image.LANCZOS)
            im.save(DIST / f.parent.relative_to(SRC) / f"t{f.name}", "JPEG", quality=78, optimize=True)
    except ImportError:
        shutil.copytree(SRC / "assets/products", DIST / "assets/products/t", dirs_exist_ok=True)
    (DIST / "data").mkdir()
    shutil.copy(ROOT / "data/products.json", DIST / "data/products.json")

    _b = [p for p in PRODUCTS if p.get("bundle")]
    _s = [p for p in PRODUCTS if not p.get("bundle")]
    featured = _b[:3] + [p for p in _s if p.get("featured")][:3]
    if len(featured) < 6: featured += [p for p in _s if p not in featured][:6 - len(featured)]
    newest = _s[:8]

    # ---------- home ----------
    pill = "".join(f'<div class="pillar">{CHECK.format(c=col)}<div><b>{t}</b><p>{d}</p></div></div>' for t, d, col in [
        ("Create", "Original designs for tumblers, shirts and cards.", "#f28b7a"),
        ("Solve", "Planners and printables that save you time.", "#3fa39b"),
        ("Grow", "New designs added every week.", "#8e7cc3")])
    _hid = ["4548434826","4538380413","4542196060","4566100712"]
    hero_art = "".join(img_for(p, full=False, eager=(k==0)) for k, i in enumerate(_hid) for p in PRODUCTS if p["id"]==i)
    home = f"""<section class="hero"><span class="blob b1"></span><span class="blob b2"></span><div class="wrap">
<div><span class="eyebrow">Instant digital downloads</span>
<h1>Smart digital solutions for work, learning &amp; life.</h1>
<p class="lead">Planners, tumbler wraps, t-shirt designs, birthday cards and classroom printables. Pick a design, check out securely, download in seconds.</p>
<div class="hero-actions"><a class="btn" href="/shop/">Browse all designs</a><a class="btn ghost" href="{CFG['etsy_shop_url']}" target="_blank" rel="noopener">Visit the Etsy shop</a></div></div>
<div class="hero-art" aria-hidden="true">{hero_art}</div></div></section>
<div class="wrap"><div class="pillars">{pill}</div></div>
<section class="block"><div class="wrap prose seo-copy"><h2>Original printable designs, ready to download</h2>
<p>PrintFluent makes original digital designs: <a href="/categories/tumbler-wraps/">20oz skinny tumbler wrap PNG files</a> for sublimation, <a href="/categories/t-shirt-designs/">t-shirt design PNGs</a> for sublimation and DTF, <a href="/categories/planners-trackers/">printable birthday planners</a>, <a href="/categories/birthday-cards/">birthday cards</a> and <a href="/categories/teacher-resources/">teacher resources</a>. Every file is an instant download, so there is nothing to wait for and nothing shipped.</p>
<p>Saving on a bigger project? Our <a href="/categories/bundles/">design bundles</a> put several designs in one download. New to sublimation? Start with the <a href="/guides/how-to-use-sublimation-tumbler-wraps/">beginner guide to tumbler wraps</a>.</p></div></section>
<section class="block"><div class="wrap"><div class="section-head"><div><h2>Shop by category</h2><p>{len(CFG["categories"])} collections, all original, all instant download.</p></div></div>
<div class="cat-grid">{cat_tiles()}</div></div></section>
<section class="block"><div class="wrap"><div class="section-head"><div><h2>Featured designs</h2><p>A few favourites from the shop.</p></div><a class="btn ghost sm" href="/shop/">See everything</a></div>
<div class="grid">{''.join(card(p) for p in featured)}</div></div></section>
<section class="block"><div class="wrap"><div class="section-head"><div><h2>New in the shop</h2><p>The latest listings, straight from Etsy.</p></div><a class="btn ghost sm" href="/shop/">View all</a></div>
<div class="grid">{''.join(card(p) for p in newest)}</div></div></section>
<section class="block"><div class="wrap"><div class="cta-band"><div><h2>Ready to print, press or plan?</h2><p>Secure checkout, instant download the moment you pay.</p></div>
<a class="btn" href="{CFG['etsy_shop_url']}" target="_blank" rel="noopener">Open the Etsy shop</a></div></div></section>"""
    org = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": f"{BASE}/#org", "name": CFG["name"], "url": BASE,
         "logo": f"{BASE}/assets/img/logo.svg", "sameAs": list(CFG["socials"].values()) + [CFG["etsy_shop_url"]]},
        {"@type": "WebSite", "@id": f"{BASE}/#site", "url": BASE, "name": CFG["name"], "publisher": {"@id": f"{BASE}/#org"}, "inLanguage": "en"}]}
    page("/", "PrintFluent | Tumbler Wraps, Shirt Designs & Planners", "Original 20oz tumbler wrap PNG designs, t-shirt design files, printable planners and birthday cards. Instant digital downloads from PrintFluent.", home,
         f'<script type="application/ld+json">{json.dumps(org)}</script>')

    # ---------- shop ----------
    chips = '<button class="chip" data-cat="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" data-cat="{c["slug"]}" aria-pressed="false">{e(c["name"])}</button>' for c in CFG["categories"])
    shop = f"""<div class="wrap"><section class="block"><h1>Shop all designs</h1>
<div class="chips" role="group" aria-label="Filter by category">{chips}</div>
<div class="toolbar"><input id="q" type="search" placeholder="Search designs…" aria-label="Search designs">
<select id="sort" aria-label="Sort"><option value="new">Newest first</option><option value="low">Price: low to high</option><option value="high">Price: high to low</option></select></div>
<p class="result-count" id="result-count" aria-live="polite"></p>
<div class="grid" id="product-grid">{''.join(card(p) for p in PRODUCTS)}</div>
<p class="empty" id="empty" hidden>No designs match that search. Try a different word.</p></section></div>"""
    page("/shop/", f"Shop Digital Designs & Printables | {CFG['name']}", "Shop original tumbler wrap PNGs, t-shirt designs, printable planners, birthday cards and design bundles. Instant digital downloads from PrintFluent.", shop)

    # ---------- category pages ----------
    for c in CFG["categories"]:
        items = [p for p in PRODUCTS if p["category"] == c["slug"]]
        sc = CAT_SEO[c["slug"]]
        intro = "".join(f"<p>{e(t)}</p>" for t in sc["intro"])
        faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in sc["faq"])
        guide = f'<p>New to this? Read our <a href="{sc["guide"]}">step-by-step guide</a>.</p>' if sc["guide"] else ""
        others = "".join(f'<li><a href="/categories/{o["slug"]}/">{e(o["name"])}</a></li>' for o in CFG["categories"] if o["slug"] != c["slug"])
        body = f"""<div class="wrap"><div class="crumbs"><a href="/">Home</a> / <a href="/shop/">Shop</a> / {e(c['name'])}</div>
<section class="block"><h1>{e(sc['h1'])}</h1><div class="prose cat-intro">{intro}</div>
<div class="grid">{''.join(card(p) for p in items)}</div></section>
<section class="block"><div class="prose"><h2>Questions about {e(c['name'].lower())}</h2><div class="faq">{faq}</div>{guide}
<p>Also browse: </p><ul class="inline-links">{others}</ul></div></section></div>"""
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "CollectionPage", "name": sc["h1"], "url": f"{BASE}/categories/{c['slug']}/", "description": sc["desc"],
             "isPartOf": {"@id": f"{BASE}/#site"}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Shop", "item": BASE + "/shop/"},
                {"@type": "ListItem", "position": 3, "name": c["name"], "item": f"{BASE}/categories/{c['slug']}/"}]},
            {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/product/{p['slug']}/"} for i, p in enumerate(items)]},
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in sc["faq"]]}]}
        page(f"/categories/{c['slug']}/", sc["title"], sc["desc"], body, f'<script type="application/ld+json">{json.dumps(ld)}</script>')

    # ---------- product pages ----------
    for p in PRODUCTS:
        cat = CATS[p["category"]]
        rel = [q for q in PRODUCTS if q["category"] == p["category"] and q["id"] != p["id"]][:4]
        fl = "".join(f'<li>{CHECK.format(c="#3fa39b")}<span>{e(f)}</span></li>' for f in facts(p))
        body = f"""<div class="wrap"><div class="crumbs"><a href="/">Home</a> / <a href="/categories/{cat['slug']}/">{e(cat['name'])}</a></div>
<div class="product"><div>{gallery_html(p)}</div><div><span class="eyebrow">{e(cat['name'])}</span><h1>{e(p['title'])}</h1>
<span class="price">{money(p['price'])}</span>
{buy_buttons(p)}
<ul class="facts">{fl}</ul>
<p class="note">{("Secure checkout. Your download link arrives right after payment." if p["checkout"] else "This pack opens for sale soon.") if p.get("bundle") else ("Secure checkout. Your files are available right after payment. Reviews and the full description are on the Etsy listing." if p["checkout"] else "Checkout, payment and your download are handled by Etsy.")}</p>
{inc_list(p)}</div></div>
<section class="block"><div class="prose"><h2>About this design</h2>{about_text(p)}</div></section>
{desc_html(p)}
<section class="block"><h2>More {e(cat['name'].lower())}</h2><div class="grid">{''.join(card(q) for q in rel)}</div></section></div>"""
        og = f"{BASE}/assets/products/{p['id']}.jpg" if (SRC / "assets/products" / f"{p['id']}.jpg").exists() else ""
        purl = f"{BASE}/product/{p['slug']}/"
        prod = {"@type": "Product", "@id": purl + "#product", "name": p["title"], "sku": p["id"], "category": cat["name"],
                "description": re.sub(r"<[^>]+>", "", about_text(p)).strip()[:500],
                "brand": {"@type": "Brand", "name": CFG["name"]},
                "offers": {"@type": "Offer", "price": f"{p['price']:.2f}", "priceCurrency": "USD", "itemCondition": "https://schema.org/NewCondition",
                           "availability": "https://schema.org/InStock", "url": purl, "seller": {"@type": "Organization", "name": CFG["name"]}}}
        if og: prod["image"] = og
        if int(p.get("gallery") or 0) > 1: prod["image"] = [f"{BASE}/assets/products/{p['id']}/{k}.jpg" for k in range(1, int(p["gallery"]) + 1)]
        if p.get("bundle") and not p["checkout"]: prod.pop("offers")
        ld = {"@context": "https://schema.org", "@graph": [prod, {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": cat["name"], "item": f"{BASE}/categories/{cat['slug']}/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": purl}]}]}
        short = p["title"] if len(p["title"]) <= 46 else p["title"][:45].rsplit(" ", 1)[0].rstrip(",|-– ") + "…"
        dshort = p["title"] if len(p["title"]) <= 95 else p["title"][:94].rsplit(" ", 1)[0].rstrip(",|-– ") + "…"
        page(f"/product/{p['slug']}/", f"{short} | {CFG['name']}", f"{dshort} Instant download, {money(p['price'])}. By PrintFluent.", body,
             f'<script type="application/ld+json">{json.dumps(ld)}</script>', og, "product")

    # ---------- guides ----------
    gcards = "".join(f'<a class="cat-tile tint-sage" href="/guides/{g["slug"]}/"><h3>{e(g["title"])}</h3><p>{e(g["desc"])}</p></a>' for g in GUIDES)
    page("/guides/", "Guides: Sublimation, DTF & Party Planning | PrintFluent", "Beginner guides from PrintFluent: how to use tumbler wrap PNGs, sublimation vs DTF for shirt designs, and a birthday party planning checklist.",
         f'<div class="wrap"><section class="block"><h1>Guides</h1><p class="lead note">Short, practical guides for using your downloads.</p><div class="cat-grid">{gcards}</div></section></div>')
    today_iso = datetime.date.today().isoformat()
    for g in GUIDES:
        secs = "".join(f"<h2>{e(h)}</h2>" + ("<ul>" + "".join(f"<li>{e(x.lstrip('• '))}</li>" for x in ps) + "</ul>" if (len(ps) > 1 and h.startswith(("What you", "Tips"))) or all(x.startswith("• ") for x in ps) else "".join(f"<p>{e(x)}</p>" for x in ps)) for h, ps in g["sections"])
        others = "".join(f'<li><a href="/guides/{o["slug"]}/">{e(o["title"])}</a></li>' for o in GUIDES if o["slug"] != g["slug"])
        body = f"""<div class="wrap"><div class="crumbs"><a href="/">Home</a> / <a href="/guides/">Guides</a> / {e(g['h1'])}</div>
<article class="block prose guide"><h1>{e(g['h1'])}</h1><p class="lead">{e(g['lead'])}</p>{secs}
<p><a class="btn" href="{g['cta'][1]}">{e(g['cta'][0])}</a></p><h2>More guides</h2><ul>{others}</ul></article></div>"""
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": g["title"], "description": g["desc"], "datePublished": today_iso, "dateModified": today_iso,
             "author": {"@type": "Organization", "name": CFG["name"]}, "publisher": {"@id": f"{BASE}/#org"},
             "mainEntityOfPage": f"{BASE}/guides/{g['slug']}/", "image": DEFAULT_OG},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Guides", "item": BASE + "/guides/"},
                {"@type": "ListItem", "position": 3, "name": g["h1"], "item": f"{BASE}/guides/{g['slug']}/"}]}]}
        page(f"/guides/{g['slug']}/", g['title'], g["desc"], body, f'<script type="application/ld+json">{json.dumps(ld)}</script>', "", "article")

    # ---------- about ----------
    about = f"""<div class="wrap"><section class="block"><div class="two"><div class="prose"><h1>About {CFG['name']}</h1>
<p>{CFG['name']} makes digital designs and printables for everyday life: tumbler wraps, shirt graphics, planners, birthday cards and classroom keepsakes.</p>
<p>Every design is original. Nothing uses licensed characters, brand logos or celebrity likenesses, so you can create with confidence.</p>
<p>Checkout is secure and your files are ready to download straight away, here or on Etsy. New designs are added regularly.</p>
<p><a class="btn" href="/shop/">Browse the shop</a></p></div>
<div class="panel"><h3>{e(CFG['tagline'])}</h3><div class="pillars" style="grid-template-columns:1fr">{pill}</div></div></div></section></div>"""
    page("/about/", f"About | {CFG['name']}", f"About {CFG['name']}: original digital designs and printables, delivered instantly through Etsy.", about)

    # ---------- contact ----------
    mail = f'<p>Email: <a href="mailto:{CFG["contact_email"]}">{CFG["contact_email"]}</a></p>' if CFG["contact_email"] else ""
    contact = f"""<div class="wrap"><section class="block"><div class="two"><div class="prose"><h1>Contact</h1>
<p>Questions about a design, a file or an order? The fastest way to reach us is a message through Etsy, where your order history is already attached.</p>
{mail}<p><a class="btn etsy" href="{CFG['etsy_shop_url']}" target="_blank" rel="noopener">Message us on Etsy</a></p></div>
<div class="panel"><h3>Files not opening?</h3><p>Open your Etsy purchases, choose the order, then Download Files. If something still looks wrong, message us from that order and we will fix it.</p></div></div></section></div>"""
    page("/contact/", f"Contact | {CFG['name']}", "Contact PrintFluent through Etsy for help with a design, file or order.", contact)

    # ---------- thank-you (after Polar checkout) ----------
    page("/thank-you/", "Thank you | PrintFluent", "Thanks for your order from PrintFluent.",
         '<div class="wrap"><section class="block prose" style="text-align:center;padding:60px 0"><h1>Thank you!</h1>'
         '<p class="lead">Your payment went through. Your download link is on the confirmation page and in the email receipt from Polar.</p>'
         '<p>Check your spam folder if you cannot find the email. Need help? <a href="/contact/">Contact us</a>.</p>'
         '<p><a class="btn" href="/shop/">Keep browsing</a></p></section></div>')
    _ty = DIST / "thank-you" / "index.html"
    _ty.write_text(_ty.read_text().replace('content="index,follow,max-image-preview:large,max-snippet:-1"', 'content="noindex,nofollow"'))

    # ---------- 404, redirects, robots, sitemap ----------
    (DIST / "404.html").write_text(head("Page not found | PrintFluent", "Page not found.", "/404.html") + header("/404") +
        '<div class="wrap"><section class="block"><h1>Page not found</h1><p>That page has moved or never existed.</p><a class="btn" href="/shop/">Go to the shop</a></section></div>' + footer(), encoding="utf-8")
    (DIST / "_redirects").write_text("\n".join([
        "/shop /shop/ 301", "/about /about/ 301", "/contact /contact/ 301", "/guides /guides/ 301", "/blog /guides/ 301",
        "/categories/planners /categories/planners-trackers/ 301",
        "/categories/journals-trackers /categories/planners-trackers/ 301",
        "/categories/kids-worksheets /categories/teacher-resources/ 301",
        "/categories/islamic-printables /shop/ 302", "/categories/household-organizers /shop/ 302"]) + "\n")
    (DIST / "_headers").write_text("""/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
/assets/css/*
  Cache-Control: public, max-age=86400
/assets/js/*
  Cache-Control: public, max-age=86400
/assets/products/*
  Cache-Control: public, max-age=604800
/assets/img/*
  Cache-Control: public, max-age=604800
""")
    (DIST / ".htaccess").write_text("""ErrorDocument 404 /404.html
DirectoryIndex index.html
Options -Indexes
Redirect 301 /categories/planners /categories/planners-trackers/
Redirect 301 /categories/journals-trackers /categories/planners-trackers/
Redirect 301 /categories/kids-worksheets /categories/teacher-resources/
Redirect 302 /categories/islamic-printables /shop/
Redirect 302 /categories/household-organizers /shop/
Redirect 301 /blog /guides/
""")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    urls = ["/", "/shop/", "/guides/", "/about/", "/contact/"] + [f"/guides/{g['slug']}/" for g in GUIDES] + [f"/categories/{c['slug']}/" for c in CFG["categories"]] + [f"/product/{p['slug']}/" for p in PRODUCTS]
    imgmap = {f"/product/{p['slug']}/": f"{BASE}/assets/products/{p['id']}.jpg" for p in PRODUCTS if (SRC / "assets/products" / f"{p['id']}.jpg").exists()}
    today = datetime.date.today().isoformat()
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">' +
        "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{today}</lastmod>" + (f"<image:image><image:loc>{imgmap[u]}</image:loc></image:image>" if u in imgmap else "") + "</url>" for u in urls) + "</urlset>")
    print(f"built {len(urls)} pages -> {DIST}")


if __name__ == "__main__":
    build()
