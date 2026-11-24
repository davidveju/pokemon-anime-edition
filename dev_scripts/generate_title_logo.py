#!/usr/bin/env python3
"""Genera el logo del título a partir del logo auténtico de Pokémon Amarillo.

Fuente: `graphics/title_screen/pokemon_logo_source.png` (wordmark "Pokémon" +
óvalo "Pika!" recortados de la referencia de Amarillo, sin "YELLOW VERSION" ni
copyright). Se escala a 152x58, se cuantiza a la paleta completa del logo
(224 colores) y se añaden "ANIME" y "EDITION" a los lados del óvalo, imitando el
"YELLOW VERSION" original.

Salidas:
  - graphics/title_screen/pokemon_logo.png   256x64, índice 0 transparente
  - graphics/title_screen/pokemon_logo.bin   tilemap 32x32 de 8 bits (1024 bytes)

Uso: python3 dev_scripts/generate_title_logo.py
"""

import os

from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "graphics/title_screen")
OUT_PNG = os.path.join(OUT_DIR, "pokemon_logo.png")
OUT_BIN = os.path.join(OUT_DIR, "pokemon_logo.bin")
SOURCE = os.path.join(OUT_DIR, "pokemon_logo_source.png")
PAL_FILE = os.path.join(OUT_DIR, "pokemon_logo.pal")

W, H = 256, 64
LOGO_W, LOGO_H = 152, 58
LOGO_X, LOGO_Y = 7, 4
YELLOW_INDEX = 2
BLUE_INDEX = 10


def load_palette():
    lines = open(PAL_FILE, encoding="latin1").read().splitlines()
    count = int(lines[2])
    palette = []
    for line in lines[3:3 + count]:
        r, g, b = map(int, line.split())
        palette.append((r, g, b))
    # El .gbapal que carga el juego tiene 14 bancos = 224 colores.
    palette = palette[:224]
    while len(palette) < 224:
        palette.append((0, 0, 0))
    return palette


def flat_palette(palette):
    flat = [c for rgb in palette for c in rgb]
    return flat + [0, 0, 0] * (256 - len(palette))


FONT5 = {
    "A": ["01110", "10001", "11111", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001"],
    "I": ["11111", "00100", "00100", "00100", "11111"],
    "M": ["10001", "11011", "10101", "10001", "10001"],
    "E": ["11111", "10000", "11110", "10000", "11111"],
    "D": ["11110", "10001", "10001", "10001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100"],
    "O": ["01110", "10001", "10001", "10001", "01110"],
}


def draw_text(pixels, text, x, y):
    for i, ch in enumerate(text):
        glyph = FONT5[ch]
        gx = x + i * 5
        for gy, row in enumerate(glyph):
            for gx2, bit in enumerate(row):
                if bit == "1":
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            nx, ny = gx + gx2 + dx, y + gy + dy
                            if 0 <= nx < W and 0 <= ny < H:
                                pixels[nx, ny] = BLUE_INDEX
    for i, ch in enumerate(text):
        glyph = FONT5[ch]
        gx = x + i * 5
        for gy, row in enumerate(glyph):
            for gx2, bit in enumerate(row):
                if bit == "1":
                    pixels[gx + gx2, y + gy] = YELLOW_INDEX


def main():
    palette = load_palette()
    flat = flat_palette(palette)
    source = Image.open(SOURCE).convert("RGBA")

    rgb = source.convert("RGB").resize((LOGO_W, LOGO_H), Image.LANCZOS)
    mask = source.getchannel("A").resize((LOGO_W, LOGO_H), Image.LANCZOS)

    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(flat)
    quant = rgb.quantize(palette=pal_img, dither=Image.Dither.NONE).convert("P")

    logo = Image.new("P", (W, H), 0)
    logo.putpalette(flat)
    qp, ap, lp = quant.load(), mask.load(), logo.load()
    for y in range(LOGO_H):
        for x in range(LOGO_W):
            if ap[x, y] >= 128:
                v = qp[x, y]
                lp[LOGO_X + x, LOGO_Y + y] = 1 if v == 0 else v

    # Halo blanco del JPEG alrededor del contorno azul: pasarlo a azul.
    fringe = []
    for y in range(H):
        for x in range(W):
            idx = lp[x, y]
            if idx == 0:
                continue
            r, g, b = palette[idx]
            if min(r, g, b) >= 190 and max(r, g, b) - min(r, g, b) <= 45:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and lp[nx, ny] == 0:
                        fringe.append((x, y))
                        break
    for x, y in fringe:
        lp[x, y] = BLUE_INDEX

    # "YELLOW VERSION" -> "ANIME" / "EDITION", en el mismo hueco.
    draw_text(lp, "ANIME", 8, 51)
    draw_text(lp, "EDITION", 124, 51)

    logo.save(OUT_PNG)
    tilemap = bytearray(1024)
    for y in range(8):
        for x in range(32):
            tilemap[y * 32 + x] = y * 32 + x
    with open(OUT_BIN, "wb") as f:
        f.write(tilemap)

    preview = Image.new("RGB", (W, H), (30, 30, 30))
    preview.paste(logo.convert("RGB"), (0, 0), logo.convert("RGBA"))
    preview.resize((W * 2, H * 2), Image.NEAREST).save(
        "/tmp/opencode/title_logo_preview.png")
    print("escritos:", OUT_PNG, OUT_BIN)


if __name__ == "__main__":
    main()
