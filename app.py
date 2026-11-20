import os, time, json
from flask import Flask, render_template, request, abort, Response
import requests

app = Flask(__name__)
API = "https://api.jikan.moe/v4"
UA = {"User-Agent": "OtakuNime/1.0 (anime watchlist web)"}

_cache = {}  # url -> (timestamp, data)
TTL = 600  # 10 menit, Jikan rate limit 3 req/s — cache wajib

def jikan(path, params=None):
    key = path + "?" + json.dumps(params or {}, sort_keys=True)
    now = time.time()
    if key in _cache and now - _cache[key][0] < TTL:
        return _cache[key][1]
    r = requests.get(API + path, params=params or {}, headers=UA, timeout=6)
    r.raise_for_status()
    d = r.json()
    _cache[key] = (now, d)
    return d

def slim(item):
    return {
        "id": item["mal_id"],
        "title": item.get("title_english") or item.get("title") or "Unknown",
        "img": (item.get("images") or {}).get("jpg", {}).get("large_image_url")
               or (item.get("images") or {}).get("jpg", {}).get("image_url"),
        "score": item.get("score"),
        "episodes": item.get("episodes"),
        "type": item.get("type"),
        "airing": item.get("airing"),
        "synopsis": item.get("synopsis") or "",
        "genres": ", ".join(g["name"] for g in (item.get("genres") or [])[:4]),
        "url": item.get("url"),
    }

def legal_links(title):
    q = requests.utils.quote(title)
    return [
        ("Crunchyroll", f"https://www.crunchyroll.com/search?q={q}"),
        ("Netflix", f"https://www.netflix.com/search?q={q}"),
        ("Bilibili", f"https://bangga.bilibili.tv/search?q={q}"),
        ("Muse Indonesia", f"https://www.youtube.com/@MuseIndonesia/search?query={q}"),
        ("iQIYI", f"https://www.iq.com/search?query={q}"),
        ("AniList Info", f"https://anilist.co/search/anime?search={q}"),
    ]

DEMO = [  # fallback tampilan kalau Jikan tak terjangkau (mis. server diblokir)
    {"mal_id": 52991, "title": "Sousou no Frieren", "images": {"jpg": {"large_image_url": "https://cdn.myanimelist.net/images/anime/1015/138006l.jpg"}}, "score": 9.3, "episodes": 28, "type": "TV", "airing": True, "synopsis": "Kisah penyihir elf Frieren.", "genres": [{"name": "Adventure"}, {"name": "Fantasy"}]},
    {"mal_id": 51150, "title": "Oshi no Ko", "images": {"jpg": {"large_image_url": "https://cdn.myanimelist.net/images/anime/2434/136470l.jpg"}}, "score": 8.6, "episodes": 11, "type": "TV", "airing": False, "synopsis": "Dunia idol dan perjudian hidup.", "genres": [{"name": "Drama"}]},
    {"mal_id": 51009, "title": "Jujutsu Kaisen S2", "images": {"jpg": {"large_image_url": "https://cdn.myanimelist.net/images/anime/1792/138022l.jpg"}}, "score": 8.8, "episodes": 23, "type": "TV", "airing": False, "synopsis": "Seksi penyumpaan.", "genres": [{"name": "Action"}]},
]

@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)
    try:
        d = jikan("/seasons/now", {"limit": 24, "page": page, "sfw": "true"})
    except Exception:
        d = {"data": DEMO, "pagination": {"has_next_page": False}}
    return render_template("index.html", animes=[slim(x) for x in d["data"]],
                           page=page, has_next=d["pagination"].get("has_next_page", False),
                           section="Anime Ongoing Musim Ini")

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    animes, has_next = [], False
    if q:
        try:
            d = jikan("/anime", {"q": q, "limit": 24, "page": page, "sfw": "true", "order_by": "members", "sort": "desc"})
            animes = [slim(x) for x in d["data"]]
            has_next = d["pagination"].get("has_next_page", False)
        except Exception:
            pass
    return render_template("index.html", animes=animes, page=page, has_next=has_next,
                           section=f"Pencarian: {q}", q=q)

@app.route("/anime/<int:aid>")
def detail(aid):
    try:
        d = jikan(f"/anime/{aid}/full")
        a = slim(d["data"])
        a.update({
            "year": d["data"].get("year"),
            "season": d["data"].get("season"),
            "status": d["data"].get("status"),
            "studio": ", ".join(s["name"] for s in (d["data"].get("studios") or [])),
            "duration": d["data"].get("duration"),
            "members": d["data"].get("members"),
            "trailer": (d["data"].get("trailer") or {}).get("url"),
        })
    except Exception:
        # fallback demo kalau API tidak terjangkau
        demo = next((x for x in DEMO if x["mal_id"] == aid), None)
        if not demo:
            abort(404)
        a = slim(demo)
        a.update({"year": 2024, "season": "summer", "status": "Currently Airing",
                  "studio": "-", "duration": "24 min per ep", "members": None, "trailer": None})
    return render_template("detail.html", a=a, links=legal_links(a["title"]))

@app.route("/healthz")
def healthz():
    return {"status": "ok"}

@app.errorhandler(404)
def nf(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
