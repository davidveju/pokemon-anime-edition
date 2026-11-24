#!/usr/bin/env python3
"""Genera el banner de versión del título: "ANIME EDITION" estilo Amarillo.

Salida: graphics/title_screen/emerald_version.png (128x32, paleta indexada de
16 colores, índice 0 = transparente), que el build convierte a 8bpp y parte en
los dos sprites de 64x32 del título.

Uso: python3 dev_scripts/generate_title_version.py
"""
import os
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "graphics/title_screen/emerald_version.png")

W, H = 128, 32
TEXT = "ANIME EDITION"
SCALE = 2
PITCH = 9  # ancho de celda (glifo 8 px + 1 de separación)

# Índices de paleta
TRANSPARENT, YELLOW, BLUE, WHITE = 0, 1, 2, 3
PALETTE = [
    (255, 0, 255),    # 0 transparente
    (255, 213, 0),    # 1 amarillo
    (32, 30, 110),    # 2 azul oscuro
    (255, 255, 255),  # 3 blanco
] + [(0, 0, 0)] * 12

# Fuente 4x6 (filas de 4 bits, MSB izquierda)
FONT = {
    "A": ["0110", "1001", "1001", "1111", "1001", "1001"],
    "B": ["1110", "1001", "1110", "1001", "1001", "1110"],
    "C": ["0111", "1000", "1000", "1000", "1000", "0111"],
    "D": ["1110", "1001", "1001", "1001", "1001", "1110"],
    "E": ["1111", "1000", "1110", "1000", "1000", "1111"],
    "F": ["1111", "1000", "1110", "1000", "1000", "1000"],
    "G": ["0111", "1000", "1011", "1001", "1001", "0111"],
    "H": ["1001", "1001", "1111", "1001", "1001", "1001"],
    "I": ["1110", "0100", "0100", "0100", "0100", "1110"],
    "J": ["0011", "0001", "0001", "0001", "1001", "0110"],
    "K": ["1001", "1010", "1100", "1100", "1010", "1001"],
    "L": ["1000", "1000", "1000", "1000", "1000", "1111"],
    "M": ["1001", "1111", "1111", "1001", "1001", "1001"],
    "N": ["1001", "1101", "1111", "1011", "1001", "1001"],
    "O": ["0110", "1001", "1001", "1001", "1001", "0110"],
    "P": ["1110", "1001", "1001", "1110", "1000", "1000"],
    "Q": ["0110", "1001", "1001", "1001", "1010", "0101"],
    "R": ["1110", "1001", "1001", "1110", "1010", "1001"],
    "S": ["0111", "1000", "0110", "0001", "0001", "1110"],
    "T": ["1110", "0100", "0100", "0100", "0100", "0100"],
    "U": ["1001", "1001", "1001", "1001", "1001", "0110"],
    "V": ["1001", "1001", "1001", "1001", "0110", "0110"],
    "W": ["1001", "1001", "1001", "1111", "1111", "1001"],
    "X": ["1001", "1001", "0110", "0110", "1001", "1001"],
    "Y": ["1010", "1010", "0100", "0100", "0100", "0100"],
    "Z": ["1111", "0001", "0010", "0100", "1000", "1111"],
    " ": ["0000"] * 6,
}


def glyph_mask(ch):
    rows = FONT.get(ch.upper(), FONT[" "])
    mask = [[False] * 4 for _ in range(6)]
    for y, row in enumerate(rows):
        for x, bit in enumerate(row):
            mask[y][x] = bit == "1"
    return mask


def main():
    img = Image.new("P", (W, H), TRANSPARENT)
    img.putpalette([c for rgb in PALETTE for c in rgb])

    # Componer máscara a 8x12 (glifo 4x6 escalado x2), una celda por carácter
    total = len(TEXT) * PITCH - (PITCH - 8)
    x0 = (W - total) // 2
    y0 = (H - 12) // 2

    mask = [[False] * W for _ in range(H)]
    for i, ch in enumerate(TEXT):
        g = glyph_mask(ch)
        gx = x0 + i * PITCH
        for y in range(6):
            for x in range(4):
                if not g[y][x]:
                    continue
                for sy in range(SCALE):
                    for sx in range(SCALE):
                        px, py = gx + x * SCALE + sx, y0 + y * SCALE + sy
                        if 0 <= px < W and 0 <= py < H:
                            mask[py][px] = True

    # Contorno azul (dilatación) + relleno amarillo + brillo blanco arriba
    px_access = img.load()
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and not mask[ny][nx]:
                        px_access[nx, ny] = BLUE
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                px_access[x, y] = YELLOW
    # Brillo: fila superior de cada trazo horizontal
    for y in range(1, H):
        for x in range(W):
            if mask[y][x] and not mask[y - 1][x]:
                px_access[x, y] = WHITE

    img.save(OUT)
    print("escrito:", OUT, img.size, "colores:", len(PALETTE))


if __name__ == "__main__":
    main()
