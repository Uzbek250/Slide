# Slide Generator

Veb-ilova: mavzu + slaydlar soni → tayyor `.pptx` fayl.
Gemini API kontent (matn/struktura) yaratadi, Wikimedia Commons'dan mavzuga
mos rasmlar qidiriladi, Playwright + HTML/CSS chiroyli slayd dizaynini
renderlaydi, python-pptx ularni bitta faylga yig'adi.

## Arxitektura

```
Brauzer (index.html — mavzu kiritish formasi)
        │  POST /generate
        ▼
FastAPI backend (Docker, Chromium bilan)
        │
        ├─ Gemini API → slayd JSON struktura (matn + rasm so'rovlari)
        ├─ Wikimedia Commons API → mavzuga mos rasm qidirish
        ├─ Jinja2 + HTML shablon → har slayd uchun HTML
        ├─ Playwright → har HTML'ni PNG screenshot
        └─ python-pptx → PNG'larni .pptx ga yig'ish
```

Bitta servis — alohida bot yoki worker kerak emas.

## Slayd shablonlari

`app/templates/` papkasida 9 ta layout turi:
- `title` — sarlavha, ixtiyoriy fon rasm, tag'lar
- `bullets` — raqamlangan ro'yxat (title + detail)
- `two_column` — ikki ustunli taqqoslash
- `timeline` — ketma-ket bosqichlar
- `icon_grid` — 4 ta ikonli karta
- `stats_grid` — raqamli statistika
- `big_stat` — bitta katta raqam
- `quote` — iqtibos
- `image_text` — rasm + matn yonma-yon
- `closing` — yakuniy slayd

4 ta tema: `minimal`, `corporate`, `gradient_dark`, `warm` — `_base.html`da
CSS o'zgaruvchilar orqali boshqariladi.

## Rasm qidirish (Wikimedia Commons)

`app/core/image_search.py` — API key kerak emas, anonim so'rov orqali
ishlaydi. Gemini har bir `image_text` yoki `title` slaydi uchun ingliz
tilida aniq qidiruv so'zi (`image_query`) generatsiya qiladi, so'ng shu
so'z bo'yicha Commons'dan eng mos rasm tanlanadi (o'lcham, format,
aspekt nisbati bo'yicha filtrlanadi).

**Xavfsizlik tarmog'i:** agar rasm topilmasa yoki tarmoq xatosi bo'lsa,
`image_text` slaydi avtomatik ravishda `bullets` turiga aylanadi — hech
qachon bo'sh yoki buzilgan slayd chiqmaydi.

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
- [ ] Pexels/Unsplash integratsiyasi — Wikimedia'da topilmagan
      (masalan biznes/lifestyle) mavzular uchun qo'shimcha manba

## O'zgarishlar tarixi

**2026-08:**
- Fayl hajmi optimallashtirildi: slaydlar endi PNG o'rniga JPEG
  (quality=90) sifatida screenshot qilinadi — o'rtacha 10x kichikroq
  fayl (10 slaydli deck ~19MB'dan ~2MB'ga tushdi), matn/gradient
  sifatida ko'zga sezilarli farq yo'q
- `bullets`, `timeline`, `two_column` shablonlaridagi vertikal
  markazlashtirish xatosi tuzatildi — 3-4 punktli slaydlarda kontent
  endi yuqoridan boshlanadi, tepa/pastda keraksiz bo'sh joy qolmaydi
  (`stats_grid`, `icon_grid`, `image_text`, `title`, `quote`,
  `big_stat`, `closing` — bularda markazlashtirish qasddan qoldirilgan,
  chunki bu layoutlar uchun to'g'ri ko'rinish)
