#!/usr/bin/env python3
"""
Генератор нового визуального брендбука, оформления YouTube/VK и графических плашек
для курса «Тележурналистика с нуля» (Ирина Тыщенко).
"""
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageOps

BASE = Path("/Users/artemtysenko/Projects/Antigraviti/tv-journalism-course")
FRAMES_DIR = BASE / "assets" / "frames"
BRAND_DIR = BASE / "assets" / "brandbook"
OVERLAYS_DIR = BASE / "assets" / "overlays"

BRAND_DIR.mkdir(parents=True, exist_ok=True)
OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)

# Шрифты macOS с отличной кириллицей
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_GEORGIA_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
FONT_IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"

# Палитра «Документальный Нео-Репортаж»
C_NAVY_DARK = (11, 18, 34)       # #0B1222
C_NAVY_MID = (22, 37, 68)        # #162544
C_RED_REC = (225, 29, 72)        # #E11D48
C_AMBER = (245, 180, 60)         # #F5B43C
C_CREAM = (248, 245, 238)        # #F8F5EE
C_SLATE = (148, 163, 184)        # #94A3B8


def fnt(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(FONT_BOLD, size)


def enhance_portrait(img_path, target_size=None):
    """Делает исходный 4K S-Log кадр контрастным, сочным и кинематографичным."""
    im = Image.open(img_path).convert("RGB")
    im = ImageEnhance.Contrast(im).enhance(1.28)
    im = ImageEnhance.Color(im).enhance(1.25)
    im = ImageEnhance.Brightness(im).enhance(1.03)
    im = ImageEnhance.Sharpness(im).enhance(1.35)
    if target_size:
        im = ImageOps.fit(im, target_size, method=Image.Resampling.LANCZOS, centering=(0.62, 0.35))
    return im


def draw_studio_bokeh(canvas, seed_offset=0):
    """Рисует глубокий студийный фон с мягкими источниками света (боке) и сеткой видоискателя."""
    w, h = canvas.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Крупные световые пятна (синий контровой и тёплый янтарный студийный свет)
    spots = [
        (int(w * 0.18), int(h * 0.25), int(min(w, h) * 0.45), (30, 64, 175, 95)),
        (int(w * 0.78), int(h * 0.22), int(min(w, h) * 0.38), (225, 29, 72, 70)),
        (int(w * 0.55), int(h * 0.72), int(min(w, h) * 0.42), (245, 158, 11, 68)),
        (int(w * 0.12), int(h * 0.80), int(min(w, h) * 0.30), (56, 189, 248, 50)),
    ]
    for cx, cy, r, col in spots:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=min(w, h) // 7))
    canvas.alpha_composite(overlay)

    # Мелкие огни студийного боке
    bokeh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bokeh)
    for i in range(18):
        angle = (i * 1.7 + seed_offset)
        bx = int((math.sin(angle * 1.3) * 0.45 + 0.5) * w)
        by = int((math.cos(angle * 0.9) * 0.42 + 0.5) * h)
        br = int(12 + (i % 5) * 14)
        col = (245, 180, 60, 38) if i % 2 == 0 else (96, 165, 250, 32)
        bd.ellipse((bx - br, by - br, bx + br, by + br), fill=col, outline=(255, 255, 255, 25), width=2)
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(radius=6))
    canvas.alpha_composite(bokeh)


def draw_viewfinder_hud(draw, w, h, margin=48, title_tag="BROADCAST 4K  •  25 FPS  •  REC"):
    """Рисует телевизионные уголки видоискателя и статусную строку камеры."""
    c_line = (255, 255, 255, 90)
    L = 36
    th = 3
    # 4 угла
    corners = [
        (margin, margin, 1, 1),
        (w - margin, margin, -1, 1),
        (margin, h - margin, 1, -1),
        (w - margin, h - margin, -1, -1),
    ]
    for x, y, dx, dy in corners:
        draw.line([(x, y), (x + dx * L, y)], fill=c_line, width=th)
        draw.line([(x, y), (x, y + dy * L)], fill=c_line, width=th)

    # REC badge
    rec_x, rec_y = margin + 22, margin + 16
    draw.rounded_rectangle((rec_x, rec_y, rec_x + 110, rec_y + 38), radius=8, fill=(225, 29, 72, 230))
    draw.ellipse((rec_x + 14, rec_y + 12, rec_x + 28, rec_y + 26), fill=(255, 255, 255, 255))
    draw.text((rec_x + 36, rec_y + 6), "LIVE", font=fnt(FONT_BLACK, 19), fill=(255, 255, 255, 255))

    draw.text((rec_x + 126, rec_y + 8), title_tag, font=fnt(FONT_BOLD, 18), fill=(226, 232, 240, 200))


def build_youtube_banner():
    """Создаёт шапку YouTube (2560x1440 с безопасной зоной 1546x423 по центру)."""
    W, H = 2560, 1440
    canvas = Image.new("RGBA", (W, H), (*C_NAVY_DARK, 255))
    draw_studio_bokeh(canvas, seed_offset=1)

    # Безопасная зона YouTube: X [507..2053], Y [508..931]
    sx1, sy1, sx2, sy2 = 507, 508, 2053, 931

    # Вставляем портрет Ирины справа внутри безопасной зоны с мягкой маской
    portrait_path = FRAMES_DIR / "c1279_4k.jpg"
    if portrait_path.exists():
        im = Image.open(portrait_path).convert("RGB")
        im = ImageEnhance.Contrast(im).enhance(1.30)
        im = ImageEnhance.Color(im).enhance(1.25)
        # Вырезаем квадрат/вертикаль вокруг Ирины
        # На 3840x2160 Ирина в районе X: 1650..3250, Y: 180..1850
        crop_irina = im.crop((1700, 180, 3250, 1730)).resize((520, 520), Image.Resampling.LANCZOS)

        # Круглая / капсульная рамка с золотым свечением
        px, py = 1490, 460
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse((px - 25, py - 25, px + 545, py + 545), fill=(245, 180, 60, 95))
        glow = glow.filter(ImageFilter.GaussianBlur(30))
        canvas.alpha_composite(glow)

        mask = Image.new("L", (520, 520), 0)
        md = ImageDraw.Draw(mask)
        md.ellipse((0, 0, 520, 520), fill=255)

        canvas.paste(crop_irina, (px, py), mask)
        d_ring = ImageDraw.Draw(canvas)
        d_ring.ellipse((px - 4, py - 4, px + 524, py + 524), outline=(245, 180, 60, 240), width=6)
        d_ring.ellipse((px - 14, py - 14, px + 534, py + 534), outline=(255, 255, 255, 60), width=2)

    d = ImageDraw.Draw(canvas)
    draw_viewfinder_hud(d, W, H, margin=440, title_tag="ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ  •  АВТОРСКИЙ КАНАЛ")

    # Текстовый блок в левой части безопасной зоны (X = 540..1460, Y = 540..900)
    # Плашка-бейдж
    bx, by = 545, 535
    d.rounded_rectangle((bx, by, bx + 470, by + 46), radius=10, fill=(225, 29, 72, 240))
    d.ellipse((bx + 18, by + 15, bx + 34, by + 31), fill=(255, 255, 255, 255))
    d.text((bx + 46, by + 9), "25+ ЛЕТ В ЭФИРЕ И ПОЛЯХ", font=fnt(FONT_BLACK, 22), fill=(255, 255, 255, 255))

    # Главный заголовок
    d.text((545, 598), "ТЕЛЕЖУРНАЛИСТИКА", font=fnt(FONT_BLACK, 64), fill=(255, 255, 255, 255))
    d.text((545, 672), "С НУЛЯ  •  ИРИНА ТЫЩЕНКО", font=fnt(FONT_BOLD, 42), fill=(*C_AMBER, 255))

    # Слоган в курсивном/классическом стиле
    d.line([(545, 742), (1420, 742)], fill=(255, 255, 255, 55), width=2)
    d.text((545, 758), "«Журналистика — это не профессия. Это состояние души»", font=fnt(FONT_GEORGIA_B, 27), fill=(248, 245, 238, 245))

    # Теги рубрик внизу безопасной зоны
    tags = ["● Будни журналиста", "● Секреты интервью", "● Сюжеты и стендап"]
    tx = 545
    ty = 822
    for t in tags:
        tw = int(d.textlength(t, font=fnt(FONT_BOLD, 21))) + 36
        d.rounded_rectangle((tx, ty, tx + tw, ty + 44), radius=22, fill=(30, 41, 59, 210), outline=(255, 255, 255, 65), width=2)
        d.text((tx + 18, ty + 9), t, font=fnt(FONT_BOLD, 21), fill=(226, 232, 240, 255))
        tx += tw + 16

    out_path = BRAND_DIR / "01_youtube_banner_2560x1440.png"
    canvas.convert("RGB").save(out_path, quality=95)
    # Также сохраним кроп безопасной зоны (витрина для предпросмотра)
    preview_path = BRAND_DIR / "01_youtube_banner_preview_crop.png"
    canvas.crop((400, 420, 2160, 1020)).convert("RGB").save(preview_path, quality=95)
    return out_path, preview_path


def build_channel_avatar():
    """Создаёт аватарку YouTube / VK / Telegram (1000x1000)."""
    S = 1000
    canvas = Image.new("RGBA", (S, S), (*C_NAVY_DARK, 255))
    draw_studio_bokeh(canvas, seed_offset=3)

    portrait_path = FRAMES_DIR / "c1279_4k.jpg"
    if portrait_path.exists():
        im = Image.open(portrait_path).convert("RGB")
        im = ImageEnhance.Contrast(im).enhance(1.30)
        im = ImageEnhance.Color(im).enhance(1.26)
        crop_irina = im.crop((1760, 160, 3160, 1560)).resize((S, S), Image.Resampling.LANCZOS)

        # Затемнение краёв и низа для читаемости бейджа
        vignette = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vignette)
        for y in range(int(S * 0.58), S):
            alpha = int(235 * ((y - S * 0.58) / (S * 0.42)) ** 1.3)
            vd.line([(0, y), (S, y)], fill=(11, 18, 34, alpha))

        base = crop_irina.convert("RGBA")
        base.alpha_composite(vignette)
        canvas = base

    d = ImageDraw.Draw(canvas)
    # Золотое кольцо по периметру (под круглую аватарку YouTube/Telegram)
    d.ellipse((18, 18, S - 18, S - 18), outline=(*C_AMBER, 240), width=14)
    d.ellipse((38, 38, S - 38, S - 38), outline=(255, 255, 255, 80), width=3)

    # Плашка в нижней части
    d.rounded_rectangle((170, 760, 830, 832), radius=36, fill=(225, 29, 72, 245))
    d.ellipse((205, 784, 229, 808), fill=(255, 255, 255, 255))
    d.text((248, 773), "ИРИНА ТЫЩЕНКО • ТВ", font=fnt(FONT_BLACK, 36), fill=(255, 255, 255, 255))

    out_path = BRAND_DIR / "02_avatar_youtube_vk_1000x1000.png"
    canvas.convert("RGB").save(out_path, quality=95)
    return out_path


def build_short_top_overlay(filename, kicker, line1, line2, accent_color=C_AMBER):
    """
    Создаёт прозрачный PNG-оверлей 1080x1920 для вертикального клипа:
    - верхний и нижний мягкий кинематографичный градиент (чтобы плашка и субтитры читались идеально)
    - стильная эфирная плашка сверху (Glassmorphism + REC + заголовок)
    - плашка спикера / водяной знак канала
    """
    W, H = 1080, 1920
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # Верхний градиент (0..420)
    for y in range(420):
        a = int(195 * (1.0 - (y / 420.0)) ** 1.5)
        d.line([(0, y), (W, y)], fill=(8, 13, 26, a))

    # Нижний градиент под крупные субтитры (1280..1920)
    for y in range(1280, H):
        a = int(225 * ((y - 1280) / (H - 1280.0)) ** 1.35)
        d.line([(0, y), (W, y)], fill=(8, 13, 26, a))

    # Верхняя карточка заголовка (X: 54..1026, Y: 88..315)
    d.rounded_rectangle((54, 88, 1026, 315), radius=28, fill=(15, 23, 42, 225), outline=(255, 255, 255, 65), width=3)
    # Акцентная полоса слева
    d.rounded_rectangle((54, 88, 74, 315), radius=10, fill=(*C_RED_REC, 255))

    # Бейдж рубрики
    k_w = int(d.textlength(kicker, font=fnt(FONT_BLACK, 22))) + 72
    d.rounded_rectangle((100, 110, 100 + k_w, 156), radius=12, fill=(225, 29, 72, 240))
    d.ellipse((118, 124, 136, 142), fill=(255, 255, 255, 255))
    d.text((148, 117), kicker, font=fnt(FONT_BLACK, 22), fill=(255, 255, 255, 255))

    # Заголовок в 2 строки
    d.text((100, 168), line1, font=fnt(FONT_BLACK, 42), fill=(255, 255, 255, 255))
    d.text((100, 226), line2, font=fnt(FONT_BLACK, 42), fill=(*accent_color, 255))

    # Нижний аккуратный бейдж автора (над зоной интерфейса Shorts)
    d.rounded_rectangle((64, 1775, 690, 1835), radius=30, fill=(15, 23, 42, 200), outline=(245, 180, 60, 130), width=2)
    d.ellipse((88, 1796, 106, 1814), fill=(*C_AMBER, 255))
    d.text((118, 1788), "Ирина Тыщенко  |  Тележурналистика с нуля", font=fnt(FONT_BOLD, 24), fill=(248, 245, 238, 240))

    out = OVERLAYS_DIR / filename
    ov.save(out)
    return out


def build_broll_card(filename, tag_text, title1, title2, quote_text, theme="danger"):
    """
    Создаёт атмосферную полноэкранную 9:16 B-roll карточку-перебивку (для наложения на 2.5 сек в ключевой момент истории),
    с телевизионным видоискателем, кинематографичным светом и цитатой-панчлайном.
    """
    W, H = 1080, 1920
    canvas = Image.new("RGBA", (W, H), (*C_NAVY_DARK, 255))

    # Подложка из реального кадра с сильным размытием и цветовым тонированием
    src_frame = FRAMES_DIR / ("c1279_4k.jpg" if theme != "frost" else "c1270_4k.jpg")
    if src_frame.exists():
        bg = Image.open(src_frame).convert("RGB")
        bg = ImageOps.fit(bg, (W, H), centering=(0.5, 0.5)).filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.32)
        canvas.paste(bg.convert("RGBA"), (0, 0))

    draw_studio_bokeh(canvas, seed_offset=7 if theme == "danger" else 12)
    d = ImageDraw.Draw(canvas)
    draw_viewfinder_hud(d, W, H, margin=56, title_tag="АРХИВ РЕПОРТЁРА  •  РЕАЛЬНЫЙ СЛУЧАЙ")

    # Центральная документальная карточка
    d.rounded_rectangle((68, 560, 1012, 1260), radius=36, fill=(15, 23, 42, 230), outline=(245, 180, 60, 180), width=3)
    d.rounded_rectangle((108, 605, 580, 662), radius=14, fill=(225, 29, 72, 245))
    d.text((132, 616), tag_text, font=fnt(FONT_BLACK, 26), fill=(255, 255, 255, 255))

    d.text((108, 700), title1, font=fnt(FONT_BLACK, 52), fill=(255, 255, 255, 255))
    d.text((108, 770), title2, font=fnt(FONT_BLACK, 52), fill=(*C_AMBER, 255))

    d.line([(108, 865), (972, 865)], fill=(255, 255, 255, 65), width=2)

    # Многострочная цитата
    y_q = 905
    for line in quote_text.split("\n"):
        d.text((108, y_q), line, font=fnt(FONT_GEORGIA_B, 36), fill=(248, 245, 238, 250))
        y_q += 54

    out = OVERLAYS_DIR / filename
    canvas.convert("RGB").save(out, quality=95)
    return out


def build_brandbook_board():
    """Создаёт единый наглядный лист нового Брендбука 2.0 (1920x1080) для презентации пользователю."""
    W, H = 1920, 1080
    canvas = Image.new("RGBA", (W, H), (*C_NAVY_DARK, 255))
    draw_studio_bokeh(canvas, seed_offset=5)
    d = ImageDraw.Draw(canvas)

    draw_viewfinder_hud(d, W, H, margin=36, title_tag="БРЕНДБУК 2.0  •  ДОКУМЕНТАЛЬНЫЙ НЕО-РЕПОРТАЖ")

    # Заголовок листа
    d.text((80, 105), "БРЕНДБУК КУРСА «ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ»", font=fnt(FONT_BLACK, 44), fill=(255, 255, 255, 255))
    d.text((80, 162), "Спикер: Ирина Витальевна Тыщенко  |  Слоган: «Журналистика — это состояние души»", font=fnt(FONT_BOLD, 26), fill=(*C_AMBER, 255))

    # 1. Блок Цветовой палитры (слева вверху)
    d.rounded_rectangle((80, 225, 920, 560), radius=24, fill=(15, 23, 42, 220), outline=(255, 255, 255, 50), width=2)
    d.text((110, 248), "1. ФИРМЕННАЯ ПАЛИТРА (НОЧНОЙ ЭФИР & ЯНТАРЬ)", font=fnt(FONT_BLACK, 20), fill=(255, 255, 255, 230))

    swatches = [
        ("#0B1222", "Глубокий эфир", (11, 18, 34)),
        ("#162544", "Студийный синий", (22, 37, 68)),
        ("#E11D48", "REC / Акцент", (225, 29, 72)),
        ("#F5B43C", "Тёплый янтарь", (245, 180, 60)),
        ("#F8F5EE", "Чистый титр", (248, 245, 238)),
    ]
    sx = 110
    for hex_code, label, rgb in swatches:
        d.rounded_rectangle((sx, 300, sx + 142, 440), radius=16, fill=(*rgb, 255), outline=(255, 255, 255, 90), width=2)
        d.text((sx + 10, 455), hex_code, font=fnt(FONT_BLACK, 20), fill=(255, 255, 255, 255))
        d.text((sx + 6, 485), label, font=fnt(FONT_REG, 16), fill=(*C_SLATE, 255))
        sx += 158

    # 2. Блок До / После цветокоррекции видео (слева внизу)
    d.rounded_rectangle((80, 590, 920, 1010), radius=24, fill=(15, 23, 42, 220), outline=(255, 255, 255, 50), width=2)
    d.text((110, 612), "2. ЦВЕТОКОРРЕКЦИЯ И КАДРИРОВАНИЕ 4K ИСХОДНИКОВ (9:16)", font=fnt(FONT_BLACK, 20), fill=(255, 255, 255, 230))

    raw_f = FRAMES_DIR / "c1279_4k.jpg"
    if raw_f.exists():
        im_raw = ImageOps.fit(Image.open(raw_f).convert("RGB"), (360, 290), centering=(0.62, 0.35))
        im_grd = enhance_portrait(raw_f, target_size=(360, 290))
        canvas.paste(im_raw, (115, 665))
        canvas.paste(im_grd, (515, 665))
        d.rounded_rectangle((115, 665, 475, 955), radius=12, outline=(255, 255, 255, 80), width=2)
        d.rounded_rectangle((515, 665, 875, 955), radius=12, outline=(*C_AMBER, 220), width=3)
        d.rounded_rectangle((128, 678, 330, 716), radius=8, fill=(0, 0, 0, 180))
        d.text((140, 685), "ДО: S-Log исходник", font=fnt(FONT_BOLD, 18), fill=(200, 200, 200, 255))
        d.rounded_rectangle((528, 678, 810, 716), radius=8, fill=(225, 29, 72, 230))
        d.text((540, 685), "ПОСЛЕ: Grade + Контраст", font=fnt(FONT_BOLD, 18), fill=(255, 255, 255, 255))

    # 3. Блок Системы плашек и субтитров (справа)
    d.rounded_rectangle((960, 225, 1840, 1010), radius=24, fill=(15, 23, 42, 220), outline=(255, 255, 255, 50), width=2)
    d.text((995, 248), "3. ЭФИРНАЯ ГРАФИКА, ПЛАШКИ И ВИРУСНЫЕ СУБТИТРЫ", font=fnt(FONT_BLACK, 22), fill=(255, 255, 255, 230))

    # Мини-макет вертикального клипа справа
    if raw_f.exists():
        phone_w, phone_h = 380, 675
        phone_x, phone_y = 1005, 305
        im_vert = enhance_portrait(raw_f, target_size=(phone_w, phone_h))
        # Наложим наш оверлей клипа №1
        ov1_path = OVERLAYS_DIR / "overlay_clip1.png"
        if ov1_path.exists():
            ov1 = Image.open(ov1_path).resize((phone_w, phone_h), Image.Resampling.LANCZOS)
            im_vert = im_vert.convert("RGBA")
            im_vert.alpha_composite(ov1)
        canvas.paste(im_vert.convert("RGB"), (phone_x, phone_y))
        d.rounded_rectangle((phone_x, phone_y, phone_x + phone_w, phone_y + phone_h), radius=20, outline=(*C_AMBER, 220), width=4)
        # Пример субтитра на экране телефона
        d.rounded_rectangle((phone_x + 24, phone_y + 475, phone_x + phone_w - 24, phone_y + 565), radius=14, fill=(11, 18, 34, 230), outline=(255, 255, 255, 70), width=2)
        d.text((phone_x + 42, phone_y + 488), "«УЕЗЖАЙТЕ БЫСТРЕЕ,", font=fnt(FONT_BLACK, 24), fill=(255, 255, 255, 255))
        d.text((phone_x + 42, phone_y + 522), "ОН ИДЁТ С РУЖЬЁМ!»", font=fnt(FONT_BLACK, 25), fill=(*C_AMBER, 255))

    # Описание правил справа от макета телефона
    rx = 1420
    rules = [
        ("● COLD OPEN (0–3 сек)", "Ролик стартует с пиковой\nфразы без приветствий."),
        ("● ВЕРХНЯЯ ПЛАШКА", "Матовое стекло #0F172A,\nкрасный индикатор REC\nи двустрочный хук."),
        ("● КРУПНЫЕ СУБТИТРЫ", "По 3–5 слов в карточке\nна уровне груди спикера,\nакцент — янтарный #F5B43C."),
        ("● ВЕРТИКАЛЬНЫЙ КРОП", "Из 4K (3840×2160) берём\n1215×2160 по лицу Ирины:\nлишний ноутбук и стакан\nуходят из кадра."),
    ]
    ry = 315
    for r_title, r_desc in rules:
        d.text((rx, ry), r_title, font=fnt(FONT_BLACK, 22), fill=(*C_AMBER, 255))
        ry += 34
        for ln in r_desc.split("\n"):
            d.text((rx, ry), ln, font=fnt(FONT_REG, 20), fill=(226, 232, 240, 240))
            ry += 26
        ry += 24

    out_path = BRAND_DIR / "00_BRANDBOOK_2_0_SHOWCASE.png"
    canvas.convert("RGB").save(out_path, quality=95)
    return out_path


if __name__ == "__main__":
    # 1. Создаём оверлеи для первых 3 вирусных клипов
    build_short_top_overlay(
        "overlay_clip1.png",
        "БУДНИ ЖУРНАЛИСТА • РЕАЛЬНЫЙ СЛУЧАЙ",
        "Выезд в станицу: «Уезжайте,",
        "муж идёт с охоты с ружьём!»",
        accent_color=C_AMBER,
    )
    build_short_top_overlay(
        "overlay_clip2.png",
        "ЗА КАДРОМ • БЭКСТЕЙДЖ ЗАПИСИ КУРСА",
        "Когда записываешь уроки",
        "вместе с сыном-оператором!",
        accent_color=C_AMBER,
    )
    build_short_top_overlay(
        "overlay_clip3.png",
        "БУДНИ ЖУРНАЛИСТА • СУРГУТ −35°C",
        "На буровую вышку в −35°C",
        "и валенках 44-го размера!",
        accent_color=C_AMBER,
    )

    # 2. Создаём B-roll карточки-перебивки для ключевых моментов
    build_broll_card(
        "broll_clip1_card.png",
        "ГОРЯЧИЙ КЛЮЧ • 1998 ГОД",
        "Срочный выезд",
        "в горную станицу",
        "«На мне строгое платье и туфли\nна каблучке після совещания —\nа машина уже ждёт у входа...»",
        theme="danger",
    )
    build_broll_card(
        "broll_clip3_card.png",
        "СУРГУТСКИЙ РАЙОН • −35°C",
        "200 км от города:",
        "буровая вышка",
        "«Валенки 44-го размера, тулуп\nповерх дублёнки, подпоясана\nшпагатом — и бегом наверх!»",
        theme="frost",
    )

    # 3. Создаём баннер YouTube, аватарку и главный лист Брендбука 2.0
    b_full, b_prev = build_youtube_banner()
    av = build_channel_avatar()
    bb = build_brandbook_board()
    print("Generated successfully:", b_full, b_prev, av, bb)
