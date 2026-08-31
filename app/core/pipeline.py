"""
To'liq pipeline: mavzu -> Gemini JSON -> HTML render -> PNG -> PPTX.
"""
import tempfile
import shutil
import os

from app.core.content_generator import generate_deck_structure
from app.core.renderer import render_deck_to_images
from app.core.pptx_builder import build_pptx
from app.core.pdf_builder import build_pdf


def generate_presentation(
    topic: str,
    slide_count: int,
    output_path: str,
    output_format: str = "pptx",
    theme: str = "minimal",
) -> str:
    """
    To'liq oqimni ishga tushiradi va tayyor fayl yo'lini qaytaradi.
    output_format: "pptx" yoki "pdf" - faqat oxirgi yig'ish bosqichi farqlanadi,
    mavzu -> Gemini JSON -> HTML render -> rasm bosqichlari umumiy.
    theme: foydalanuvchi tanlagan dizayn (minimal / corporate / warm / forest).
    """
    deck = generate_deck_structure(topic, slide_count, theme=theme)

    with tempfile.TemporaryDirectory() as tmp_dir:
        image_paths = render_deck_to_images(deck, tmp_dir)
        deck_title = deck.get("title", topic)
        if output_format == "pdf":
            build_pdf(image_paths, output_path, deck_title=deck_title)
        else:
            build_pptx(image_paths, output_path, deck_title=deck_title)

    return output_path
