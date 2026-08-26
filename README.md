# Slide Generator

Veb-ilova: mavzu + slaydlar soni → tayyor `.pptx` fayl.
Gemini API kontent (matn/struktura) yaratadi, Playwright + HTML/CSS chiroyli
slayd dizaynini renderlaydi, python-pptx ularni bitta faylga yig'adi.

Ilova ataylab **faqat matnga** asoslangan — rasm yoki fotosurat ishlatilmaydi.
Vizual boylik layout xilma-xilligi, ikonlar (emoji), raqamlar, tipografiya
va rang orqali beriladi.

## Arxitektura

```
Brauzer (index.html — mavzu kiritish formasi)
        │  POST /generate
        ▼
FastAPI backend (Docker, Chromium bilan)
        │
        ├─ Gemini API → slayd JSON struktura (matn)
        ├─ Jinja2 + HTML shablon → har slayd uchun HTML
        ├─ Playwright → har HTML'ni JPEG screenshot
        └─ python-pptx → JPEG'larni .pptx ga yig'ish
```

Bitta servis — alohida bot yoki worker kerak emas.

## Slayd shablonlari

`app/templates/` papkasida 8 ta layout turi:
- `title` — sarlavha, tag'lar
- `bullets` — raqamlangan ro'yxat (title + detail)
- `two_column` — ikki ustunli taqqoslash
- `timeline` — ketma-ket bosqichlar
- `icon_grid` — 4 ta ikonli karta
- `stats_grid` — raqamli statistika
- `big_stat` — bitta katta raqam + majburiy kontekst matn
- `quote` — iqtibos + majburiy kontekst matn
- `closing` — yakuniy slayd

4 ta tema: `minimal`, `corporate`, `gradient_dark`, `warm` — `_base.html`da
CSS o'zgaruvchilar orqali boshqariladi.

**Matn zichligi:** promptda har bir bullet/detail matni kamida 10-18 so'z
bo'lishi, `big_stat` va `quote` kabi "kam matnli" layoutlarda qo'shimcha
kontekst (kamida 20-30 so'z) berilishi qat'iy talab qilinadi — maqsad
hech qanday slayd bo'sh yoki yuzaki ko'rinmasligi.

## Lokal ishga tushirish

```bash
# 1. Dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Muhit o'zgaruvchisi
export GEMINI_API_KEY="sizning_kalitingiz"

# 3. Ishga tushirish
uvicorn app.main:app --reload --port 8000
```

Brauzerda `http://localhost:8000` oching.

Gemini'siz, faqat render pipeline'ni sinash uchun:
```bash
python test_pipeline.py
```
Bu qo'lda yozilgan JSON bilan to'liq render+pptx oqimini ishga tushiradi,
natija `test_output/` papkasida chiqadi.

## Render.com'ga deploy qilish

1. Kodni GitHub repo'ga yuklang
2. Render dashboardida **New → Web Service** tanlang, repo'ni ulang
   (yoki `render.yaml` orqali **New → Blueprint**)
3. **Runtime**: Docker, **Dockerfile Path**: `./Dockerfile`
4. Environment Variables qismiga `GEMINI_API_KEY` qo'shing
5. Deploy qiling

**MUHIM — xotira haqida:** Chromium'ga kamida ~1GB RAM tavsiya etiladi.
Render'ning free tarifi (512MB) bilan ba'zan "out of memory" xatosi
chiqishi mumkin, ayniqsa bir nechta so'rov bir vaqtda kelsa. Barqaror
ishlashi uchun `Starter` yoki undan yuqori tarifga o'tish tavsiya etiladi.

## Keyingi qadamlar (hali qilinmagan)

- [ ] Rate limiting — bir foydalanuvchi ketma-ket ko'p so'rov yubormasin
- [ ] Ko'p bir vaqtdagi so'rovlar uchun navbat (queue) tizimi
- [ ] Gemini javobi sifatini yanada nazorat qilish (masalan har bir
      detail matnining so'z sonini serverda tekshirib, juda qisqa
      bo'lsa qayta so'rash)
