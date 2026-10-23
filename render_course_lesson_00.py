#!/usr/bin/env python3
"""
Рендер пилотного урока: «Урок 0. Вводное слово автора» (C1265.MP4).
Профессиональный монтаж двух планов (мультикам 4K FX30):
- Часть 1: Общий план (0:00.0 - 0:43.0) + плашка титра спикера
- Часть 2: Крупный план (0:46.2 - 1:29.8, зум-акцент 1.25x)
- Часть 3: Общий план (1:53.6 - 2:19.8, финал)
- Эфирные заставки 16:9 + звук -16 LUFS + LUT Sony S-Log3 Type A
"""
import os, subprocess
from pathlib import Path

BASE = Path("/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course")
SRC_VIDEO = Path("/Volumes/Arttistfoto/241016 Irina V/Общий/C1265.MP4")
LUT_PATH = BASE / "assets/luts/sony_slog3_typeA.cube"
OVERLAYS_DIR = BASE / "assets/course_overlays"
LESSONS_DIR = BASE / "lessons"
LESSONS_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = LESSONS_DIR / "00_intro_greeting_lesson.mp4"
INTRO_BUMPER = OVERLAYS_DIR / "intro_lesson00_bumper.mp4"
OUTRO_BUMPER = OVERLAYS_DIR / "outro_lesson00_bumper.mp4"
LOWER_THIRD = OVERLAYS_DIR / "lower_third_author_16x9.png"

FFMPEG = "/opt/homebrew/bin/ffmpeg"

def main():
    print(f"🎬 Рендерим Урок 0: Вводное слово автора...")
    print(f"📁 Источник: {SRC_VIDEO}")

    # Сегмент 1: 0.0 -> 43.0 (Общий план + Нижний титр с 3 по 12 сек)
    seg1_tmp = "/tmp/lesson00_seg1.mp4"
    dur1 = 43.0
    cmd1 = [
        FFMPEG, "-y",
        "-i", str(SRC_VIDEO),
        "-loop", "1", "-t", str(dur1), "-i", str(LOWER_THIRD),
        "-filter_complex",
        f"[0:v]trim=start=0:duration={dur1},setpts=PTS-STARTPTS,lut3d={LUT_PATH},scale=1920:1080:flags=lanczos[base];"
        f"[1:v]fade=t=in:st=3:d=0.5:alpha=1,fade=t=out:st=11:d=0.5:alpha=1[titr];"
        f"[base][titr]overlay=0:0:enable='between(t,2.5,12)'[v1];"
        f"[0:a]atrim=start=0:duration={dur1},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.1[a1]",
        "-map", "[v1]", "-map", "[a1]",
        "-t", str(dur1),
        "-c:v", "h264_videotoolbox", "-b:v", "6000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        seg1_tmp
    ]
    print("▶ Экспорт сегмента 1 (Общий план + титр)...")
    subprocess.run(cmd1, check=True)

    # Сегмент 2: 46.2 -> 129.8 (Крупный план / Crop 1.25x из 4K)
    seg2_tmp = "/tmp/lesson00_seg2.mp4"
    start2 = 46.2
    dur2 = 129.8 - 46.2  # 83.6 sec
    cmd2 = [
        FFMPEG, "-y",
        "-i", str(SRC_VIDEO),
        "-filter_complex",
        f"[0:v]trim=start={start2}:duration={dur2},setpts=PTS-STARTPTS,crop=w=3072:h=1728:x=384:y=216,scale=1920:1080:flags=lanczos,lut3d={LUT_PATH}[v2];"
        f"[0:a]atrim=start={start2}:duration={dur2},asetpts=PTS-STARTPTS[a2]",
        "-map", "[v2]", "-map", "[a2]",
        "-t", str(dur2),
        "-c:v", "h264_videotoolbox", "-b:v", "6000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        seg2_tmp
    ]
    print("▶ Экспорт сегмента 2 (Крупный план 1.25x)...")
    subprocess.run(cmd2, check=True)

    # Сегмент 3: 153.6 -> 219.8 (Общий план, финал)
    seg3_tmp = "/tmp/lesson00_seg3.mp4"
    start3 = 153.6
    dur3 = 219.8 - 153.6  # 66.2 sec
    cmd3 = [
        FFMPEG, "-y",
        "-i", str(SRC_VIDEO),
        "-filter_complex",
        f"[0:v]trim=start={start3}:duration={dur3},setpts=PTS-STARTPTS,lut3d={LUT_PATH},scale=1920:1080:flags=lanczos[v3];"
        f"[0:a]atrim=start={start3}:duration={dur3},asetpts=PTS-STARTPTS,afade=t=out:st={dur3-0.5}:d=0.5[a3]",
        "-map", "[v3]", "-map", "[a3]",
        "-t", str(dur3),
        "-c:v", "h264_videotoolbox", "-b:v", "6000k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        seg3_tmp
    ]
    print("▶ Экспорт сегмента 3 (Финал, общий план)...")
    subprocess.run(cmd3, check=True)

    # Финальная склейка через concat с нормализацией громкости EBU R128 (-16 LUFS)
    concat_list = "/tmp/lesson00_concat.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{INTRO_BUMPER}'\n")
        f.write(f"file '{seg1_tmp}'\n")
        f.write(f"file '{seg2_tmp}'\n")
        f.write(f"file '{seg3_tmp}'\n")
        f.write(f"file '{OUTRO_BUMPER}'\n")

    cmd_concat = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v", "h264_videotoolbox", "-b:v", "5500k", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(OUT_FILE)
    ]
    print("▶ Финальная сборка с нормализацией EBU R128...")
    subprocess.run(cmd_concat, check=True)

    # Удаляем временные файлы
    for tmp in [seg1_tmp, seg2_tmp, seg3_tmp, concat_list]:
        if os.path.exists(tmp):
            os.remove(tmp)

    size_mb = os.path.getsize(OUT_FILE) / (1024 * 1024)
    print(f"✅ Урок 0 готов: {OUT_FILE} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
