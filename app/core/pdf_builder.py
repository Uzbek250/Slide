"""
Screenshot qilingan rasmlarni (JPEG) bitta .pdf faylga yig'adi.
Har bir rasm - bitta sahifaga to'liq (full-bleed) joylashtiriladi.

Pillow'ning o'zi (qo'shimcha dependency shart emas) - JPEG rasmlarni
ochib, ularni bitta ko'p sahifali PDF sifatida saqlaydi.
"""
from PIL import Image


def build_pdf(image_paths: list[str], output_path: str, deck_title: str = "Presentation") -> str:
    if not image_paths:
        raise ValueError("PDF yaratish uchun kamida bitta rasm kerak")

    images = [Image.open(p).convert("RGB") for p in image_paths]
    first, rest = images[0], images[1:]

    first.save(
        output_path,
        format="PDF",
        save_all=True,
        append_images=rest,
        title=deck_title,
        resolution=150.0,
    )
    return output_path
