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

**2026-08 (5):**
- KRITIK TUZATISH: ba'zi slaydlarda rasm o'rniga qora to'rtburchak
  chiqib, HATTO MATN HAM YO'QOLIB QOLAYOTGAN muammo tuzatildi. Sabab:
  `networkidle` faqat tarmoq so'rovlari tugashini kutadi, rasmning
  ekranga chizilishini (decode/paint) kafolatlamaydi - ba'zan rasm
  hali chizilmagan holatda screenshot olinardi. Yechim: har bir
  `<img>` uchun JS orqali `decode()` tugashini kutish (max 8s/rasm) +
  agar networkidle 20s ichida tugamasa `load` holatiga fallback -
  eng yomon holatda ham matn hech qachon yo'qolmaydi, faqat rasm
  bo'sh qoladi

**2026-08 (4):**
- Rasm topilmayotgan muammoni diagnostika qilish uchun to'liq logging
  qo'shildi (`image_search:` va `renderer:` prefikslari bilan Render
  loglarida ko'rinadi) — sabab hozirgacha noaniq edi, chunki xatolar
  jimgina yutilardi
- `main.py`da logging INFO darajasiga sozlandi (standart WARNING edi,
  ya'ni logger.info() chaqiruvlari hech qachon ko'rinmasdi)
- Wikimedia so'rovidan `origin=*` parametri olib tashlandi (bu faqat
  brauzer-JS CORS so'rovlari uchun kerak, server-tomonli so'rovda
  keraksiz/potentsial muammoli)
- Openverse (api.openverse.org) ikkinchi qatlam zaxira manba sifatida
  qo'shildi — Wikimedia bo'sh/xato qaytarsa avtomatik sinaladi.
  Ikkalasi ham API key talab qilmaydi
- KEYINGI QADAM: Render loglarida `image_search[wikimedia]:` yoki
  `image_search[openverse]:` satrlarini tekshirib, aniq status
  kodini (403/timeout/bo'sh natija) ko'rish kerak — agar ikkalasi
  ham doimiy 403 bersa, bu Render'ning IP diapazoni bloklangani
  degani bo'lishi mumkin va boshqa yechim (masalan tashqi proxy
  yoki kalitli API) kerak bo'ladi

**2026-08 (3):**
- Fayl nomi endi mavzudan yasaladi (`presentation.pptx` o'rniga masalan
  `Yurak-qon_tomir_tizimi.pptx`) — `/generate` javobida `filename` maydoni
  qaytariladi, `/download` shu nomni `Content-Disposition`da ishlatadi
- Title slaydda rasm ("image_query") ko'pincha chiqmayotgan muammo
  tuzatildi — Gemini promptida bu maydon "ixtiyoriy" emas, "deyarli har
  doim kerak" deb belgilandi, va mavhum (iqtisodiy/ijtimoiy) mavzular
  uchun ham mos vizual so'rov topish yo'riqnomasi qo'shildi (masalan
  "O'zbekiston iqtisodiyoti" -> "Tashkent city skyline")
- MUHIM: fayl nomlari xotirada (`_FILENAME_REGISTRY` dict) saqlanadi —
  server qayta ishga tushsa (deploy/qayta yuklanish), eski file_id'lar
  uchun nom "presentation.pptx"ga qaytadi. Kelajakda buni fayl nomining
  o'ziga yoki bazaga ko'chirish kerak bo'lishi mumkin

**2026-08 (2):**
- Detail/subtitle matn shrift hajmi ko'tarildi (21-27px → 27-32px) —
  `bullets`, `two_column`, `timeline`, `icon_grid`, `image_text`
  shablonlarida ikkinchi darajali matn (izoh qatorlari) 1920px
  canvas'ga nisbatan juda kichik edi, uzoqdan yoki kichik ekranda
  o'qishni qiyinlashtirardi

**2026-08 (1):**
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
