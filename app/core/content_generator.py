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
Maqsad — Gamma.app darajasidagi zich, professional, "bo'sh joy qolmaydigan" taqdimot.

Qat'iy qoidalar:
1. Faqat JSON qaytar, boshqa hech qanday matn yozma (preambula yo'q, izoh yo'q, markdown fence yo'q)
2. Birinchi slayd har doim "title" turida bo'lishi kerak
3. Oxirgi slayd "closing" yoki "stats_grid" turida bo'lishi mumkin (xulosa)
4. Har bir kontent slaydi uchun MOS layout tanlang va turlarni ARALASHTIRIB ishlating — bir xil turni
   ketma-ket 2 martadan ortiq ishlatmang:
   - "bullets": ro'yxat (3-5 punkt), har biri title+detail bilan
   - "two_column": ikki tushuncha/guruhni taqqoslash, har ustunda 2-3 punkt (title+detail)
   - "timeline": ketma-ket bosqichlar/jarayon/tasniflash (3-4 bosqich, har biri title+detail)
   - "icon_grid": 4 ta parallel jihat/xususiyat, har biri emoji ikon + title + detail bilan
   - "stats_grid": 3-4 ta raqam/fakt (masalan o'lcham, son, foiz, muddat)
   - "big_stat": bitta juda muhim yakka raqam/fakt uchun
   - "quote": iqtibos yoki muhim tezis
   - "image_text": mavzu vizual/jismoniy narsa haqida bo'lsa (anatomiya, tabiat, joy, obyekt,
     tarixiy voqea, texnika) — rasm + matn yonma-yon. Prezentatsiyada KAMIDA 1-2 marta ishlating,
     agar mavzu buni oqlasa (mavhum/abstrakt mavzularda — masalan sof falsafa, matematik
     nazariya — ishlatmasa ham bo'ladi)
5. HAR BIR "detail" yoki bullet matni KAMIDA 8-15 so'zdan iborat bo'lsin — bitta so'zli yoki juda
   qisqa javoblar taqiqlanadi, slayd bo'sh ko'rinmasligi kerak. Aniq, faktik, ma'lumotga boy yozing.
6. "bullets" massividagi har bir element {"title": "...", "detail": "..."} obyekt bo'lsin (oddiy
   satr emas) — title qisqa (3-6 so'z), detail tushuntiruvchi jumla (8-15 so'z)
7. Matn tili: foydalanuvchi mavzuni qaysi tilda yozgan bo'lsa, o'sha tilda javob ber
8. "tags" (title slaydida) — mavzuga oid 2-3 ta qisqa kalit so'z/kategoriya
9. "image_query" maydoni — FAQAT "image_text" turidagi slaydlarda, va "title" slaydida ixtiyoriy
   ravishda bering. Bu Wikimedia Commons'da qidiriladigan, ANIQ va TOR qidiruv so'zi bo'lishi
   kerak, INGLIZ TILIDA, 2-5 so'zdan iborat (masalan: "human elbow joint anatomy",
   "shoulder bones diagram", "Amazon rainforest canopy", "steam locomotive 19th century").
   Umumiy yoki mavhum so'zlar (masalan faqat "anatomy" yoki "science") ishlatmang — imkon qadar
   spetsifik yozing, chunki bu qidiruv sifatini belgilaydi.

JSON formati:
{
  "title": "Prezentatsiya nomi",
  "theme": "minimal" | "corporate" | "gradient_dark" | "warm",
  "slides": [
    {
      "type": "title",
      "heading": "...",
      "subheading": "...",
      "tags": ["...", "...", "..."],
      "image_query": "... (ixtiyoriy)"
    },
    {
      "type": "bullets",
      "heading": "...",
      "subheading": "... (ixtiyoriy qisqa kirish)",
      "bullets": [
        {"title": "...", "detail": "..."},
        {"title": "...", "detail": "..."}
      ]
    },
    {
      "type": "two_column",
      "heading": "...",
      "left_title": "...",
      "left_points": [{"title": "...", "detail": "..."}, {"title": "...", "detail": "..."}],
      "right_title": "...",
      "right_points": [{"title": "...", "detail": "..."}, {"title": "...", "detail": "..."}]
    },
    {
      "type": "timeline",
      "heading": "...",
      "subheading": "... (ixtiyoriy)",
      "steps": [
        {"title": "...", "detail": "..."},
        {"title": "...", "detail": "..."},
        {"title": "...", "detail": "..."}
      ]
    },
    {
      "type": "icon_grid",
      "heading": "...",
      "subheading": "... (ixtiyoriy)",
      "items": [
        {"icon": "emoji", "title": "...", "detail": "..."},
        {"icon": "emoji", "title": "...", "detail": "..."},
        {"icon": "emoji", "title": "...", "detail": "..."},
        {"icon": "emoji", "title": "...", "detail": "..."}
      ]
    },
    {
      "type": "stats_grid",
      "heading": "...",
      "stats": [
        {"value": "12-14 sm", "label": "..."},
        {"value": "500ml", "label": "..."}
      ]
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
      "type": "image_text",
      "heading": "...",
      "paragraph": "... (2-3 jumlali tushuntirish, kamida 25 so'z)",
      "bullets": [
        {"title": "...", "detail": "..."},
        {"title": "...", "detail": "..."}
      ],
      "image_query": "..."
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
