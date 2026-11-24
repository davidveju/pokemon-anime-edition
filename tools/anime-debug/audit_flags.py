#!/usr/bin/env python3
"""Audita flags de `include/constants/flags.h` y su uso en mapas.

Detecta:
  1. Duplicados (mismo valor con varios nombres).
  2. Flags usadas por objetos de mapa pero stubbeadas a 0 (siempre visibles).
  3. Flags `FLAG_UNUSED_*` libres, listas para reasignar.

Uso: python3 tools/anime-debug/audit_flags.py
"""
import glob
import os
import re
import collections

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLAGS_H = os.path.join(REPO, "include/constants/flags.h")
SCAN_ROOTS = ("data", "src", "include", "asm")
SKIP_EXT = (".o", ".d", ".bin", ".png", ".lz", ".gbapal", ".4bpp", ".8bpp", ".smol")


def parse_flags():
    names = {}
    by_value = collections.defaultdict(list)
    text = open(FLAGS_H, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"^#define\s+(FLAG_\w+)\s+\(?\s*(0x[0-9A-Fa-f]+|\d+)\s*\)?", text, re.M):
        name, val = m.group(1), int(m.group(2), 0)
        names[name] = val
        by_value[val].append(name)
    return names, by_value


def index_referenced_flags():
    """Todas las FLAG_* mencionadas fuera de flags.h (una sola pasada)."""
    refs = collections.defaultdict(set)
    pat = re.compile(r"\b(FLAG_\w+)\b")
    for root in SCAN_ROOTS:
        for path in glob.glob(os.path.join(REPO, root, "**/*"), recursive=True):
            if not os.path.isfile(path) or path.endswith(SKIP_EXT):
                continue
            if os.path.abspath(path) == os.path.abspath(FLAGS_H):
                continue
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for name in pat.findall(text):
                refs[name].add(path)
    return refs


def used_in_maps():
    used = collections.defaultdict(set)
    for path in glob.glob(os.path.join(REPO, "data/maps/**/*.json"), recursive=True):
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for f in re.findall(r'"flag"\s*:\s*"(FLAG_\w+)"', text):
            used[f].add(os.path.basename(os.path.dirname(path)))
    return used


def main():
    names, by_value = parse_flags()
    used = used_in_maps()
    refs = index_referenced_flags()

    print("== Duplicados (mismo valor, distinto nombre) ==")
    dups = {v: n for v, n in by_value.items() if len(n) > 1 and v != 0}
    if not dups:
        print("  ninguno")
    for v, n in sorted(dups.items()):
        print("  0x%03X: %s" % (v, ", ".join(sorted(n))))

    print("\n== Flags usadas por mapas pero stubbeadas a 0 ==")
    stubbed = [(f, sorted(m)) for f, m in used.items() if names.get(f) == 0]
    if not stubbed:
        print("  ninguna")
    for f, maps in sorted(stubbed):
        print("  %-50s %s" % (f, ", ".join(maps[:2]) + ("…" if len(maps) > 2 else "")))

    free = [(val, name) for name, val in names.items()
            if name.startswith("FLAG_UNUSED_") and val != 0 and val < 0x500
            and name not in refs]
    print("\n== FLAG_UNUSED libres (<0x500, sin referencias) ==")
    print("  total: %d" % len(free))
    for val, name in sorted(free)[:30]:
        print("  0x%03X  %s" % (val, name))
    if len(free) > 30:
        print("  ...")


if __name__ == "__main__":
    main()
