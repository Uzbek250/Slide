"""
FastAPI backend. Telegram bot shu servisga HTTP orqali murojaat qiladi.
Bot va backend ni ataylab ajratdik: agar kelajakda web frontend yoki
boshqa mijoz (masalan Flutter ilova) qo'shilsa, backend o'zgarmaydi.
"""
import os
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.core.pipeline import generate_presentation

app = FastAPI(title="Slide Generator API")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

OUTPUT_DIR = "/tmp/slide_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=300)
    slide_count: int = Field(..., ge=3, le=20)  # 20+ = Gemini free tier/vaqt uchun xavfli


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate(req: GenerateRequest):
    file_id = uuid.uuid4().hex
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.pptx")

    try:
        generate_presentation(req.topic, req.slide_count, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generatsiya xatoligi: {e}")

    return {"file_id": file_id}


@app.get("/download/{file_id}")
def download(file_id: str):
    path = os.path.join(OUTPUT_DIR, f"{file_id}.pptx")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Fayl topilmadi")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="presentation.pptx",
    )
