#!/usr/bin/env python3
"""Oráculo de arranque: ¿la partida nueva llega al campo o se reinicia?

Arranca mGBA con el GDB stub, pone un breakpoint en `CB2_Overworld`, pulsa A
y espera. Si el breakpoint salta, el mapa cargó (imprime mapa/pos/party).
Si no salta en el tiempo dado, el arranque se colgó o se reinició.

Uso:
    python3 tools/anime-debug/boottest.py [segundos] [ruta_rom]
"""
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsp as R

DISPLAY = os.environ.get("DISPLAY", ":99")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_ROM = os.path.join(REPO, "pokemon-anime-edition.gba")


def xdo(*a):
    subprocess.run(["xdotool"] + list(a), env={**os.environ, "DISPLAY": DISPLAY},
                   capture_output=True)


def wid():
    out = subprocess.run(["xdotool", "search", "--name", "mGBA - POKEMON"],
                         capture_output=True, text=True,
                         env={**os.environ, "DISPLAY": DISPLAY})
    ids = out.stdout.split()
    return ids[0] if ids else None


def main():
    timeout = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
    rom = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_ROM

    subprocess.run(["pkill", "-9", "-x", "mgba-qt"], capture_output=True)
    time.sleep(2)
    for f in os.listdir(REPO):
        if f.endswith(".sav"):
            try:
                os.unlink(os.path.join(REPO, f))
            except OSError:
                pass
    subprocess.Popen(["/usr/games/mgba-qt", "-g", rom],
                     env={**os.environ, "DISPLAY": DISPLAY},
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     cwd="/tmp")
    time.sleep(8)

    w = wid()
    if not w:
        print("RESULT: no window")
        return 2

    syms = R.load_symbols()
    addr = syms["CB2_Overworld"] | 1
    r = R.RSP(timeout=timeout + 5)
    r.s.settimeout(timeout + 5)
    r.cmd("Z0,%x,2" % addr)

    def driver():
        xdo("windowactivate", w)
        t = time.time()
        while time.time() - t < timeout:
            xdo("keydown", "--window", w, "x")
            time.sleep(0.05)
            xdo("keyup", "--window", w, "x")
            time.sleep(0.30)

    threading.Thread(target=driver, daemon=True).start()
    t0 = time.time()
    try:
        r.cmd("c")
        dt = time.time() - t0
        sb1 = r.ptr(syms["gSaveBlock1Ptr"])
        print("RESULT: FIELD OK  %.1fs  map=%s pos=%s party=%d" % (
            dt,
            (r.u8(sb1 + 5), r.u8(sb1 + 4)),
            (r.s16(sb1), r.s16(sb1 + 2)),
            r.u8(syms["gPartiesCount"])))
        return 0
    except Exception:
        print("RESULT: NO FIELD (crash/timeout)")
        return 1
    finally:
        try:
            r.cmd("z0,%x,2" % addr)
        except Exception:
            pass
        r.close()


if __name__ == "__main__":
    sys.exit(main())
