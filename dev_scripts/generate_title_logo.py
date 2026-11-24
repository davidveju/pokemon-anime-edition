#!/usr/bin/env python3
"""Genera el logo del título a partir del logo auténtico de Pokémon Amarillo.

Fuente: `graphics/title_screen/pokemon_logo_source.png` (wordmark "Pokémon" +
óvalo "Pika!" recortados de la referencia de Amarillo, sin "YELLOW VERSION" ni
copyright). Se escala a 152x58, se cuantiza a la paleta completa del logo
(224 colores). No lleva textos de edición: el nombre del juego queda en el
copyright inferior "© 2026 ANIME EDITION".

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
