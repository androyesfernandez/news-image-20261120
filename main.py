#!/usr/bin/env python3
"""make.fun news-image-20261120 entry.

Writes one 1024x1024 PNG summing up the world news of Friday
20 November 2026 to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

Design: a classic broadsheet front page on one square canvas.
A masthead with a giant date, a UTC timeline of the day, a
colour-coded region strip with story counts (all eight regions,
including Oceania), a row of the day's six big numbers, three
illustrated lead stories, eight more illustrated stories in two
rows, a dotted world map with numbered pins, 35 numbered one-line
briefs, a red DATE CHECK box naming what was left out and why,
and sources.

Every story below was first reported on Friday 20 November 2026;
the DATE CHECK box lists the tempting stories that were NOT that
day's news (first reported Thursday 19 November or earlier) and
so are excluded. Claims are attributed to their makers.

Pure Python standard library, fully deterministic: no clock, no
random, no network, no file input. Two runs write identical bytes.
"""

import math
import os
import struct
import zlib
from math import isqrt

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 233)
WHITE = (255, 254, 248)
INK = (18, 22, 28)
GRAY = (70, 76, 86)
FAINT = (203, 196, 178)
RED = (178, 32, 40)
DARKRED = (120, 18, 26)
NAVY = (16, 42, 84)
BLUE = (26, 72, 128)
TEAL = (14, 110, 104)
GOLD = (196, 138, 30)
GREEN = (38, 110, 58)
YELLOW = (250, 210, 60)
PURPLE = (96, 52, 140)
ORANGE = (198, 96, 26)
SKY = (168, 200, 232)
DEEP = (10, 16, 40)
SAND = (232, 205, 150)
CREAM = (240, 226, 196)
BROWN = (122, 84, 52)

_buf = bytearray(W * H * 3)


def _set_row(x, y, w, rgb):
    i = (y * W + x) * 3
    _buf[i:i + 3 * w] = bytes(rgb) * w


def rect(x, y, w, h, rgb):
    if w <= 0 or h <= 0:
        return
    x0 = max(0, x)
    x1 = min(W, x + w)
    if x1 <= x0:
        return
    for yy in range(max(0, y), min(H, y + h)):
        _set_row(x0, yy, x1 - x0, rgb)


def outline(x, y, w, h, rgb, t=3):
    rect(x, y, w, t, rgb)
    rect(x, y + h - t, w, t, rgb)
    rect(x, y, t, h, rgb)
    rect(x + w - t, y, t, h, rgb)


def circle(cx, cy, r, rgb):
    for dy in range(-r, r + 1):
        dx = isqrt(r * r - dy * dy)
        _set_row(cx - dx, cy + dy, 2 * dx + 1, rgb)


def line(x0, y0, x1, y1, rgb, t=3):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    half = t // 2
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i // steps
        y = y0 + (y1 - y0) * i // steps
        rect(x - half, y - half, t, t, rgb)


def vgrad(x, y, w, h, c_top, c_bot, bands=5):
    """Vertical gradient in flat bands (cheap, deterministic)."""
    for b in range(bands):
        t = b / (bands - 1) if bands > 1 else 0
        rgb = tuple(int(c_top[i] + (c_bot[i] - c_top[i]) * t)
                    for i in range(3))
        rect(x, y + b * h // bands, w, h // bands + 1, rgb)


def dither(x, y, w, h, c1, c2, step=3):
    """Checkerboard blend of two colours (adds drawn texture)."""
    for yy in range(y, y + h, step):
        for xx in range(x, x + w, step):
            if ((xx // step) + (yy // step)) % 2 == 0:
                rect(xx, yy, step, step, c1)
            else:
                rect(xx, yy, step, step, c2)


def speckle(x, y, w, h, rgb, step=7, seed=11):
    """Deterministic pseudo-random dots (no random module)."""
    i = 0
    for yy in range(y + 2, y + h - 2, step):
        for xx in range(x + 2, x + w - 2, step):
            i += 1
            if (i * 2654435761 + seed * 97) % 5 < 2:
                rect(xx, yy, 2, 2, rgb)


# ------------------------------------------------------------------- font
# 5x7 bitmap font. '#' = ink pixel.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"),
    '2': (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    '3': (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#..##", "#..##"),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", "...#."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '*': (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    '€': (".###.", "#....", "#####", "#....", "#####", "#....", ".###."),
    '£': (".###.", "#..#.", "#....", "#####", "#....", "#....", "#####"),
    '×': (".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."),
    '°': (".##..", "#..#.", ".##..", ".....", ".....", ".....", "....."),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale if s else 0


def text(x, y, s, scale, rgb):
    """Draw string s with top-left at (x, y); returns its pixel width."""
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == '#':
                    rect(x + gx * scale, y + gy * scale, scale, scale, rgb)
        x += 6 * scale
    return text_w(s, scale)


def text_c(cx, y, s, scale, rgb):
    return text(cx - text_w(s, scale) // 2, y, s, scale, rgb)


def wrap(s, scale, max_w):
    """Greedy word wrap: list of lines that fit max_w pixels."""
    words = s.split()
    lines = []
    cur = ""
    for wd in words:
        trial = (cur + " " + wd) if cur else wd
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ scenes
# Dense flat-vector illustration panels. Each paints inside (x, y, w, h):
# layered gradient skies, dithered texture, shading and many small props.

def scene_cyclone(x, y, w, h):
    """Cyclone Akvan: spiral over a teal sea, bearing on the Odisha coast."""
    vgrad(x, y, w, h, (10, 70, 88), (20, 130, 122), 5)
    # sea swell: darker bands with white wave dashes
    rect(x, y + h - 26, w, 26, (8, 58, 74))
    for wx in range(8, w - 10, 34):
        rect(x + wx, y + h - 18, 18, 2, WHITE)
        rect(x + wx + 12, y + h - 9, 14, 2, (200, 230, 228))
    # coastline and shelters on the right
    rect(x + w - 44, y, 44, h, SAND)
    dither(x + w - 44, y, 44, h, SAND, (222, 192, 132), 4)
    line(x + w - 44, y, x + w - 52, y + h, (210, 178, 118), 8)
    for hx, hy in ((w - 38, h - 52), (w - 24, h - 44), (w - 36, h - 74),
                   (w - 18, h - 66)):
        rect(x + hx, y + hy, 12, 9, WHITE)
        rect(x + hx - 1, y + hy - 5, 14, 5, RED)
        rect(x + hx + 4, y + hy + 4, 4, 5, INK)
    # palm by the shore
    line(x + w - 12, y + h - 30, x + w - 10, y + h - 58, BROWN, 4)
    for a in (-42, -16, 10, 34):
        ex = x + w - 10 + int(18 * math.sin(a * 3.14159 / 180))
        ey = y + h - 58 - int(10 * math.cos(a * 3.14159 / 180))
        line(x + w - 10, y + h - 58, ex, ey, GREEN, 3)
    # rain streaks slanting across the sky
    for rx in range(6, w - 50, 16):
        line(x + rx, y + 6, x + rx - 8, y + 22, (190, 220, 226), 2)
    for rx in range(14, w - 50, 22):
        line(x + rx, y + 34, x + rx - 8, y + 48, (190, 220, 226), 2)
    # spiral: concentric rings of cloud dots around the eye
    cx, cy = x + w // 2 - 30, y + h // 2 - 2
    for r in (40, 31, 22, 14):
        for a in range(0, 360, 10):
            px = cx + int(r * math.cos(a * 3.14159 / 180))
            py = cy + int(r * math.sin(a * 3.14159 / 180) * 0.72)
            rect(px - 3, py - 2, 6, 4, WHITE)
    circle(cx, cy, 7, NAVY)
    circle(cx, cy, 3, WHITE)
    # wind arrows curling in
    for ax, ay, dx in ((cx - 52, cy - 26, 14), (cx + 46, cy + 20, -14),
                       (cx - 40, cy + 30, 12)):
        line(ax, ay, ax + dx, ay, YELLOW, 3)
        line(ax + dx, ay, ax + dx - 6, ay - 4, YELLOW, 2)
        line(ax + dx, ay, ax + dx - 6, ay + 4, YELLOW, 2)
    rect(x + 6, y + h - 20, 126, 13, NAVY)
    text(x + 10, y + h - 17, "70-80 KM/H, GUSTS 90", 1, WHITE)


def scene_rout(x, y, w, h):
    """The AI rout: red candles plunging off the grid, indexes in free fall."""
    vgrad(x, y, w, h, (40, 8, 10), (96, 14, 18), 5)
    for gx in range(16, w, 26):
        rect(x + gx, y + 34, 1, h - 40, (120, 40, 44))
    for gy in range(40, h, 14):
        rect(x + 4, y + gy, w - 8, 1, (120, 40, 44))
    # descending red candles with wicks, kept below the headline text
    candles = ((14, 36, 50), (44, 42, 56), (74, 48, 62), (104, 52, 66),
               (134, 56, 70), (164, 60, 72), (194, 62, 74), (224, 64, 76))
    for cx, top, bot in candles:
        if cx < w - 22:
            line(x + cx + 6, y + top - 4, x + cx + 6, y + bot + 5, YELLOW, 2)
            rect(x + cx, y + top, 13, bot - top + 8, RED)
            outline(x + cx, y + top, 13, bot - top + 8, (255, 120, 110), 1)
    # jagged gold trend line through the fall
    pts = ((215, 30), (245, 38), (270, 46), (292, 54))
    for i in range(len(pts) - 1):
        line(x + pts[i][0], y + pts[i][1], x + pts[i + 1][0],
             y + pts[i + 1][1], GOLD, 3)
    for px, py in pts:
        circle(x + px, y + py, 3, YELLOW)
    text(x + 44, y + 8, "-6.6%", 3, YELLOW)
    text(x + 140, y + 12, "TAIEX", 2, WHITE)
    text(x + 8, y + h - 12, "KOSPI -5.2 * NIKKEI -5.1 * NSDQ -5.3", 1, WHITE)


def scene_cop(x, y, w, h):
    """COP31 in overtime: a conference hall under a low sun, clock past time."""
    vgrad(x, y, w, h, (250, 222, 170), (238, 190, 130), 5)
    # low sun with rays over the hall roofline
    circle(x + w - 40, y + 24, 15, ORANGE)
    for dx, dy in ((22, 0), (-22, 0), (0, 22), (0, -22), (16, 16),
                   (16, -16), (-16, 16), (-16, -16)):
        line(x + w - 40, y + 24, x + w - 40 + dx, y + 24 + dy, ORANGE, 3)
    # hall: stage, podium, rows of delegates
    rect(x + 8, y + h - 34, w - 16, 26, (120, 96, 70))
    rect(x + 8, y + h - 38, w - 16, 4, BROWN)
    for sx in range(16, w - 16, 20):
        rect(x + sx, y + h - 30, 12, 10, NAVY)
        circle(x + sx + 6, y + h - 36, 4, (210, 170, 120))
    for sx in range(26, w - 16, 20):
        rect(x + sx, y + h - 16, 12, 8, TEAL)
        circle(x + sx + 6, y + h - 21, 4, (230, 200, 160))
    # podium with speaker
    rect(x + w // 2 - 16, y + h - 58, 32, 20, WHITE)
    outline(x + w // 2 - 16, y + h - 58, 32, 20, INK, 1)
    circle(x + w // 2, y + h - 66, 6, INK)
    rect(x + w // 2 - 8, y + h - 60, 16, 4, RED)
    # flag strip: host and co-presidency
    for i, (fx, col) in enumerate(((14, RED), (34, WHITE), (54, TEAL))):
        rect(x + fx, y + 44, 16, 11, col)
        outline(x + fx, y + 44, 16, 11, INK, 1)
        rect(x + fx + 7, y + 55, 2, 12, INK)
    # wall clock, hands past the hour
    circle(x + 52, y + 22, 13, WHITE)
    outline(x + 39, y + 9, 26, 26, INK, 2)
    line(x + 52, y + 22, x + 52, y + 12, INK, 2)
    line(x + 52, y + 22, x + 62, y + 26, INK, 2)
    rect(x + 72, y + 10, 100, 16, RED)
    text(x + 76, y + 14, "OVERTIME", 2, WHITE)
    rect(x + 8, y + h - 52, 150, 12, NAVY)
    text(x + 11, y + h - 49, "DRAFT: NO FOSSIL FUELS", 1, WHITE)


def scene_kyiv(x, y, w, h):
    """Kyiv overnight: a dark skyline, two blasts, a bridge under fire."""
    vgrad(x, y, w, h, (12, 18, 44), (30, 44, 84), 4)
    speckle(x, y, w, 22, WHITE, 11, 3)
    # skyline silhouettes with lit windows
    for bx, bh in ((4, 18), (26, 26), (52, 15), (76, 30), (104, 20),
                   (130, 26), (156, 16), (182, 24), (206, 18)):
        if bx < w - 16:
            rect(x + bx, y + h - 10 - bh, 18, bh, DEEP)
            for wy in range(4, bh - 4, 7):
                rect(x + bx + 4, y + h - 10 - bh + wy, 3, 3, YELLOW)
                rect(x + bx + 11, y + h - 10 - bh + wy + 3, 3, 3, YELLOW)
    rect(x, y + h - 10, w, 10, (60, 64, 70))
    # bridge arc across the river
    line(x + 60, y + h - 10, x + w // 2, y + h - 26, WHITE, 2)
    line(x + w // 2, y + h - 26, x + w - 60, y + h - 10, WHITE, 2)
    # two explosion starbursts
    for ex, ey in ((x + 66, y + 16), (x + w - 60, y + 12)):
        for dx, dy in ((12, 0), (-12, 0), (0, -12), (9, -9), (-9, -9),
                       (9, 7), (-9, 7)):
            line(ex, ey, ex + dx, ey + dy, ORANGE, 3)
        circle(ex, ey, 5, YELLOW)
        circle(ex, ey, 2, WHITE)
    # smoke puffs drifting
    for sx, sy in ((x + 84, y + 8), (x + 92, y + 4), (x + w - 44, y + 6)):
        circle(sx, sy, 4, GRAY)


def scene_riyadh(x, y, w, h):
    """Riyadh at dusk: the PIF Tower, lit windows, interceptors overhead."""
    vgrad(x, y, w, h, (240, 170, 110), (120, 70, 120), 4)
    circle(x + 26, y + 14, 8, YELLOW)
    # PIF tower: tall slab, pointed crown, window grid
    tx = x + w // 2 - 16
    rect(tx, y + 8, 32, h - 16, (70, 80, 100))
    line(tx, y + 8, tx + 16, y - 2, (70, 80, 100), 4)
    line(tx + 32, y + 8, tx + 16, y - 2, (70, 80, 100), 4)
    for wy in range(12, h - 14, 8):
        for wx in range(4, 28, 8):
            rect(tx + wx, y + wy, 4, 4, YELLOW)
    # flanking towers
    for bx, bh in ((tx - 34, h - 30), (tx + 34, h - 36)):
        rect(x + bx, y + h - 8 - bh, 16, bh, (90, 96, 110))
        for wy in range(6, bh - 4, 8):
            rect(x + bx + 4, y + h - 8 - bh + wy, 3, 3, YELLOW)
    rect(x, y + h - 8, w, 8, (50, 52, 60))
    # four interceptor streaks with burst dots
    for sx in (14, 52, w - 66, w - 28):
        line(x + sx, y + 40, x + sx + 16, y + 12, WHITE, 2)
        circle(x + sx + 16, y + 12, 3, WHITE)
        circle(x + sx + 16, y + 12, 6, ORANGE)
    text(x + 8, y + h - 7, "4 DOWNED", 1, WHITE)


def scene_euuk(x, y, w, h):
    """Brussels: the Berlaymont, the EU and Union flags side by side."""
    vgrad(x, y, w, h, (200, 222, 240), (170, 196, 226), 4)
    speckle(x, y, w, 16, WHITE, 13, 5)
    # Berlaymont: grey slab with a window grid
    bx = x + w // 2 - 52
    rect(bx, y + 16, 104, h - 24, (150, 156, 162))
    outline(bx, y + 16, 104, h - 24, INK, 1)
    for wy in range(20, h - 26, 8):
        for wx in range(6, 98, 10):
            rect(bx + wx, y + wy, 5, 4, (60, 70, 84))
    rect(bx, y + 12, 104, 4, (110, 116, 122))
    # EU flag
    rect(x + 38, y + 6, 26, 17, BLUE)
    outline(x + 38, y + 6, 26, 17, INK, 1)
    for a in range(0, 360, 30):
        px = x + 51 + int(6 * math.cos(a * 3.14159 / 180))
        py = y + 14 + int(6 * math.sin(a * 3.14159 / 180))
        rect(px, py, 2, 2, YELLOW)
    rect(x + 50, y + 23, 2, 12, INK)
    # Union Jack (simplified)
    rect(x + w - 40, y + 10, 26, 17, BLUE)
    outline(x + w - 40, y + 10, 26, 17, INK, 1)
    rect(x + w - 40, y + 16, 26, 5, WHITE)
    rect(x + w - 28, y + 10, 5, 17, WHITE)
    rect(x + w - 40, y + 17, 26, 3, RED)
    rect(x + w - 27, y + 10, 3, 17, RED)
    rect(x + w - 28, y + 27, 2, 12, INK)
    rect(x, y + h - 8, w, 8, GREEN)
    for gx in range(6, w, 18):
        rect(x + gx, y + h - 6, 8, 2, (120, 200, 130))


def scene_cricket(x, y, w, h):
    """Wellington: a green pitch, stumps, bat and ball, the scoreboard."""
    vgrad(x, y, w, h, (120, 190, 110), (70, 150, 70), 4)
    # crowd dots along the top
    for cx in range(8, w - 6, 10):
        circle(x + cx, y + 6, 2, (250, 240, 200) if cx % 20 else RED)
    # pitch strip
    rect(x + w // 2 - 26, y + 10, 52, h - 18, (200, 180, 130))
    rect(x + w // 2 - 26, y + 10, 52, 2, WHITE)
    rect(x + w // 2 - 26, y + h - 10, 52, 2, WHITE)
    # stumps at both ends
    for sy in (y + 12, y + h - 22):
        for sx in (x + w // 2 - 8, x + w // 2 - 2, x + w // 2 + 4):
            rect(sx, sy, 3, 8, YELLOW)
        rect(x + w // 2 - 8, sy - 2, 14, 2, YELLOW)
    # bat leaning on the pitch, red ball in play
    line(x + w // 2 + 14, y + 18, x + w // 2 + 26, y + 36, BROWN, 5)
    rect(x + w // 2 + 22, y + 34, 10, 14, BROWN)
    circle(x + w // 2 - 14, y + h - 16, 4, RED)
    # scoreboard chip
    rect(x + 8, y + h - 20, 74, 15, INK)
    text(x + 11, y + h - 17, "368 * 159/1", 1, WHITE)


def scene_anthropic(x, y, w, h):
    """Anthropic day two: the debut chart turns down, hard."""
    vgrad(x, y, w, h, (16, 40, 60), (10, 24, 40), 4)
    for gx in range(14, w, 24):
        rect(x + gx, y + 4, 1, h - 8, (24, 60, 84))
    for gy in range(10, h, 14):
        rect(x + 4, y + gy, w - 8, 1, (24, 60, 84))
    # opening spike, then the slide: green candle, then red candles
    line(x + 120, y + 6, x + 120, y + 26, GREEN, 2)
    rect(x + 114, y + 8, 12, 16, GREEN)
    candles = ((148, 16, 28), (176, 24, 36), (204, 30, 42))
    for cx, top, bot in candles:
        if cx < w - 20:
            line(x + cx + 6, y + top - 3, x + cx + 6, y + bot + 5, YELLOW, 2)
            rect(x + cx, y + top, 12, bot - top + 8, RED)
    text(x + 40, y + 4, "$88.91", 2, YELLOW)
    text(x + w - 68, y + 6, "ANT -8.5%", 1, WHITE)
    text(x + 8, y + h - 12, "IPO $83", 1, WHITE)


def scene_poland(x, y, w, h):
    """Poland's airspace: a radar screen with three blips and two jets."""
    vgrad(x, y, w, h, (8, 40, 20), (6, 26, 14), 4)
    cx, cy = x + w // 2, y + h // 2 + 2
    for r in (20, 14, 8):
        circle(cx, cy, r, (30, 90, 50))
        # ring outline: draw circle then clear the inside
        for dy in range(-r + 1, r):
            dx = isqrt((r - 1) * (r - 1) - dy * dy)
            _set_row(cx - dx, cy + dy, 2 * dx + 1, (10, 44, 24))
    line(cx, cy, cx + 18, cy - 10, GREEN, 2)
    # three red blips with rings
    for bx, by in ((cx - 26, cy - 12), (cx + 12, cy - 18), (cx + 24, cy + 8)):
        circle(bx, by, 3, RED)
        circle(bx, by, 6, (200, 60, 60))
        for dy in range(-5, 6):
            dx = isqrt(25 - dy * dy)
            _set_row(bx - dx, by + dy, 2 * dx + 1, (10, 44, 24))
        circle(bx, by, 3, RED)
    # two jet silhouettes
    for jx, jy in ((x + 40, y + 8), (x + w - 44, y + h - 18)):
        line(jx, jy, jx + 18, jy + 4, WHITE, 3)
        line(jx + 6, jy + 2, jx + 2, jy - 6, WHITE, 2)
        line(jx + 6, jy + 2, jx + 2, jy + 10, WHITE, 2)
    text(x + 8, y + h - 12, "3 OBJECTS", 1, GREEN)


def scene_yemen(x, y, w, h):
    """Yemen: a displacement camp in the desert, mountains behind."""
    vgrad(x, y, w, h, (250, 220, 170), (238, 196, 140), 4)
    # mountain ridge
    for mx, mh in ((4, 16), (30, 24), (62, 18), (92, 26), (124, 16),
                   (154, 22), (184, 14), (212, 20)):
        if mx < w - 10:
            line(x + mx, y + 30, x + mx + 14, y + 30 - mh, BROWN, 4)
            line(x + mx + 14, y + 30 - mh, x + mx + 28, y + 30, BROWN, 4)
    circle(x + w - 24, y + 10, 8, YELLOW)
    # sand ground with dither
    rect(x, y + 30, w, h - 30, SAND)
    dither(x, y + 30, w, h - 30, SAND, (222, 192, 132), 4)
    # tents: triangles with doors, in two rows
    for tx, ty, s in ((10, h - 26, 18), (40, h - 22, 15), (66, h - 28, 19),
                      (96, h - 22, 15), (122, h - 27, 18), (152, h - 22, 15),
                      (180, h - 26, 17), (206, h - 21, 14)):
        if tx < w - s:
            line(x + tx, y + ty, x + tx + s // 2, y + ty - s, WHITE, 4)
            line(x + tx + s // 2, y + ty - s, x + tx + s, y + ty, WHITE, 4)
            rect(x + tx + s // 2 - 2, y + ty - 6, 4, 6, INK)
    # footpath and figures
    line(x + 8, y + h - 6, x + w - 8, y + h - 6, BROWN, 2)
    for fx in (30, 90, 150, 200):
        if fx < w - 6:
            circle(x + fx, y + h - 12, 2, INK)
            rect(x + fx - 1, y + h - 10, 2, 5, INK)


def scene_bukele(x, y, w, h):
    """El Salvador: the blue-white-blue flag, a ballot box, a vote cast."""
    rect(x, y, w, h // 3, BLUE)
    rect(x, y + h // 3, w, h // 3, WHITE)
    rect(x, y + 2 * h // 3, w, h - 2 * h // 3, BLUE)
    # coat of arms: small sun and mountains on the white band
    circle(x + w // 2, y + h // 2 - 4, 7, GOLD)
    line(x + w // 2 - 16, y + h // 2 + 6, x + w // 2 - 4, y + h // 2 - 6,
         GREEN, 3)
    line(x + w // 2 - 4, y + h // 2 - 6, x + w // 2 + 8, y + h // 2 + 6,
         GREEN, 3)
    line(x + w // 2 + 4, y + h // 2 + 6, x + w // 2 + 16, y + h // 2 - 6,
         GREEN, 3)
    # ballot box front and centre
    bx, by = x + w // 2 - 30, y + h - 34
    rect(bx, by, 60, 26, WHITE)
    outline(bx, by, 60, 26, INK, 2)
    rect(bx + 18, by + 4, 24, 4, INK)
    text(bx + 14, by + 12, "VOTA", 2, RED)
    # a ballot sliding into the slot
    rect(bx + 22, by - 12, 16, 14, YELLOW)
    outline(bx + 22, by - 12, 16, 14, INK, 1)
    rect(bx + 25, by - 9, 10, 2, INK)
    rect(bx + 25, by - 5, 10, 2, INK)
    text(x + 40, y + 4, "3RD TERM", 2, WHITE)


def badge(n, x, y, rgb=RED):
    """Numbered story badge: filled circle, white number."""
    circle(x + 13, y + 13, 13, rgb)
    s = str(n)
    text(x + 13 - text_w(s, 2) // 2, y + 6, s, 2, WHITE)


# ---------------------------------------------------------------- world map
# Dotted world map on an 84 x 38 grid (col ~ longitude, row ~ latitude).
# Land is a list of (row, first col, last col) spans.

LAND = [
    (1, 2, 8), (1, 13, 21), (1, 33, 37), (1, 54, 82),
    (2, 1, 9), (2, 12, 26), (2, 31, 37), (2, 48, 52), (2, 53, 83),
    (3, 2, 8), (3, 12, 27), (3, 33, 36), (3, 47, 52), (3, 53, 83),
    (4, 3, 7), (4, 11, 28), (4, 43, 44), (4, 48, 83),
    (5, 4, 7), (5, 10, 27), (5, 43, 45), (5, 48, 52), (5, 53, 82),
    (6, 11, 27), (6, 45, 56), (6, 57, 80),
    (7, 12, 26), (7, 44, 57), (7, 61, 79),
    (8, 12, 26), (8, 43, 58), (8, 59, 76),
    (9, 12, 27), (9, 44, 52), (9, 53, 58), (9, 60, 77),
    (10, 12, 27), (10, 43, 47), (10, 50, 52), (10, 53, 56),
    (10, 57, 62), (10, 63, 70), (10, 68, 77),
    (11, 12, 26), (11, 54, 58), (11, 59, 63), (11, 64, 68),
    (11, 68, 78),
    (12, 13, 26), (12, 44, 56), (12, 57, 62), (12, 60, 67),
    (12, 66, 70), (12, 70, 77),
    (13, 14, 25), (13, 43, 58), (13, 57, 63), (13, 65, 71),
    (13, 71, 76),
    (14, 13, 18), (14, 42, 59), (14, 58, 63), (14, 66, 71),
    (14, 72, 76),
    (15, 15, 17), (15, 42, 60), (15, 67, 70), (15, 73, 77),
    (16, 14, 17), (16, 43, 60), (16, 67, 69), (16, 73, 77),
    (16, 78, 79),
    (17, 21, 27), (17, 44, 59), (17, 60, 61), (17, 67, 69),
    (17, 74, 77),
    (18, 21, 29), (18, 45, 58), (18, 59, 61), (18, 74, 76),
    (18, 78, 80),
    (19, 21, 30), (19, 45, 57), (19, 72, 74), (19, 76, 79),
    (19, 81, 82),
    (20, 22, 30), (20, 46, 57), (20, 73, 76), (20, 78, 80),
    (20, 82, 83),
    (21, 22, 30), (21, 47, 57), (21, 74, 78), (21, 80, 82),
    (22, 23, 31), (22, 47, 56),
    (23, 23, 31), (23, 48, 56), (23, 59, 59),
    (24, 23, 30), (24, 48, 56), (24, 59, 60), (24, 76, 80),
    (25, 23, 30), (25, 49, 56), (25, 59, 60), (25, 75, 85),
    (26, 23, 29), (26, 49, 56), (26, 74, 86),
    (27, 23, 29), (27, 50, 55), (27, 74, 86),
    (28, 23, 28), (28, 50, 55), (28, 75, 85),
    (29, 22, 27), (29, 51, 54), (29, 76, 84),
    (30, 22, 26), (30, 51, 54), (30, 77, 83),
    (31, 22, 25), (31, 82, 83),
    (32, 22, 24), (32, 82, 83),
    (33, 22, 24),
    (34, 22, 23),
    (35, 22, 23),
]

# story number -> (col, row) pin on the map grid
PINS = {
    1: (62, 15), 2: (71, 13), 3: (48, 10), 4: (50, 6), 5: (52, 13),
    6: (43, 8), 7: (82, 33), 8: (23, 10), 9: (46, 5), 10: (55, 17),
    11: (21, 18),
}


def draw_map(x, y):
    """Dotted world map with numbered pins and brief dots."""
    text(x + 4, y, "WHERE IT HAPPENED", 2, INK)
    oy = y + 30
    for r, c0, c1 in LAND:
        for c in range(c0, c1 + 1):
            rect(x + c * 4 + 1, oy + r * 4 + 1, 2, 2, (176, 168, 148))
    for n, dot in BRIEF_DOTS.items():
        c, r = dot
        circle(x + c * 4 + 2, oy + r * 4 + 2, 2, GRAY)
    for n, pin in PINS.items():
        c, r = pin
        px, py = x + c * 4 + 2, oy + r * 4 + 2
        circle(px, py, 8, RED)
        s = str(n)
        text(px - text_w(s, 1) // 2, py - 3, s, 1, WHITE)
    text(x + 4, oy + 146, "RED NUMBERS: STORIES 1-11 * GREY DOTS: BRIEFS", 1, GRAY)
    text(x + 4, oy + 156, "POSITIONS ARE APPROXIMATE", 1, GRAY)


# ------------------------------------------------------------------- cards
def lead_card(x, y, w, h, n, kicker, head, dek, src, scene, accent):
    rect(x, y, w, h, WHITE)
    outline(x, y, w, h, INK, 3)
    scene(x + 3, y + 3, w - 6, 96)
    badge(n, x + 10, y + 10, accent)
    text(x + 12, y + 104, kicker, 2, accent)
    text(x + w - 12 - text_w(src, 1), y + 108, src, 1, GRAY)
    yy = y + 124
    for ln in wrap(head, 3, w - 24)[:2]:
        text(x + 12, yy, ln, 3, INK)
        yy += 23
    yy = y + 174
    for ln in wrap(dek, 2, w - 24)[:2]:
        text(x + 12, yy, ln, 2, GRAY)
        yy += 16


def row_card(x, y, w, h, n, kicker, head, dek, src, scene, accent):
    rect(x, y, w, h, WHITE)
    outline(x, y, w, h, INK, 2)
    scene(x + 2, y + 2, w - 4, 54)
    badge(n, x + 6, y + 6, accent)
    text(x + 8, y + 60, kicker, 1, accent)
    yy = y + 72
    for ln in wrap(head, 2, w - 16)[:2]:
        text(x + 8, yy, ln, 2, INK)
        yy += 16
    yy = y + 106
    for ln in wrap(dek, 1, w - 16)[:2]:
        text(x + 8, yy, ln, 1, GRAY)
        yy += 9
    text(x + 8, y + h - 11, src, 1, GRAY)


# -------------------------------------------------------------------- data
# Briefs: (number, place, text, map dot). Every brief was first reported
# on Friday 20 November 2026.

BRIEFS = [
    (12, "ESTONIA", "BORDER WITH RUSSIA SHUT FOR 6 MONTHS", (48, 3)),
    (13, "BERLIN", "MERZ REJECTS A NEW YALTA OVER EUROPE", (41, 6)),
    (14, "LONDON", "UK PLEDGES 1,000+ DRONES FOR UKRAINE", (40, 8)),
    (15, "BRUSSELS", "EPPO CHARGES €213.7M RAILWAY FRAUD", (47, 7)),
    (16, "WARSAW", "THREE HELD IN VAST VAT EVASION PROBE", (43, 5)),
    (17, "RIGA", "LATVIA PLANS DE-RUSSIFICATION MOVE", (49, 4)),
    (18, "VIENNA", "EU TAKES AUSTRIA TO COURT OVER WARRANTS", (45, 9)),
    (19, "BRUSSELS", "NATO CHIEF MEETS INTELLIGENCE CHIEFS", (44, 8)),
    (20, "EUROPE", "YOUTH ACTION CALLED OVER LIVING COSTS", (41, 5)),
    (21, "WASHINGTON", "US SANCTIONS COMANCHEROS, 'NDRANGHETA", (20, 12)),
    (22, "WASHINGTON", "DOJ SEEKS 200+ ALASKA VOTE SUBPOENAS", (8, 5)),
    (23, "WASHINGTON", "SENATE LEADER RAPS TRUMP 'FRIEND' LINE", (26, 12)),
    (24, "WASHINGTON", "CYBER CHIEF FIRED AFTER MASS OUTAGES", (26, 9)),
    (25, "BAGHDAD", "TROOPS DEPLOY VS IRAN-BACKED MILITIA", (55, 14)),
    (26, "GAZA", "ISRAELI TROOPS CROSS YELLOW LINE", (49, 13)),
    (27, "HORMUZ", "TANKER ABLAZE AFTER HITTING A MINE", (56, 14)),
    (28, "RIYADH", "CROWN PRINCE, CENTCOM CHIEF IN TALKS", (49, 14)),
    (29, "BAHRAIN", "BAPCO PLANT NEARS FULL RESTART", (58, 15)),
    (30, "GULF", "RAILWAY TO LINK SIX NATIONS PLANNED", (55, 13)),
    (31, "SUDAN", "DRONE STRIKE KILLS 10 AT GOLD MINE", (51, 19)),
    (32, "SENEGAL", "BOAT TOLL NOW 4; DOZENS STILL MISSING", (40, 18)),
    (33, "SUDAN", "RSF COMMANDER DEFECTS; UAE JAILS EIGHT", (49, 20)),
    (34, "AFRICA", "MINISTERS STAGE COP31 FLOOR PROTEST", (52, 21)),
    (35, "PHNOM PENH", "US SANCTIONS CHEN ZHI-LINKED OPERATOR", (66, 16)),
    (36, "TAIPEI", "SHORT-SELLING CURBS TIGHTENED", (72, 12)),
    (37, "TOKYO", "CPI DATA BACKS A BANK OF JAPAN HIKE", (74, 11)),
    (38, "MANILA", "VIETJET EXPANDS PHILIPPINES ROUTES", (69, 17)),
    (39, "SUVA", "CYCLONE XAVIER TRACK UPDATED: NADI", (83, 25)),
    (40, "AUCKLAND", "OCEANIA CHALLENGE BOWLS UNDER WAY", (81, 30)),
    (41, "WELLINGTON", "NZ NAMED AND SHAMED AT COP31", (83, 31)),
    (42, "PANAMA", "THREATENS TO BLOCK COP31 CONSENSUS", (20, 18)),
    (43, "HAITI", "POLICE KILL 34 SUSPECTED GANG MEMBERS", (24, 16)),
    (44, "CRIMEA", "KERCH BRIDGE RAIL TRAFFIC RESUMES", (53, 8)),
    (45, "MARKETS", "MSCI ASIA-PAC WEEK WORST SINCE 2020", (68, 15)),
    (46, "CANBERRA", "AUSTRALIA CO-PRESIDES STALLED COP31", (78, 28)),
]

BRIEF_DOTS = {n: dot for n, _p, _t, dot in BRIEFS}

NUMBERS = [
    ("372,000", "EVACUATED IN ODISHA AHEAD OF AKVAN"),
    ("-17.5%", "TAIEX WEEKLY FALL; WORST SINCE 1991"),
    ("357,000", "DISPLACED IN YEMEN SINCE AUGUST (UN)"),
    ("-5.3%", "NASDAQ FALL; S&P + DOW IN CORRECTION"),
    ("€213.7M", "BULGARIA RAIL FRAUD CHARGED BY EPPO"),
    ("1,000+", "DRONES IN UK'S £260M UKRAINE PACKAGE"),
]

# label, colour, width — the eight regions sum to 972 px incl. gaps
REGIONS = [
    ("ASIA-PAC 4", PURPLE, 130), ("EUROPE 13", BLUE, 118),
    ("AMERICAS 6", GREEN, 130), ("AFRICA 4", ORANGE, 106),
    ("MID EAST 8", RED, 130), ("S ASIA 1", GOLD, 106),
    ("OCEANIA 5", TEAL, 118), ("GLOBAL 5", GRAY, 106),
]

TIMELINE = ("UTC 00:05 RSF DEFECTION * 00:52 357,000 FLEE YEMEN * "
            "02:00 AKVAN LANDFALL * 05:30 TAIEX -6.6% * "
            "20:47 COP31 OVERTIME * 21:00 NASDAQ -5.3%")


# -------------------------------------------------------------- composition
def compose():
    rect(0, 0, W, H, PAPER)
    outline(6, 6, W - 12, H - 12, INK, 3)

    # Masthead: classic broadsheet, the date in huge ink type
    text(24, 16, "THE WORLD IN ONE DAY", 3, RED)
    top_r = "FRIDAY'S NEWS * ONE PAGE * 46 STORIES"
    text(W - 24 - text_w(top_r, 2), 22, top_r, 2, GRAY)
    rect(24, 46, W - 48, 3, INK)
    rect(24, 52, W - 48, 2, RED)
    text_c(W // 2, 62, "FRIDAY 20 NOVEMBER 2026", 6, INK)
    text_c(W // 2, 110,
           "AKVAN LANDFALL * AI ROUT SINKS MARKETS * COP31 RUNS INTO OVERTIME",
           2, RED)

    # UTC timeline of the day, in the masthead band
    rect(24, 128, W - 48, 20, NAVY)
    text_c(W // 2, 133, TIMELINE, 1, WHITE)

    # Region strip: colour-coded counts of the stories on this page
    rx = 24
    for label, rgb, wid in REGIONS:
        rect(rx, 152, wid, 24, rgb)
        text_c(rx + wid // 2, 157, label, 2, WHITE)
        rx += wid + 4

    # The day in six numbers
    nx = 24
    for big, small in NUMBERS:
        rect(nx, 182, 157, 54, WHITE)
        outline(nx, 182, 157, 54, INK, 2)
        text_c(nx + 78, 190, big, 3, RED)
        ly = 216
        for ln in wrap(small, 1, 145)[:2]:
            text_c(nx + 78, ly, ln, 1, INK)
            ly += 9
        nx += 163

    # Three lead stories
    lead_card(24, 242, 318, 210, 1, "INDIA * CYCLONE",
              "AKVAN HITS ODISHA COAST",
              "372,000 EVACUATED; NO DEATHS REPORTED",
              "IMD", scene_cyclone, GOLD)
    lead_card(353, 242, 318, 210, 2, "MARKETS * AI ROUT",
              "AI ROUT SINKS ASIA, WALL ST",
              "TAIEX -6.6% IN A DAY; -17.5% IN A WEEK",
              "REUTERS", scene_rout, RED)
    lead_card(682, 242, 318, 210, 3, "CLIMATE * ANTALYA",
              "COP31 TALKS RUN INTO OVERTIME",
              "DRAFT DROPS FOSSIL FUELS; PANAMA MAY BLOCK IT",
              "UNRIC", scene_cop, GREEN)

    # Illustrated stories, row of four (4-7)
    row_card(24, 458, 238, 146, 4, "UKRAINE * KYIV",
             "RUSSIA STRIKES KYIV: 11 KILLED",
             "BRIDGES TARGETED; 28 HURT ACROSS 9 REGIONS",
             "RFE/RL * AP", scene_kyiv, NAVY)
    row_card(268, 458, 238, 146, 5, "SAUDI ARABIA",
             "SAUDI DEFENCES DOWN FOUR MISSILES",
             "FOUR BALLISTIC MISSILES DOWNED OVER SOUTH",
             "SPA * REUTERS", scene_riyadh, ORANGE)
    row_card(512, 458, 238, 146, 6, "EU * UK",
             "EU AND UK MEET IN BRUSSELS",
             "SECOND SUMMIT OF THE RENEWED PARTNERSHIP",
             "EU COUNCIL", scene_euuk, BLUE)
    row_card(756, 458, 238, 146, 7, "CRICKET * WELLINGTON",
             "NICHOLLS 175* AS NZ POST 368",
             "INDIA REPLY 159/1; JAISWAL 85, RAHUL 52*",
             "AP * BCCI", scene_cricket, GREEN)

    # Illustrated stories, row of four (8-11)
    row_card(24, 610, 238, 146, 8, "TECH * NASDAQ",
             "ANTHROPIC FALLS 8.5% ON DAY TWO",
             "CLOSES AT $88.91; IPO COMPLETE AT $83",
             "CAIXIN * REUTERS", scene_anthropic, PURPLE)
    row_card(268, 610, 238, 146, 9, "POLAND",
             "RUSSIA VIOLATES POLISH AIRSPACE",
             "TWO MISSILES, ONE DRONE; DRILLS UNDER WAY",
             "POLISH DEFENCE MINISTRY", scene_poland, RED)
    row_card(512, 610, 238, 146, 10, "YEMEN",
             "357,000 FLEE IN YEMEN SINCE AUGUST",
             "UN AGENCY COUNTS THE FLIGHT SINCE AUGUST",
             "UN AGENCY", scene_yemen, BROWN)
    row_card(756, 610, 238, 146, 11, "EL SALVADOR",
             "BUKELE REGISTERS FOR THIRD TERM",
             "EL SALVADOR PRESIDENT FILES FOR 2027 VOTE",
             "NEWS MEDIA HOUSE", scene_bukele, TEAL)

    # Bottom left: the map. Bottom right: the briefs.
    outline(24, 762, 336, 200, INK, 2)
    draw_map(28, 764)
    text(372, 764, "ALSO ON FRIDAY", 3, RED)
    text(372 + text_w("ALSO ON FRIDAY", 3) + 10, 771,
         "* 35 MORE STORIES", 2, GRAY)
    by = 790
    for i, (n, place, txt, _dot) in enumerate(BRIEFS):
        col_x = 372 if i < 18 else 686
        row_y = by + (i % 18) * 9
        text(col_x, row_y, str(n), 1, RED)
        text(col_x + 16, row_y, place + " - " + txt, 1, INK)

    # Date check: what was left out, and why it was not this day's news
    outline(24, 966, W - 48, 48, RED, 2)
    text(36, 972, "DATE CHECK", 2, RED)
    body = [
        "NOT THIS DAY'S NEWS - FIRST REPORTED THU 19 NOV: TRUMP-XI-PUTIN SUMMIT + PEACE DECLARATION * ICJ MYANMAR GENOCIDE RULING * ANTHROPIC $81.3BN IPO * GTA VI LAUNCH * HOUTHI STRIKE ON RIYADH PIF TOWER * KYIV STRIKES HIT EMBASSIES",
        "ALSO NOT 20 NOV: VAN GOGH $190.4M (WED 18 NOV) * PETE ROSE PARDON (19 NOV) * US-VENEZUELA DEAL (18-19 NOV) * FIJI DROUGHT (19 NOV) * KENYA EBOLA DISCHARGE (11 NOV)",
        "EVERY STORY ABOVE WAS REPORTED ON FRI 20 NOV 2026. SOURCES: REUTERS * AP * AFP * BBC * IMD * UN * COP31 * NASA",
    ]
    ly = 970
    for ln_text in body:
        for ln in wrap(ln_text, 1, 806):
            text(190, ly, ln, 1, INK)
            ly += 9


# -------------------------------------------------------------------- png
def png_bytes():
    raw = bytearray()
    row = W * 3
    for y in range(H):
        raw.append(0)
        raw += _buf[y * row:(y + 1) * row]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    compose()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png_bytes())


if __name__ == "__main__":
    main()
