"""
Har bir slayd uchun alohida render qilingan vektor PDF sahifalarini
(page.pdf() natijasi) bitta ko'p sahifali PDF faylga birlashtiradi.

Avval bu funksiya Pillow bilan JPEG rasmlarni PDF sahifalariga aylantirardi
(matn rasm sifatida saqlanardi). Endi renderer.py to'g'ridan-to'g'ri vektor
PDF sahifa yasagani uchun bu yerda faqat sahifalarni BIRLASHTIRISH kifoya -
pypdf buni sifat yo'qotmasdan (screenshot/encode bosqichisiz) bajaradi.
"""
from pypdf import PdfWriter


def build_pdf(pdf_page_paths: list[str], output_path: str, deck_title: str = "Presentation") -> str:
    if not pdf_page_paths:
        raise ValueError("PDF yaratish uchun kamida bitta sahifa kerak")

    writer = PdfWriter()
    for page_path in pdf_page_paths:
        writer.append(page_path)

    writer.add_metadata({"/Title": deck_title})

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
