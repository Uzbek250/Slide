"""
Har bir slayd JSON obyektini HTML shablonga quyadi, so'ng Playwright (headless
Chromium) orqali 1920x1080 rasmga (JPEG) screenshot qiladi.

Nega screenshot yondashuvi: LLM chiqargan struktura ustida CSS orqali to'liq
nazorat saqlaymiz (gradient, shrift, layout) — bular python-pptx'ning
o'zida ishonchli chiqmaydi. Buning evaziga matn PowerPoint ichida
tahrirlanmaydi (rasm sifatida joylashadi) — MVP uchun bu qabul qilinadigan
chegara.

Eslatma: bu ilova ataylab faqat matnga asoslangan — tashqi rasm/fotosurat
qidirish yo'q (avval Wikimedia/Openverse bilan sinalgan, lekin natija
sifat/mos kelish jihatidan qoniqarli bo'lmagani uchun olib tashlandi).
Vizual boylik faqat ikon (emoji), rang, tipografiya va layout xilma-xilligi
orqali beriladi.
"""
import logging
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

logger = logging.getLogger("renderer")

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080

_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def render_slide_html(slide: dict, theme: str, page_num: int) -> str:
    """Bitta slayd uchun to'liq HTML matnini qaytaradi."""
    slide_type = slide.get("type", "bullets")
    template_name = f"{slide_type}.html"

    if not (TEMPLATES_DIR / template_name).exists():
        template_name = "bullets.html"  # fallback

    template = _jinja_env.get_template(template_name)
    context = {**slide, "theme": theme, "page_num": page_num}
    return template.render(**context)


def render_deck_to_images(deck: dict, output_dir: str) -> list[str]:
    """
    Butun deck (title + slides) uchun har bir slaydni JPEG faylga screenshot
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
            device_scale_factor=1,  # 1920x1080 - vektor matn/emoji uchun
            # sifat farqi ko'zga sezilmaydi (na ekranda, na chop etishda),
            # lekin render vaqti va fayl hajmi sezilarli kamayadi (o'lchangan:
            # scale=2 dan ~2.6x tezroq, sekin VPS/noutbuklarda muhim)
        )

        for i, slide in enumerate(deck["slides"]):
            html = render_slide_html(slide, theme, page_num=i + 1)
            page.set_content(html, wait_until="load", timeout=15000)

            img_path = os.path.join(output_dir, f"slide_{i:03d}.jpg")
            # JPEG (quality=90) — PNG'ga nisbatan 3-5x kichikroq fayl beradi,
            # gradient/rang fonlarda lossless PNG hech qanday amaliy sifat
            # farqisiz keraksiz katta chiqadi. 20 slaydlik deck bir necha
            # o'nlab MB o'rniga bir necha MB atrofida qoladi (yuklab olish
            # tezligi uchun muhim).
            page.screenshot(path=img_path, type="jpeg", quality=90)
            image_paths.append(img_path)

        browser.close()

    return image_paths
