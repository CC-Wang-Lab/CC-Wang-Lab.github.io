#!/usr/bin/env python3
"""
A dependency-free Chrome DevTools Protocol client, used by shoot.py --emulate.

WHY THIS EXISTS
---------------
`msedge.exe --window-size=320,4000 --screenshot=x.png` does NOT lay the page
out at 320 CSS px. Headless Edge on Windows refuses to open a window narrower
than about 508 DIP, lays the page out at ~484 px, and then CROPS the PNG to
320. The picture looks like a phone and is a lie: it is a 484 px layout with
164 px cut off the right. `NARROWEST = 492` in shoot.py exists to stop that lie
being written to a filename, at the cost of never testing a real phone width.

`Emulation.setDeviceMetricsOverride` sets the LAYOUT viewport instead of the
window, so 320 really is 320. That call is only reachable over CDP, which is
why this file exists.

    +---------------------+-------------------+----------------------+
    | mechanism           | layout viewport   | screenshot           |
    +---------------------+-------------------+----------------------+
    | --window-size=320   | 484 px (clamped)  | 320 px (cropped)     |
    | setDeviceMetrics    | 320 px            | 320 px               |
    +---------------------+-------------------+----------------------+

THE PORT WARNING IN shoot.py IS STILL TRUE, AND THIS IS WHY IT IS SAFE HERE
--------------------------------------------------------------------------
shoot.py says never to add --remote-debugging-port, because that is the flag
that makes a Chromium binary attach to an instance already running. That is
true when the launch shares the user's own profile directory. Chromium decides
"am I already running?" from a lock inside --user-data-dir, NOT from the port.

Every launch here gets a throwaway --user-data-dir, exactly as the existing
screenshot path does, so there is no instance to attach to and a real browser
process always starts. The port is 0, so the OS picks a free one and Edge
writes it to DevToolsActivePort inside that same throwaway directory. Two runs
cannot collide on a port, and neither can touch the reviewer's own browser.

WHAT IS DELIBERATELY NOT HERE
-----------------------------
No permessage-deflate. The handshake never offers it, so every frame arrives
uncompressed and the reader below does not need an inflater. A screenshot of a
tall page is several megabytes of base64 and arrives as continuation frames;
those ARE handled.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

# Frame opcodes, from RFC 6455 section 5.2.
OP_CONT, OP_TEXT, OP_BIN, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA


class WebSocket:
    """The 5% of RFC 6455 a CDP client needs: text frames, one connection."""

    def __init__(self, url: str, timeout: float = 60.0):
        parts = urlsplit(url)
        self.sock = socket.create_connection(
            (parts.hostname, parts.port), timeout=timeout)
        self.sock.settimeout(timeout)
        path = parts.path + (("?" + parts.query) if parts.query else "")
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        self.sock.sendall((
            "GET %s HTTP/1.1\r\n"
            "Host: %s:%d\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n" % (path, parts.hostname, parts.port, key)
        ).encode("ascii"))
        self._buf = b""
        while b"\r\n\r\n" not in self._buf:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise RuntimeError("websocket closed during handshake")
            self._buf += chunk
        head, self._buf = self._buf.split(b"\r\n\r\n", 1)
        status = head.split(b"\r\n", 1)[0]
        if b" 101" not in status:
            raise RuntimeError("websocket handshake refused: %s"
                               % status.decode("latin-1"))

    # -- reading ----------------------------------------------------------
    def _read(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self.sock.recv(max(65536, n - len(self._buf)))
            if not chunk:
                raise RuntimeError("websocket closed by peer")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def recv(self) -> str:
        """One complete text message, reassembled across continuation frames."""
        payload = bytearray()
        opcode = None
        while True:
            b0, b1 = self._read(2)
            fin, op = b0 & 0x80, b0 & 0x0F
            masked, length = b1 & 0x80, b1 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._read(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._read(8))[0]
            mask = self._read(4) if masked else b""
            data = self._read(length)
            if masked:
                data = bytes(c ^ mask[i % 4] for i, c in enumerate(data))
            if op == OP_CLOSE:
                raise RuntimeError("websocket closed by peer")
            if op == OP_PING:
                self._frame(OP_PONG, data)
                continue
            if op == OP_PONG:
                continue
            if opcode is None:
                opcode = op
            payload += data
            if fin:
                if opcode != OP_TEXT:
                    raise RuntimeError("unexpected binary frame from CDP")
                return payload.decode("utf-8")

    # -- writing ----------------------------------------------------------
    def _frame(self, opcode: int, data: bytes) -> None:
        # Client frames MUST be masked. The mask is not security, it is a
        # proxy-poisoning guard, and a server will drop an unmasked frame.
        mask = os.urandom(4)
        body = bytes(c ^ mask[i % 4] for i, c in enumerate(data))
        n = len(data)
        if n < 126:
            header = struct.pack("!BB", 0x80 | opcode, 0x80 | n)
        elif n < (1 << 16):
            header = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, n)
        else:
            header = struct.pack("!BBQ", 0x80 | opcode, 0x80 | 127, n)
        self.sock.sendall(header + mask + body)

    def send(self, text: str) -> None:
        self._frame(OP_TEXT, text.encode("utf-8"))

    def close(self) -> None:
        try:
            self._frame(OP_CLOSE, b"")
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


class Browser:
    """One throwaway headless Edge, driven over CDP. Use as a context manager."""

    def __init__(self, edge: Path, profile: Path, extra_args=()):
        # One profile per PROCESS, never a fixed name. A run killed part way
        # through leaves a live msedge.exe holding the profile's lockfile, and
        # the NEXT launch then finds an instance already running, refuses to
        # start a browser of its own, and writes no DevToolsActivePort. The
        # symptom is "Edge never started" and the cause is the previous run.
        # A pid suffix makes that collision impossible.
        profile = profile.parent / ("%s-%d" % (profile.name, os.getpid()))
        profile.mkdir(parents=True, exist_ok=True)
        # ABSOLUTE, always. A relative --user-data-dir is resolved against the
        # BROWSER's working directory, not this process's, so Edge silently
        # starts somewhere else and DevToolsActivePort never appears where we
        # are polling. That failure looks exactly like "Edge never started".
        profile = profile.resolve()
        self.profile = profile
        self.proc = subprocess.Popen(
            [str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1", "--force-color-profile=srgb",
             "--disable-lcd-text", "--no-first-run", "--no-default-browser-check",
             "--disable-extensions", "--disable-sync",
             "--disable-features=Translate,MediaRouter,OptimizationHints",
             # Port 0 plus a throwaway profile: see the module docstring.
             "--remote-debugging-port=0",
             "--user-data-dir=" + str(profile),
             "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.port = self._await_port()
        self.ws = WebSocket(self._page_target())
        self._id = 0
        self._events: list[dict] = []

    def _await_port(self, deadline: float = 40.0) -> int:
        # Edge writes DevToolsActivePort into the profile once the socket is
        # listening. Polling that file is the only supported way to learn a
        # port chosen by the OS.
        #
        # DO NOT add `if self.proc.poll() is not None: fail` here. It was here
        # once and made every launch fail instantly. Point 5 of shoot.py's
        # docstring is the reason: the msedge.exe you launch is a STUB. It
        # hands the work to a detached process and exits 0 straight away, so
        # `poll()` returns 0 while the real browser is still starting up. The
        # port file is the only honest signal, and the deadline is the only
        # honest failure.
        stamp = self.profile / "DevToolsActivePort"
        end = time.monotonic() + deadline
        while time.monotonic() < end:
            try:
                # Windows hands the file back before Edge has released its
                # exclusive handle, so an existing file can still refuse to
                # open. Both "not there yet" and "not readable yet" mean the
                # same thing: keep waiting.
                text = stamp.read_text(encoding="utf-8").strip()
            except OSError:
                text = ""
            if "\n" in text:
                return int(text.split("\n", 1)[0])
            time.sleep(0.05)
        raise RuntimeError("Edge never wrote DevToolsActivePort in %.0fs" % deadline)

    def _page_target(self, deadline: float = 20.0) -> str:
        end = time.monotonic() + deadline
        while time.monotonic() < end:
            with urllib.request.urlopen(
                    "http://127.0.0.1:%d/json/list" % self.port, timeout=10) as fh:
                for t in json.load(fh):
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        return t["webSocketDebuggerUrl"]
            time.sleep(0.1)
        raise RuntimeError("Edge exposed no page target")

    # -- protocol ---------------------------------------------------------
    def call(self, method: str, params: dict | None = None, timeout: float = 90.0):
        self._id += 1
        want = self._id
        self.ws.send(json.dumps({"id": want, "method": method,
                                 "params": params or {}}))
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == want:
                if "error" in msg:
                    raise RuntimeError("%s failed: %s" % (method, msg["error"]))
                return msg.get("result", {})
            if "method" in msg:
                self._events.append(msg)
        raise TimeoutError("%s did not answer in %.0fs" % (method, timeout))

    def clear_events(self) -> None:
        """Drop buffered events. Call before every navigation.

        Without this, `await_event("Page.loadEventFired")` returns instantly on
        the SECOND page because the FIRST page's load is still in the buffer,
        and every shot after the first is taken before its page exists.
        """
        self._events.clear()

    def seen(self, method: str) -> bool:
        return any(e.get("method") == method for e in self._events)

    def await_event(self, method: str, timeout: float = 60.0) -> dict:
        if self.seen(method):
            return next(e for e in self._events if e.get("method") == method)
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            msg = json.loads(self.ws.recv())
            if "method" in msg:
                self._events.append(msg)
                if msg["method"] == method:
                    return msg
        raise TimeoutError("no %s in %.0fs" % (method, timeout))

    def evaluate(self, expression: str, timeout: float = 60.0):
        """Run JS in the page and return its value. Throws on a page exception."""
        res = self.call("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        }, timeout=timeout)
        if res.get("exceptionDetails"):
            raise RuntimeError("page threw: %s" % json.dumps(
                res["exceptionDetails"].get("exception", {}).get("description",
                res["exceptionDetails"])))
        return res.get("result", {}).get("value")

    # -- teardown ---------------------------------------------------------
    def close(self) -> None:
        # `Browser.close` over the protocol, NOT proc.terminate(). self.proc is
        # the stub described in _await_port; it has already exited, so killing
        # it would leave the real browser running and holding the profile.
        try:
            self.call("Browser.close", timeout=10)
        except Exception:
            pass
        try:
            self.ws.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
