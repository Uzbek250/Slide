"""
Gemini orqali slayd strukturasini (JSON) generatsiya qilish.

MUHIM: Bu qism faqat MATN va STRUKTURA yaratadi.
Dizayn (ranglar, layout, shrift) HTML shablonlarda alohida belgilanadi.
"""
import json
import os
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.1-flash-lite"  # foydalanuvchi tanlovi bo'yicha

SYSTEM_PROMPT = """Sen professional prezentatsiya kontenti yaratuvchi yordamchisan.
Foydalanuvchi bergan mavzu va slayd soniga qarab, har bir slayd uchun struktura yaratasan.

Qat'iy qoidalar:
1. Faqat JSON qaytar, boshqa hech qanday matn yozma (preambula yo'q, izoh yo'q, markdown fence yo'q)
2. Birinchi slayd har doim "title" turida bo'lishi kerak (sarlavha + subtitle)
3. Oxirgi slayd "closing" turida bo'lishi mumkin (xulosa/rahmat)
4. Har bir kontent slaydi uchun mos layout tanlang: "bullets" (ro'yxat), "two_column" (ikki ustun,
   taqqoslash uchun), "big_stat" (bitta katta raqam/fakt), "quote" (iqtibos), "image_text"
   (rasm tavsifi + matn)
5. Har bir bullet punkt qisqa va aniq bo'lsin (maksimal 12-15 so'z)
6. Matn tili: foydalanuvchi mavzuni qaysi tilda yozgan bo'lsa, o'sha tilda javob ber
7. "image_prompt" faqat image_text yoki title layoutlarida bering — u yerda mos rasm tasviri uchun
   qisqa ingliz tilida prompt yozing (masalan: "abstract blue gradient representing technology")

JSON formati:
{
  "title": "Prezentatsiya nomi",
  "theme": "minimal" | "corporate" | "gradient_dark" | "warm",
  "slides": [
    {
      "type": "title",
      "heading": "...",
      "subheading": "...",
      "image_prompt": "..."
    },
    {
      "type": "bullets",
      "heading": "...",
      "bullets": ["...", "...", "..."]
    },
    {
      "type": "two_column",
      "heading": "...",
      "left_title": "...",
      "left_points": ["...", "..."],
      "right_title": "...",
      "right_points": ["...", "..."]
    },
    {
      "type": "big_stat",
      "heading": "...",
      "stat": "87%",
      "stat_label": "..."
    },
    {
      "type": "quote",
      "quote_text": "...",
      "quote_author": "..."
    },
    {
      "type": "closing",
      "heading": "Rahmat!",
      "subheading": "..."
    }
  ]
}
"""


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY muhit o'zgaruvchisi topilmadi")
    return genai.Client(api_key=api_key)


def generate_deck_structure(topic: str, slide_count: int) -> dict:
    """
    Mavzu va slayd soni asosida to'liq JSON strukturani qaytaradi.
    """
    client = get_client()

    user_prompt = (
        f"Mavzu: {topic}\n"
        f"Jami slayd soni: {slide_count} ta (title va closing slaydlari shu songa kiradi)\n\n"
        f"Yuqoridagi qoidalarga qat'iy amal qilib, {slide_count} ta slaydlik JSON struktura yarat."
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            response_mime_type="application/json",
        ),
    )

    raw_text = response.text.strip()
    # Ehtiyot chorasi: ba'zan model baribir ```json fence bilan qaytarishi mumkin
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    data = json.loads(raw_text)

    # Slayd sonini talab qilingan songa moslashtirish (model ba'zan ±1 xato qilishi mumkin)
    slides = data.get("slides", [])
    if len(slides) > slide_count:
        data["slides"] = slides[:slide_count]

    return data
