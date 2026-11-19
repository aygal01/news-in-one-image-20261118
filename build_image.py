#!/usr/bin/env python3
"""Composite the 18 Nov 2026 world-news panels into a single 1024x1024 image.

Reads the text-free panel art in assets/ and writes entry.png (JPEG bytes)
at the repo root. Deterministic: same inputs -> same output bytes.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "entry.png"

W = H = 1024
MARGIN = 12
GAP = 8

BG = (9, 20, 38)            # dark navy
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
BAR = (0, 0, 0, 190)        # semi-transparent caption bar
TICKER_BG = (122, 18, 32)   # deep red ticker strip
BORDER = (140, 160, 190)    # thin light panel border

# Vertical crop focus per panel (0 = top of art, 1 = bottom)
ANCHORS = {
    "summit": 0.42,
    "gulf": 0.85,
    "bridge": 0.8,
    "senate": 0.32,
    "cop31": 0.45,
    "cyclone": 0.5,
    "nvidia": 0.5,
}

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CAPTIONS = {
    "summit": "SHENZHEN SUMMIT — Xi and Putin meet, Trump flies in for trilateral talks",
    "gulf": "U.S. SINKS 5 IRANIAN TANKERS — TEHRAN STRIKES BACK AT HORMUZ",
    "bridge": "UKRAINE HITS THE CRIMEA BRIDGE A SECOND NIGHT",
    "senate": "PELTOLA WINS ALASKA — DEMOCRATS TAKE THE SENATE 56–44",
    "cop31": "COP31 ANTALYA — CLIMATE TALKS ENTER THEIR DECISIVE DAYS",
    "cyclone": "CYCLONE AKVAN — SEVERE STORM, ODISHA ON HIGH ALERT",
    "nvidia": "NVIDIA BOARD RULES OUT A HUANG COMEBACK",
}
TICKER = ("ALSO TODAY — UN WARNS OF WINTER DEATHS IN GAZA AS THE CEASEFIRE "
          "FALTERS · EU PROPOSES €45BN LOAN FOR UKRAINE")


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    """Greedy word-wrap to pixel width; returns list of lines."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(img, w, h, anchor_y=0.5):
    """Scale image to cover (w, h) and crop, anchor_y 0=top .. 1=bottom."""
    scale = max(w / img.width, h / img.height)
    nw, nh = round(img.width * scale), round(img.height * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int((nh - h) * anchor_y)
    return img.crop((x, y, x + w, y + h))


def caption_bar(canvas, draw, box, text, size):
    """Draw a semi-transparent black bar at the bottom of box with wrapped text."""
    x0, y0, x1, y1 = box
    fnt = font(FONT_BOLD, size)
    lines = wrap(draw, text, fnt, (x1 - x0) - 20)
    line_h = int(size * 1.28)
    bar_h = line_h * len(lines) + 14
    bar_y = y1 - bar_h
    draw.rectangle([x0, bar_y, x1, y1], fill=BAR)
    ty = bar_y + 7
    for line in lines:
        draw.text((x0 + 10, ty), line, font=fnt, fill=WHITE)
        ty += line_h


def panel(canvas, draw, name, box, cap_size):
    x0, y0, x1, y1 = box
    art = Image.open(ASSETS / f"{name}.webp").convert("RGB")
    canvas.paste(fit(art, x1 - x0, y1 - y0, ANCHORS.get(name, 0.5)), (x0, y0))
    draw.rectangle(box, outline=BORDER, width=2)
    caption_bar(canvas, draw, box, CAPTIONS[name], cap_size)


def tracked(draw, cx, y, text, fnt, tracking, fill):
    """Draw centered text with letter tracking; returns total width."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, wch in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += wch + tracking
    return total


def main():
    canvas = Image.new("RGBA", (W, H), BG + (255,))
    draw = ImageDraw.Draw(canvas, "RGBA")

    # --- Masthead -------------------------------------------------------
    tracked(draw, W / 2, 12, "THE WORLD IN ONE DAY", font(FONT_BOLD, 25), 7, GOLD)
    date_fnt = font(FONT_BOLD, 54)
    date = "WEDNESDAY 18 NOVEMBER 2026"
    dw = draw.textlength(date, font=date_fnt)
    draw.text(((W - dw) / 2, 46), date, font=date_fnt, fill=WHITE)
    draw.rectangle([MARGIN, 112, W - MARGIN, 115], fill=GOLD)

    inner_w = W - 2 * MARGIN            # 1000
    col_w = (inner_w - GAP) // 2        # 496

    # --- Hero ------------------------------------------------------------
    hero = (MARGIN, 124, W - MARGIN, 452)
    panel(canvas, draw, "summit", hero, 27)

    # --- Grid: gulf / bridge, senate / cop31 -----------------------------
    rows = [(460, 630), (638, 808)]
    grid = [["gulf", "bridge"], ["senate", "cop31"]]
    for (gy0, gy1), row in zip(rows, grid):
        for i, name in enumerate(row):
            x0 = MARGIN + i * (col_w + GAP)
            panel(canvas, draw, name, (x0, gy0, x0 + col_w, gy1), 24)

    # --- Bottom row: cyclone / nvidia -------------------------------------
    for i, name in enumerate(["cyclone", "nvidia"]):
        x0 = MARGIN + i * (col_w + GAP)
        panel(canvas, draw, name, (x0, 816, x0 + col_w, 948), 24)

    # --- Ticker ------------------------------------------------------------
    draw.rectangle([0, 956, W, H], fill=TICKER_BG + (255,))
    draw.rectangle([0, 956, W, 959], fill=GOLD)
    tfnt = font(FONT_BOLD, 22)
    lines = wrap(draw, TICKER, tfnt, W - 28)
    line_h = int(22 * 1.3)
    ty = 956 + (68 - line_h * len(lines)) // 2 + 2
    for line in lines:
        lw = draw.textlength(line, font=tfnt)
        draw.text(((W - lw) / 2, ty), line, font=tfnt, fill=WHITE)
        ty += line_h

    out = canvas.convert("RGB")
    out.save(OUT, format="JPEG", quality=88)
    print(f"wrote {OUT} {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
