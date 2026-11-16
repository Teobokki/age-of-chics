#!/usr/bin/env python3
"""Build AGE OF CHICS icon, wizard images, and placeholder store art from slide 1."""
from __future__ import annotations
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(ROOT, "assets", "deck")
ASSETS = os.path.join(ROOT, "assets")
STORE = os.path.join(ROOT, "store_art")
SLIDE1 = os.path.join(DECK, "slide-1.png")
GOLD = (245, 168, 4)
BLACK = (0, 0, 0)
DARK = (11, 11, 13)
CREAM = (244, 244, 240)


def load_font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = os.path.join(ASSETS, "fonts", name)
    return ImageFont.truetype(path, size)



def is_gold(p):
    r, g, b = p[:3]
    return r >= 180 and g >= 100 and b <= 80 and r > g and g > b


def is_mark(p):
    r, g, b = p[:3]
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    return lum < 90 and not is_gold(p)


def gold_field(im: Image.Image) -> tuple[Image.Image, tuple]:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            if is_gold(px[x, y]):
                xs.append(x); ys.append(y)
    field = rgb.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))
    fw, fh = field.size
    fp = field.load()
    samples = []
    for (x, y) in ((8, 8), (fw - 9, 8), (8, fh - 9), (fw - 9, fh - 9), (20, 20), (fw // 4, 10)):
        if 0 <= x < fw and 0 <= y < fh and is_gold(fp[x, y]):
            samples.append(fp[x, y])
    samples.sort()
    gold = samples[len(samples) // 2] if samples else GOLD
    return field, gold


def emblem_square(size: int) -> Image.Image:
    """Yellow square with the H mark from slide 1, no frame."""
    field, gold = gold_field(Image.open(SLIDE1))
    fw, fh = field.size
    fp = field.load()
    mx, my = [], []
    for y in range(fh):
        for x in range(fw):
            if is_mark(fp[x, y]):
                mx.append(x); my.append(y)
    ml, mt, mr, mb = min(mx), min(my), max(mx) + 1, max(my) + 1
    pad = int(min(fw, fh) * 0.08)
    mark = field.crop((max(0, ml - pad), max(0, mt - pad), min(fw, mr + pad), min(fh, mb + pad)))
    mw, mh = mark.size
    mp = mark.load()
    side = max(mw, mh)
    margin = int(side * 0.08)
    canvas_s = side + 2 * margin
    clean = Image.new("RGB", mark.size, gold)
    alpha = Image.new("L", mark.size, 0)
    cp, ap = clean.load(), alpha.load()
    for y in range(mh):
        for x in range(mw):
            p = mp[x, y]
            if is_gold(p):
                continue
            if is_mark(p) or p[0] < 180:
                clean_p = p
                lum = 0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]
                cp[x, y] = clean_p
                ap[x, y] = max(0, min(255, int(255 * (1 - lum / 140))))
    rgba = clean.convert("RGBA")
    rgba.putalpha(alpha)
    base = Image.new("RGBA", (canvas_s, canvas_s), gold + (255,))
    base.alpha_composite(rgba, ((canvas_s - mw) // 2, (canvas_s - mh) // 2))
    return base.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)


def save_ico(square: Image.Image, path: str):
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    square.convert("RGBA").save(path, format="ICO", sizes=sizes)


def cover_text(im: Image.Image, lines):
    draw = ImageDraw.Draw(im)
    # lines: list of (text, font, fill, y)
    for text, font, fill, y in lines:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((im.width - tw) // 2, y), text, font=font, fill=fill)


def make_store_placeholders(emblem: Image.Image):
    os.makedirs(STORE, exist_ok=True)
    # icon
    emblem.resize((256, 256), Image.Resampling.LANCZOS).save(os.path.join(STORE, "icon.png"))
    emblem.resize((256, 256), Image.Resampling.LANCZOS).save(os.path.join(ASSETS, "icon.png"))
    for s in (48, 64, 128, 256, 512):
        emblem.resize((s, s), Image.Resampling.LANCZOS).save(os.path.join(ASSETS, "icon%d.png" % s))

    # capsule 616x353
    cap = Image.new("RGB", (616, 353), DARK)
    e = emblem.resize((200, 200), Image.Resampling.LANCZOS)
    cap.paste(e, (40, (353 - 200) // 2))
    d = ImageDraw.Draw(cap)
    font_s = load_font(16, True)
    font_b = load_font(36, True)
    d.text((270, 110), "EX PRESENTS", font=font_s, fill=GOLD)
    d.text((270, 138), "AGE OF CHICS™", font=load_font(28, True), fill=CREAM)
    d.text((270, 178), "BY HYPERION", font=load_font(16, True), fill=CREAM)
    d.text((270, 210), "ARVICIA CITY", font=load_font(14, True), fill=(160, 160, 155))
    cap.save(os.path.join(STORE, "capsule.jpg"), quality=92, optimize=True)

    # cover / shots default 1280x800 — cinematic still + title
    city = Image.open(os.path.join(DECK, "slide-5.png")).convert("RGB")
    cover = _cover_frame(city, 1280, 800, emblem)
    cover.save(os.path.join(STORE, "cover.jpg"), quality=92, optimize=True)
    for i, src_name in enumerate(["slide-1.png", "slide-5.png", "slide-3.png", "slide-6.png"]):
        # placeholders replaced later with real app screenshots when available
        fr = Image.open(os.path.join(DECK, src_name)).convert("RGB")
        shot = _letterbox(fr, 1280, 800, DARK)
        shot.save(os.path.join(STORE, "shot%d.jpg" % i), quality=90, optimize=True)

    # hero 1600x600
    hero_src = Image.open(os.path.join(DECK, "slide-4.png")).convert("RGB")
    hero = _cover_frame(hero_src, 1600, 600, emblem, tight=True)
    hero.save(os.path.join(STORE, "hero.jpg"), quality=92, optimize=True)
    # hero_bg: same photo, slightly darker, no type
    bg = _letterbox(hero_src, 1600, 600, DARK)
    # darken
    overlay = Image.new("RGB", bg.size, DARK)
    bg = Image.blend(bg, overlay, 0.35)
    bg.save(os.path.join(STORE, "hero_bg.jpg"), quality=90, optimize=True)


def _letterbox(im, w, h, color):
    out = Image.new("RGB", (w, h), color)
    scale = min(w / im.width, h / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    out.paste(r, ((w - nw) // 2, (h - nh) // 2))
    return out


def _cover_frame(photo, w, h, emblem, tight=False):
    # Fill (crop to cover)
    scale = max(w / photo.width, h / photo.height)
    nw, nh = int(photo.width * scale), int(photo.height * scale)
    r = photo.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    canvas = r.crop((left, top, left + w, top + h))
    # darken lower/left for type, no glow
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, w, h), fill=(0, 0, 0, 110))
    canvas = canvas.convert("RGBA")
    canvas = Image.alpha_composite(canvas, overlay).convert("RGB")
    d = ImageDraw.Draw(canvas)
    es = 120 if tight else 160
    e = emblem.resize((es, es), Image.Resampling.LANCZOS)
    margin = 48 if tight else 64
    canvas.paste(e, (margin, (h - es) // 2))
    tx = margin + es + 36
    d.text((tx, h // 2 - 80), "EX PRESENTS", font=load_font(18, True), fill=GOLD)
    d.text((tx, h // 2 - 54), "AGE OF CHICS™", font=load_font(44 if not tight else 36, True), fill=CREAM)
    d.text((tx, h // 2 + 4), "BY HYPERION", font=load_font(22, True), fill=CREAM)
    d.text((tx, h // 2 + 38), "ARVICIA CITY", font=load_font(18, True), fill=(200, 200, 195))
    return canvas


def make_wizard(emblem: Image.Image):
    # Inno wizard: large 164x314 and 2x, small 55x55 and 2x
    def tall(w, h):
        im = Image.new("RGB", (w, h), DARK)
        s = int(w * 0.72)
        e = emblem.resize((s, s), Image.Resampling.LANCZOS)
        im.paste(e, ((w - s) // 2, int(h * 0.12)))
        d = ImageDraw.Draw(im)
        font = load_font(max(9, w // 14), True)
        text = "AGE OF CHICS™"
        bbox = d.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        d.text(((w - tw) // 2, int(h * 0.12) + s + 12), text, font=font, fill=CREAM)
        return im

    tall(164, 314).save(os.path.join(ASSETS, "wizard_large.bmp"))
    tall(328, 628).save(os.path.join(ASSETS, "wizard_large2x.bmp"))
    emblem.resize((55, 55), Image.Resampling.LANCZOS).save(os.path.join(ASSETS, "wizard_small.bmp"))
    emblem.resize((110, 110), Image.Resampling.LANCZOS).save(os.path.join(ASSETS, "wizard_small2x.bmp"))


def main():
    os.makedirs(ASSETS, exist_ok=True)
    emblem = emblem_square(512)
    emblem.save(os.path.join(ASSETS, "emblem.png"))
    save_ico(emblem, os.path.join(ASSETS, "logo.ico"))
    # splash background used by the update-check window (also a standalone image)
    splash = Image.new("RGB", (640, 360), DARK)
    e = emblem.resize((128, 128), Image.Resampling.LANCZOS)
    splash.paste(e, ((640 - 128) // 2, 48))
    d = ImageDraw.Draw(splash)
    font_b = load_font(28, True)
    text = "AGE OF CHICS™"
    bbox = d.textbbox((0, 0), text, font=font_b)
    d.text(((640 - (bbox[2] - bbox[0])) // 2, 190), text, font=font_b, fill=CREAM)
    font_s = load_font(14, False)
    sub = "Checking for updates\u2026"
    bbox = d.textbbox((0, 0), sub, font=font_s)
    d.text(((640 - (bbox[2] - bbox[0])) // 2, 240), sub, font=font_s, fill=(160, 160, 155))
    splash.save(os.path.join(ASSETS, "splash.png"))
    make_wizard(emblem)
    make_store_placeholders(emblem)
    print("assets written")


if __name__ == "__main__":
    main()
