#!/usr/bin/env python3
"""
Генератор эфирной инфографики, заставок и финальной сборки для:
1. Урок 0 (Вводное слово автора) -> lessons/00_intro_greeting_lesson.mp4
2. Занятие 1 (Знакомство с мастером. Журналистика от древности до наших дней) -> lessons/01_lesson_1_full.mp4

Все карточки рисуются строго в левой безопасной зоне (X = 70..860 px)
и появляются ТОЛЬКО на Общем плане (где спикер находится справа X = 940..1720 px),
никогда не перекрывая лицо и не попадая на Крупный план.
"""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FFMPEG = "/opt/homebrew/bin/ffmpeg"
BASE = Path("/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course")
OVERLAYS_DIR = BASE / "assets" / "course_overlays" / "lesson01"
LESSONS_DIR = BASE / "lessons"
OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)
LESSONS_DIR.mkdir(parents=True, exist_ok=True)

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"

def draw_lower_third(out_path: Path, badge_text: str, name_text: str, sub_text: str):
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 80, 865, 900, 995
    # Тень и стеклянная плашка
    d.rounded_rectangle([x0+6, y0+8, x1+6, y1+8], radius=18, fill=(0, 0, 0, 120))
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=(11, 18, 34, 240), outline=(245, 180, 60, 200), width=2)
    d.rounded_rectangle([x0, y0, x0+12, y1], radius=6, fill=(245, 180, 60, 255))

    f_badge = ImageFont.truetype(FONT_BOLD, 18)
    f_name = ImageFont.truetype(FONT_BOLD, 34)
    f_sub = ImageFont.truetype(FONT_REG, 22)

    bw = int(d.textlength(badge_text, font=f_badge)) + 44
    d.rounded_rectangle([x0+30, y0+20, x0+30+bw, y0+50], radius=7, fill=(225, 29, 72, 240))
    d.ellipse([x0+42, y0+30, x0+52, y0+40], fill=(255, 255, 255, 255))
    d.text((x0+60, y0+24), badge_text, font=f_badge, fill=(255, 255, 255, 255))

    d.text((x0+44+bw, y0+17), name_text, font=f_name, fill=(255, 255, 255, 255))
    d.text((x0+32, y0+68), sub_text, font=f_sub, fill=(251, 191, 36, 255))
    img.save(out_path)


def draw_left_card(
    out_path: Path,
    badge_text: str,
    title_lines: list,
    bullet_lines: list,
    accent_rgb=(245, 180, 60)
):
    """
    Рисует премиальную карточку инфографики слева (X=70..860) на Общем плане.
    Спикер находится справа (X=940..1720), перекрытие лица = 0%.
    """
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    f_badge = ImageFont.truetype(FONT_BOLD, 19)
    f_title = ImageFont.truetype(FONT_BOLD, 32)
    f_body = ImageFont.truetype(FONT_REG, 25)

    x0, x1 = 70, 865
    card_h = 125 + len(title_lines) * 44 + len(bullet_lines) * 38 + 20
    # Центрируем по вертикали в верхней/средней левой зоне (Y=190..)
    y0 = 200
    y1 = y0 + card_h

    # Мягкая тень
    d.rounded_rectangle([x0+8, y0+10, x1+8, y1+10], radius=22, fill=(0, 0, 0, 125))
    # Основной блок тёмно-сапфирового цвета
    d.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=22,
        fill=(11, 18, 34, 238),
        outline=(accent_rgb[0], accent_rgb[1], accent_rgb[2], 195),
        width=2
    )
    # Акцентная полоса слева
    d.rounded_rectangle([x0, y0, x0+12, y1], radius=6, fill=(accent_rgb[0], accent_rgb[1], accent_rgb[2], 255))

    # Плашка бейджа
    bw = int(d.textlength(badge_text, font=f_badge)) + 36
    d.rounded_rectangle([x0+32, y0+24, x0+32+bw, y0+58], radius=8, fill=(225, 29, 72, 240))
    d.text((x0+50, y0+30), badge_text, font=f_badge, fill=(255, 255, 255, 255))

    curr_y = y0 + 74
    for tline in title_lines:
        d.text((x0+32, curr_y), tline, font=f_title, fill=(251, 191, 36, 255))
        curr_y += 42

    curr_y += 8
    d.line([(x0+32, curr_y), (x1-32, curr_y)], fill=(255, 255, 255, 45), width=1)
    curr_y += 16

    for bline in bullet_lines:
        d.text((x0+32, curr_y), bline, font=f_body, fill=(241, 245, 249, 255))
        curr_y += 38

    img.save(out_path)


def render_bumper(out_mp4: Path, pill_text: str, main_title: str, sub_title: str, freq: float = 220.0):
    frame_png = out_mp4.with_suffix(".png")
    img = Image.new("RGBA", (1920, 1080), (7, 11, 20, 255))
    d = ImageDraw.Draw(img)
    for r in range(550, 0, -25):
        alpha = int(42 * (1 - r / 550))
        d.ellipse([960 - r, 540 - r, 960 + r, 540 + r], fill=(245, 158, 11, alpha))

    f_badge = ImageFont.truetype(FONT_BOLD, 24)
    f_title = ImageFont.truetype(FONT_BOLD, 64)
    f_sub = ImageFont.truetype(FONT_REG, 32)
    f_pill = ImageFont.truetype(FONT_BOLD, 28)

    d.rounded_rectangle([960 - 150, 330, 960 + 150, 380], radius=10, fill=(225, 29, 72, 240))
    d.ellipse([960 - 118, 347, 960 - 102, 363], fill=(255, 255, 255, 255))
    d.text((960 + 12, 355), "ТЕЛЕШКОЛА", font=f_badge, fill=(255, 255, 255, 255), anchor="mm")

    d.text((960, 465), main_title, font=f_title, fill=(255, 255, 255, 255), anchor="mm")
    d.text((960, 545), sub_title, font=f_sub, fill=(251, 191, 36, 255), anchor="mm")

    pw = int(d.textlength(pill_text, font=f_pill)) + 80
    d.rounded_rectangle([960 - pw//2, 620, 960 + pw//2, 680], radius=12, fill=(19, 28, 49, 255), outline=(245, 158, 11, 190), width=2)
    d.text((960, 650), pill_text, font=f_pill, fill=(255, 255, 255, 255), anchor="mm")
    img.save(frame_png)

    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-t", "2.0", "-i", str(frame_png),
        "-f", "lavfi", "-t", "2.0", "-i", f"sine=frequency={freq}:duration=2.0",
        "-vf", "format=yuv420p,fade=t=in:st=0:d=0.4,fade=t=out:st=1.6:d=0.4",
        "-af", "aresample=48000,pan=stereo|c0=c0|c1=c0,volume=0.25,afade=t=in:st=0:d=0.2,afade=t=out:st=1.1:d=0.9",
        "-c:v", "h264_videotoolbox", "-b:v", "8000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(out_mp4)
    ]
    subprocess.run(cmd, check=True)


def overlay_cards_on_multicam(src_multicam: Path, cards_spec: list, intro_bumper: Path, outro_bumper: Path, final_out: Path, total_dur: float):
    """
    Накладывает набор прозрачных PNG-карточек (cards_spec = [(png_path, t_in, t_out), ...])
    на готовый двухкамерный монтаж в один быстрый проход и приклеивает заставки.
    """
    body_with_gfx = f"/tmp/{final_out.stem}_body_gfx.mp4"
    inputs = ["-hwaccel", "videotoolbox", "-i", str(src_multicam)]
    for png_path, _, _ in cards_spec:
        inputs.extend(["-i", str(png_path)])

    fc_lines = ["[0:v]format=yuv420p[v0]"]
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

    filter_complex = ";".join(fc_lines)
    cmd_body = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", prev_v, "-map", "0:a",
        "-t", str(total_dur),
        "-c:v", "h264_videotoolbox", "-b:v", "8000k", "-r", "25",
        "-c:a", "copy",
        body_with_gfx
    ]
    print(f"▶ Наложение инфографики ({len(cards_spec)} плашек) на {src_multicam.name}...")
    subprocess.run(cmd_body, check=True)

    concat_txt = f"/tmp/{final_out.stem}_concat.txt"
    with open(concat_txt, "w") as f:
        f.write(f"file '{intro_bumper}'\n")
        f.write(f"file '{body_with_gfx}'\n")
        f.write(f"file '{outro_bumper}'\n")

    cmd_concat = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(final_out)
    ]
    print(f"▶ Сборка финального мастера с заставками -> {final_out.name}...")
    subprocess.run(cmd_concat, check=True)

    for tmp in [body_with_gfx, concat_txt]:
        if os.path.exists(tmp):
            os.remove(tmp)


def build_lesson_00():
    print("\n=== СБОРКА УРОКА 0 (С ГРАФИКОЙ И ДВУМЯ ПЛАНАМИ) ===")
    intro_b = OVERLAYS_DIR / "bumper_intro_00.mp4"
    outro_b = OVERLAYS_DIR / "bumper_outro_00.mp4"
    render_bumper(intro_b, "УРОК 0 • ВВОДНОЕ СЛОВО АВТОРА", "ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ", "Авторский курс Ирины Тыщенко • 25+ лет в эфире", 220.0)
    render_bumper(outro_b, "ДАЛЕЕ • ЗАНЯТИЕ 1", "ЖУРНАЛИСТИКА — СОСТОЯНИЕ ДУШИ", "Переходите к первому практическому уроку курса", 261.63)

    lt_00 = OVERLAYS_DIR / "l00_lower_third.png"
    draw_lower_third(lt_00, "ЭФИР", "ИРИНА ТЫЩЕНКО", "Тележурналист • Стаж 25+ лет • Автор курса")

    c1_00 = OVERLAYS_DIR / "l00_card1_audience.png"
    draw_left_card(
        c1_00,
        "ДЛЯ КОГО ЭТОТ КУРС",
        ["Кому пригодятся занятия:"],
        [
            "• Начинающим журналистам и телерепортёрам",
            "• Блогерам и авторам медиапроектов",
            "• Педагогам дополнительного образования",
            "• Всем, кто хочет уверенно говорить и писать",
        ]
    )

    c2_00 = OVERLAYS_DIR / "l00_card2_skills.png"
    draw_left_card(
        c2_00,
        "ПРАКТИКА И ОПЫТ",
        ["На курсе вы научитесь:"],
        [
            "• Задавать точные вопросы и брать интервью",
            "• Писать живые тексты и сценарии репортажей",
            "• Работать с героями в любых ситуациях",
            "• Относиться к трудностям с юмором и достоинством",
        ]
    )

    cards_00 = [
        (lt_00, 1.5, 11.5),
        (c1_00, 21.5, 38.5),
        (c2_00, 66.0, 83.0),
    ]
    overlay_cards_on_multicam(
        LESSONS_DIR / "00_intro_greeting_multicam.mp4",
        cards_00,
        intro_b,
        outro_b,
        LESSONS_DIR / "00_intro_greeting_lesson.mp4",
        85.80
    )


def build_lesson_01():
    print("\n=== СБОРКА ЗАНЯТИЯ 1 (С ГРАФИКОЙ, ИНФОГРАФИКОЙ И ДВУМЯ ПЛАНАМИ) ===")
    intro_b = OVERLAYS_DIR / "bumper_intro_01.mp4"
    outro_b = OVERLAYS_DIR / "bumper_outro_01.mp4"
    render_bumper(intro_b, "ЗАНЯТИЕ 1 • ОТ ДРЕВНОСТИ ДО НАШИХ ДНЕЙ", "ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ", "Знакомство с мастером • История профессии • Дикция", 220.0)
    render_bumper(outro_b, "ДОМАШНЕЕ ЗАДАНИЕ • 3 ДНЯ НА ВЫПОЛНЕНИЕ", "ДО ВСТРЕЧИ НА ЗАНЯТИИ 2!", "Приготовьте тетрадь, микрофон, зеркало и телефон", 261.63)

    lt_01 = OVERLAYS_DIR / "l01_card01_lower_third.png"
    draw_lower_third(lt_01, "ЗАНЯТИЕ 1", "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "Тележурналист • Стаж 25+ лет • СурГУ")

    c02 = OVERLAYS_DIR / "l01_card02_bio.png"
    draw_left_card(
        c02,
        "ПУТЬ В ПРОФЕССИЮ",
        ["Начало журналистской практики:"],
        [
            "• Со школьной скамьи — стенгазеты и заметки",
            "• Помощь соседям в составлении писем и обращений",
            "• Районная газета «Колос» (Северный Казахстан):",
            "  ведущая радиоэфира, корреспондент, зав. отделом писем",
        ]
    )

    c03 = OVERLAYS_DIR / "l01_card03_school.png"
    draw_left_card(
        c03,
        "ШКОЛА ТЕЛЕЖУРНАЛИСТИКИ",
        ["Опыт преподавания с 2008 года:"],
        [
            "• 2008 г. — телестудия «Школа плюс ТВ» (г. Лянтор)",
            "• Более 100 выпускников за первые 4 года работы",
            "• Детско-юношеская телестудия «3Т» (г. Тюмень)",
            "• ТВ «Горячий Ключ», РЕН-ТВ, ГТРК «ЛянторИнформ»",
        ]
    )

    c04 = OVERLAYS_DIR / "l01_card04_program.png"
    draw_left_card(
        c04,
        "ПРОГРАММА КУРСА",
        ["Чему мы учимся на занятиях:"],
        [
            "• Правильно и чётко говорить (тренировка дикции)",
            "• Разрабатывать вопросы и брать интервью",
            "• Свободно держаться в кадре и знать правила съёмки",
            "• Писать тексты для ТВ, печати и интернет-блогов",
        ]
    )

    c05 = OVERLAYS_DIR / "l01_card05_topic1.png"
    draw_left_card(
        c05,
        "ТЕМА ЗАНЯТИЯ 1 • ЗАПИШИТЕ",
        ["Журналистика:", "от древности до наших дней"],
        [
            "• Правило №1: Представление журналиста",
            "  «Здравствуйте! Я журналист телестудии [...] /",
            "   автор блога [...], меня зовут [...]»",
            "• Доверие героя начинается с открытого знакомства!",
        ]
    )

    c06 = OVERLAYS_DIR / "l01_card06_definition.png"
    draw_left_card(
        c06,
        "ОПРЕДЕЛЕНИЕ ПОД ЗАПИСЬ",
        ["Что такое журналистика?"],
        [
            "Профессиональная деятельность по сбору,",
            "обработке и публикации информации.",
            "• «Четвёртая власть» в государстве (после",
            "  законодательной, исполнительной и судебной)",
        ]
    )

    c07 = OVERLAYS_DIR / "l01_card07_history.png"
    draw_left_card(
        c07,
        "ИСТОРИЯ РОССИЙСКОЙ ПЕЧАТИ",
        ["Главные исторические даты:"],
        [
            "• 1621 г. — первые рукописные газеты («Куранты»)",
            "• 15 декабря 1702 г. — Указ Петра I о печати «Ведомостей»",
            "• 13 января 1703 г. — День российской печати",
            "• 27 июня 1709 г. — первый репортаж Петра I (Полтава)",
        ]
    )

    c08 = OVERLAYS_DIR / "l01_card08_mission.png"
    draw_left_card(
        c08,
        "ЗАДАЧА СОВРЕМЕННОГО АВТОРА",
        ["Главное правило медиа:"],
        [
            "• Новости появляются каждую минуту",
            "• Задача журналиста и блогера — не просто",
            "  сообщить о событии, а рассказать о нём",
            "  БЫСТРЕЕ и ИНТЕРЕСНЕЕ, чем другие!",
        ]
    )

    c09 = OVERLAYS_DIR / "l01_card09_diction.png"
    draw_left_card(
        c09,
        "ТРЕНАЖЁР ДИКЦИИ • ЗАПИШИТЕ",
        ["Скороговорка урока:"],
        [
            "«Расскажите про покупки!",
            "Про какие про покупки?",
            "Про покупки, про покупки,",
            "про покупочки свои!»",
            "• Открываем рот свободно, говорим чётко в ритме",
        ]
    )

    c10 = OVERLAYS_DIR / "l01_card10_quiz.png"
    draw_left_card(
        c10,
        "ЗАКРЕПЛЕНИЕ МАТЕРИАЛА",
        ["Ответьте вслух своими словами:"],
        [
            "1. Почему важно представиться и назвать своё СМИ?",
            "2. Кто написал первый репортаж и когда мы",
            "   отмечаем День российской печати?",
            "3. Какое СМИ сегодня самое главное на ваш взгляд?",
        ]
    )

    c11 = OVERLAYS_DIR / "l01_card11_homework.png"
    draw_left_card(
        c11,
        "ДОМАШНЕЕ ЗАДАНИЕ №1 • 3 ДНЯ",
        ["Кейс «Интервью с гимнасткой»:"],
        [
            "• Героиня: Мария (10 класс), занимается с 5 лет,",
            "  заняла 2-е место на республиканских соревнованиях",
            "• Тренер: Вера Сергеевна гордится ученицей",
            "• ЗАДАНИЕ: составить минимум 7 вопросов к Марии",
            "  + выучить скороговорку «Расскажите про покупки»",
        ]
    )

    cards_01 = [
        (lt_01, 2.0, 14.0),
        (c02, 43.0, 61.5),
        (c03, 114.0, 131.5),
        (c04, 185.0, 218.0),
        (c05, 245.0, 294.0),
        (c06, 341.0, 363.5),
        (c07, 408.0, 463.0),
        (c08, 502.0, 527.0),
        (c09, 580.0, 618.0),
        (c10, 675.0, 720.0),
        (c11, 770.0, 812.5),
    ]
    overlay_cards_on_multicam(
        LESSONS_DIR / "01_lesson_1_multicam.mp4",
        cards_01,
        intro_b,
        outro_b,
        LESSONS_DIR / "01_lesson_1_full.mp4",
        888.50
    )


if __name__ == "__main__":
    build_lesson_00()
    build_lesson_01()
    print("\n🎉 ОБА УРОКА С ПОЛНОЙ ИНФОГРАФИКОЙ И ДВУМЯ КАМЕРАМИ ГОТОВЫ!")
