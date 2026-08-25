"""Gemini'siz sinov — qo'lda yozilgan JSON bilan render+pptx pipeline'ni tekshirish."""
import sys
sys.path.insert(0, ".")
from app.core.renderer import render_deck_to_images
from app.core.pptx_builder import build_pptx

fake_deck = {
    "title": "Sun'iy intellekt kelajagi",
    "theme": "gradient_dark",
    "slides": [
        {
            "type": "title",
            "heading": "Sun'iy intellekt kelajagi",
            "subheading": "Texnologiya qanday hayotimizni o'zgartirmoqda"
        },
        {
            "type": "bullets",
            "heading": "Asosiy yo'nalishlar",
            "bullets": [
                "Tibbiyotda diagnostika aniqligini oshirish",
                "Ta'limda shaxsiylashtirilgan yondashuv",
                "Sanoatda avtomatlashtirish jarayonlari",
                "Ijodiy sohalarda yangi vositalar"
            ]
        },
        {
            "type": "two_column",
            "heading": "Imkoniyat va xavflar",
            "left_title": "Imkoniyatlar",
            "left_points": ["Tezlik", "Aniqlik", "Masshtablanish"],
            "right_title": "Xavflar",
            "right_points": ["Ishsizlik", "Ma'lumot xavfsizligi", "Noto'g'ri qarorlar"]
        },
        {
            "type": "big_stat",
            "heading": "Bozor hajmi 2030 yilga borib",
            "stat": "1.8T$",
            "stat_label": "global AI bozori prognozi"
        },
        {
            "type": "quote",
            "quote_text": "Sun'iy intellekt — bu yangi elektr energiyasi",
            "quote_author": "Andrew Ng"
        },
        {
            "type": "closing",
            "heading": "Rahmat!",
            "subheading": "Savollaringiz bo'lsa, marhamat"
        }
    ]
}

image_paths = render_deck_to_images(fake_deck, "/home/claude/slide-bot/test_output/images")
print(f"Rendered {len(image_paths)} slides")
build_pptx(image_paths, "/home/claude/slide-bot/test_output/test_deck.pptx", deck_title=fake_deck["title"])
print("PPTX built successfully")
