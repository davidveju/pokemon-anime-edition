#!/usr/bin/env python3
"""Genera el fondo del título (BG0) con temática Kanto/anime.

Sustituye el panorama de Rayquaza por Pueblo Paleta: cielo, montañas, colinas,
casas y un Pikachu en primer plano. Mantiene el formato del motor:
  - graphics/title_screen/kanto.png       128x128, atlas de tiles (16x16)
  - graphics/title_screen/kanto.bin       tilemap 32x32 (u16 LE)
  - graphics/title_screen/kanto_and_clouds.pal  banco 14 (JASC-PAL)

El PNG es un atlas: cada tile 8x8 único se coloca en orden (16 por fila) para
que el conversor del build genere exactamente los índices que usa el tilemap.
El tilemap usa el banco de paleta 14 para todos los tiles. La capa de nubes
(BG1) comparte ese banco y usa los índices 0 (transparente), 2 (blanco) y
12 (gris claro): esos tres se mantienen compatibles.

Uso: python3 dev_scripts/generate_title_bg.py
"""

import os
import struct

from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PNG = os.path.join(REPO, "graphics/title_screen/kanto.png")
OUT_BIN = os.path.join(REPO, "graphics/title_screen/kanto.bin")
OUT_PAL = os.path.join(REPO, "graphics/title_screen/kanto_and_clouds.pal")
OUT_GBAPAL = os.path.join(REPO, "graphics/title_screen/kanto_and_clouds.gbapal")

W, H = 240, 160
ATLAS_COLS = 16
ATLAS_ROWS = 16
BANK = 14  # banco de paleta usado por BG0 y las nubes

# Índices de paleta (0 = transparente; el cielo usa 1/3/4/5)
SKY_DEEP, SKY_MID, SKY_LIGHT, SKY_PALE = 1, 3, 4, 5
WHITE, CLOUD_GREY = 2, 12
GRASS_LIGHT, GRASS, GRASS_DARK = 6, 7, 8
SAND, WALL, OUTLINE = 9, 10, 11
MOUNTAIN, RED, YELLOW = 13, 14, 15
SKY = SKY_DEEP

PALETTE = [
    (16, 40, 120),    # 0 azul profundo (fondo de cielo / transparente en BG1)
    (40, 72, 160),    # 1 azul noche
    (255, 255, 255),  # 2 blanco (nubes)
    (72, 120, 216),   # 3 azul medio
    (128, 184, 248),  # 4 azul claro
    (200, 232, 255),  # 5 azul pálido (reserva)
    (152, 216, 112),  # 6 verde claro
    (96, 184, 80),    # 7 verde
    (56, 136, 56),    # 8 verde oscuro
    (216, 184, 120),  # 9 camino
    (232, 232, 232),  # 10 pared
    (40, 48, 64),     # 11 contorno
    (208, 208, 208),  # 12 gris claro (nubes)
    (120, 136, 168),  # 13 montaña
    (200, 64, 56),    # 14 tejado / mejillas
    (248, 208, 48),   # 15 amarillo Pikachu
]


def draw_scene(img):
    d = ImageDraw.Draw(img)

    # Cielo por bandas (pocos tiles únicos)
    d.rectangle([0, 0, W, 44], fill=SKY_DEEP)
    d.rectangle([0, 44, W, 72], fill=SKY_MID)
    d.rectangle([0, 72, W, 90], fill=SKY_LIGHT)
    d.rectangle([0, 90, W, 100], fill=SKY_PALE)

    # Nubes estáticas (la capa BG1 añade nubes animadas encima)
    def cloud(cx, cy, s):
        d.ellipse([cx - 15 * s, cy - 5 * s, cx + 15 * s, cy + 5 * s], fill=WHITE)
        d.ellipse([cx - 22 * s, cy - 1 * s, cx - 3 * s, cy + 5 * s], fill=WHITE)
        d.ellipse([cx + 3 * s, cy - 3 * s, cx + 23 * s, cy + 5 * s], fill=WHITE)
        d.rectangle([cx - 21 * s, cy + 3 * s, cx + 21 * s, cy + 5 * s], fill=CLOUD_GREY)

    cloud(42, 34, 1)
    cloud(206, 54, 1)

    # Montañas con nieve
    d.polygon([(0, 106), (52, 66), (104, 106)], fill=MOUNTAIN)
    d.polygon([(62, 106), (124, 56), (186, 106)], fill=MOUNTAIN)
    d.polygon([(152, 106), (210, 70), (240, 106)], fill=MOUNTAIN)
    d.polygon([(41, 78), (52, 66), (63, 78)], fill=WHITE)
    d.polygon([(112, 69), (124, 56), (136, 69)], fill=WHITE)
    d.polygon([(201, 81), (210, 70), (219, 81)], fill=WHITE)

    # Colinas y suelo
    d.rectangle([0, 98, W, H], fill=GRASS)
    d.ellipse([-50, 92, 130, 210], fill=GRASS_LIGHT)
    d.ellipse([70, 104, 280, 230], fill=GRASS)
    d.ellipse([-40, 128, 150, 240], fill=GRASS_DARK)
    d.ellipse([160, 122, 330, 236], fill=GRASS_DARK)
    d.ellipse([100, 114, 200, 200], fill=GRASS_LIGHT)

    # Camino de Pueblo Paleta
    d.polygon([(110, 160), (150, 160), (142, 132), (124, 132)], fill=SAND)
    d.polygon([(124, 132), (142, 132), (138, 124), (128, 124)], fill=SAND)

    # Casas
    def house(x, y, w, h):
        # pared
        d.rectangle([x, y + 9, x + w, y + 9 + h], fill=WALL, outline=OUTLINE)
        # tejado
        d.polygon(
            [(x - 4, y + 10), (x + w // 2, y), (x + w + 4, y + 10)],
            fill=RED,
            outline=OUTLINE,
        )
        # puerta
        d.rectangle([x + w // 2 - 4, y + 9 + h - 13, x + w // 2 + 4, y + 9 + h],
                    fill=OUTLINE)
        # ventanas
        d.rectangle([x + 5, y + 15, x + 13, y + 22], fill=SKY_LIGHT, outline=OUTLINE)
        d.rectangle([x + w - 13, y + 15, x + w - 5, y + 22],
                    fill=SKY_LIGHT, outline=OUTLINE)

    house(18, 104, 42, 24)
    house(78, 100, 36, 22)
    house(138, 108, 30, 18)

    # Árboles
    def tree(x, y, s):
        d.rectangle([x - s, y - 8 * s, x + s, y], fill=OUTLINE)
        d.ellipse([x - 9 * s, y - 22 * s, x + 9 * s, y - 4 * s],
                  fill=GRASS_DARK)
        d.ellipse([x - 6 * s, y - 20 * s, x + 6 * s, y - 7 * s], fill=GRASS)

    tree(6, 140, 1)
    tree(70, 144, 1)
    tree(176, 142, 1)
    tree(232, 150, 1)

    # Pikachu en primer plano (derecha, debajo del banner de versión)
    def pikachu():
        # cola (detrás del cuerpo)
        d.polygon(
            [(205, 136), (194, 128), (199, 123), (190, 117), (198, 118),
             (193, 110), (207, 123), (202, 127), (210, 132)],
            fill=YELLOW,
            outline=OUTLINE,
        )
        # cuerpo y patas
        d.ellipse([203, 128, 225, 150], fill=YELLOW, outline=OUTLINE)
        d.ellipse([201, 146, 211, 153], fill=YELLOW, outline=OUTLINE)
        d.ellipse([217, 146, 227, 153], fill=YELLOW, outline=OUTLINE)
        # orejas
        d.polygon([(205, 118), (199, 100), (210, 114)], fill=YELLOW, outline=OUTLINE)
        d.polygon([(219, 114), (226, 100), (223, 119)], fill=YELLOW, outline=OUTLINE)
        d.polygon([(199, 104), (199, 100), (203, 103)], fill=OUTLINE)
        d.polygon([(226, 104), (226, 100), (224, 104)], fill=OUTLINE)
        # cabeza
        d.ellipse([202, 110, 224, 132], fill=YELLOW, outline=OUTLINE)
        # ojos
        d.rectangle([206, 117, 208, 121], fill=OUTLINE)
        d.rectangle([217, 117, 219, 121], fill=OUTLINE)
        d.point((207, 118), fill=WHITE)
        d.point((218, 118), fill=WHITE)
        # mejillas
        d.rectangle([202, 122, 206, 125], fill=RED)
        d.rectangle([220, 122, 224, 125], fill=RED)
        # nariz y boca
        d.point((213, 122), fill=OUTLINE)
        d.line([(211, 125), (213, 126), (215, 125)], fill=OUTLINE)
        # brazos
        d.ellipse([199, 132, 205, 138], fill=YELLOW, outline=OUTLINE)
        d.ellipse([223, 132, 229, 138], fill=YELLOW, outline=OUTLINE)

    pikachu()


def main():
    scene = Image.new("P", (W, H), SKY)
    scene.putpalette([c for rgb in PALETTE for c in rgb])
    draw_scene(scene)

    # Deduplicar tiles 8x8 en orden de aparición.
    tiles = {}
    order = []
    entries = []
    for ty in range(20):
        for tx in range(32):
            if tx >= W // 8:
                entries.append(BANK << 12)  # fuera de la imagen: tile 0
                continue
            patch = scene.crop((tx * 8, ty * 8, tx * 8 + 8, ty * 8 + 8))
            data = patch.tobytes()
            if data not in tiles:
                tiles[data] = len(order)
                order.append(patch)
            entries.append(tiles[data] | (BANK << 12))
    # filas 20..31 (fuera de pantalla): tile de cielo
    for _ in range((32 - 20) * 32):
        entries.append(BANK << 12)

    print("tiles únicos:", len(order), "/", ATLAS_COLS * ATLAS_ROWS)
    assert len(order) <= ATLAS_COLS * ATLAS_ROWS, (
        "demasiados tiles únicos; simplifica el dibujo"
    )

    # Atlas 16x16: el conversor del build genera los tiles en este orden.
    atlas = Image.new("P", (ATLAS_COLS * 8, ATLAS_ROWS * 8), SKY)
    atlas.putpalette([c for rgb in PALETTE for c in rgb])
    for i, patch in enumerate(order):
        atlas.paste(patch, ((i % ATLAS_COLS) * 8, (i // ATLAS_COLS) * 8))

    atlas.save(OUT_PNG)
    with open(OUT_BIN, "wb") as f:
        f.write(struct.pack("<%dH" % len(entries), *entries))

    # Fuente versionada (JASC-PAL): el build la convierte a .gbapal.
    with open(OUT_PAL, "w", newline="\r\n") as f:
        f.write("JASC-PAL\n0100\n16\n")
        for r, g, b in PALETTE:
            f.write(f"{r} {g} {b}\n")

    # Copia ya convertida para poder compilar sin esperar al conversor.
    with open(OUT_GBAPAL, "wb") as f:
        for r, g, b in PALETTE:
            c = ((r >> 3) & 0x1F) | (((g >> 3) & 0x1F) << 5) | (((b >> 3) & 0x1F) << 10)
            f.write(struct.pack("<H", c))

    print("escrito:", OUT_PNG, OUT_BIN, OUT_PAL, OUT_GBAPAL)


if __name__ == "__main__":
    main()
