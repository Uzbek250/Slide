"""
Slaydlar uchun mavzuga mos rasm qidirish.

Ikki bosqichli manba:
1. Wikimedia Commons (Action API) — birinchi urinish. Tibbiyot/ilmiy mavzular
   uchun ataylab tanlangan: Gray's Anatomy, Blausen Medical va shunga o'xshash
   ochiq litsenziyali tibbiy diagrammalar katta miqdorda mavjud — bu
   Pexels/Unsplash kabi umumiy stok-foto servislarida yo'q.
2. Openverse (api.openverse.org) — Wikimedia bo'sh yoki xato qaytarsa zaxira
   sifatida sinaladi. Openverse ham Wikimedia Commons'ni indekslaydi, shu bilan
   birga Flickr, muzey arxivlari va boshqa manbalarni ham qamrab oladi — rasmiy
   REST API bo'lgani uchun ba'zan Action API'dan ko'ra ishonchliroq bo'ladi.

Ikkalasi ham API key talab qilmaydi, anonim so'rovlar bilan ishlaydi.

MUHIM: bu modul hech qachon istisno (exception) tashlab pipeline'ni to'xtatmasligi
kerak — tarmoq xatosi yoki natija topilmasa, shunchaki None qaytaradi, chaqiruvchi
tomon (pipeline) buni "rasmsiz layout"ga qaytish signali sifatida ishlatadi.
Har bir muvaffaqiyatsizlik SABABI bilan birga logga yoziladi — Render loglarida
"image_search:" prefiksi bilan qidirib, aniq sababni ko'rish mumkin.
"""
import logging
import re
import httpx

logger = logging.getLogger("image_search")

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"
USER_AGENT = "SlideGeneratorBot/1.0 (https://github.com/Uzbek250/Slide; contact via GitHub)"
REQUEST_TIMEOUT = 6  # sekund — sekin javob butun generatsiyani sekinlashtirmasin

# Fayl kengaytmalari bo'yicha keraksiz formatlarni chetlab o'tamiz (svg logotiplar,
# audio, video ba'zan search natijasiga aralashib qoladi)
_ALLOWED_EXT = (".jpg", ".jpeg", ".png", ".webp")


def search_image(query: str, min_width: int = 900) -> dict | None:
    """
    Berilgan so'rov (ingliz tilida bo'lishi tavsiya etiladi) bo'yicha eng mos
    bitta rasmni qaytaradi. Avval Wikimedia, u bo'sh qaytsa Openverse sinaladi.

    Qaytadi: {"url": str, "width": int, "height": int, "author": str, "license": str}
    yoki hech narsa topilmasa/xato bo'lsa None.
    """
    if not query or not query.strip():
        logger.warning("image_search: bo'sh query berildi, qidiruv o'tkazib yuborildi")
        return None

    result = _search_wikimedia(query, min_width)
    if result:
        return result

    logger.info("image_search: Wikimedia'da topilmadi, Openverse sinalmoqda query=%r", query)
    result = _search_openverse(query, min_width)
    if result:
        return result

    logger.warning("image_search: ikkala manbada ham topilmadi query=%r", query)
    return None


def _search_wikimedia(query: str, min_width: int) -> dict | None:
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
        # origin=* qasddan qo'yilmagan: bu faqat brauzer-JS CORS so'rovlari
        # uchun kerak, server-tomonli so'rovda keraksiz/xato manbai bo'lishi mumkin
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
    except httpx.HTTPStatusError as e:
        logger.warning(
            "image_search[wikimedia]: HTTP xato query=%r status=%s",
            query, e.response.status_code,
        )
        return None
    except httpx.HTTPError as e:
        logger.warning("image_search[wikimedia]: tarmoq xatosi query=%r error=%s", query, e)
        return None
    except ValueError as e:
        logger.warning("image_search[wikimedia]: JSON parse xatosi query=%r error=%s", query, e)
        return None

    pages = data.get("query", {}).get("pages")
    if not pages:
        logger.info("image_search[wikimedia]: natija topilmadi query=%r", query)
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
        logger.info("image_search[wikimedia]: filtrdan o'tuvchi natija yo'q query=%r", query)
        return None

    candidates.sort(key=lambda c: c["score"], reverse=True)
    best = candidates[0]
    best.pop("score", None)
    logger.info("image_search[wikimedia]: topildi query=%r url=%s", query, best["url"])
    return best


def _search_openverse(query: str, min_width: int) -> dict | None:
    params = {
        "q": query,
        "license_type": "all-cc",  # CC0/CC-BY/CC-BY-SA — qayta ishlatishga ochiq
        "page_size": 8,
        "mature": "false",
    }

    try:
        resp = httpx.get(
            OPENVERSE_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.warning(
            "image_search[openverse]: HTTP xato query=%r status=%s",
            query, e.response.status_code,
        )
        return None
    except httpx.HTTPError as e:
        logger.warning("image_search[openverse]: tarmoq xatosi query=%r error=%s", query, e)
        return None
    except ValueError as e:
        logger.warning("image_search[openverse]: JSON parse xatosi query=%r error=%s", query, e)
        return None

    results = data.get("results", [])
    if not results:
        logger.info("image_search[openverse]: natija topilmadi query=%r", query)
        return None

    candidates = []
    for item in results:
        width = item.get("width") or 0
        height = item.get("height") or 0
        if width and width < min_width:
            continue

        url = item.get("url")
        if not url or not any(url.lower().split("?")[0].endswith(ext) for ext in _ALLOWED_EXT):
            continue

        aspect = width / height if height else 1
        score = 1.0
        if aspect < 0.6 or aspect > 2.8:
            score -= 0.4

        candidates.append({
            "url": url,
            "width": width,
            "height": height,
            "author": (item.get("creator") or "")[:120],
            "license": (item.get("license") or "").upper(),
            "score": score,
        })

    if not candidates:
        logger.info("image_search[openverse]: filtrdan o'tuvchi natija yo'q query=%r", query)
        return None

    candidates.sort(key=lambda c: c["score"], reverse=True)
    best = candidates[0]
    best.pop("score", None)
    logger.info("image_search[openverse]: topildi query=%r url=%s", query, best["url"])
    return best


def _strip_html(text: str) -> str:
    """extmetadata muallif maydoni ko'pincha HTML linklar bilan keladi — tozalaymiz."""
    return re.sub(r"<[^>]+>", "", text or "").strip()
