#!/usr/bin/env python3
"""
Конвейерная сборка Занятия 2 («История возникновения телевидения и телевизионной профессии»):
- Исходники: C1256.mp4 (Общий) и Timeline 13.mp4 (Крупный) на SSD
- Точный пофазовый синхрон: 0.0000s lag
- Вырезание технического брака на старте (0.00..24.60s)
- Вырезание дубля (723.60..733.90s, «Да что ты, все пошло не так. Артем, еще раз я начну»)
- Бесшовная маскировка склейки переключением камеры: Общий -> Крупный
- 4.0-секундная современная графическая заставка без фото (с водяным знаком «02»)
- 10 инфографических карточек (Glassmorphism, безопасная зона X=70..790)
- Финальный звук: вещательный стандарт EBU R128 (-16 LUFS)
"""
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FFMPEG = "/opt/homebrew/bin/ffmpeg"
BASE = Path("/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course")
LESSONS_DIR = BASE / "lessons"
OVERLAYS_DIR = BASE / "assets" / "course_overlays" / "lesson02"
WORKSPACE_DIR = Path("/Users/artemtysenko/Projects/Курс По Журналистике/Готовые_Уроки")

SSD_WIDE = Path("/Volumes/ArtemTys/В работе/Курс/Общий/C1256.mp4")
SSD_CLOSE = Path("/Volumes/ArtemTys/В работе/Курс/Крупный/Timeline 13.mp4")

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def fnt(bold: bool, size: int):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def render_modern_bumper(
    out_mp4: Path,
    watermark_num: str,
    badge_text: str,
    meta_text: str,
    title_lines: list,
    bullet_lines: list,
    footer_title: str,
    footer_sub: str,
    duration: float = 4.0,
    freq: float = 220.0
):
    W, H = 1920, 1080
    frame_png = out_mp4.with_suffix(".png")

    bg = Image.new("RGBA", (W, H), (6, 10, 20, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((1100, -100, 1950, 750), fill=(22, 42, 82, 95))
    gd.ellipse((-150, 400, 650, 1150), fill=(18, 32, 64, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=90))
    bg = Image.alpha_composite(bg, glow)

    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grd = ImageDraw.Draw(grid)
    for gx in range(0, W, 120):
        grd.line([(gx, 0), (gx, H)], fill=(255, 255, 255, 9), width=1)
    for gy in range(0, H, 120):
        grd.line([(0, gy), (W, gy)], fill=(255, 255, 255, 9), width=1)

    c_len = 44
    c_col = (251, 191, 36, 140)
    grd.line([(56, 56), (56 + c_len, 56)], fill=c_col, width=3)
    grd.line([(56, 56), (56, 56 + c_len)], fill=c_col, width=3)
    grd.line([(W - 56 - c_len, 56), (W - 56, 56)], fill=c_col, width=3)
    grd.line([(W - 56, 56), (W - 56, 56 + c_len)], fill=c_col, width=3)
    grd.line([(56, H - 56), (56 + c_len, H - 56)], fill=c_col, width=3)
    grd.line([(56, H - 56 - c_len), (56, H - 56)], fill=c_col, width=3)
    grd.line([(W - 56 - c_len, H - 56), (W - 56, H - 56)], fill=c_col, width=3)
    grd.line([(W - 56, H - 56 - c_len), (W - 56, H - 56)], fill=c_col, width=3)
    bg = Image.alpha_composite(bg, grid)

    px1, py1, px2, py2 = 220, 115, 1700, 965
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((px1 + 12, py1 + 16, px2 + 12, py2 + 16), radius=32, fill=(0, 0, 0, 190))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=28))
    bg = Image.alpha_composite(bg, shadow)

    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((px1, py1, px2, py2), radius=30, fill=(8, 13, 25, 248), outline=(251, 191, 36, 175), width=2)
    pd.rounded_rectangle((px1, py1 + 52, px1 + 12, py2 - 52), radius=6, fill=(251, 191, 36, 255))

    f_wm = fnt(True, 200)
    f_badge = fnt(True, 22)
    f_meta = fnt(True, 20)
    f_h1 = fnt(True, 60)
    f_sub = fnt(False, 29)
    f_author = fnt(True, 25)
    f_role = fnt(False, 22)

    pd.text((1345, 195), watermark_num, font=f_wm, fill=(255, 255, 255, 14))
    pd.rounded_rectangle((1320, 440, 1625, 660), radius=20, fill=(15, 23, 42, 180), outline=(255, 255, 255, 25), width=1)
    pd.ellipse((1355, 478, 1373, 496), fill=(225, 29, 72, 255))
    pd.text((1388, 474), "В ЭФИРЕ • 4K STUDIO", font=f_meta, fill=(248, 250, 252, 220))
    pd.line([(1355, 520), (1590, 520)], fill=(255, 255, 255, 30), width=1)
    pd.text((1355, 540), "Журналистика —\nэто состояние души", font=fnt(False, 24), fill=(251, 191, 36, 230))

    bx, by = px1 + 56, py1 + 52
    bw = int(pd.textlength(badge_text, font=f_badge)) + 62
    pd.rounded_rectangle((bx, by, bx + bw, by + 48), radius=12, fill=(225, 29, 72, 255))
    pd.ellipse((bx + 18, by + 16, bx + 34, by + 32), fill=(255, 255, 255, 255))
    pd.text((bx + 44, by + 11), badge_text, font=f_badge, fill=(255, 255, 255, 255))

    sx = bx + bw + 18
    sw = int(pd.textlength(meta_text, font=f_meta)) + 40
    pd.rounded_rectangle((sx, by, sx + sw, by + 48), radius=12, fill=(19, 28, 49, 255), outline=(251, 191, 36, 110), width=1)
    pd.text((sx + 20, by + 13), meta_text, font=f_meta, fill=(248, 250, 252, 240))

    ty = by + 84
    for line_txt, col in title_lines:
        pd.text((bx, ty), line_txt, font=f_h1, fill=col)
        ty += 74

    ty += 14
    pd.line([(bx, ty), (px1 + 1040, ty)], fill=(251, 191, 36, 95), width=2)
    ty += 28

    for bline in bullet_lines:
        pd.text((bx, ty), bline, font=f_sub, fill=(241, 245, 249, 255))
        ty += 48

    fy = py2 - 142
    pd.rounded_rectangle((bx, fy, px2 - 56, py2 - 42), radius=18, fill=(15, 23, 42, 255), outline=(255, 255, 255, 35), width=1)
    pd.text((bx + 28, fy + 18), footer_title, font=f_author, fill=(255, 255, 255, 255))
    pd.text((bx + 28, fy + 54), footer_sub, font=f_role, fill=(251, 191, 36, 245))

    final_img = Image.alpha_composite(bg, panel)
    final_img.save(frame_png)

    fade_out_st = round(duration - 0.5, 2)
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-t", str(duration), "-i", str(frame_png),
        "-f", "lavfi", "-t", str(duration), "-i", f"sine=frequency={freq}:duration={duration}",
        "-vf", f"format=yuv420p,fade=t=in:st=0:d=0.45,fade=t=out:st={fade_out_st}:d=0.50",
        "-af", f"aresample=48000,pan=stereo|c0=c0|c1=c0,volume=0.22,afade=t=in:st=0:d=0.25,afade=t=out:st=1.2:d={round(duration-1.2, 2)}",
        "-c:v", "h264_videotoolbox", "-b:v", "8000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(out_mp4)
    ]
    subprocess.run(cmd, check=True)


def create_lower_third(out_png: Path, name: str, role: str):
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    x0, y0, x1, y1 = 70, 890, 810, 1010

    shadow = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x0 + 4, y0 + 6, x1 + 4, y1 + 6], radius=18, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
    img = Image.alpha_composite(img, shadow)

    panel = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(8, 13, 25, 246), outline=(245, 180, 60, 185), width=2)
    draw.rounded_rectangle([x0, y0 + 20, x0 + 8, y1 - 20], radius=4, fill=(245, 180, 60, 255))
    draw.text((x0 + 36, y0 + 26), name, font=fnt(True, 32), fill=(255, 255, 255, 255))
    draw.text((x0 + 36, y0 + 72), role, font=fnt(False, 22), fill=(251, 191, 36, 245))

    out = Image.alpha_composite(img, panel)
    out.save(out_png)


def create_info_card(out_png: Path, badge_text: str, title_lines: list, body_lines: list, w: int = 760, h: int = 440):
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    x0, y0 = 70, 90
    x1, y1 = x0 + w, y0 + h

    shadow = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x0 + 6, y0 + 8, x1 + 6, y1 + 8], radius=22, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=16))
    img = Image.alpha_composite(img, shadow)

    panel = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=(8, 13, 25, 246), outline=(245, 180, 60, 185), width=2)
    draw.rounded_rectangle([x0, y0 + 30, x0 + 8, y1 - 30], radius=4, fill=(245, 180, 60, 255))

    f_badge = fnt(True, 19)
    f_title = fnt(True, 30)
    f_body = fnt(False, 23)

    badge_w = int(draw.textlength(badge_text, font=f_badge)) + 40
    draw.rounded_rectangle([x0 + 30, y0 + 24, x0 + 30 + badge_w, y0 + 62], radius=10, fill=(225, 29, 72, 255))
    draw.ellipse([x0 + 44, y0 + 37, x0 + 56, y0 + 49], fill=(255, 255, 255, 255))
    draw.text((x0 + 64, y0 + 31), badge_text, font=f_badge, fill=(255, 255, 255, 255))

    curr_y = y0 + 82
    for line in title_lines:
        draw.text((x0 + 30, curr_y), line, font=f_title, fill=(251, 191, 36, 255))
        curr_y += 42

    curr_y += 8
    draw.line([(x0 + 30, curr_y), (x1 - 30, curr_y)], fill=(255, 255, 255, 45), width=1)
    curr_y += 18

    for line in body_lines:
        col = (255, 255, 255, 255) if line.startswith("•") else (226, 232, 240, 245)
        draw.text((x0 + 30, curr_y), line, font=f_body, fill=col)
        curr_y += 36

    out = Image.alpha_composite(img, panel)
    out.save(out_png)


def generate_all_lesson02_assets():
    OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Заставки (Intro / Outro Bumpers)
    intro_mp4 = OVERLAYS_DIR / "modern_intro_02.mp4"
    outro_mp4 = OVERLAYS_DIR / "modern_outro_02.mp4"

    print("▶ Рендер заставки 02 (Intro 4.0s)...")
    render_modern_bumper(
        intro_mp4, "02",
        "ЗАНЯТИЕ 02", "КУРС «ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ»",
        [("ИСТОРИЯ ТВ И", (255, 255, 255, 255)), ("ТЕЛЕВИЗИОННОЙ", (255, 255, 255, 255)), ("ПРОФЕССИИ", (251, 191, 36, 255))],
        ["• Разбор домашнего задания: интервью со спортсменкой", "• Практика: работа с микрофоном и съёмка на смартфон", "• От диска Нипкова до электронного луча и Шаболовки"],
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "Тележурналист с опытом 25+ лет в эфире • Автор курса",
        duration=4.0, freq=220.0
    )

    print("▶ Рендер заставки 02 (Outro 3.5s)...")
    render_modern_bumper(
        outro_mp4, "02",
        "ДОМАШНЕЕ ЗАДАНИЕ • 3 ДНЯ", "КОНЕЦ ЗАНЯТИЯ №2",
        [("ДО ВСТРЕЧИ", (255, 255, 255, 255)), ("НА ТРЕТЬЕМ", (255, 255, 255, 255)), ("ЗАНЯТИИ КУРСА!", (251, 191, 36, 255))],
        ["• Отчитайте новость о землетрясении на Урале как диктор", "• Выучите наизусть скороговорки на звуки [Т] и [С]", "• На урок 3: тетрадь, ручка и боевой настрой!"],
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "На выполнение домашнего задания — 3 дня",
        duration=3.5, freq=261.63
    )

    # 2. Инфографические плашки (10 карточек)
    print("▶ Генерация 10 инфографических карточек...")
    create_lower_third(
        OVERLAYS_DIR / "l02_card01_lower_third.png",
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО",
        "Тележурналист • Педагог телестудий"
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card02_topic.png",
        "ТЕМА ЗАНЯТИЯ 2 • ЗАПИШИТЕ",
        ["История телевидения и", "телевизионной профессии"],
        [
            "• Повторение пройденного: почему журналистика — 4-я власть?",
            "• Практикум работы с микрофоном и камерой смартфона",
            "• Разбор домашнего задания: 7 вопросов для интервью",
            "• История ТВ: от механического диска до первого эфира в СССР",
            "• Практический тренажёр: артикуляционная гимнастика и дикция"
        ],
        w=790, h=410
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card03_phone.png",
        "ПРАКТИКУМ • СЪЁМКА ИНТЕРВЬЮ",
        ["Съёмка на смартфон: только 16:9!"],
        [
            "• Телефон держим СТРОГО ГОРИЗОНТАЛЬНО (16:9)",
            "• Это необходимо для монтажа в общий репортаж",
            "• Руки держим статично у груди, без рывков и тряски",
            "• Используйте штатив или монопод при возможности"
        ],
        w=770, h=350
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card04_mic_rule.png",
        "ПРАВИЛО РАБОТЫ С МИКРОФОНОМ",
        ["Не подносите микрофон к своему рту!"],
        [
            "• Микрофон держится на уровне груди собеседника",
            "• Не двигайте микрофоном туда-сюда во время диалога",
            "• На монтаже нужны ОТВЕТЫ героя, а не ваши вопросы",
            "• Если потребуется вопрос — оператор подскажет подсъёмку"
        ],
        w=780, h=360
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card05_3sec_rule.png",
        "ЗОЛОТОЕ ПРАВИЛО ТЕЛЕЖУРНАЛИСТА",
        ["Правило 3 секунд перед вопросом"],
        [
            "• После отмашки оператора сосчитайте про себя: 1... 2... 3...",
            "• Зачем: страховка от срезанного начала фразы при старте записи",
            "• Даёт секунду сосредоточиться и собраться с мыслями",
            "• Взгляд — открытый, доброжелательный и внимательный к герою"
        ],
        w=790, h=360
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card06_interview_7q.png",
        "РАЗБОР ДОМАШНЕГО ЗАДАНИЯ",
        ["7 ключевых вопросов для интервью (Мария)"],
        [
            "1. Представление: имя и телестудия",
            "2. Сколько лет в гимнастике и чем привлекает этот спорт?",
            "3. Эмоции от соревнований в чужом городе и поддержка зала",
            "4. Как удаётся справиться с волнением перед выходом?",
            "5. Какие советы тренера выручают на выступлениях?",
            "6. Чем занимаетесь в свободное от учёбы и спорта время?",
            "7. Заветная мечта и пожелание покорения новых высот!"
        ],
        w=790, h=480
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card07_tv_history.png",
        "ИСТОРИЯ ТЕЛЕВИДЕНИЯ",
        ["От механического ТВ к электронному"],
        [
            "• 1884 г. — Пауль Нипков изобретает диск механической развёртки",
            "• 1907 г. — Борис Розинг патентует электронно-лучевую трубку",
            "• Владимир Зворыкин — изобретатель иконоскопа и кинескопа",
            "• 1 октября 1931 г. — первое регулярное вещание в СССР (Шаболовка)",
            "• 1938 г. — открытие первых телецентров на Шаболовке и в Ленинграде"
        ],
        w=790, h=420
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card08_diction_t.png",
        "ТРЕНАЖЁР ДИКЦИИ • ЗВУК [ Т ]",
        ["Скороговорка под запись в тетрадь:"],
        [
            "«Белыми копытами лёд колотя,",
            " Тени по Литейному быстро летят,",
            " Тени по Литейному летят назад,",
            " Боевые лошади копытами стучат!»",
            "",
            "• Чётко выбиваем согласный звук [Т] с расстановкой и ритмом"
        ],
        w=770, h=410
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card09_diction_s.png",
        "ТРЕНАЖЁР ДИКЦИИ • ЗВУК [ С ]",
        ["Скороговорка под запись в тетрадь:"],
        [
            "«Сон Татьяне снится,",
            " Лёгкий, как ресница,",
            " Сон нечаянных чудес,",
            " Сон, где всё наоборот...»",
            "",
            "• Ротик открываем шире, губки округлые, чёткий свистящий [С]"
        ],
        w=770, h=410
    )

    create_info_card(
        OVERLAYS_DIR / "l02_card10_homework.png",
        "ДОМАШНЕЕ ЗАДАНИЕ К УРОКУ №3",
        ["Задание: отчитать новостную заметку как диктор"],
        [
            "• Запишите текст о землетрясении на Урале",
            "• Отработайте чёткую дикцию на цифрах («магнитуда 5,5» и «4,5»)",
            "• Запишите себя на видео или отчитайте перед зеркалом",
            "• Выучите наизусть скороговорки на звуки [Т] и [С]",
            "• На Урок 3: тетрадь, ручка и хорошее настроение!"
        ],
        w=790, h=420
    )
    print("✅ Все графические ассеты сгенерированы!")


def build_multicam_blocks():
    """
    Рендерит два чистовых мультикам-блока:
    Take 1: 24.60s .. 723.60s (dur: 699.00s)
    Take 2: 733.90s .. 1518.70s (dur: 784.80s)
    На границе 723.60/733.90 вырезается дубль («все пошло не так»),
    при этом Take 1 заканчивается на ОБЩЕМ плане, а Take 2 начинается на КРУПНОМ —
    склейка становится на 100% невидимой!
    """
    tmp_take1 = "/tmp/l02_take1_multicam.mp4"
    tmp_take2 = "/tmp/l02_take2_multicam.mp4"

    # Take 1: длительность 699.00s. Интервалы КРУПНОГО плана (в локальных секундах t от 0 до 699):
    # Общий план ~65%, Крупный план ~35%
    c1_intervals = [
        (35.0, 68.0),     # Объявление темы и 1-й вопрос повторения
        (130.0, 165.0),   # Репортаж Петра I и переход к микрофону
        (225.0, 260.0),   # Жестикуляция с микрофоном
        (315.0, 360.0),   # Подготовка к вопросам интервью
        (405.0, 445.0),   # Вопросы Марии (заветная мечта)
        (515.0, 560.0),   # Сравнение кино и ТВ
        (625.0, 665.0),   # Первые опыты телевещания
        # Конец Take 1 (665.0..699.0) — ОБЩИЙ план!
    ]
    enable_c1 = "+".join([f"between(t,{st},{en})" for st, en in c1_intervals])

    fc1 = (
        f"[0:v]fps=25,scale=1920:1080:flags=lanczos,format=yuv420p,setpts=PTS-STARTPTS[w0];"
        f"[1:v]fps=25,scale=1920:1080:flags=lanczos,format=yuv420p,setpts=PTS-STARTPTS[c0];"
        f"[w0][c0]overlay=0:0:shortest=1:enable='{enable_c1}'[vout1];"
        f"[0:a]aresample=48000,asetpts=PTS-STARTPTS[aout1]"
    )

    cmd_take1 = [
        FFMPEG, "-y",
        "-hwaccel", "videotoolbox", "-ss", "24.60", "-t", "699.00", "-i", str(SSD_WIDE),
        "-hwaccel", "videotoolbox", "-ss", "24.60", "-t", "699.00", "-i", str(SSD_CLOSE),
        "-filter_complex", fc1,
        "-map", "[vout1]", "-map", "[aout1]",
        "-c:v", "h264_videotoolbox", "-b:v", "8000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        tmp_take1
    ]
    print("▶ Рендер мультикама Take 1 (11 мин 39 сек, 2 камеры)...")
    subprocess.run(cmd_take1, check=True)

    # Take 2: длительность 784.80s (начиная с 733.90s сырого).
    # СТАРТ Take 2 — КРУПНЫЙ план (0.0..32.0), что идеально маскирует склейку с Take 1!
    c2_intervals = [
        (0.0, 34.0),       # КРУПНЫЙ СТАРТ: «Это изобретение позволило телевидению...»
        (85.0, 125.0),     # Развитие телецентров в СССР
        (165.0, 235.0),    # Артикуляционная гимнастика (щеки, губы — крупно!)
        (275.0, 315.0),    # Скороговорка на звук [Т]
        (335.0, 375.0),    # Скороговорка на звук [С]
        (475.0, 540.0),    # Личная история «За лысинкой ходила / Не бойтесь быть смешными»
        (610.0, 655.0),    # Закрепление пройденного материала
        (710.0, 755.0),    # Диктовка домашнего задания о землетрясении
        # Финал (755.0..784.8) — ОБЩИЙ план («До новых встреч!»)
    ]
    enable_c2 = "+".join([f"between(t,{st},{en})" for st, en in c2_intervals])

    fc2 = (
        f"[0:v]fps=25,scale=1920:1080:flags=lanczos,format=yuv420p,setpts=PTS-STARTPTS[w1];"
        f"[1:v]fps=25,scale=1920:1080:flags=lanczos,format=yuv420p,setpts=PTS-STARTPTS[c1];"
        f"[w1][c1]overlay=0:0:shortest=1:enable='{enable_c2}'[vout2];"
        f"[0:a]aresample=48000,asetpts=PTS-STARTPTS[aout2]"
    )

    cmd_take2 = [
        FFMPEG, "-y",
        "-hwaccel", "videotoolbox", "-ss", "733.90", "-t", "784.80", "-i", str(SSD_WIDE),
        "-hwaccel", "videotoolbox", "-ss", "733.90", "-t", "784.80", "-i", str(SSD_CLOSE),
        "-filter_complex", fc2,
        "-map", "[vout2]", "-map", "[aout2]",
        "-c:v", "h264_videotoolbox", "-b:v", "8000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        tmp_take2
    ]
    print("▶ Рендер мультикама Take 2 (13 мин 05 сек, 2 камеры)...")
    subprocess.run(cmd_take2, check=True)

    # Склейка двух тейков в единый мультикам-мастер (без перекодирования видео!)
    concat_list = "/tmp/l02_multicam_concat.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{tmp_take1}'\n")
        f.write(f"file '{tmp_take2}'\n")

    multicam_master = LESSONS_DIR / "02_lesson_2_multicam.mp4"
    cmd_concat = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(multicam_master)
    ]
    print("▶ Бесшовная склейка чистового мультикама (02_lesson_2_multicam.mp4)...")
    subprocess.run(cmd_concat, check=True)

    for tmp in [tmp_take1, tmp_take2, concat_list]:
        if os.path.exists(tmp):
            os.remove(tmp)

    print(f"✅ Чистовой мультикам готов: {multicam_master} ({os.path.getsize(multicam_master)/(1024*1024):.1f} MB)")
    return multicam_master


def overlay_all_graphics_and_bumpers(multicam_video: Path):
    """
    Накладывает 10 карточек на чистовой мультикам и добавляет эфирные заставки.
    Общая длительность чистового тела: 699.00 + 784.80 = 1483.80s (24 мин 43.8 сек).
    Тайминги карточек в чистовом теле:
    Take 1: t_clean = t_raw - 24.60
    Take 2: t_clean = (t_raw - 733.90) + 699.00 = t_raw - 34.90
    """
    body_dur = 1483.80
    body_with_gfx = "/tmp/02_lesson_2_body_gfx.mp4"
    final_lesson_mp4 = LESSONS_DIR / "02_lesson_2_clean.mp4"

    intro_bumper = OVERLAYS_DIR / "modern_intro_02.mp4"
    outro_bumper = OVERLAYS_DIR / "modern_outro_02.mp4"

    cards_spec = [
        # (карточка, t_in, t_out) в секундах от начала чистового видео:
        (OVERLAYS_DIR / "l02_card01_lower_third.png", 2.0, 14.0),                      # Ирина Витальевна Тыщенко
        (OVERLAYS_DIR / "l02_card02_topic.png", 20.0, 58.0),                          # Тема урока (t_raw=44.6)
        (OVERLAYS_DIR / "l02_card03_phone.png", 175.0, 212.0),                        # Смартфон горизонтально (t_raw=199.6)
        (OVERLAYS_DIR / "l02_card04_mic_rule.png", 225.0, 260.0),                     # Правило микрофона (t_raw=249.6)
        (OVERLAYS_DIR / "l02_card05_3sec_rule.png", 276.0, 312.0),                    # Правило 3 секунд (t_raw=300.6)
        (OVERLAYS_DIR / "l02_card06_interview_7q.png", 342.0, 405.0),                 # 7 вопросов интервью (t_raw=366.6)
        (OVERLAYS_DIR / "l02_card07_tv_history.png", 635.0, 692.0),                   # История ТВ Нипков/Зворыкин (t_raw=660)
        # Карточки из Take 2 (смещение -34.90s):
        (OVERLAYS_DIR / "l02_card08_diction_t.png", round(972.0 - 34.90, 2), round(1015.0 - 34.90, 2)),   # Звук Т (937.1 .. 980.1)
        (OVERLAYS_DIR / "l02_card09_diction_s.png", round(1025.0 - 34.90, 2), round(1065.0 - 34.90, 2)),  # Звук С (990.1 .. 1030.1)
        (OVERLAYS_DIR / "l02_card10_homework.png", round(1412.0 - 34.90, 2), round(1470.0 - 34.90, 2)),   # Домашка (1377.1 .. 1435.1)
    ]

    inputs = ["-hwaccel", "videotoolbox", "-i", str(multicam_video)]
    for png_path, _, _ in cards_spec:
        inputs.extend(["-i", str(png_path)])

    fade_out_v = round(body_dur - 0.5, 2)
    fc_lines = [f"[0:v]format=yuv420p,setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out_v}:d=0.50[v0]"]
    prev_v = "[v0]"

    for idx, (_, t_in, t_out) in enumerate(cards_spec, start=1):
        c_tag = f"[c{idx}]"
        v_tag = f"[v{idx}]"
        fade_out_st = round(t_out - 0.35, 2)
        fc_lines.append(
            f"[{idx}:v]format=rgba,loop=loop=-1:size=1:start=0,fps=25,trim=duration={t_out},setpts=PTS-STARTPTS,"
            f"fade=t=in:st={t_in}:d=0.35:alpha=1,fade=t=out:st={fade_out_st}:d=0.35:alpha=1{c_tag}"
        )
        fc_lines.append(
            f"{prev_v}{c_tag}overlay=0:0:eof_action=pass:enable='between(t,{t_in},{t_out})'{v_tag}"
        )
        prev_v = v_tag

    fc_lines.append(f"[0:a]aresample=48000,asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.20,afade=t=out:st={fade_out_v}:d=0.50[aout]")
    filter_complex = ";".join(fc_lines)

    cmd_body = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", prev_v, "-map", "[aout]",
        "-t", str(body_dur),
        "-c:v", "h264_videotoolbox", "-b:v", "8000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        body_with_gfx
    ]
    print(f"▶ Рендер графики урока 2 ({body_dur:.1f}s / ~24.7 мин) с {len(cards_spec)} карточками и нормализацией -16 LUFS...")
    subprocess.run(cmd_body, check=True)

    concat_txt = "/tmp/l02_final_concat.txt"
    with open(concat_txt, "w") as f:
        f.write(f"file '{intro_bumper}'\n")
        f.write(f"file '{body_with_gfx}'\n")
        f.write(f"file '{outro_bumper}'\n")

    cmd_final = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(final_lesson_mp4)
    ]
    print("▶ Финальная сшивка с эфирными заставками...")
    subprocess.run(cmd_final, check=True)

    for tmp in [body_with_gfx, concat_txt]:
        if os.path.exists(tmp):
            os.remove(tmp)

    # Копия в рабочую папку пользователя
    workspace_copy = WORKSPACE_DIR / "02_lesson_2_clean.mp4"
    shutil.copy2(str(final_lesson_mp4), str(workspace_copy))
    print(f"✅ Урок 2 полностью готов: {final_lesson_mp4} ({os.path.getsize(final_lesson_mp4)/(1024*1024):.1f} MB)")
    print(f"📁 Скопирован в рабочую папку: {workspace_copy}")


def main():
    print("=== СТАРТ СБОРКИ ЗАНЯТИЯ 2 ===")
    generate_all_lesson02_assets()
    multicam_video = build_multicam_blocks()
    overlay_all_graphics_and_bumpers(multicam_video)
    print("=== ЗАНЯТИЕ 2 УСПЕШНО СОБРАНО! ===")


if __name__ == "__main__":
    main()
