#!/usr/bin/env python3
"""Genera el fondo estilo Pokémon Amarillo y la capa de destellos.

Salidas:
  - graphics/title_screen/yellow_bg.png    atlas 128x128 (16x16 tiles)
  - graphics/title_screen/yellow_bg.bin    tilemap 32x32 (u16 LE)
  - graphics/title_screen/yellow_bg.pal    paleta JASC de 16 colores (banco 14)
  - graphics/title_screen/sparkles.png     128x56, 16 colores
  - graphics/title_screen/sparkles.bin     tilemap 32x32 (u16 LE, banco 14)

El fondo BG0 es un sunburst amarillo con un Pikachu grande en primer plano.
El Pikachu se toma de `pikachu_yellow.png` (128x88, índice 0 transparente),
extraído y limpiado del arte de referencia de Pokémon Amarillo y cuantizado a
esta misma paleta de 16 colores. La capa BG1 son destellos semitransparentes que
se desplazan sobre el fondo. El PNG de BG0 es un atlas de tiles para no superar
los 512 tiles del char base.

Uso: python3 dev_scripts/generate_title_bg.py
"""

import math
import os
import struct

from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "graphics/title_screen")

W, H = 240, 160
ATLAS_COLS, ATLAS_ROWS = 16, 16
BANK = 14

# 0 = transparente; el fondo usa 1..15
PALETTE = [
    (0, 0, 0),        # 0 transparente
    (255, 248, 208),  # 1 crema
    (255, 220, 0),    # 2 amarillo Pikachu
    (248, 192, 0),    # 3 oro (rayos)
    (255, 255, 255),  # 4 blanco
    (216, 152, 0),    # 5 oro oscuro
    (28, 24, 20),     # 6 contorno
    (80, 56, 24),     # 7 marrón
    (224, 48, 48),    # 8 rojo mejillas
    (255, 136, 136),  # 9 rosa boca
    (255, 246, 128),  # 10 amarillo claro
    (255, 176, 48),   # 11 naranja
    (224, 224, 224),  # 12 gris claro
    (64, 96, 200),    # 13 azul
    (160, 32, 32),    # 14 rojo oscuro
    (120, 80, 40),    # 15 marrón claro
]

TRANSPARENT, CREAM, YELLOW, GOLD, WHITE = 0, 1, 2, 3, 4
DARK_GOLD, OUTLINE, BROWN, RED, PINK = 5, 6, 7, 8, 9
LIGHT_YELLOW, ORANGE, LIGHT_GRAY = 10, 11, 12


def draw_sunburst(d):
    cx, cy, radius = 120, 78, 320
    for i in range(16):
        a0 = math.radians(i * 360 / 16)
        a1 = math.radians((i + 1) * 360 / 16)
        if i % 2 == 0:
            d.polygon(
                [
                    (cx, cy),
                    (cx + radius * math.cos(a0), cy + radius * math.sin(a0)),
                    (cx + radius * math.cos(a1), cy + radius * math.sin(a1)),
                ],
                fill=GOLD,
            )


def draw_bolt(d, x, y, s):
    d.polygon(
        [
            (x, y),
            (x + 3 * s, y + 10 * s),
            (x + 1 * s, y + 10 * s),
            (x + 5 * s, y + 22 * s),
            (x - 2 * s, y + 12 * s),
            (x, y + 12 * s),
        ],
        fill=WHITE,
        outline=GOLD,
    )


def draw_star(d, x, y, s):
    d.polygon(
        [
            (x, y - 2 * s),
            (x + s, y - s),
            (x, y),
            (x + s, y + s),
            (x, y + 2 * s),
            (x - s, y + s),
            (x, y),
            (x - s, y - s),
        ],
        fill=WHITE,
    )


def make_scene():
    scene = Image.new("P", (W, H), CREAM)
    scene.putpalette([c for rgb in PALETTE for c in rgb])
    d = ImageDraw.Draw(scene)
    draw_sunburst(d)
    draw_bolt(d, 44, 58, 1)
    draw_bolt(d, 194, 74, 1)
    for x, y, s in [(30, 95, 2), (205, 45, 1), (25, 30, 1),
                    (215, 120, 1), (178, 70, 1), (60, 125, 1)]:
        draw_star(d, x, y, s)

    # Pikachu extraído del arte de Pokémon Amarillo y limpiado/quantizado.
    pika = Image.open(os.path.join(OUT_DIR, "pikachu_yellow.png"))
    scene_px = scene.load()
    pika_px = pika.load()
    px, py = (W - pika.width) // 2, 68
    for y in range(pika.height):
        for x in range(pika.width):
            v = pika_px[x, y]
            if v != TRANSPARENT:
                scene_px[px + x, py + y] = v
    return scene


def make_atlas(scene):
    tiles = {}
    order = []
    entries = []
    for ty in range(20):
        for tx in range(32):
            if tx >= W // 8:
                entries.append(BANK << 12)
                continue
            patch = scene.crop((tx * 8, ty * 8, tx * 8 + 8, ty * 8 + 8))
            data = patch.tobytes()
            if data not in tiles:
                tiles[data] = len(order)
                order.append(patch)
            entries.append(tiles[data] | (BANK << 12))
    for _ in range((32 - 20) * 32):
        entries.append(BANK << 12)

    assert len(order) <= ATLAS_COLS * ATLAS_ROWS, "demasiados tiles únicos"
    atlas = Image.new("P", (ATLAS_COLS * 8, ATLAS_ROWS * 8), CREAM)
    atlas.putpalette([c for rgb in PALETTE for c in rgb])
    for i, patch in enumerate(order):
        atlas.paste(patch, ((i % ATLAS_COLS) * 8, (i // ATLAS_COLS) * 8))
    return atlas, entries, len(order)


def make_sparkles():
    img = Image.new("P", (128, 56), TRANSPARENT)
    img.putpalette([c for rgb in PALETTE for c in rgb])
    d = ImageDraw.Draw(img)
    # No dibujar en el tile 0 (0..7,0..7): se usa como tile vacío.
    stars = [
        (24, 12, 1), (48, 30, 2), (80, 18, 1), (104, 42, 1),
        (136, 24, 2), (16, 48, 1), (72, 50, 1), (120, 8, 1),
        (92, 34, 1), (40, 50, 1), (112, 52, 1),
    ]
    for x, y, s in stars:
        draw_star(d, x, y, s)
        d.point((x, y), fill=GOLD)
    # Pequeños destellos dorados
    for x, y in [(32, 22), (58, 8), (88, 44), (128, 36), (8, 32)]:
        d.rectangle([x, y, x + 1, y + 1], fill=GOLD)

    entries = []
    for ty in range(32):
        for tx in range(32):
            idx = (ty * 16 + tx) | (BANK << 12) if tx < 16 and ty < 7 else (BANK << 12)
            entries.append(idx)
    return img, entries


def main():
    scene = make_scene()
    atlas, bg_entries, count = make_atlas(scene)
    sparkles, spark_entries = make_sparkles()

    atlas.save(os.path.join(OUT_DIR, "yellow_bg.png"))
    with open(os.path.join(OUT_DIR, "yellow_bg.bin"), "wb") as f:
        f.write(struct.pack("<%dH" % len(bg_entries), *bg_entries))
    sparkles.save(os.path.join(OUT_DIR, "sparkles.png"))
    with open(os.path.join(OUT_DIR, "sparkles.bin"), "wb") as f:
        f.write(struct.pack("<%dH" % len(spark_entries), *spark_entries))

    with open(os.path.join(OUT_DIR, "yellow_bg.pal"), "w", newline="\r\n") as f:
        f.write("JASC-PAL\n0100\n16\n")
        for r, g, b in PALETTE:
            f.write(f"{r} {g} {b}\n")
    with open(os.path.join(OUT_DIR, "yellow_bg.gbapal"), "wb") as f:
        for r, g, b in PALETTE:
            c = ((r >> 3) & 0x1F) | (((g >> 3) & 0x1F) << 5) | (((b >> 3) & 0x1F) << 10)
            f.write(struct.pack("<H", c))

    scene.resize((W * 3, H * 3), Image.NEAREST).save("/tmp/opencode/yellow_bg_preview.png")
    print("tiles únicos:", count, "/", ATLAS_COLS * ATLAS_ROWS)
    print("escritos: yellow_bg.png/.bin/.pal y sparkles.png/.bin")


if __name__ == "__main__":
    main()
