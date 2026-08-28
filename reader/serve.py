#!/usr/bin/env python3
"""Development server for the reader with Range request support.

`python3 -m http.server` does NOT support ranges, and without ranges the
<audio> can't seek inside the mp3 (it jumps back to 0:00).
Usage:  python3 serve.py [port]
"""
import os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
        size = os.path.getsize(path)
        if not m or (not m.group(1) and not m.group(2)):
            return super().send_head()
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2)))
        end = min(int(m.group(2)), size - 1) if m.group(1) and m.group(2) else size - 1
        if end < start:                          # inverted range: ignore it (RFC 7233)
            return super().send_head()
        if start >= size:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._range_left = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        left = getattr(self, "_range_left", None)
        if left is None:
            return super().copyfile(source, outputfile)
        while left > 0:
            buf = source.read(min(64 * 1024, left))
            if not buf:
                break
            outputfile.write(buf)
            left -= len(buf)
        self._range_left = None

    def end_headers(self):
        if not any(h.lower() == "accept-ranges" for h in self._headers_buffer_names()):
            self.send_header("Accept-Ranges", "bytes")
        # development server: no caching at all (phones cache aggressively)
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _headers_buffer_names(self):
        try:
            return [b.decode().split(":")[0] for b in self._headers_buffer]
        except Exception:
            return []

if __name__ == "__main__":
    # bind to localhost by default; --lan exposes it to the network (needed
    # to read from a phone/tablet, but then anyone on the Wi-Fi can reach it)
    args = [a for a in sys.argv[1:] if a != "--lan"]
    lan = "--lan" in sys.argv
    port = int(args[0]) if args else 8123
    host, shown = ("", "tu-IP-local") if lan else ("127.0.0.1", "localhost")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"escolib en http://{shown}:{port}/  (biblioteca; un texto: /?doc=<slug>)"
          + ("" if lan else "  ·  usá --lan para leer desde el celular"))
    ThreadingHTTPServer((host, port), RangeHandler).serve_forever()
