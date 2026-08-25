"""
To'liq pipeline: mavzu -> Gemini JSON -> HTML render -> PNG -> PPTX.
"""
import tempfile
import shutil
import os

from app.core.content_generator import generate_deck_structure
from app.core.renderer import render_deck_to_images
from app.core.pptx_builder import build_pptx


def generate_presentation(topic: str, slide_count: int, output_path: str) -> str:
    """
    To'liq oqimni ishga tushiradi va tayyor .pptx fayl yo'lini qaytaradi.
    """
    deck = generate_deck_structure(topic, slide_count)

    with tempfile.TemporaryDirectory() as tmp_dir:
        image_paths = render_deck_to_images(deck, tmp_dir)
        build_pptx(image_paths, output_path, deck_title=deck.get("title", topic))

    return output_path
