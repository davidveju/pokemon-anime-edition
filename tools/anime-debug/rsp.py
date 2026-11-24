#!/usr/bin/env python3
"""Minimal GDB-RSP client for mGBA's (old) GDB stub.

No gdb needed: speaks the wire protocol directly so we can read memory
(map, party, flags, vars) and set breakpoints without screenshots.
"""
import socket, sys, time, re, argparse

import os
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP_FILE = os.environ.get("ANIME_MAP", os.path.join(_REPO, "pokeemerald.map"))

def load_symbols(path=MAP_FILE):
    syms = {}
    rx = re.compile(r"^\s+0x([0-9a-fA-F]{8})\s+(\S+)\s*$")
    with open(path, "r", errors="ignore") as f:
        for line in f:
            m = rx.match(line)
            if m:
                syms.setdefault(m.group(2), int(m.group(1), 16))
    return syms

class RSP:
    def __init__(self, host="127.0.0.1", port=2345, timeout=5.0):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
        self.buf = b""

    def _recv_byte(self):
        while not self.buf:
            self.buf += self.s.recv(4096)
        b, self.buf = self.buf[:1], self.buf[1:]
        return b

    def _recv_packet(self):
        # skip until '$'
        while True:
            b = self._recv_byte()
            if b == b"$":
                break
        data = b""
        while True:
            b = self._recv_byte()
            if b == b"#":
                break
            data += b
        csum = self._recv_byte() + self._recv_byte()
        # ack
        self.s.sendall(b"+")
        return data.decode("latin1")

    def cmd(self, payload, retries=3):
        for attempt in range(retries):
            pkt = payload.encode("latin1")
            csum = sum(pkt) & 0xFF
            self.s.sendall(b"$" + pkt + b"#" + ("%02x" % csum).encode())
            try:
                return self._recv_packet()
            except socket.timeout:
                if attempt == retries - 1:
                    raise
        return None

    def read(self, addr, length):
        out = b""
        while length > 0:
            n = min(length, 512)
            resp = self.cmd("m%x,%x" % (addr, n))
            if not resp:
                raise RuntimeError("empty read at 0x%x" % addr)
            out += bytes.fromhex(resp)
            addr += n
            length -= n
        return out

    def u8(self, addr):
        return self.read(addr, 1)[0]

    def u16(self, addr):
        return int.from_bytes(self.read(addr, 2), "little", signed=False)

    def s16(self, addr):
        return int.from_bytes(self.read(addr, 2), "little", signed=True)

    def u32(self, addr):
        return int.from_bytes(self.read(addr, 4), "little", signed=False)

    def ptr(self, sym_addr):
        return self.u32(sym_addr)

    def breakpoint(self, addr):
        return self.cmd("Z0,%x,2" % addr)

    def clear_breakpoint(self, addr):
        return self.cmd("z0,%x,2" % addr)

    def regs(self):
        r = self.cmd("g")
        if not r or len(r) < 16 * 8:
            return {}
        # ARM layout in mGBA stub: r0-r15 then cpsr etc.
        vals = [int(r[i*8:(i+1)*8], 16) for i in range(len(r)//8)]
        names = ["r%d" % i for i in range(16)] + ["cpsr"]
        return dict(zip(names, vals))

    def reg(self, name):
        return self.regs().get(name)

    def alive(self):
        try:
            return self.cmd("?") is not None
        except Exception:
            return False

    def pause(self):
        # send interrupt over the socket
        self.s.sendall(b"\x03")
        try:
            return self._recv_packet()
        except socket.timeout:
            return None

    def cont(self):
        pkt = b"c"
        csum = sum(pkt) & 0xFF
        self.s.sendall(b"$" + pkt + b"#" + ("%02x" % csum).encode())
        # wait for stop packet ('S..'/'T..')
        return self._recv_packet()

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def dump_state(addr_override=None):
    syms = load_symbols()
    rsp = RSP()
    try:
        rsp.pause()
        gmain = syms["gMain"]
        sb1p = syms["gSaveBlock1Ptr"]
        sb2p = syms["gSaveBlock2Ptr"]
        partc = syms["gPartiesCount"]

        cb2 = rsp.u32(gmain + 4)
        state = rsp.u8(gmain + 0x438)
        sb1 = rsp.ptr(sb1p)
        sb2 = rsp.ptr(sb2p)
        posx = rsp.s16(sb1 + 0x00)
        posy = rsp.s16(sb1 + 0x02)
        mg = rsp.u8(sb1 + 0x04)
        mn = rsp.u8(sb1 + 0x05)
        parties = rsp.u8(partc)

        out = {
            "cb2": cb2,
            "cb2_sym": next((n for n, a in syms.items() if a == cb2), "?"),
            "gmain_state": state,
            "saveblock1": sb1,
            "saveblock2": sb2,
            "pos": (posx, posy),
            "map_group": mg,
            "map_num": mn,
            "party_count": parties,
        }
        if addr_override:
            out["custom"] = rsp.read(addr_override, 32).hex()
        return out
    finally:
        rsp.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", nargs="?", default="state")
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()
    if a.action == "state":
        st = dump_state()
        for k, v in st.items():
            print("%s = %s" % (k, v))
    elif a.action == "read":
        rsp = RSP()
        try:
            addr = int(a.args[0], 0)
            ln = int(a.args[1], 0) if len(a.args) > 1 else 16
            print(rsp.read(addr, ln).hex())
        finally:
            rsp.close()
    else:
        print("unknown action")

def run_for(rsp, seconds):
    pkt = b"c"
    rsp.s.sendall(b"$" + pkt + b"#" + ("%02x" % (sum(pkt) & 0xFF)).encode())
    time.sleep(seconds)
    rsp.s.sendall(b"\x03")
    try:
        rsp._recv_packet()
    except Exception:
        pass


def sync(rsp, syms=None):
    """Stop the CPU at the next frame boundary (breakpoint on RunTasks)."""
    if syms is None:
        syms = load_symbols()
    addr = syms.get("RunTasks") + 1  # thumb bit for breakpoint match
    if addr is None:
        raise RuntimeError("RunTasks symbol not found")
    rsp.cmd("Z0,%x,2" % addr)
    rsp.cmd("c")
    return rsp


def state():
    syms = load_symbols()
    rsp = RSP()
    try:
        sync(rsp, syms)
        gmain = syms["gMain"]
        sb1p = syms["gSaveBlock1Ptr"]
        sb2p = syms["gSaveBlock2Ptr"]
        partc = syms["gPartiesCount"]
        cb1 = rsp.u32(gmain + 0)
        cb2 = rsp.u32(gmain + 4)
        st = rsp.u8(gmain + 0x438)
        sb1 = rsp.ptr(sb1p)
        sb2 = rsp.ptr(sb2p)
        d = {
            "cb1": cb1,
            "cb1_sym": sym_name(syms, cb1),
            "cb2": cb2,
            "cb2_sym": sym_name(syms, cb2),
            "gmain_state": st,
            "saveblock1": hex(sb1),
            "saveblock2": hex(sb2),
            "pos": (rsp.s16(sb1), rsp.s16(sb1 + 2)),
            "map": (rsp.u8(sb1 + 5), rsp.u8(sb1 + 4)),  # (num, group)
            "party_count": rsp.u8(partc),
        }
        return d
    finally:
        rsp.close()


def sym_name(syms, addr):
    addr &= ~1
    for n, a in syms.items():
        if a == addr:
            return n
    return "?"


def resume():
    """Clear the frame breakpoint and let the game run (then disconnect)."""
    syms = load_symbols()
    rsp = RSP()
    try:
        addr = syms["RunTasks"] + 1
        rsp.cmd("z0,%x,2" % addr)
        pkt = b"c"
        rsp.s.sendall(b"$" + pkt + b"#" + ("%02x" % (sum(pkt) & 0xFF)).encode())
        time.sleep(0.05)
    finally:
        rsp.close()
