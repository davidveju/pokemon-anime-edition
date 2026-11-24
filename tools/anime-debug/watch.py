#!/usr/bin/env python3
"""Run the game freely and stop at a symbol breakpoint, then dump state.

Usage: watch.py <symbol> [timeout_seconds] [mash_key]
Example: watch.py ScrCmd_createmon 120 x
"""
import os, subprocess, sys, threading, time

sys.path.insert(0, "/tmp/gbatest")
import rsp as R

DISPLAY = ":99"

def wid():
    out = subprocess.run(["xdotool", "search", "--name", "mGBA - POKEMON"],
                         capture_output=True, text=True,
                         env={**os.environ, "DISPLAY": DISPLAY})
    ids = out.stdout.split()
    return ids[0] if ids else None

def mash(key, seconds, window):
    env = {**os.environ, "DISPLAY": DISPLAY}
    end = time.time() + seconds
    # hold fast-forward
    subprocess.run(["xdotool", "keydown", "--window", window, "Tab"], env=env, capture_output=True)
    try:
        while time.time() < end:
            subprocess.run(["xdotool", "keydown", "--window", window, key], env=env, capture_output=True)
            time.sleep(0.06)
            subprocess.run(["xdotool", "keyup", "--window", window, key], env=env, capture_output=True)
            time.sleep(0.22)
    finally:
        subprocess.run(["xdotool", "keyup", "--window", window, "Tab"], env=env, capture_output=True)

def main():
    sym = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
    key = sys.argv[3] if len(sys.argv) > 3 else None

    syms = R.load_symbols()
    addr = syms.get(sym)
    if addr is None:
        print("symbol not found:", sym)
        return 2
    w = wid()
    if not w:
        print("no mGBA window")
        return 2

    r = R.RSP(timeout=timeout + 10)
    r.s.settimeout(timeout + 10)
    print("breakpoint %s @ 0x%08x" % (sym, addr), flush=True)
    r.cmd("Z0,%x,2" % (addr | 1))

    if key:
        t = threading.Thread(target=mash, args=(key, timeout, w), daemon=True)
        t.start()

    t0 = time.time()
    try:
        stop = r.cmd("c")
        elapsed = time.time() - t0
        print("STOP after %.1fs: %s" % (elapsed, stop), flush=True)
        regs = r.regs()
        pc = regs.get("r15", 0)
        lr = regs.get("r14", 0)
        print("pc=%s lr=%s" % (R.sym_name(syms, pc), R.sym_name(syms, lr)), flush=True)
        gmain = syms["gMain"]
        sb1 = r.ptr(syms["gSaveBlock1Ptr"])
        print("cb2=%s state=%d map=%s pos=%s party=%d" % (
            R.sym_name(syms, r.u32(gmain + 4)),
            r.u8(gmain + 0x438),
            (r.u8(sb1 + 5), r.u8(sb1 + 4)),
            (r.s16(sb1), r.s16(sb1 + 2)),
            r.u8(syms["gPartiesCount"])), flush=True)
        return 0
    except Exception as e:
        print("timeout/err:", e, flush=True)
        return 1
    finally:
        try:
            r.cmd("z0,%x,2" % (addr | 1))
        except Exception:
            pass
        r.close()

if __name__ == "__main__":
    sys.exit(main())
