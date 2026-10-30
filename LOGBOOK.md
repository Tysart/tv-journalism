# Флагман «Тележурналистика»

- **ID:** tv-journalism-course
- **Статус:** Готов к спуску на воду (Готовность 95%)
- **Бейдж:** Готовый продукт
- **Цвет:** #3b82f6
- **Маршрут монетизации:** Нарезка сочных историй из 31 урока мамы ➔ Reels/Shorts ➔ Телеграм-канал ➔ Продажа курса

## Текущий статус
Полностью срендерен стартовый пакет из всех 7 вирусных вертикальных клипов (Shorts/Reels/VK Клипы) в 1080×1920 по эталонному конвейеру v4 (официальный 3D LUT Sony S-Log3.Cine -> Rec.709, взрывные Cold Open хуки с плашкой ОСТРЫЙ МОМЕНТ, 2-секундная анимированная ТВ-перебивка со сглаженным звуком и покадровая склейка по тишине).

## Узкое горлышко (почему нет денег)
7 готовых клипов ещё не выложены на YouTube/VK и не собран конверсионный лендинг + бот с кнопкой оплаты ЮKassa.

## Сделано
- [x] 31 аудиоурок оцифрован и полностью транскрибирован через Whisper. Есть программа и брендбук.
- [x] Создана чистая рабочая папка `/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course`, проведён аудит бэкапа и ТЗ вырезки.
- [x] Разработано вирусное посекундное ТЗ (`ТЗ_ВИРУСНЫЕ_КЛИПЫ_И_YOUTUBE.md`) для 7 стартовых клипов и упаковки YouTube/VK.
- [x] Сгенерирован новый визуальный Брендбук 2.0 (`assets/brandbook/`).
- [x] Автоматически смонтированы все 7 стартовых вирусных клипов (`shorts/01_*.mp4` .. `07_*.mp4`) в эталонном качестве v4.

## Следующий шаг (фокус)
- [ ] Подготовить файл с готовыми кликбейтными заголовками, описаниями и хештегами для публикации всех 7 клипов на YouTube Shorts и VK Клипы, а затем собрать лендинг + бот с кнопкой оплаты ЮKassa.

## 2026-10-23 — Course Landing Page & Delivery Architecture
- **Course Delivery Roadmap:** Designed the 3-tier production and distribution pipeline for the 31 video lessons (10 core lessons + 7 "Будни журналиста" stories) via private Telegram channel + interactive Telegram Bot & Web player.
- **Landing Page Launched:** Created `/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course/landing/`:
  - `index.html`: Complete responsive HTML5 landing page with TV broadcast aesthetic (Dark Sapphire & Gold, REC badges, Viewfinder HUD).
  - `styles.css`: Custom broadcast design system, responsive grid, gold glow effects, interactive accordions.
  - `app.js`: Module & FAQ accordions, mobile drawer navigation, interactive payment modal with YooKassa / Telegram Bot integration.
  - Visuals integrated: Authentic portrait of Irina Vitalyevna, avatar badges, and 7 story teasers.

## 2026-10-23 — Published to GitHub & Live on GitHub Pages
- **GitHub Repository Created:** https://github.com/Tysart/tv-journalism
- **Live Landing Page Published (GitHub Pages):** https://tysart.github.io/tv-journalism/
- **Documentation & Syllabus in README:** Formatted for easy reading and review by Irina Vitalyevna.

## 2026-10-23 — Mobile Polish & Course Lesson 00 Render Started
- **Mobile Overhaul:** Fully responsive header, clamp-based titles, zero horizontal scroll, iOS input zoom fixed (16px font-size).
- **Free vs. Paid Funnel Strategy Approved:** 16:9 full stories («Будни журналиста») will be published for free on YouTube & VK to build trust and audience reach, while the structured 10-lesson course remains the paid flagship product.
- **Course Video Standard Built:** 16:9 Full HD, Sony S-Log3 Type A 3D LUT, Lower Third graphic overlay («Ирина Тыщенко — тележурналист, 25+ лет в эфире»), 2-second broadcast bumpers, and multicam punch-ins from 4K FX30 footage.
- **Pilot Lesson 00 Launched:** Started batch rendering of `00_intro_greeting_lesson.mp4` (~1.5 min clean cut).

## 2026-10-23 — Pilot Lesson 00 Render Complete
- **File Rendered:** `/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course/lessons/00_intro_greeting_lesson.mp4` (2:22 min, 88.1 MB, 1080p Full HD).
- **Production Pipeline Proven:**
  - Applied Sony S-Log3 Type A 3D LUT (perfect warm contrast & skin tone).
  - Cleaned audio with EBU R128 (-16 LUFS) normalization.
  - Added Lower Third TV overlay («ИРИНА ТЫЩЕНКО — Тележурналист • Стаж 25+ лет • Автор курса»).
  - Seamless multicam switch between Wide shot and 1.25x Close-up crop from 4K FX30 source.
  - 2.0-second broadcast intro and outro bumpers with smooth synth audio chimes.

## 2026-10-30 — Dual-Camera Multicam Pipeline, AI Video Editing Bible & Lesson 00 + Lesson 01 Master Renders
- **SSD Dual-Camera Mapping Completed:** Matched all 24 graded close-up timelines (`/Volumes/ArtemTys/В работе/Курс/Крупный/Timeline *.mp4`) to the 31 graded wide-angle files (`Общий/C1253..C1283.mp4`) with 0.0000s audio sync lag.
- **Created Master SOP (`AI_VIDEO_EDITING_BIBLE.md`):** Documented the complete end-to-end architecture for any AI model (Flash/Argon/Claude/GPT) and future podcast-to-Reels SaaS packaging:
  - 50ms RMS audio silence/speech boundary detector.
  - 21x realtime single-pass multicam switching via `-hwaccel videotoolbox` and `[wide][close]overlay=enable='...'`.
  - Safe-zone coordinates for 9:16 Reels (`Y=340..1250` face protection zone) and 16:9 Course Infographics (`X=70..865` left split-screen zone).
  - In-memory PNG loop filter (`loop=loop=-1:size=1:start=0`) + `eof_action=pass` to prevent infinite loops and speed up multi-card overlays.
- **Rendered Clean Multicam & Full Broadcast Graphics Masters:**
  - `lessons/00_intro_greeting_multicam.mp4` (1:25.8 clean 2-camera cut) & `lessons/00_intro_greeting_lesson.mp4` (1:29.8 with bumpers + lower third + 2 infographic cards).
  - `lessons/01_lesson_1_multicam.mp4` (14:48.5 clean 2-camera cut, 27 switches) & `lessons/01_lesson_1_full.mp4` (14:52.5 with bumpers + lower third + 10 educational infographic cards).
