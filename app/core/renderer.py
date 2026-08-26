"""
Har bir slayd JSON obyektini HTML shablonga quyadi, so'ng Playwright (headless
Chromium) orqali 1920x1080 PNG rasmga screenshot qiladi.

Nega screenshot yondashuvi: LLM chiqargan struktura ustida CSS orqali to'liq
nazorat saqlaymiz (gradient, shrift, layout) — bular python-pptx'ning
o'zida ishonchli chiqmaydi. Buning evaziga matn PowerPoint ichida
tahrirlanmaydi (rasm sifatida joylashadi) — MVP uchun bu qabul qilinadigan
chegara.

RASM QIDIRISH: agar slayd JSON'ida "image_query" bo'lsa, render qilishdan oldin
Wikimedia Commons'dan mos rasm qidiramiz. Topilmasa yoki tarmoq xatosi bo'lsa,
slayd HECH QACHON "unutilib" bo'sh qolmaydi — image_text turi avtomatik ravishda
rasmsiz layoutga (bullets) tushiriladi, title esa rasmsiz variantda davom etadi.
"""
import logging
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from app.core.image_search import search_image

logger = logging.getLogger("renderer")

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080

_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def _resolve_image(slide: dict) -> dict:
    """
    Agar slaydda image_query bo'lsa, Wikimedia'dan qidirib image_url va
    image_credit maydonlarini qo'shadi. Har doim yangi dict qaytaradi
    (original slide obyektini o'zgartirmaydi).

    image_text turi uchun: rasm topilmasa, "bullets" turiga avtomatik almashadi
    (paragraph -> subheading, bullets saqlanib qoladi) — shunda kontent
    hech qachon yo'qolmaydi, faqat vizual taqdimoti o'zgaradi.
    """
    query = slide.get("image_query")
    if not query:
        logger.info(
            "renderer: slayd type=%r uchun Gemini image_query bermadi (heading=%r)",
            slide.get("type"), slide.get("heading"),
        )
        return slide

    result = search_image(query)
    updated = dict(slide)

    if result:
        updated["image_url"] = result["url"]
        author = result.get("author")
        license_name = result.get("license")
        if author or license_name:
            credit_parts = [p for p in [author, license_name] if p]
            updated["image_credit"] = " · ".join(credit_parts)
        return updated

    # Rasm topilmadi -> fallback
    logger.warning(
        "renderer: rasm topilmadi query=%r (type=%r) - fallback ishlatiladi",
        query, slide.get("type"),
    )
    if slide.get("type") == "image_text":
        updated["type"] = "bullets"
        if slide.get("paragraph") and not slide.get("subheading"):
            updated["subheading"] = slide["paragraph"]
        # bullets maydoni allaqachon mavjud bo'lsa shunday qoladi
        if not updated.get("bullets"):
            updated["bullets"] = []
    # title uchun image_url shunchaki qo'yilmaydi, shablon o'zi rasmsiz ishlaydi

    return updated


def render_slide_html(slide: dict, theme: str, page_num: int) -> str:
    """Bitta slayd uchun to'liq HTML matnini qaytaradi."""
    slide = _resolve_image(slide)

    slide_type = slide.get("type", "bullets")
    template_name = f"{slide_type}.html"

    if not (TEMPLATES_DIR / template_name).exists():
        template_name = "bullets.html"  # fallback

    template = _jinja_env.get_template(template_name)
    context = {**slide, "theme": theme, "page_num": page_num}
    return template.render(**context)


def render_deck_to_images(deck: dict, output_dir: str) -> list[str]:
    """
    Butun deck (title + slides) uchun har bir slaydni PNG faylga screenshot
    qiladi. Fayl yo'llari ro'yxatini tartib bilan qaytaradi.
    """
    os.makedirs(output_dir, exist_ok=True)
    theme = deck.get("theme", "minimal")
    image_paths = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(
            viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT},
            device_scale_factor=2,  # retina — HD sifat
        )

        for i, slide in enumerate(deck["slides"]):
            html = render_slide_html(slide, theme, page_num=i + 1)
            # networkidle: tashqi rasm (Wikimedia/Openverse) va shriftlar
            # so'rovlari tugaguncha kutadi. Lekin bu rasmning EKRANGA
            # CHIZILGANINI (decode/paint) kafolatlamaydi - rasm ba'zan
            # tarmoqdan kelib bo'lgan, lekin browser hali uni chizmagan
            # holatda screenshot olinib, natija qora chiqishi mumkin edi.
            #
            # HIMOYA: agar tashqi rasm serveri juda sekin/javobsiz bo'lib,
            # networkidle 20 soniyada yetib bo'lmasa, TimeoutError tashlanadi.
            # Bunday holatda ham slayd matni butunlay yo'qolib qolmasligi
            # uchun "load" holatiga (faqat asosiy HTML yuklanishi, tashqi
            # rasmlarni kutmaydi) tushib, screenshot baribir olinadi -
            # natijada eng yomon holatda rasm yo'q, lekin matn bor bo'ladi.
            try:
                page.set_content(html, wait_until="networkidle", timeout=20000)
            except Exception as e:
                logger.warning(
                    "renderer: networkidle timeout slide=%d, 'load' bilan qayta urinilmoqda: %s",
                    i, e,
                )
                page.set_content(html, wait_until="load", timeout=10000)

            # Har bir <img> uchun decode() orqali chizishga tayyor bo'lishini
            # kutamiz. Bitta rasm juda sekin/muvaffaqiyatsiz bo'lsa ham,
            # try/except orqali shu rasmni o'tkazib yuboramiz - butun
            # generatsiya to'xtab qolmaydi, faqat o'sha rasm bo'sh joy
            # sifatida qoladi (bu holatda ham matn hech qachon yo'qolmaydi,
            # chunki bu faqat rasm elementiga tegishli kutish).
            try:
                page.eval_on_selector_all(
                    "img",
                    """
                    async (imgs) => {
                        await Promise.all(imgs.map(img => {
                            if (img.complete) return img.decode().catch(() => {});
                            return new Promise(resolve => {
                                img.addEventListener('load', () => img.decode().then(resolve).catch(resolve));
                                img.addEventListener('error', resolve);
                                // Bitta rasm uchun maksimal 8 soniya kutamiz -
                                // undan ko'p kutish butun slaydni sekinlashtiradi
                                setTimeout(resolve, 8000);
                            });
                        }));
                    }
                    """,
                )
            except Exception as e:
                logger.warning("renderer: rasm decode kutishda xato slide=%d error=%s", i, e)

            img_path = os.path.join(output_dir, f"slide_{i:03d}.jpg")
            # JPEG (quality=90) — PNG'ga nisbatan 3-5x kichikroq fayl beradi,
            # gradient/rang fonlarda lossless PNG hech qanday amaliy sifat
            # farqisiz keraksiz katta chiqadi. 20 slaydlik deck bir necha
            # o'nlab MB o'rniga bir necha MB atrofida qoladi (Telegram orqali
            # yuborish/yuklab olish tezligi uchun muhim).
            page.screenshot(path=img_path, type="jpeg", quality=90)
            image_paths.append(img_path)

        browser.close()

    return image_paths
