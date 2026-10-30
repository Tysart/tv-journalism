#!/usr/bin/env python3
"""
Обновлённая сборка v2 по обратной связи:
1. Новая современная 4.0-секундная заставка (MasterClass / Netflix Doc style):
   - Справа: студийный 4K-кадр Ирины Витальевны в фокусе
   - Слева: тёмно-сапфировая матовая панель с контрастом 21:1 (крупный белый и янтарный текст без жёлтого пятна сзади)
   - Длительность: 4.0 секунды (удобно прочитать все строки)
2. Разделение первого файла (C1253) ровно по границе 04:04.80 (исходник 05:00.78):
   - Видео А: lessons/00_biography_master_lesson.mp4 (4 мин 12 сек) — «Знакомство с мастером: автобиография и путь в профессию»
   - Видео Б: lessons/01_lesson_1_full.mp4 (10 мин 52 сек) — ЧИСТОЕ Занятие 1, начинается с первой же секунды словами:
     «Итак, начинаем наше первое занятие! В тетрадях запишем: Тема урока — Журналистика от древности до наших дней»
3. Обновление Урока 0 (приветствие C1265) с новой 4-секундной современной заставкой.
"""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

FFMPEG = "/opt/homebrew/bin/ffmpeg"
BASE = Path("/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course")
OVERLAYS_DIR = BASE / "assets" / "course_overlays" / "lesson01"
LESSONS_DIR = BASE / "lessons"
SCRATCH_DIR = Path("/Users/artemtysenko/.gemini/antigravity/brain/57f7e0cd-5197-4cdf-acb9-6c7f2211ee9b/scratch")

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"


def render_modern_bumper(
    out_mp4: Path,
    bg_frame_path: Path,
    badge_text: str,
    meta_text: str,
    title_lines: list,      # Список кортежей: (текст, цвет_RGBA)
    bullet_lines: list,
    footer_title: str,
    footer_sub: str,
    duration: float = 4.0,
    freq: float = 220.0
):
    """
    Генерирует современную 4-секундную широкоэкранную заставку (1920x1080)
    со студийным портретом справа и контрастной тёмно-сапфировой панелью слева.
    """
    frame_png = out_mp4.with_suffix(".png")
    bg = Image.open(bg_frame_path).convert("RGBA").resize((1920, 1080), Image.Resampling.LANCZOS)

    bg_blur = bg.filter(ImageFilter.GaussianBlur(radius=30))
    bg_blur = ImageEnhance.Brightness(bg_blur).enhance(0.20)

    bg_right = ImageEnhance.Brightness(bg).enhance(0.90)
    bg_right = ImageEnhance.Contrast(bg_right).enhance(1.10)

    grad = Image.new("L", (1920, 1080), 0)
    gd = ImageDraw.Draw(grad)
    for x in range(1920):
        if x < 820:
            val = 0
        elif x > 1080:
            val = 255
        else:
            val = int(255 * ((x - 820) / 260.0))
        gd.line([(x, 0), (x, 1080)], fill=val)

    canvas = Image.composite(bg_right, bg_blur, grad)
    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    # Левая контрастная панель (X=75..965)
    od.rounded_rectangle([75, 105, 965, 975], radius=28, fill=(8, 13, 25, 244), outline=(245, 180, 60, 185), width=2)
    od.rounded_rectangle([75, 165, 89, 915], radius=6, fill=(245, 180, 60, 255))

    f_badge = ImageFont.truetype(FONT_BOLD, 21)
    f_meta = ImageFont.truetype(FONT_BOLD, 19)
    f_h1 = ImageFont.truetype(FONT_BOLD, 56)
    f_sub = ImageFont.truetype(FONT_REG, 26)
    f_author = ImageFont.truetype(FONT_BOLD, 25)
    f_role = ImageFont.truetype(FONT_REG, 21)

    bw = int(od.textlength(badge_text, font=f_badge)) + 58
    od.rounded_rectangle([120, 155, 120 + bw, 205], radius=10, fill=(225, 29, 72, 255))
    od.ellipse([140, 172, 156, 188], fill=(255, 255, 255, 255))
    od.text((168, 168), badge_text, font=f_badge, fill=(255, 255, 255, 255))

    mx0 = 120 + bw + 18
    mw = int(od.textlength(meta_text, font=f_meta)) + 44
    od.rounded_rectangle([mx0, 155, mx0 + mw, 205], radius=10, fill=(19, 29, 52, 255), outline=(245, 180, 60, 120), width=1)
    od.text((mx0 + 22, 169), meta_text, font=f_meta, fill=(248, 250, 252, 240))

    curr_y = 248
    for t_str, t_col in title_lines:
        od.text((120, curr_y), t_str, font=f_h1, fill=t_col)
        curr_y += 74

    curr_y += 18
    od.line([(120, curr_y), (915, curr_y)], fill=(255, 255, 255, 45), width=2)
    curr_y += 34

    for bline in bullet_lines:
        od.text((120, curr_y), bline, font=f_sub, fill=(241, 245, 249, 255))
        curr_y += 46

    od.rounded_rectangle([120, 770, 915, 910], radius=16, fill=(16, 24, 44, 255), outline=(255, 255, 255, 35), width=1)
    od.text((150, 800), footer_title, font=f_author, fill=(255, 255, 255, 255))
    od.text((150, 843), footer_sub, font=f_role, fill=(251, 191, 36, 245))

    final_img = Image.alpha_composite(canvas, overlay)
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


def overlay_cards_and_bumpers(src_video: Path, trim_start: float, trim_dur: float, cards_spec: list, intro_bumper: Path, outro_bumper: Path, final_out: Path):
    body_with_gfx = f"/tmp/{final_out.stem}_body_gfx.mp4"
    inputs = ["-hwaccel", "videotoolbox", "-ss", str(trim_start), "-t", str(trim_dur), "-i", str(src_video)]
    for png_path, _, _ in cards_spec:
        inputs.extend(["-i", str(png_path)])

    fade_out_v = round(trim_dur - 0.5, 2)
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

    fc_lines.append(f"[0:a]aresample=48000,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.20,afade=t=out:st={fade_out_v}:d=0.50[aout]")
    filter_complex = ";".join(fc_lines)

    cmd_body = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", prev_v, "-map", "[aout]",
        "-t", str(trim_dur),
        "-c:v", "h264_videotoolbox", "-b:v", "8000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        body_with_gfx
    ]
    print(f"▶ Рендер основного тела {final_out.name} ({trim_dur:.1f}s) с {len(cards_spec)} карточками...")
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
    subprocess.run(cmd_concat, check=True)
    for tmp in [body_with_gfx, concat_txt]:
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f"✅ Готово: {final_out} ({os.path.getsize(final_out)/(1024*1024):.1f} MB)")


def main():
    wide_c1265 = SCRATCH_DIR / "check_c1265_wide.jpg"
    wide_c1253 = SCRATCH_DIR / "check_c1253_wide.jpg"

    # 1. Заставки для Урока 0 (Вводное приветствие, C1265)
    intro_00 = OVERLAYS_DIR / "modern_intro_00.mp4"
    outro_00 = OVERLAYS_DIR / "modern_outro_00.mp4"
    render_modern_bumper(
        intro_00, wide_c1265,
        "ВВОДНЫЙ УРОК", "КУРС «ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ»",
        [("ДОБРО ПОЖАЛОВАТЬ", (255, 255, 255, 255)), ("НА АВТОРСКИЙ КУРС", (255, 255, 255, 255)), ("ТЕЛЕЖУРНАЛИСТИКИ", (251, 191, 36, 255))],
        ["• Для кого создан этот практический курс", "• Навыки работы в кадре, текста и интервью", "• Живой опыт регионального и федерального ТВ"],
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "Тележурналист с опытом 25+ лет в эфире • Автор курса",
        duration=4.0, freq=220.0
    )
    render_modern_bumper(
        outro_00, wide_c1265,
        "ДАЛЕЕ В КУРСЕ", "ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ",
        [("ЖУРНАЛИСТИКА —", (255, 255, 255, 255)), ("ЭТО СОСТОЯНИЕ", (255, 255, 255, 255)), ("ДУШИ!", (251, 191, 36, 255))],
        ["• Переходите к видеознакомству с мастером", "• И начинайте Занятие 1 с рабочей тетрадью", "• Желаем успехов в обучении!"],
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "Переходите к следующему видео",
        duration=3.5, freq=261.63
    )

    cards_00 = [
        (OVERLAYS_DIR / "l00_lower_third.png", 1.5, 11.5),
        (OVERLAYS_DIR / "l00_card1_audience.png", 21.5, 38.5),
        (OVERLAYS_DIR / "l00_card2_skills.png", 66.0, 83.0),
    ]
    overlay_cards_and_bumpers(
        LESSONS_DIR / "00_intro_greeting_multicam.mp4",
        0.0, 85.80,
        cards_00, intro_00, outro_00,
        LESSONS_DIR / "00_intro_greeting_lesson.mp4"
    )

    # 2. Видеовизитка / Автобиография мастера (первые 4:03.8 из C1253)
    intro_bio = OVERLAYS_DIR / "modern_intro_bio.mp4"
    outro_bio = OVERLAYS_DIR / "modern_outro_bio.mp4"
    render_modern_bumper(
        intro_bio, wide_c1253,
        "ЗНАКОМСТВО С МАСТЕРОМ", "КУРС «ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ»",
        [("ПУТЬ В ПРОФЕССИЮ:", (255, 255, 255, 255)), ("25+ ЛЕТ В ПЕЧАТИ", (255, 255, 255, 255)), ("И ТЕЛЕЭФИРЕ", (251, 191, 36, 255))],
        ["• От первых школьных заметок до газеты «Колос»", "• Работа на РЕН-ТВ, ТВ «Горячий Ключ» и в Югре", "• Создание детских телестудий «Школа плюс ТВ» и «3Т»"],
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "Тележурналист • Педагог дополнительного образования",
        duration=4.0, freq=220.0
    )
    render_modern_bumper(
        outro_bio, wide_c1253,
        "ТЯЖЕЛО В УЧЕНИИ — ЛЕГКО В БОЮ", "КУРС «ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ»",
        [("ГОТОВЫ К ПРАКТИКЕ?", (255, 255, 255, 255)), ("ПЕРЕХОДИМ", (255, 255, 255, 255)), ("К ЗАНЯТИЮ №1", (251, 191, 36, 255))],
        ["• Приготовьте рабочую тетрадь и ручку", "• Впереди: история журналистики и тренажёр дикции", "• До встречи в первом уроке!"],
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "Переходите к Занятию 1",
        duration=3.5, freq=261.63
    )

    cards_bio = [
        (OVERLAYS_DIR / "l01_card01_lower_third.png", 2.0, 14.0),
        (OVERLAYS_DIR / "l01_card02_bio.png", 43.0, 61.5),
        (OVERLAYS_DIR / "l01_card03_school.png", 114.0, 131.5),
        (OVERLAYS_DIR / "l01_card04_program.png", 185.0, 218.0),
    ]
    overlay_cards_and_bumpers(
        LESSONS_DIR / "01_lesson_1_multicam.mp4",
        0.0, 243.80,
        cards_bio, intro_bio, outro_bio,
        LESSONS_DIR / "00_biography_master_lesson.mp4"
    )

    # 3. ЧИСТОЕ Занятие 1 (начинается на 244.80s прямо со слов «Итак, начинаем наше первое занятие!»)
    # Длительность чистого урока: 888.50 - 244.80 = 643.70s (10 мин 43.7 сек)
    # Все таймкоды карточек смещаются на -244.80s!
    intro_01 = OVERLAYS_DIR / "modern_intro_01.mp4"
    outro_01 = OVERLAYS_DIR / "modern_outro_01.mp4"
    render_modern_bumper(
        intro_01, wide_c1253,
        "ЗАНЯТИЕ 01", "КУРС «ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ»",
        [("ЖУРНАЛИСТИКА:", (255, 255, 255, 255)), ("ОТ ДРЕВНОСТИ", (255, 255, 255, 255)), ("ДО НАШИХ ДНЕЙ", (251, 191, 36, 255))],
        ["• Правило первого представления герою и зрителю", "• История российской печати и первый репортаж Петра I", "• Практический тренажёр артикуляции и дикции"],
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "Тележурналист с опытом 25+ лет в эфире • Педагог телестудий",
        duration=4.0, freq=220.0
    )
    render_modern_bumper(
        outro_01, wide_c1253,
        "ДОМАШНЕЕ ЗАДАНИЕ • 3 ДНЯ", "КОНЕЦ ЗАНЯТИЯ №1",
        [("ДО ВСТРЕЧИ", (255, 255, 255, 255)), ("НА ВТОРОМ", (255, 255, 255, 255)), ("ЗАНЯТИИ КУРСА!", (251, 191, 36, 255))],
        ["• Выучите скороговорку «Расскажите про покупки»", "• Составьте 7 вопросов для интервью с гимнасткой Марией", "• На урок 2: тетрадь, микрофон, зеркало и телефон"],
        "ИРИНА ВИТАЛЬЕВНА ТЫЩЕНКО", "На выполнение домашнего задания — 3 дня",
        duration=4.0, freq=261.63
    )

    off = 244.80
    cards_clean_01 = [
        (OVERLAYS_DIR / "l01_card05_topic1.png", round(246.0 - off, 2), round(294.0 - off, 2)),
        (OVERLAYS_DIR / "l01_card06_definition.png", round(341.0 - off, 2), round(363.5 - off, 2)),
        (OVERLAYS_DIR / "l01_card07_history.png", round(408.0 - off, 2), round(463.0 - off, 2)),
        (OVERLAYS_DIR / "l01_card08_mission.png", round(502.0 - off, 2), round(527.0 - off, 2)),
        (OVERLAYS_DIR / "l01_card09_diction.png", round(580.0 - off, 2), round(618.0 - off, 2)),
        (OVERLAYS_DIR / "l01_card10_quiz.png", round(675.0 - off, 2), round(720.0 - off, 2)),
        (OVERLAYS_DIR / "l01_card11_homework.png", round(770.0 - off, 2), round(812.5 - off, 2)),
    ]
    overlay_cards_and_bumpers(
        LESSONS_DIR / "01_lesson_1_multicam.mp4",
        off, round(888.50 - off, 2),
        cards_clean_01, intro_01, outro_01,
        LESSONS_DIR / "01_lesson_1_clean.mp4"
    )


if __name__ == "__main__":
    main()
