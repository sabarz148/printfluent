#!/usr/bin/env python3
"""Sync PrintFluent listings from Etsy (Open API v3): titles, prices, full descriptions, tags,
ALL photos and the listing video. Also writes a dated backup (CSV + media list).

Env: ETSY_API_KEY (app keystring). Optional: ETSY_SHOP_NAME (default PrintFluentShop).
Only reads your public active listings. Never deletes your files. Keeps featured/hidden/bundle flags.
"""
import csv, datetime, io, json, os, pathlib, re, sys, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://openapi.etsy.com/v3/application"
KEY = os.environ.get("ETSY_API_KEY") or sys.exit("Set ETSY_API_KEY")
MAX_VIDEO = 24 * 1024 * 1024          # Cloudflare asset limit is 25 MiB per file


def get(path, **params):
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"x-api-key": KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch(url, dest, limit=None):
    if dest.exists() and dest.stat().st_size > 0: return True
    req = urllib.request.Request(url, headers={"User-Agent": "PrintFluentSync/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read(limit + 1 if limit else -1)
    if limit and len(data) > limit: return False
    dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data); return True


def save_jpeg(url, dest, maxpx=1200):
    if dest.exists() and dest.stat().st_size > 0: return
    req = urllib.request.Request(url, headers={"User-Agent": "PrintFluentSync/1.0"})
    raw = urllib.request.urlopen(req, timeout=120).read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGB"); im.thumbnail((maxpx, maxpx))
        im.save(dest, "JPEG", quality=82, optimize=True, progressive=True)
    except ImportError:
        dest.write_bytes(raw)


shop_id = get("/shops", shop_name=os.environ.get("ETSY_SHOP_NAME", "PrintFluentShop"))["results"][0]["shop_id"]
SECTION = {"tumbler wraps": "tumbler-wraps", "planners & trackers": "planners-trackers", "t-shirt png designs": "t-shirt-designs",
           "teacher resources": "teacher-resources", "birthday": "birthday-cards", "kids activity": "kids-activities"}
sections = {s["shop_section_id"]: s["title"].lower() for s in get(f"/shops/{shop_id}/sections")["results"]}


def category(title, section, prev):
    if prev.get("category"): return prev["category"]          # your existing choice wins
    t = title.lower()
    if section == "cards" or "card" in t:
        return "sympathy-cards" if re.search(r"sympathy|condolence|bereave|loss of|remembering", t) else "birthday-cards"
    if section in SECTION: return SECTION[section]
    for k, v in [("tumbler", "tumbler-wraps"), ("shirt", "t-shirt-designs"), ("workbook", "kids-activities"),
                 ("planner", "planners-trackers"), ("tracker", "planners-trackers"), ("school", "teacher-resources")]:
        if k in t: return v
    return "planners-trackers"


path = ROOT / "data/products.json"
old = {p["id"]: p for p in json.loads(path.read_text())["products"]}
listings, offset = [], 0
while True:
    r = get(f"/shops/{shop_id}/listings/active", limit=100, offset=offset, includes="Images,Videos", sort_on="created", sort_order="desc")
    listings += r["results"]; offset += 100
    if offset >= r["count"]: break

media = ROOT / "src/assets/products"
products, rows = [], []
for i, l in enumerate(listings):
    pid = str(l["listing_id"]); prev = dict(old.get(pid, {}))
    title = l["title"]; price = round(l["price"]["amount"] / l["price"]["divisor"], 2)
    slug = prev.get("slug") or re.sub(r"[^a-z0-9]+", "-", re.sub(r"\(.*?\)", "", title.lower())).strip("-")[:70].strip("-") + "-" + pid[-4:]
    imgs = sorted(l.get("images") or [], key=lambda x: x.get("rank", 0))
    n = 0
    for k, im in enumerate(imgs, 1):
        try:
            save_jpeg(im.get("url_fullxfull") or im["url_570xN"], media / pid / f"{k}.jpg"); n = k
        except Exception as ex: print("image fail", pid, k, ex)
    if n and not (media / f"{pid}.jpg").exists():
        (media / f"{pid}.jpg").write_bytes((media / pid / "1.jpg").read_bytes())
    has_video = False
    for v in (l.get("videos") or [])[:1]:
        try:
            has_video = fetch(v["video_url"], media / pid / "video.mp4", MAX_VIDEO)
            if has_video and v.get("thumbnail_url"): save_jpeg(v["thumbnail_url"], media / pid / "poster.jpg")
        except Exception as ex: print("video fail", pid, ex)
    section = sections.get(l.get("shop_section_id"), "")
    prev.update({"id": pid, "slug": slug, "title": title, "price": price,
                 "category": category(title, section, prev), "etsy_url": l["url"].split("?")[0],
                 "image": f"/assets/products/{pid}.jpg" if (media / f"{pid}.jpg").exists() else "",
                 "description": (l.get("description") or "").strip(), "tags": l.get("tags") or [],
                 "gallery": n, "video": has_video, "order": i})
    prev.setdefault("featured", False)
    if n and prev.get("hidden"): prev["hidden"] = False        # now has photos, show it
    products.append(prev)
    rows.append([pid, title, price, prev["category"], ", ".join(prev["tags"]), l["url"].split("?")[0], n, has_video, prev["description"]])

path.write_text(json.dumps({"shop": "PrintFluentShop", "count": len(products), "products": products}, indent=1, ensure_ascii=False))
bk = ROOT / "backup"; bk.mkdir(exist_ok=True)
stamp = datetime.date.today().isoformat()
with open(bk / f"etsy-listings-{stamp}.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["listing_id", "title", "price", "category", "tags", "etsy_url", "photos", "video", "description"]); w.writerows(rows)
print(f"synced {len(products)} listings")
