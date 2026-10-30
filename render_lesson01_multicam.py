#!/usr/bin/env python3
"""
Двухкамерный монтаж (Общий + Крупный план) для Занятия 1:
«Знакомство с мастером. Журналистика от древности до наших дней»
Источники (уже покрашенные в DaVinci Resolve, синхрон 0.0000 сек):
- Общий: /Volumes/ArtemTys/В работе/Курс/Общий/C1253.mp4
- Крупный: /Volumes/ArtemTys/В работе/Курс/Крупный/Timeline 1.mp4
"""
import os
import subprocess
from pathlib import Path

FFMPEG = "/opt/homebrew/bin/ffmpeg"
WIDE_SRC = "/Volumes/ArtemTys/В работе/Курс/Общий/C1253.mp4"
CLOSE_SRC = "/Volumes/ArtemTys/В работе/Курс/Крупный/Timeline 1.mp4"
OUT_DIR = Path("/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course/lessons")
OUT_FILE = OUT_DIR / "01_lesson_1_multicam.mp4"

# Четыре непрерывных чистовых блока (между ними вырезаны все тех. реплики и дубли):
# На каждом стыке между блоками происходит смена плана (Общий -> Крупный),
# что на 100% маскирует монтажную склейку.
TAKES = [
    {
        "name": "take1",
        "start": 9.00,
        "end": 93.60,
        "fade_in": True,
        "fade_out": False,
        # Интервалы (в координатах исходника), где включается КРУПНЫЙ план:
        "close_intervals": [
            (31.20, 50.30),   # Личная история про маму и медколледж
            (72.50, 81.84),   # «Мама мной гордилась и говорила: моя дочка соображает!»
        ],
    },
    {
        "name": "take2",
        "start": 111.75,
        "end": 179.95,
        "fade_in": False,
        "fade_out": False,
        # Начинается с КРУПНОГО плана, чтобы скрыть склейку 93.60 -> 111.75
        "close_intervals": [
            (111.75, 132.60), # СМИ: «Горячий Ключ», РЕН-ТВ, ГТРК «ЛянторИнформ»
            (159.90, 171.15), # Первая школьная телестудия «Школа плюс ТВ», 100+ учеников
        ],
    },
    {
        "name": "take3",
        "start": 210.20,
        "end": 677.25,
        "fade_in": False,
        "fade_out": False,
        # Начинается с КРУПНОГО плана, чтобы скрыть склейку 179.95 -> 210.20
        "close_intervals": [
            (210.20, 230.70), # Детско-юношеская телестудия «3Т» г. Тюмени
            (278.90, 300.78), # Домашние задания и цитата Суворова «Тяжело в учении — легко в бою»
            (354.30, 388.00), # Доверие героя и познавательно-досуговая журналистика
            (422.20, 451.20), # Цитата Пушкина «Глаголом жечь сердца людей», Демосфен и Цицерон
            (522.90, 555.75), # Монета «газета» и первый репортаж Петра I о Полтавском бое
            (587.10, 617.40), # «Каждый из вас талантлив и трудолюбив!» + качества журналиста
        ],
    },
    {
        "name": "take4",
        "start": 688.70,
        "end": 957.30,
        "fade_in": False,
        "fade_out": True,
        # Начинается с КРУПНОГО плана, чтобы скрыть склейку 677.25 -> 688.70
        # и показать крупно артикуляцию скороговорки «Расскажите про покупки»
        "close_intervals": [
            (688.70, 735.00), # Тренировка скороговорки 3 раза (крупный план артикуляции)
            (790.94, 837.86), # Вопросы №2 и №3 для закрепления урока
            (882.98, 921.60), # Что приготовить к следующему уроку (микрофон, зеркало, телефон)
        ],
    },
]

def render_take(take, idx):
    t_start = take["start"]
    t_end = take["end"]
    dur = round(t_end - t_start, 3)
    tmp_out = f"/tmp/lesson01_multicam_{take['name']}.mp4"

    # Формируем выражение enable для фильтра overlay (в локальном времени сегмента 0..dur)
    between_exprs = []
    for c_start, c_end in take["close_intervals"]:
        rel_s = max(0.0, round(c_start - t_start, 3))
        rel_e = min(dur, round(c_end - t_start, 3))
        between_exprs.append(f"between(t,{rel_s},{rel_e})")
    enable_str = "+".join(between_exprs) if between_exprs else "0"

    v_post = ""
    a_post = ""
    if take["fade_in"]:
        v_post += ",fade=t=in:st=0:d=0.35"
        a_post += ",afade=t=in:st=0:d=0.20"
    if take["fade_out"]:
        v_post += f",fade=t=out:st={round(dur - 0.6, 2)}:d=0.60"
        a_post += f",afade=t=out:st={round(dur - 0.6, 2)}:d=0.60"

    filter_complex = (
        f"[0:v]fps=25,scale=1920:1080:flags=lanczos,format=yuv420p,setpts=PTS-STARTPTS[wide];"
        f"[1:v]fps=25,scale=1920:1080:flags=lanczos,format=yuv420p,setpts=PTS-STARTPTS[close];"
        f"[wide][close]overlay=0:0:shortest=1:enable='{enable_str}'{v_post}[vout];"
        f"[0:a]aresample=48000,asetpts=PTS-STARTPTS{a_post}[aout]"
    )

    cmd = [
        FFMPEG, "-y",
        "-hwaccel", "videotoolbox", "-ss", str(t_start), "-t", str(dur), "-i", WIDE_SRC,
        "-hwaccel", "videotoolbox", "-ss", str(t_start), "-t", str(dur), "-i", CLOSE_SRC,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-t", str(dur),
        "-c:v", "h264_videotoolbox", "-b:v", "8000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        tmp_out
    ]
    print(f"▶ Рендерим {take['name']} ({t_start:.2f}s -> {t_end:.2f}s, длит. {dur:.2f}s)...")
    subprocess.run(cmd, check=True)
    return tmp_out

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp_files = []
    for idx, take in enumerate(TAKES):
        tmp_files.append(render_take(take, idx))

    concat_list = "/tmp/lesson01_multicam_concat.txt"
    with open(concat_list, "w") as f:
        for tf in tmp_files:
            f.write(f"file '{tf}'\n")

    # Склеиваем 4 чистовых блока с нормализацией звука EBU R128 (-16 LUFS), видео копируем без перекодирования!
    cmd_concat = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:v", "copy",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(OUT_FILE)
    ]
    print("▶ Финальная склейка и мастеринг звука (-16 LUFS)...")
    subprocess.run(cmd_concat, check=True)

    for tf in tmp_files + [concat_list]:
        if os.path.exists(tf):
            os.remove(tf)

    size_mb = os.path.getsize(OUT_FILE) / (1024 * 1024)
    print(f"✅ Занятие 1 (двухкамерный монтаж) готово: {OUT_FILE} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
