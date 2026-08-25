"""
Wikimedia Commons'dan mavzuga mos rasm qidirish.

API key kerak emas — ochiq, anonim so'rovlar orqali ishlaydi.
Litsenziyasi qayta ishlatishga ochiq bo'lgan (CC0, CC-BY, CC-BY-SA, Public Domain)
rasmlarni afzal ko'ramiz.

MUHIM: bu modul hech qachon istisno (exception) tashlab pipeline'ni to'xtatmasligi
kerak — tarmoq xatosi yoki natija topilmasa, shunchaki None qaytaradi, chaqiruvchi
tomon (pipeline) buni "rasmsiz layout"ga qaytish signali sifatida ishlatadi.
"""
import httpx

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "SlideGeneratorBot/1.0 (https://github.com/Uzbek250/Slide; contact via GitHub)"
REQUEST_TIMEOUT = 6  # sekund — sekin javob butun generatsiyani sekinlashtirmasin

# Fayl kengaytmalari bo'yicha keraksiz formatlarni chetlab o'tamiz (svg logotiplar,
# audio, video ba'zan search natijasiga aralashib qoladi)
_ALLOWED_EXT = (".jpg", ".jpeg", ".png", ".webp")


def search_image(query: str, min_width: int = 900) -> dict | None:
    """
    Berilgan so'rov (ingliz tilida bo'lishi tavsiya etiladi — Commons'da ingliz
    tavsiflari ko'proq) bo'yicha eng mos bitta rasmni qaytaradi.

    Qaytadi: {"url": str, "width": int, "height": int, "author": str, "license": str}
    yoki hech narsa topilmasa/xato bo'lsa None.
    """
    if not query or not query.strip():
        return None

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}",
        "gsrnamespace": 6,  # File: nomlar maydoni
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": 1600,
        "format": "json",
        "origin": "*",
    }

    try:
        resp = httpx.get(
            COMMONS_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    pages = data.get("query", {}).get("pages")
    if not pages:
        return None

    candidates = []
    for page in pages.values():
        imageinfo = page.get("imageinfo")
        if not imageinfo:
            continue
        info = imageinfo[0]

        width = info.get("width", 0)
        height = info.get("height", 0)
        if width < min_width:
            continue

        url = info.get("thumburl") or info.get("url")
        if not url or not url.lower().endswith(_ALLOWED_EXT):
            continue

        # Juda vertikal (portret, masalan odam surati) yoki juda cho'ziq
        # rasmlarni pastroq ustuvorlikka qo'yamiz — slaydga yotiq/kvadrat mosroq
        aspect = width / height if height else 1
        score = 1.0
        if aspect < 0.6 or aspect > 2.8:
            score -= 0.4

        extmeta = info.get("extmetadata", {})
        license_short = extmeta.get("LicenseShortName", {}).get("value", "")
        artist = extmeta.get("Artist", {}).get("value", "")

        candidates.append({
            "url": url,
            "width": width,
            "height": height,
            "author": _strip_html(artist)[:120],
            "license": license_short,
            "score": score,
        })

    if not candidates:
        return None

    candidates.sort(key=lambda c: c["score"], reverse=True)
    best = candidates[0]
    best.pop("score", None)
    return best


def _strip_html(text: str) -> str:
    """extmetadata muallif maydoni ko'pincha HTML linklar bilan keladi — tozalaymiz."""
    import re
    return re.sub(r"<[^>]+>", "", text or "").strip()
