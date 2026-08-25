# Slide Generator Bot

Telegram bot: mavzu + slayd soni → tayyor `.pptx` fayl.
Gemini API kontent (matn/struktura) yaratadi, Playwright + HTML/CSS chiroyli
slayd dizaynini renderlaydi, python-pptx ularni bitta faylga yig'adi.

## Arxitektura

```
Telegram bot (yengil, doim ishlaydi)
        │  HTTP
        ▼
FastAPI backend (Docker, Chromium bilan)
        │
        ├─ Gemini API → slayd JSON struktura
        ├─ Jinja2 + HTML shablon → har slayd uchun HTML
        ├─ Playwright → har HTML'ni PNG screenshot
        └─ python-pptx → PNG'larni .pptx ga yig'ish
```

Bot va backend ataylab ikkita alohida servis: bot yengil (Chromium yo'q,
doim tekin tarifda ishlashi mumkin), backend og'ir (Chromium uchun
ko'proq RAM kerak).

## Loyihaning holati (nima tayyor, nima yo'q)

**Tayyor va sinovdan o'tgan:**
- HTML shablonlar (6 ta layout turi: title, bullets, two_column, big_stat, quote, closing)
- 4 ta tayyor tema (minimal, corporate, gradient_dark, warm)
- Render pipeline (HTML → PNG → PPTX) — real skrinshotlar bilan sinaldi, natija yuqorida ko'rsatilgan
- FastAPI backend skeleti

**Sinalmagan (API kalitingiz kerak):**
- `content_generator.py` — Gemini chaqiruvi kodi yozilgan, lekin haqiqiy
  `GEMINI_API_KEY` bilan hali ishga tushirilmagan. Birinchi ishga tushirishda
  Gemini qaytargan JSON formatini tekshirib, kerak bo'lsa prompt'ni moslashtiring.
- Telegram bot — kod tayyor, lekin `TELEGRAM_BOT_TOKEN` bilan hali sinalmagan

## Lokal ishga tushirish

```bash
# 1. Dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Muhit o'zgaruvchilari
export GEMINI_API_KEY="sizning_kalitingiz"
export TELEGRAM_BOT_TOKEN="bot_father_dan_olingan_token"
export BACKEND_URL="http://localhost:8000"

# 3. Backend'ni ishga tushirish
uvicorn app.main:app --reload --port 8000

# 4. Alohida terminalda — botni ishga tushirish
python bot.py
```

Backend'ni Gemini'siz sinash uchun (faqat render pipeline):
```bash
python test_pipeline.py
```
Bu qo'lda yozilgan JSON bilan to'liq render+pptx oqimini ishga tushiradi,
natija `test_output/` papkasida chiqadi.

## Render.com'ga deploy qilish

1. Kodni GitHub repo'ga yuklang
2. Render dashboardida **New → Blueprint** tanlang, repo'ni ulang
   (`render.yaml` avtomatik ikkala servisni — backend va bot — yaratadi)
3. Backend servisida `GEMINI_API_KEY` environment variable qo'shing
4. Bot servisida `TELEGRAM_BOT_TOKEN` environment variable qo'shing
5. Deploy tugagach, Telegram'da botga `/start` yozib sinang

**MUHIM — xotira haqida:** Backend uchun `render.yaml`da `plan: starter`
qo'yilgan (free emas). Sababi: Chromium'ga kamida ~1GB RAM kerak, Render'ning
free tarifi (512MB) bilan tez-tez "out of memory" xatosi berishi mumkin.
Agar avval free tarifda sinab ko'rmoqchi bo'lsangiz, mumkin — lekin
tayyor bo'ling, ba'zan so'rov muvaffaqiyatsiz tugashi mumkin, ayniqsa
concurrent (bir vaqtdagi) so'rovlarda.

## Keyingi qadamlar (hali qilinmagan)

- [ ] Gemini bilan haqiqiy sinov, JSON formatini moslashtirish
- [ ] Telegram bot haqiqiy tokendan sinash
- [ ] Xatolik holatlari: Gemini javob bermasa / noto'g'ri JSON qaytarsa nima bo'ladi
- [ ] Rate limiting — bir foydalanuvchi ketma-ket ko'p so'rov yubormasin
- [ ] Free tier limitiga yetganda foydalanuvchiga aniq xabar (hozir generic xato chiqadi)
- [ ] Fayl hajmini kichraytirish (hozir 6 slayd ~9MB — device_scale_factor=1
      ga tushirish yoki PNG siqishni sinash mumkin)
- [ ] Ko'p bir vaqtdagi so'rovlar kelsa navbat (queue) tizimi kerak bo'lishi mumkin
