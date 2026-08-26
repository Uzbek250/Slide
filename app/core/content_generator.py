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

Bu ilova FAQAT MATNGA asoslangan — rasm, fotosurat yoki tashqi vizual elementlar YO'Q va
BO'LMAYDI. Vizual boylik faqat: layout xilma-xilligi, ikonlar (emoji), raqamlar, tipografiya
va rang orqali beriladi. Shuning uchun matn MAZMUNI va ZICHLIGI eng muhim mezon — har bir
slayd o'zi mustaqil holda to'liq, ma'lumotga boy va ishonchli bo'lishi shart.

Qat'iy qoidalar:
1. Faqat JSON qaytar, boshqa hech qanday matn yozma (preambula yo'q, izoh yo'q, markdown fence yo'q)
2. Birinchi slayd har doim "title" turida bo'lishi kerak
3. Oxirgi slayd "closing" yoki "stats_grid" turida bo'lishi mumkin (xulosa)
4. Har bir kontent slaydi uchun MOS layout tanlang va turlarni ARALASHTIRIB ishlating — bir xil
   turni ketma-ket 2 martadan ortiq ishlatmang:
   - "bullets": ro'yxat (3-5 punkt), har biri title+detail bilan — ENG KO'P ishlatiladigan tur
   - "two_column": ikki tushuncha/guruhni taqqoslash, har ustunda 2-3 punkt (title+detail)
   - "timeline": ketma-ket bosqichlar/jarayon/tasniflash (3-4 bosqich, har biri title+detail)
   - "icon_grid": 4 ta parallel jihat/xususiyat, har biri emoji ikon + title + detail bilan
   - "stats_grid": 3-4 ta raqam/fakt (masalan o'lcham, son, foiz, muddat), har birida label
     albatta to'liq tushuntiruvchi jumla bo'lsin (nafaqat 2-3 so'z)
   - "big_stat": bitta juda muhim yakka raqam/fakt — LEKIN "context" maydoni MAJBURIY va
     kamida 20-30 so'zdan iborat bo'lishi kerak (bu raqam nima uchun muhimligini tushuntiradi).
     Prezentatsiyada 1 martadan ko'p ishlatmang.
   - "quote": iqtibos yoki muhim tezis — LEKIN "context" maydoni MAJBURIY va kamida 20-30
     so'zdan iborat bo'lishi kerak (iqtibosning ahamiyati/kontekstini tushuntiradi).
     Prezentatsiyada 1 martadan ko'p ishlatmang.
5. HAR BIR "detail" yoki bullet matni KAMIDA 10-18 so'zdan iborat bo'lsin — bitta so'zli yoki
   juda qisqa javoblar QATIYAN TAQIQLANADI. Slayd hech qachon "kam matnli" yoki bo'sh
   ko'rinmasligi kerak. Har doim aniq, faktik, raqamli, ma'lumotga boy yozing — umumiy
   gaplardan ("bu muhim", "bu foydali") qoching, o'rniga sabab, mexanizm yoki misol bering.
6. "bullets", "left_points", "right_points", "steps", "items" massividagi har bir element
   {"title": "...", "detail": "..."} obyekt bo'lsin (oddiy satr emas) — title qisqa (3-6 so'z),
   detail to'liq tushuntiruvchi jumla (10-18 so'z)
7. Matn tili: foydalanuvchi mavzuni qaysi tilda yozgan bo'lsa, o'sha tilda javob ber
8. "tags" (title slaydida) — mavzuga oid 2-3 ta qisqa kalit so'z/kategoriya
9. Har bir slaydning "heading"i mavzuga xos va aniq bo'lsin — umumiy sarlavhalardan
   ("Kirish", "Xulosa", "Qo'shimcha ma'lumot") imkon qadar qoching, o'rniga slayd
   mazmunini aniq ifodalovchi sarlavha yozing

JSON formati:
{
  "title": "Prezentatsiya nomi",
  "theme": "minimal" | "corporate" | "gradient_dark" | "warm",
  "slides": [
    {
      "type": "title",
      "heading": "...",
      "subheading": "...",
      "tags": ["...", "...", "..."]
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
      "stat_label": "...",
      "context": "... (kamida 20-30 so'z, majburiy)"
    },
    {
      "type": "quote",
      "quote_text": "...",
      "quote_author": "...",
      "context": "... (kamida 20-30 so'z, majburiy)"
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


def _parse_json_lenient(raw_text: str) -> dict:
    """
    Gemini javobini JSON sifatida o'qiydi. Ba'zan model to'g'ri JSON'dan keyin
    qo'shimcha matn (masalan yana bir bo'sh JSON yoki izoh) qo'shib yuborishi
    mumkin — bu "Extra data" xatosiga olib keladi. json.JSONDecoder.raw_decode
    faqat birinchi to'liq obyektni o'qib, qoldiqni e'tiborsiz qoldiradi.

    Agar JSON o'rtada kesilgan bo'lsa (token limiti tufayli), aniq xato beradi.
    """
    decoder = json.JSONDecoder()
    try:
        obj, _end_index = decoder.raw_decode(raw_text)
        return obj
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Gemini javobini JSON sifatida o'qib bo'lmadi — javob kesilgan yoki "
            f"noto'g'ri formatda bo'lishi mumkin (slaydlar sonini kamaytirib ko'ring). "
            f"Texnik tafsilot: {e}"
        ) from e


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
            max_output_tokens=16384,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )

    raw_text = (response.text or "").strip()
    if not raw_text:
        finish_reason = None
        try:
            finish_reason = response.candidates[0].finish_reason
        except (AttributeError, IndexError, TypeError):
            pass
        raise RuntimeError(
            "Gemini bo'sh javob qaytardi (ehtimol token limiti yoki xavfsizlik filtri "
            f"tufayli javob kesilgan bo'lishi mumkin). finish_reason={finish_reason}"
        )

    # Ehtiyot chorasi: ba'zan model baribir ```json fence bilan qaytarishi mumkin
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    data = _parse_json_lenient(raw_text)

    # Slayd sonini talab qilingan songa moslashtirish (model ba'zan ±1 xato qilishi mumkin)
    slides = data.get("slides", [])
    if len(slides) > slide_count:
        data["slides"] = slides[:slide_count]

    return data
