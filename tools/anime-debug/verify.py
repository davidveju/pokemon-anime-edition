#!/usr/bin/env python3
"""Verify anime flags/vars right after the lab intro sets its variables."""
import os, subprocess, sys, threading, time

sys.path.insert(0, "/tmp/gbatest")
import rsp as R

DISPLAY = ":99"
VAR_LAB = 0x4055          # VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB
VAR_TOWN_OAK = 0x4050
FLAGS_OFF = 0x1270        # SaveBlock1 flags[] offset
VARS_OFF = 0x139C         # SaveBlock1 vars[] offset

def wid():
    out = subprocess.run(["xdotool", "search", "--name", "mGBA - POKEMON"],
                         capture_output=True, text=True,
                         env={**os.environ, "DISPLAY": DISPLAY})
    ids = out.stdout.split()
    return ids[0] if ids else None

def mash(key, seconds, window):
    env = {**os.environ, "DISPLAY": DISPLAY}
    end = time.time() + seconds
    subprocess.run(["xdotool", "keydown", "--window", window, "Tab"], env=env, capture_output=True)
    try:
        while time.time() < end:
            subprocess.run(["xdotool", "keydown", "--window", window, key], env=env, capture_output=True)
            time.sleep(0.06)
            subprocess.run(["xdotool", "keyup", "--window", window, key], env=env, capture_output=True)
            time.sleep(0.2)
    finally:
        subprocess.run(["xdotool", "keyup", "--window", window, "Tab"], env=env, capture_output=True)

def flag(r, sb1, fid):
    b = r.u8(sb1 + FLAGS_OFF + (fid >> 3))
    return (b >> (fid & 7)) & 1

def var(r, sb1, vid):
    return r.u16(sb1 + VARS_OFF + (vid - 0x4000) * 2)

def main():
    syms = R.load_symbols()
    addr = syms["VarSet"]
    w = wid()
    if not w:
        print("no window"); return 2
    r = R.RSP(timeout=200)
    r.s.settimeout(200)
    r.cmd("Z0,%x,2" % (addr | 1))
    threading.Thread(target=mash, args=("x", 150, w), daemon=True).start()
    t0 = time.time()
    try:
        while time.time() - t0 < 160:
            stop = r.cmd("c")
            regs = r.regs()
            vid = regs.get("r0", 0) & 0xFFFF
            val = regs.get("r1", 0) & 0xFFFF
            if vid in (VAR_LAB, VAR_TOWN_OAK):
                sb1 = r.ptr(syms["gSaveBlock1Ptr"])
                print("VarSet(0x%04X, %d)" % (vid, val))
                names = [
                    ("LANG_BIT0", 0x493), ("LANG_BIT1", 0x494),
                    ("PIKACHU_RECEIVED", 0x495), ("CANNOT_EVOLVE", 0x496),
                    ("CANNOT_DEPOSIT", 0x497),
                ]
                for n, f in names:
                    print("  %-18s = %d" % (n, flag(r, sb1, f)))
                for v in (VAR_LOCAL if False else VAR_TOWN_OAK, VAR_LAB):
                    print("  var 0x%04X = %d" % (v, var(r, sb1, v)))
                print("  party =", r.u8(syms["gPartiesCount"]))
                print("  map   =", (r.u8(sb1 + 5), r.u8(sb1 + 4)), "pos =", (r.s16(sb1), r.s16(sb1 + 2)))
                return 0
        print("no VarSet hit for target vars")
        return 1
    finally:
        try:
            r.cmd("z0,%x,2" % (addr | 1))
        except Exception:
            pass
        r.close()

if __name__ == "__main__":
    sys.exit(main())
