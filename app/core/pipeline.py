"""
To'liq pipeline: mavzu -> Gemini JSON -> HTML render -> vektor PDF sahifalar
-> birlashtirilgan PDF.

Eslatma: ilova avval PPTX va PDF ikkalasini ham qo'llab-quvvatlagan, lekin
ikkalasi ham bir xil screenshot(JPEG) rasmlaridan yig'ilgani va matn
tahrirlanmasligi (rasm sifatida joylashgani) uchun PPTX'ning amaliy foydasi
kam edi, shuning uchun PPTX yo'li olib tashlandi.

Keyinroq screenshot(JPEG)+Pillow bosqichi ham page.pdf() (Chromium "Print to
PDF") bilan almashtirildi — natija endi vektor PDF, matn rasm emas, zoom
qilinganda sifat yo'qolmaydi, va oraliq JPEG encode/decode bosqichi
yo'qolgani uchun biroz tezroq.
"""
import tempfile

from app.core.content_generator import generate_deck_structure
from app.core.renderer import render_deck_to_pdf_pages
from app.core.pdf_builder import build_pdf


def generate_presentation(
    topic: str,
    slide_count: int,
    output_path: str,
    theme: str = "minimal",
) -> str:
    """
    To'liq oqimni ishga tushiradi va tayyor PDF fayl yo'lini qaytaradi.
    theme: foydalanuvchi tanlagan dizayn (minimal / corporate / warm / forest).
    """
    deck = generate_deck_structure(topic, slide_count, theme=theme)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_page_paths = render_deck_to_pdf_pages(deck, tmp_dir)
        deck_title = deck.get("title", topic)
        build_pdf(pdf_page_paths, output_path, deck_title=deck_title)

    return output_path
