"""
Har bir slayd JSON obyektini HTML shablonga quyadi, so'ng Playwright (headless
Chromium) orqali 1920x1080 PNG rasmga screenshot qiladi.

Nega screenshot yondashuvi: LLM chiqargan struktura ustida CSS orqali to'liq
nazorat saqlaymiz (gradient, shrift, layout) — bular python-pptx'ning
o'zida ishonchli chiqmaydi. Buning evaziga matn PowerPoint ichida
tahrirlanmaydi (rasm sifatida joylashadi) — MVP uchun bu qabul qilinadigan
chegara.
"""
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

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
    Butun deck (title + slides) uchun har bir slaydni PNG faylga screenshot
    qiladi. Fayl yo'llari ro'yxatini tartib bilan qaytaradi.
    """
    os.makedirs(output_dir, exist_ok=True)
    theme = deck.get("theme", "minimal")
    image_paths = []

    browser_path_env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")

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
            page.set_content(html, wait_until="networkidle")
            img_path = os.path.join(output_dir, f"slide_{i:03d}.png")
            page.screenshot(path=img_path)
            image_paths.append(img_path)

        browser.close()

    return image_paths
