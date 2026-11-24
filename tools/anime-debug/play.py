#!/usr/bin/env python3
"""Drive the ROM through mGBA's GDB stub while reading game memory.

The stub pauses on disconnect, so we keep the connection open and step one
frame at a time via a breakpoint on RunTasks. Keys are injected with xdotool
between frame steps.
"""
import subprocess, sys, time, re, os

sys.path.insert(0, "/tmp/gbatest")
import rsp as R

DISPLAY = ":99"

def wid():
    out = subprocess.run(["xdotool", "search", "--name", "mGBA - POKEMON"],
                         capture_output=True, text=True, env={**os.environ, "DISPLAY": DISPLAY})
    ids = out.stdout.split()
    return ids[0] if ids else None

def key_down(k, w):
    subprocess.run(["xdotool", "keydown", "--window", w, k], env={**os.environ, "DISPLAY": DISPLAY},
                   capture_output=True)

def key_up(k, w):
    subprocess.run(["xdotool", "keyup", "--window", w, k], env={**os.environ, "DISPLAY": DISPLAY},
                   capture_output=True)

def read_state(r, syms):
    gmain = syms["gMain"]
    sb1 = r.ptr(syms["gSaveBlock1Ptr"])
    partc = syms["gPartiesCount"]
    return {
        "cb2": r.u32(gmain + 4),
        "state": r.u8(gmain + 0x438),
        "pos": (r.s16(sb1), r.s16(sb1 + 2)),
        "map": (r.u8(sb1 + 5), r.u8(sb1 + 4)),
        "party": r.u8(partc),
        "frames": r.u32(gmain + 0x20),
    }

def main():
    syms = R.load_symbols()
    w = wid()
    if not w:
        print("no mGBA window")
        return 2
    r = R.RSP()
    runtasks = syms["RunTasks"] + 1
    r.cmd("Z0,%x,2" % runtasks)
    r.cmd("c")

    target_map = (3, 38)  # (mapNum, mapGroup) Oak's lab
    presses = 0
    start = time.time()
    last_report = 0
    try:
        while time.time() - start < 300:
            r.cmd("c")  # advance one frame, stop again
            st = read_state(r, syms)
            now = time.time()
            if now - last_report > 5:
                last_report = now
                print("t=%3ds frames=%d cb2=%s map=%s pos=%s party=%d" % (
                    now - start, st["frames"], R.sym_name(syms, st["cb2"]),
                    st["map"], st["pos"], st["party"]), flush=True)
            if st["map"] == target_map:
                print("REACHED LAB: pos=%s party=%d frames=%d" % (st["pos"], st["party"], st["frames"]), flush=True)
                # give it a few frames to run the intro script
                for _ in range(120):
                    r.cmd("c")
                st = read_state(r, syms)
                print("FINAL: map=%s pos=%s party=%d" % (st["map"], st["pos"], st["party"]), flush=True)
                return 0
            # inject a key every 30 frames
            if st["frames"] % 30 < 2:
                key_down("x", w)
                r.cmd("c")
                key_up("x", w)
                presses += 1
        print("timeout; last:", st, flush=True)
        return 1
    finally:
        try:
            r.cmd("z0,%x,2" % runtasks)
        except Exception:
            pass
        r.close()

if __name__ == "__main__":
    sys.exit(main())
