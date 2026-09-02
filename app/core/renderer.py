"""
Har bir slayd JSON obyektini HTML shablonga quyadi, so'ng Playwright (headless
Chromium) orqali to'g'ridan-to'g'ri vektor PDF sahifasiga ("Print to PDF")
render qiladi.

Nega HTML+CSS render yondashuvi: LLM chiqargan struktura ustida CSS orqali
to'liq nazorat saqlaymiz (gradient, shrift, layout) — bular python-pptx'ning
o'zida ishonchli chiqmaydi.

Nega screenshot(JPEG)+Pillow emas, balki page.pdf(): avvalgi versiyada har
bir slayd JPEG rasmga screenshot qilinib, keyin Pillow bilan PDF sahifalariga
yig'ilardi — bu matnni RASM qilib qo'yardi (zoom qilganda xiralashadi,
device_scale_factor past bo'lsa sifat pasayadi). page.pdf() esa Chromium'ning
o'z "Print to PDF" mexanizmidan foydalanadi: natija VEKTOR PDF (matn haqiqiy
matn sifatida qoladi, istalgan darajada zoom qilinsa ham aniq turadi) va
screenshot+JPEG encode+Pillow decode bosqichlari umuman yo'qoladi.
WeasyPrint kabi CSS-to-PDF renderer'lar sinalgan, lekin ular flexbox/grid'ni
to'liq qo'llab-quvvatlamagani uchun layout buzilib chiqqan — bu yerda esa
haqiqiy Chromium rendering engine ishlatilgani uchun layout screenshot
versiyasi bilan bir xil aniqlikda chiqadi.

Eslatma: bu ilova ataylab faqat matnga asoslangan — tashqi rasm/fotosurat
qidirish yo'q (avval Wikimedia/Openverse bilan sinalgan, lekin natija
sifat/mos kelish jihatidan qoniqarli bo'lmagani uchun olib tashlangan).
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

# page.pdf() sahifa o'lchamini piksel emas, balki fizik birlikda (dyuym)
# kutadi. CSS'dagi @page { size: 1920px 1080px } qoidasi ham bor, lekin
# ba'zi Playwright versiyalarida width/height parametrlari @page'dan
# ustun turadi - shuning uchun ikkalasini ham mos qilib beramiz.
# 1920px / 144 (standart CSS px->in, 1.5 device_scale hisobga olingan
# holda ekvivalent) o'rniga soddaroq: 96 CSS px = 1in standart nisbat.
_PDF_WIDTH_IN = SLIDE_WIDTH / 96  # = 20in
_PDF_HEIGHT_IN = SLIDE_HEIGHT / 96  # = 11.25in

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


def render_deck_to_pdf_pages(deck: dict, output_dir: str) -> list[str]:
    """
    Butun deck (title + slides) uchun har bir slaydni bitta sahifali vektor
    PDF faylga render qiladi. Fayl yo'llari ro'yxatini tartib bilan
    qaytaradi - keyinroq pdf_builder bularni bitta ko'p sahifali faylga
    birlashtiradi.
    """
    os.makedirs(output_dir, exist_ok=True)
    theme = deck.get("theme", "minimal")
    pdf_paths = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(
            viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT},
        )

        for i, slide in enumerate(deck["slides"]):
            html = render_slide_html(slide, theme, page_num=i + 1)
            page.set_content(html, wait_until="load", timeout=15000)
            # Google Fonts @import CSS orqali asinxron yuklanadi. Vektor
            # PDF'da agar shrift hali tayyor bo'lmasa, matn fallback shrift
            # bilan "qotib" qolishi mumkin (screenshot'da bu faqat vizual
            # kamchilik edi, PDF'da esa embed qilingan holatda saqlanadi).
            page.evaluate("document.fonts.ready.then(() => true)")

            pdf_path = os.path.join(output_dir, f"slide_{i:03d}.pdf")
            page.pdf(
                path=pdf_path,
                width=f"{_PDF_WIDTH_IN}in",
                height=f"{_PDF_HEIGHT_IN}in",
                print_background=True,  # fon rang/gradientlarni chop etish
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
            pdf_paths.append(pdf_path)

        browser.close()

    return pdf_paths
