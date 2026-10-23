#!/usr/bin/env python3
"""
Автоматический монтажный конвейер v4 для вирусных Shorts / Reels / VK Клипов
курса «Тележурналистика с нуля» (Ирина Тыщенко).
- ИСПРАВЛЕН ТАЙМКОД ФИЛЬТРОВ (trim/atrim + setpts=PTS-STARTPTS до fade/afade — никаких 4-секундных зависаний плашки и обрывов звука!)
- 2-СЕКУНДНАЯ ПЛАВНАЯ АНИМАЦИЯ ПЕРЕБИВКИ с мягким звуковым переходом и плавным сглаживанием голоса на стыках
- МОЩНЫЙ ХУК В НАЧАЛЕ каждого клипа
- ЦВЕТОКОРРЕКЦИЯ SONY S-LOG3 / S-GAMUT3.CINE -> REC.709 (3D LUT DaVinci Resolve)
"""
import math
import os
import random
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FFMPEG = "/opt/homebrew/bin/ffmpeg"
SRC_DIR = Path("/Volumes/Arttistfoto/241016 Irina V/Общий")
BASE = Path("/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course")
OVERLAYS_DIR = BASE / "assets" / "overlays"
LUTS_DIR = BASE / "assets" / "luts"
SHORTS_DIR = BASE / "shorts"
SHORTS_DIR.mkdir(parents=True, exist_ok=True)

SONY_LUT = LUTS_DIR / "sony_slog3_typeA.cube"

FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

C_WHITE = (255, 255, 255, 255)
C_AMBER = (245, 180, 60, 255)
C_RED = (225, 45, 75, 255)
C_CARD_BG = (11, 18, 34, 235)


def fnt(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(FONT_BOLD, size)


def render_subtitle_png(out_path, line1, line2="", highlight_line=2, is_hook=False):
    """Рендерит прозрачный PNG 1080x1920 с крупной карточкой субтитра в нижней трети."""
    W, H = 1080, 1920
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    lines = [l.strip() for l in [line1, line2] if l.strip()]
    if not lines:
        im.save(out_path)
        return

    fsize = 42
    font_main = fnt(FONT_BLACK, fsize)
    max_w = max(int(d.textlength(l, font=font_main)) for l in lines)
    while max_w > 910 and fsize > 30:
        fsize -= 2
        font_main = fnt(FONT_BLACK, fsize)
        max_w = max(int(d.textlength(l, font=font_main)) for l in lines)
    pad_x = 40
    pad_y = 24
    line_h = 56
    box_w = min(1000, max_w + pad_x * 2)
    box_h = len(lines) * line_h + pad_y * 2 - 8

    x1 = (W - box_w) // 2
    y1 = 1525 - box_h // 2
    x2 = x1 + box_w
    y2 = y1 + box_h

    border_col = (225, 45, 75, 230) if is_hook else (245, 180, 60, 185)
    d.rounded_rectangle((x1 + 4, y1 + 6, x2 + 4, y2 + 6), radius=24, fill=(0, 0, 0, 160))
    d.rounded_rectangle((x1, y1, x2, y2), radius=24, fill=C_CARD_BG, outline=border_col, width=4 if is_hook else 3)

    if is_hook:
        badge_f = fnt(FONT_BLACK, 24)
        b_txt = "ОСТРЫЙ МОМЕНТ"
        bw = int(d.textlength(b_txt, font=badge_f)) + 62
        bx1 = (W - bw) // 2
        by1 = y1 - 44
        d.rounded_rectangle((bx1, by1, bx1 + bw, y1 - 6), radius=12, fill=C_RED)
        d.ellipse((bx1 + 16, by1 + 12, bx1 + 30, by1 + 26), fill=C_WHITE)
        d.text((bx1 + 38, by1 + 4), b_txt, font=badge_f, fill=C_WHITE)

    curr_y = y1 + pad_y - 4
    for idx, text in enumerate(lines, start=1):
        tw = int(d.textlength(text, font=font_main))
        tx = (W - tw) // 2
        color = C_AMBER if idx == highlight_line else C_WHITE
        d.text((tx + 2, curr_y + 2), text, font=font_main, fill=(0, 0, 0, 225))
        d.text((tx, curr_y), text, font=font_main, fill=color)
        curr_y += line_h

    im.save(out_path)


def generate_transition_sfx(wav_path, duration=2.0, sr=48000):
    """
    Синтезирует мягкий 2-секундный телевизионный саунд-дизайн перебивки:
    плавный входной свуш -> мягкая перемотка -> тёплый эфирный аккорд с плавным затуханием.
    """
    n_samples = int(duration * sr)
    rng = random.Random(42)
    frames = bytearray()

    for i in range(n_samples):
        t = i / sr
        # Плавная общая огибающая (fade-in 0.18s, fade-out 0.25s)
        master_env = 1.0
        if t < 0.18:
            master_env = t / 0.18
        elif t > duration - 0.25:
            master_env = max(0.0, (duration - t) / 0.25)

        # 1. Мягкий входной Whoosh (0.0 -> 0.55s)
        whoosh_env = math.exp(-((t - 0.22) / 0.15) ** 2)
        noise = (rng.random() * 2.0 - 1.0)
        sweep_freq = 160.0 + 620.0 * min(1.0, t / 0.6) ** 1.4
        whoosh = (0.22 * noise + 0.38 * math.sin(2.0 * math.pi * sweep_freq * t)) * whoosh_env

        # 2. Мягкие импульсы перемотки/загрузки (0.30 -> 1.45s)
        rewind = 0.0
        if 0.25 <= t <= 1.50:
            rt = t - 0.25
            pulse = 0.5 * (1.0 + math.sin(2.0 * math.pi * 14.0 * rt))
            tone_f = 380.0 + 240.0 * (rt / 1.25)
            rewind_env = math.sin(math.pi * (rt / 1.25))
            rewind = 0.20 * pulse * rewind_env * math.sin(2.0 * math.pi * tone_f * t)

        # 3. Тёплый эфирный аккорд + мягкий басовый импульс на выходе (1.35 -> 2.00s)
        hit = 0.0
        if t >= 1.32:
            ht = t - 1.32
            hit_env = math.exp(-ht * 4.8)
            sub_freq = 88.0 * math.exp(-ht * 2.5) + 46.0
            chime = (
                0.20 * math.sin(2.0 * math.pi * 440.0 * ht)
                + 0.15 * math.sin(2.0 * math.pi * 554.37 * ht)
                + 0.12 * math.sin(2.0 * math.pi * 659.25 * ht)
            )
            hit = (0.55 * math.sin(2.0 * math.pi * sub_freq * ht) + chime) * hit_env

        val = (whoosh + rewind + hit) * 0.48 * master_env
        val = max(-0.92, min(0.92, val))
        sample_int = int(val * 32767)
        frames.extend(struct.pack("<hh", sample_int, sample_int))

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(bytes(frames))


def render_transition_bumper(out_mp4, badge_text, title_line1, title_line2, duration=2.0, fps=25):
    """
    Создаёт 2.0-секундную плавную анимированную ТВ-перебивку 1080x1920 (50 кадров при 25 fps)
    с бегущей полосой загрузки и мягким саунд-дизайном.
    """
    tmp_b = Path(tempfile.mkdtemp(prefix="bumper_"))
    try:
        W, H = 1080, 1920
        n_frames = int(duration * fps)
        f_badge = fnt(FONT_BLACK, 30)
        f_title1 = fnt(FONT_BLACK, 52)
        f_title2 = fnt(FONT_BLACK, 44)
        f_sub = fnt(FONT_BOLD, 30)

        for idx in range(n_frames):
            p = idx / max(1, n_frames - 1)  # 0.0 -> 1.0 за все 2.0 секунды!
            # S-curve (smoothstep) для плавной анимации полосы загрузки с первого же кадра
            smooth_p = p * p * (3.0 - 2.0 * p)

            im = Image.new("RGBA", (W, H), (10, 16, 30, 255))
            d = ImageDraw.Draw(im)

            # Фоновые эфирные линии
            for y in range(0, H, 24):
                alpha_line = 18 if (y // 24) % 2 == 0 else 8
                d.line([(0, y), (W, y)], fill=(245, 180, 60, alpha_line), width=2)

            # Лёгкие динамические световые акценты в начале и конце
            rng = random.Random(idx * 17 + 7)
            if p < 0.16 or p > 0.84:
                for _ in range(5):
                    gy = rng.randint(180, H - 180)
                    gh = rng.randint(6, 24)
                    gx = rng.randint(0, 300)
                    gw = rng.randint(400, W)
                    col = (245, 180, 60, 85) if rng.random() > 0.4 else (225, 45, 75, 85)
                    d.rectangle((gx, gy, min(W, gx + gw), gy + gh), fill=col)

            # Центральная эфирная карточка
            cx1, cy1, cx2, cy2 = 70, 720, 1010, 1200
            d.rounded_rectangle((cx1 - 6, cy1 - 6, cx2 + 6, cy2 + 6), radius=36, fill=(0, 0, 0, 180))
            d.rounded_rectangle((cx1, cy1, cx2, cy2), radius=32, fill=(15, 24, 46, 248), outline=C_AMBER, width=5)

            # Красный бейдж сверху карточки с векторным индикатором REC
            bw = int(d.textlength(badge_text, font=f_badge)) + 84
            bx1 = (W - bw) // 2
            by1 = cy1 + 42
            d.rounded_rectangle((bx1, by1, bx1 + bw, by1 + 54), radius=16, fill=C_RED)
            d.ellipse((bx1 + 22, by1 + 18, bx1 + 40, by1 + 36), fill=C_WHITE)
            d.text((bx1 + 52, by1 + 9), badge_text, font=f_badge, fill=C_WHITE)

            # Заголовок в 2 строки
            tw1 = int(d.textlength(title_line1, font=f_title1))
            d.text(((W - tw1) // 2, cy1 + 135), title_line1, font=f_title1, fill=C_WHITE)

            tw2 = int(d.textlength(title_line2, font=f_title2))
            d.text(((W - tw2) // 2, cy1 + 210), title_line2, font=f_title2, fill=C_AMBER)

            # Плавная шкала загрузки на все 2 секунды (от 8% до 100%)
            bar_w = 720
            bar_x1 = (W - bar_w) // 2
            bar_y1 = cy1 + 305
            d.rounded_rectangle((bar_x1, bar_y1, bar_x1 + bar_w, bar_y1 + 22), radius=11, fill=(35, 48, 78, 255))
            fill_ratio = 0.08 + 0.92 * smooth_p
            d.rounded_rectangle(
                (bar_x1, bar_y1, bar_x1 + int(bar_w * fill_ratio), bar_y1 + 22),
                radius=11,
                fill=C_AMBER,
            )

            sub_t = "ПЕРЕМОТКА В НАЧАЛО ИСТОРИИ..."
            stw = int(d.textlength(sub_t, font=f_sub))
            sx = (W - (stw + 50)) // 2
            sy = cy1 + 350
            d.polygon([(sx, sy + 18), (sx + 18, sy + 6), (sx + 18, sy + 30)], fill=C_AMBER)
            d.polygon([(sx + 20, sy + 18), (sx + 38, sy + 6), (sx + 38, sy + 30)], fill=C_AMBER)
            d.text((sx + 50, sy), sub_t, font=f_sub, fill=(200, 215, 240, 255))

            im.convert("RGB").save(tmp_b / f"frame_{idx:03d}.png")

        wav_path = tmp_b / "sfx.wav"
        generate_transition_sfx(wav_path, duration=duration)

        subprocess.run([
            FFMPEG, "-y", "-loglevel", "error",
            "-framerate", str(fps),
            "-i", str(tmp_b / "frame_%03d.png"),
            "-i", str(wav_path),
            "-vf", "fade=t=in:st=0:d=0.15:color=0x0A101E,fade=t=out:st=1.85:d=0.15:color=0x0A101E,format=yuv420p",
            "-r", str(fps),
            "-c:v", "h264_videotoolbox", "-b:v", "11M",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-shortest",
            str(out_mp4),
        ], check=True)
    finally:
        shutil.rmtree(tmp_b, ignore_errors=True)


def assemble_short(output_name, top_overlay_png, segments, subtitles):
    """
    ВАЖНО: использует trim/atrim + setpts=PTS-STARTPTS ПЕРВЫМ фильтром в цепочке!
    Благодаря этому fade и afade работают строго по локальному времени сегмента [0..dur],
    и звук/картинка НИКОГДА не обрываются за 4 секунды до конца!
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="short_v4_"))
    try:
        seg_files = []
        for i, seg in enumerate(segments):
            seg_out = tmp_dir / f"seg_{i:02d}.mp4"
            kind = seg[0]

            if kind == "BUMPER":
                _, badge_t, t1, t2, b_dur = seg
                render_transition_bumper(seg_out, badge_t, t1, t2, duration=b_dur)
                seg_files.append(seg_out)
                continue

            _, vname, s_sec, e_sec, zoom, gain_db, trans_mode = seg
            src_path = SRC_DIR / vname
            dur = round(e_sec - s_sec, 3)

            fast_ss = max(0.0, s_sec - 4.0)
            exact_ss = round(s_sec - fast_ss, 3)
            decode_span = round(exact_ss + dur + 0.5, 3)

            if zoom > 1.05:
                crop_filter = "crop=1080:1920:1845:90,scale=1080:1920"
            else:
                crop_filter = "crop=1215:2160:1780:0,scale=1080:1920"

            # trim + setpts=PTS-STARTPTS сбрасывает таймкод в 0.0 ровно на точке входа!
            vf_parts = [
                f"trim=start={exact_ss:.3f}:duration={dur:.3f}",
                "setpts=PTS-STARTPTS",
                crop_filter,
                f"lut3d='{SONY_LUT}'",
                "eq=contrast=1.06:saturation=1.08:brightness=0.01",
                "unsharp=3:3:0.45:3:3:0.0",
            ]
            if "smooth_in" in trans_mode:
                vf_parts.append("fade=t=in:st=0:d=0.16:color=0x0A101E")
            if "smooth_out" in trans_mode:
                vf_parts.append(f"fade=t=out:st={max(0.05, dur - 0.16):.3f}:d=0.16:color=0x0A101E")
            vf_parts.append("format=yuv420p")
            vf = ",".join(vf_parts)

            # Аудио: atrim + asetpts=PTS-STARTPTS + плавное сглаживание голоса на входе и выходе
            fade_in_d = 0.12 if "smooth_in" in trans_mode else 0.035
            fade_out_d = 0.14 if "smooth_out" in trans_mode else 0.035
            af_parts = [
                f"atrim=start={exact_ss:.3f}:duration={dur:.3f}",
                "asetpts=PTS-STARTPTS",
            ]
            if abs(gain_db) > 0.1:
                af_parts.append(f"volume={gain_db}dB")
            af_parts.append("alimiter=limit=0.92:attack=5:release=50")
            af_parts.append(f"afade=t=in:st=0:d={fade_in_d:.3f}")
            af_parts.append(f"afade=t=out:st={max(0.02, dur - fade_out_d):.3f}:d={fade_out_d:.3f}")
            af = ",".join(af_parts)

            cmd = [
                FFMPEG, "-y", "-loglevel", "error",
                "-ss", f"{fast_ss:.3f}",
                "-t", f"{decode_span:.3f}",
                "-i", str(src_path),
                "-vf", vf,
                "-af", af,
                "-r", "25",
                "-c:v", "h264_videotoolbox", "-b:v", "11M",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                str(seg_out),
            ]
            subprocess.run(cmd, check=True)
            seg_files.append(seg_out)

        concat_list = tmp_dir / "concat.txt"
        with open(concat_list, "w") as f:
            for sf in seg_files:
                f.write(f"file '{sf}'\n")

        merged_video = tmp_dir / "merged.mp4"
        subprocess.run([
            FFMPEG, "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c", "copy", str(merged_video)
        ], check=True)

        inputs = ["-i", str(merged_video), "-i", str(top_overlay_png)]
        filter_parts = ["[0:v][1:v]overlay=0:0[v0]"]
        last_v = "v0"

        for idx, sub_item in enumerate(subtitles):
            st, et, l1, l2, is_hook = sub_item
            sub_png = tmp_dir / f"sub_{idx:02d}.png"
            render_subtitle_png(sub_png, l1, l2, highlight_line=2 if l2 else 1, is_hook=is_hook)
            inputs.extend(["-i", str(sub_png)])
            inp_idx = idx + 2
            next_v = f"v{idx + 1}"
            filter_parts.append(
                f"[{last_v}][{inp_idx}:v]overlay=0:0:enable='between(t,{st:.2f},{et:.2f})'[{next_v}]"
            )
            last_v = next_v

        final_out = SHORTS_DIR / output_name
        cmd_final = [
            FFMPEG, "-y", "-loglevel", "error",
            *inputs,
            "-filter_complex", ";".join(filter_parts),
            "-map", f"[{last_v}]", "-map", "0:a",
            "-c:v", "h264_videotoolbox", "-b:v", "10M",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(final_out)
        ]
        subprocess.run(cmd_final, check=True)
        print(f"✅ Готов эталонный клип v4: {final_out}")
        return final_out
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def build_all():
    # =========================================================================
    # КЛИП №1: Выезд в станицу (Горячий Ключ)
    # 0.00..8.95s — ХУК про мужа с ружьём
    # 8.95..10.95s — 2-секундная плавная ТВ-перебивка
    # 10.95s..финал — Полная история с начала
    # =========================================================================
    c1_segments = [
        ("VIDEO", "C1279.MP4", 414.95, 423.90, 1.12, 2.5, "smooth_out"),
        ("BUMPER", "РЕАЛЬНЫЙ СЛУЧАЙ", "С ЧЕГО ВСЁ НАЧАЛОСЬ:", "ВЫЕЗД В ГОРНУЮ СТАНИЦУ", 2.0),
        ("VIDEO", "C1279.MP4", 47.85, 98.35, 1.0, 2.0, "smooth_in"),
        ("VIDEO", "C1279.MP4", 204.40, 242.16, 1.0, 2.0, ""),
        ("VIDEO", "C1279.MP4", 314.20, 324.40, 1.12, 2.0, ""),
        ("VIDEO", "C1279.MP4", 391.05, 434.70, 1.12, 2.0, ""),
        ("VIDEO", "C1279.MP4", 547.00, 558.25, 1.0, 2.0, ""),
        ("VIDEO", "C1279.MP4", 597.35, 612.75, 1.12, 2.0, "smooth_out"),
    ]
    c1_subs = [
        (0.0, 4.4, "«Знаете, лучше уж вы", "ПОБЫСТРЕЕ ОТСЮДА УЕЗЖАЙТЕ!»", True),
        (4.4, 8.9, "«Он сейчас на охоте С РУЖЬЁМ —", "вернётся, не поздоровится всем!»", True),
        # 8.95..10.95 — 2-секундная перебивка
        (11.0, 24.5, "Совещание в администрации:", "я в строгом платье и на каблуках", False),
        (24.5, 36.8, "Подходит директор: «Ирина, срочно", "выезжаем со службой в станицу!»", False),
        (36.8, 61.4, "Сигнал: «В станице молодая мать", "ведёт аморальный образ жизни...»", False),
        (61.4, 79.0, "Приезжаем: выходит совсем юная", "девушка на последних месяцах...", False),
        (79.0, 99.2, "Заходим в дом с проверкой —", "а там СТЕРИЛЬНАЯ ЧИСТОТА!", False),
        (99.2, 109.4, "Но открываются шкафы — а еды нет...", "Мне стало стыдно, что нет даже пряника", False),
        (109.4, 126.0, "Наедине она просит: «Не пишите,", "что муж запрещает мне работать!»", False),
        (126.0, 142.0, "«И лучше уезжайте побыстрее:", "он идёт с охоты С РУЖЬЁМ!»", False),
        (142.0, 153.0, "Я задумалась: «Блин, куда же тут", "бежать на каблуках, если он с ружьём?!»", False),
        (153.0, 164.3, "Я не стала раздувать скандал,", "написала мягко и подняла соцслужбы", False),
        (164.3, 179.6, "Итог: встретила её позже — ей дали", "квартиру, работает и пошла учиться!", False),
    ]
    assemble_short(
        "01_stanitsa_husband_with_gun_short.mp4",
        OVERLAYS_DIR / "overlay_clip1.png",
        c1_segments,
        c1_subs,
    )

    # =========================================================================
    # КЛИП №2: Бэкстейдж «Иконоскоп / Наши на ТВ к моим матеркам привыкли!»
    # 0.00..9.65s — ХУК
    # 9.65..11.65s — 2-секундная плавная ТВ-перебивка
    # 11.65..65.00s — Полная сцена без единого обрыва звука!
    # =========================================================================
    c2_segments = [
        ("VIDEO", "C1256.MP4", 709.15, 716.30, 1.12, 3.5, ""),
        ("VIDEO", "C1262.MP4", 129.95, 132.45, 1.12, 3.5, "smooth_out"),
        ("BUMPER", "ЗА КУЛИСАМИ ЗАПИСИ", "ЗА МИНУТУ ДО ЭТОГО:", "КАК МЫ ПИСАЛИ УРОК №2", 2.0),
        ("VIDEO", "C1256.MP4", 668.90, 682.80, 1.0, 2.0, "smooth_in"),
        ("VIDEO", "C1256.MP4", 684.40, 686.50, 1.12, 14.0, ""),
        ("VIDEO", "C1256.MP4", 687.20, 688.85, 1.12, 3.5, ""),
        ("VIDEO", "C1256.MP4", 691.80, 696.80, 1.0, 15.0, ""),
        ("VIDEO", "C1256.MP4", 700.00, 704.35, 1.0, 3.0, ""),
        ("VIDEO", "C1256.MP4", 705.35, 716.55, 1.12, 3.0, ""),
        ("VIDEO", "C1256.MP4", 724.00, 728.60, 1.12, 3.0, ""),
        ("VIDEO", "C1256.MP4", 731.40, 739.45, 1.0, 2.0, ""),
        ("VIDEO", "C1262.MP4", 129.95, 132.45, 1.12, 3.5, "smooth_out"),
    ]
    c2_subs = [
        (0.0, 7.1, "— ТВОЮ МАТЬ! Извиняюсь, ребята,", "наши на ТВ привыкли к моим матеркам!", True),
        (7.1, 9.6, "— Ты бы хоть камеру отключал!", "Чё-то она у тебя включена!", True),
        # 9.65..11.65 — 2-секундная перебивка
        (11.7, 18.5, "В 1931 году Владимир Зворыкин", "создал трубку — ИКОНОСКОП", False),
        (18.5, 25.5, "Это изобретение позволило", "телевидению стать продуктовым...", False),
        (25.5, 29.3, "— ТВОЮ МАТЬ!", "Можно так сказать?!", False),
        (29.3, 34.3, "[Сын за камерой]: Раз в 10 минут", "запинаешься и так переживаешь!", False),
        (34.3, 38.6, "— Что, не говорить всё?", "Ладно, пробуем ещё раз!", False),
        (38.6, 43.5, "Дубль №2: ...позволило стать", "продуктовым... ТВОЮ МАТЬ!", False),
        (43.5, 49.8, "Извиняюсь, ребята! Наши-то на ТВ", "привыкли к моим матеркам!", False),
        (49.8, 54.4, "Дубль №3: В СССР телевидение...", "Да что ты, всё пошло не так!", False),
        (54.4, 62.5, "Артём, ещё раз я начну! Идеально:", "«продукт массового потребления!»", False),
        (62.5, 65.0, "— Ты бы хоть камеру отключал!", "Чё-то она у тебя включена!", False),
    ]
    assemble_short(
        "02_backstage_ikonoskop_short.mp4",
        OVERLAYS_DIR / "overlay_clip2.png",
        c2_segments,
        c2_subs,
    )

    # =========================================================================
    # КЛИП №3: Сургут −35°C (На буровую вышку в валенках 44 размера)
    # 0.00..13.85s — ХУК
    # 13.85..15.85s — 2-секундная плавная ТВ-перебивка
    # 15.85..120.30s — Полная история
    # =========================================================================
    c3_segments = [
        ("VIDEO", "C1270.MP4", 64.90, 70.25, 1.12, 2.5, ""),
        ("VIDEO", "C1270.MP4", 119.80, 128.30, 1.12, 2.5, "smooth_out"),
        ("BUMPER", "ЭКСТРИМ НА СЪЁМКАХ", "КАК ЭТО БЫЛО:", "200 КМ ОТ СУРГУТА • −35°C", 2.0),
        ("VIDEO", "C1270.MP4", 55.15, 107.55, 1.0, 2.0, "smooth_in"),
        ("VIDEO", "C1270.MP4", 162.15, 200.30, 1.12, 2.0, ""),
        ("VIDEO", "C1270.MP4", 242.20, 256.10, 1.12, 2.5, "smooth_out"),
    ]
    c3_subs = [
        (0.0, 5.3, "Сибирь, мороз МИНУС 35 ГРАДУСОВ!", "Представляете такой колотун?!", True),
        (5.3, 13.8, "Аппаратура замерзает на ходу —", "и мы БЕГОМ лезем на буровую вышку!", True),
        # 13.85..15.85 — 2-секундная перебивка
        (15.9, 30.4, "Приезжаем на месторождение за 200 км:", "а там мороз — МИНУС 35 ГРАДУСОВ!", False),
        (30.4, 39.4, "Бригадир: «Посидите в вагончике,", "куда же вы на вышку в такой мороз?»", False),
        (39.4, 48.4, "«Столько километров проехать и сидеть?!", "Нет уж, я иду с вами!»", False),
        (48.4, 68.2, "На меня надели валенки 44-го размера,", "фуфайку поверх дублёнки и шпагат!", False),
        (68.2, 86.0, "Лезу на вышку: нога в валенке", "как карандаш в стакане!", False),
        (86.0, 106.4, "И думаю: какая же я молодец,", "прямо ПАРЮ НАД ЗЕМЛЁЙ на поворотах!", False),
        (106.4, 114.4, "В вагончике хвастаюсь: «Видели,", "как я почти бегом забиралась?!»", False),
        (114.4, 120.3, "Бригадир: «Конечно! Я же вас сзади", "ЗА БАШЛЫК на поворотах поднимал!»", False),
    ]
    assemble_short(
        "03_surgut_frost35_valenki_short.mp4",
        OVERLAYS_DIR / "overlay_clip3.png",
        c3_segments,
        c3_subs,
    )


if __name__ == "__main__":
    build_all()
