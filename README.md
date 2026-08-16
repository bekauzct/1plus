# BIR+ Website — Stage 1

BIR+ uchun ishlaydigan premium frontend prototype.

## Ishga tushirish

Bu loyiha build toolsiz yozilgan:

1. ZIP faylni oching.
2. `index.html` faylini browserda oching.
3. Yoki VS Code Live Server orqali ishga tushiring.

## Tuzilishi

- `index.html` — semantic page structure
- `style.css` — responsive premium UI
- `script.js` — interactions, filters, mobile menu, form demo, UI sound
- `assets/bir-plus-logo.jpg` — foydalanuvchi bergan BIR+ logo, o‘zgartirilmagan

## Hozir ishlaydi

- Responsive desktop/tablet/mobile layout
- BIR+ logo bilan branded UI
- Xizmatlar
- Portfolio demo + category filter
- Jarayon
- Buyurtma formasi
- Mobile navigation
- Scroll reveal
- Hover/tilt interaction
- Optional UI sound
- Accessibility basics
- Reduced-motion support
- No fake backend/payment success

## Keyingi bosqichga tayyor

### 3D
`hero-visual` konteynerini Three.js/WebGL scene bilan almashtirish yoki kengaytirish mumkin. WebGL browser canvas ichida GPU-accelerated 3D rendering uchun mos. 

### Sound
Hozir UI tovushlari Web Audio API orqali generated. Keyinchalik real audio fayllar, effects, analyser yoki spatial/3D audio qo‘shish mumkin. Web Audio API audio effects va spatialization/PannerNode imkoniyatlarini beradi.

## Muhim

Portfolio rasmlari hozircha demo UI graphics. Real portfolio ishlarini keyinchalik almashtiring.

Order form backendga ulanmagan. Form submit qilganda sayt muvaffaqiyatli buyurtma yuborildi deb da’vo qilmaydi.

## Keyingi production bosqichi

1. Real portfolio assets
2. Real Telegram/CRM integration
3. Backend/API
4. Product catalog + dynamic pricing
5. File upload
6. Order tracking
7. Admin panel
8. Optional Three.js/WebGL 3D layer
9. Real sound design + spatial audio
