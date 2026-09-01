# Slide Generator

Veb-ilova: mavzu + slaydlar soni → tayyor `.pptx` yoki `.pdf` fayl.
Gemini API kontent (matn/struktura) yaratadi, Playwright + HTML/CSS chiroyli
slayd dizaynini renderlaydi, python-pptx/Pillow ularni bitta faylga yig'adi.

Ilova ataylab **faqat matnga** asoslangan — rasm yoki fotosurat ishlatilmaydi.
Vizual boylik layout xilma-xilligi, ikonlar (emoji), raqamlar, tipografiya
va rang orqali beriladi.

## Arxitektura

```
Brauzer (index.html — mavzu, slayd soni, fayl turi, dizayn tanlash formasi)
        │  POST /generate
        ▼
FastAPI backend (Docker, Chromium bilan)
        │
        ├─ Gemini API → slayd JSON struktura (matn)
        ├─ Jinja2 + HTML shablon → har slayd uchun HTML
        ├─ Playwright → har HTML'ni JPEG screenshot
        └─ python-pptx yoki Pillow → JPEG'larni .pptx/.pdf ga yig'ish
```

Bitta servis — alohida bot yoki worker kerak emas.

## Slayd shablonlari

`app/templates/` papkasida 10 ta layout turi:
- `title` — sarlavha, tag'lar
- `bullets` — raqamlangan ro'yxat (title + detail)
- `two_column` — ikki ustunli taqqoslash
- `timeline` — ketma-ket bosqichlar
- `icon_grid` — 4 ta ikonli karta
- `stats_grid` — raqamli statistika
- `big_stat` — bitta katta raqam + majburiy kontekst matn
- `quote` — iqtibos + majburiy kontekst matn
- `bar_chart` — ustunli diagramma (faqat mavzuga mos taqqoslanadigan sonli
  ma'lumot bo'lsa ishlatiladi, majburiy emas)
- `table` — ustun/qatorli jadval (faqat mavzuga mos tuzilgan ma'lumot
  bo'lsa ishlatiladi, majburiy emas)
- `closing` — yakuniy slayd

4 ta tema: `minimal`, `corporate`, `warm`, `forest` — `_base.html`da
CSS o'zgaruvchilar orqali boshqariladi. **Barcha temalar oq fonli** —
printerda siyoh tejash uchun ataylab shunday qilingan, faqat urg'u rangi
(chiziq, sarlavha, teg ranglari) farqlanadi. Dizaynni Gemini emas,
foydalanuvchi formadan bevosita tanlaydi.

**Matn zichligi:** promptda har bir bullet/detail matni kamida 10-18 so'z
bo'lishi, `big_stat` va `quote` kabi "kam matnli" layoutlarda qo'shimcha
kontekst (kamida 20-30 so'z) berilishi qat'iy talab qilinadi — maqsad
hech qanday slayd bo'sh yoki yuzaki ko'rinmasligi. Generatsiyadan keyin
har bir slayd avtomatik tekshiriladi (`_ensure_slide_quality`) — juda
qisqa yoki bo'sh chiqqan slaydlar Gemini'dan qayta so'raladi.

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
chiqishi mumkin, ayniqsa bir nechta so'rov bir vaqtda kelsa. Hozircha
faqat bitta foydalanuvchi (loyiha egasi) uchun ishlatilyapti, shu sababli
rate limiting/queue hali qo'shilmagan. Kelajakda 4 CPU / 8GB RAM'li
Contabo VPS'ga ko'chirish rejalashtirilgan.

## Keyingi qadamlar (hali qilinmagan)

- [ ] Rate limiting — bir foydalanuvchi ketma-ket ko'p so'rov yubormasin
- [ ] Ko'p bir vaqtdagi so'rovlar uchun navbat (queue) tizimi
- [ ] Har bir slaydda grammatika/faktik xato tekshiruvi (hozir faqat
      so'z soni tekshiriladi)
- [ ] Fayllarni doimiy saqlash (hozir `/tmp` — server qayta ishga
      tushsa eski fayllar yo'qoladi)

