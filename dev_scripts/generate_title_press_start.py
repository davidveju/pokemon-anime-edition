#!/usr/bin/env python3
"""Genera los banners "PRESS START" y copyright localizados del título.

Salida (160x24, indexado 16 colores, índice 0 transparente):
  - graphics/title_screen/press_start_es.png   PULSA START
  - graphics/title_screen/press_start_en.png   PRESS START
  - graphics/title_screen/press_start_pt.png   PRESSIONE START
  - graphics/title_screen/press_start_it.png   PREMI START
  - copyright común: ©2026 ANIME EDITION

El motor usa 5 segmentos de 32x8 por frase y otros 5 para el copyright; el
primer tile de cada fila es margen, por eso el texto se centra en el área
visible x=8..159. La fila inferior queda transparente.

Uso: python3 dev_scripts/generate_title_press_start.py
"""

import os

from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "graphics/title_screen")

W, H = 160, 24
VISIBLE_LEFT, VISIBLE_RIGHT = 8, 159
VISIBLE_WIDTH = VISIBLE_RIGHT - VISIBLE_LEFT + 1

# Paleta del sprite (0 = transparente)
TRANSPARENT, BLACK, GRAY, LIGHT_GRAY, OFF_WHITE, WHITE = 0, 1, 2, 3, 4, 5
PALETTE = [
    (0, 0, 0),        # 0 transparente
    (0, 0, 0),        # 1 contorno
    (148, 156, 164),  # 2 gris
    (180, 189, 189),  # 3 gris claro
    (222, 222, 238),  # 4 blanco roto
    (255, 255, 255),  # 5 blanco
] + [(0, 0, 0)] * 10

# Fuente 5x5 de bloque
FONT = {
    "A": ["01110", "10001", "11111", "10001", "10001"],
    "B": ["11110", "10001", "11110", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "11110", "10000", "11111"],
    "F": ["11111", "10000", "11110", "10000", "10000"],
    "G": ["01111", "10000", "10111", "10001", "01111"],
    "H": ["10001", "10001", "11111", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "11100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001"],
    "O": ["01110", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "11110", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10011", "01111"],
    "R": ["11110", "10001", "11110", "10010", "10001"],
    "S": ["01111", "10000", "01110", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10101", "11011", "10001"],
    "X": ["10001", "01010", "00100", "01010", "10001"],
    "Y": ["10001", "01010", "00100", "00100", "00100"],
    "Z": ["11111", "00010", "00100", "01000", "11111"],
    "0": ["01110", "10011", "10101", "11001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00110", "01000", "11111"],
    "3": ["11110", "00001", "01110", "00001", "11110"],
    "4": ["00010", "00110", "01010", "11111", "00010"],
    "5": ["11111", "10000", "11110", "00001", "11110"],
    "6": ["01110", "10000", "11110", "10001", "01110"],
    "7": ["11111", "00010", "00100", "01000", "01000"],
    "8": ["01110", "10001", "01110", "10001", "01110"],
    "9": ["01110", "10001", "01111", "00001", "01110"],
    "©": ["01110", "10001", "10101", "10001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000"],
}

COPYRIGHT = "© 2026 ANIME EDITION"
PHRASES = {
    "es": "PULSA START",
    "en": "PRESS START",
    "pt": "PRESSIONE START",
    "it": "PREMI START",
}


def glyph_mask(ch):
    rows = FONT.get(ch.upper(), FONT[" "])
    return [[bit == "1" for bit in row] for row in rows]


def text_width(text, advance):
    return (len(text) - 1) * advance + 7


def draw_text(img, text, y, advance):
    """Dibuja el texto centrado en el área visible, con contorno negro."""
    width = text_width(text, advance)
    left = VISIBLE_LEFT + (VISIBLE_WIDTH - width) // 2
    x = left + 1  # el contorno sobresale 1 px a la izquierda

    pixels = img.load()
    for ch in text:
        mask = glyph_mask(ch)
        # contorno
        for py in range(5):
            for px in range(5):
                if not mask[py][px]:
                    continue
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = x + px + dx, y + 1 + py + dy
                        if 0 <= nx < W and 0 <= ny < H:
                            pixels[nx, ny] = BLACK
        # relleno con bisel suave (fila superior e inferior)
        for py in range(5):
            for px in range(5):
                if not mask[py][px]:
                    continue
                if py == 0:
                    color = OFF_WHITE
                elif py == 4:
                    color = LIGHT_GRAY
                else:
                    color = WHITE
                pixels[x + px, y + 1 + py] = color
        x += advance


def make_sheet(phrase, path):
    img = Image.new("P", (W, H), TRANSPARENT)
    img.putpalette([c for rgb in PALETTE for c in rgb])
    draw_text(img, phrase, 0, 10)
    draw_text(img, COPYRIGHT, 8, 7)
    img.save(path)
    print("escrito:", path, img.size)


def main():
    for lang, phrase in PHRASES.items():
        make_sheet(phrase, os.path.join(OUT_DIR, f"press_start_{lang}.png"))


if __name__ == "__main__":
    main()
