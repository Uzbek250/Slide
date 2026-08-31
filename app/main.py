"""
FastAPI backend: veb-forma orqali mavzu qabul qiladi, Gemini + Playwright
yordamida taqdimot generatsiya qiladi va .pptx faylini qaytaradi.
"""
import logging
import os
import re
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.core.pipeline import generate_presentation

# Standart logging darajasi WARNING - bizning ichki modullardagi
# logger.info() chaqiruvlari shu sozlamasiz Render loglarida ko'rinmay
# qoladi. INFO darajasini yoqamiz va formatga vaqt+modul nomini
# qo'shamiz, shunda qidirish oson bo'ladi.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
# httpx har bir so'rovni INFO darajasida logga yozadi - bizga faqat
# o'zimizning modullar xabarlari kerak, shuning uchun httpx'ning
# ortiqcha "chiqindi" logini pasaytiramiz
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title="Slide Generator API")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

OUTPUT_DIR = "/tmp/slide_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# file_id -> (foydalanuvchiga ko'rsatiladigan fayl nomi, format)
_FILENAME_REGISTRY: dict[str, tuple[str, str]] = {}

_MEDIA_TYPES = {
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pdf": "application/pdf",
}


def _slugify_filename(topic: str) -> str:
    """
    Mavzu matnidan xavfsiz fayl nomi yasaydi: papka ajratuvchilari, kavychalar
    va boshqa maxsus belgilarni olib tashlaydi, bo'sh joylarni pastki chiziqqa
    almashtiradi. Lotin va kiril harflari, raqamlar saqlanadi (o'zbekcha
    mavzular ko'p hollarda shu alifbolarda bo'ladi).
    """
    cleaned = re.sub(r"[^\w\s-]", "", topic, flags=re.UNICODE).strip()
    cleaned = re.sub(r"[\s]+", "_", cleaned)
    cleaned = cleaned[:80]  # juda uzun mavzu nomini cheklash
    return cleaned or "prezentatsiya"


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=300)
    slide_count: int = Field(..., ge=3, le=20)  # 20+ = Gemini free tier/vaqt uchun xavfli
    output_format: str = Field("pptx", pattern="^(pptx|pdf)$")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate(req: GenerateRequest):
    file_id = uuid.uuid4().hex
    ext = req.output_format
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.{ext}")

    try:
        generate_presentation(req.topic, req.slide_count, output_path, output_format=ext)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generatsiya xatoligi: {e}")

    display_name = f"{_slugify_filename(req.topic)}.{ext}"
    _FILENAME_REGISTRY[file_id] = (display_name, ext)

    return {"file_id": file_id, "filename": display_name}


@app.get("/download/{file_id}")
def download(file_id: str):
    filename, ext = _FILENAME_REGISTRY.get(file_id, ("presentation.pptx", "pptx"))
    path = os.path.join(OUTPUT_DIR, f"{file_id}.{ext}")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Fayl topilmadi")
    return FileResponse(
        path,
        media_type=_MEDIA_TYPES.get(ext, "application/octet-stream"),
        filename=filename,
    )
