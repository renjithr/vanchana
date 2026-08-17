#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preview server with inline editing.

Serves build/ and accepts edits from the in-page editor at POST /__cms/save.
An edit rewrites the matching block in content/ml.txt and rebuilds the site,
so what you type is written back to the real source, not to a database.

Deliberately local-only:
  - binds 127.0.0.1, so nothing outside this machine can reach it
  - rejects any request whose client address is not loopback
  - only accepts block ids that already exist in content/ml.txt, so a request
    cannot create entries or reach any other file
  - the editor is compiled in only when CMS_EDIT=1; `./preview.sh --no-edit`
    and every production build omit it entirely
"""
import json, os, re, subprocess, sys, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
BUILD = os.path.join(ROOT, "build")
FILES = [os.path.join(ROOT, "content/ml.txt"),
         os.path.join(ROOT, "content/en.txt")]
PORT = int(os.environ.get("CMS_PORT", "8765"))

sys.path.insert(0, SRC)
import mltext

build_lock = threading.Lock()

def rebuild(edit=True):
    env = dict(os.environ, CMS_EDIT="1" if edit else "0")
    r = subprocess.run([sys.executable, "build_archive.py"], cwd=SRC, env=env,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout).strip()[-800:])
    return r.stdout.strip()

def write_blocks(edits):
    """Replace the body of each [id] block in whichever content file holds it.

    Malayalam ids live in content/ml.txt and English ids in content/en.txt; the
    id is looked up rather than guessed, so an edit can never land in the wrong
    language's file. Only the blocks named are rewritten — comments, ordering
    and untouched blocks stay exactly as they were.
    """
    texts = {f: open(f, encoding="utf-8").read() for f in FILES if os.path.exists(f)}
    known = {f: mltext.parse(t) for f, t in texts.items()}
    written, touched = [], set()
    for path, value in edits.items():
        for one in path.split(","):          # a value can live at several ids
            one = one.strip()
            target = next((f for f in texts if one in known[f]), None)
            if target is None:
                raise KeyError("unknown block: %s" % one)
            val = " ".join(str(value).split())        # normalise whitespace
            pat = re.compile(r"(\[%s\]\n)(?:(?!\n\[).)*" % re.escape(one), re.S)
            new, n = pat.subn(lambda m: m.group(1) + val, texts[target], count=1)
            if not n:
                raise KeyError("could not locate block: %s" % one)
            texts[target] = new
            touched.add(target)
            written.append(one)
    for f in touched:
        open(f, "w", encoding="utf-8").write(texts[f])
    return written

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=BUILD, **kw)

    def _local_only(self):
        host = self.client_address[0]
        if host not in ("127.0.0.1", "::1"):
            self.send_error(403, "local only")
            return False
        return True

    def do_POST(self):
        if self.path != "/__cms/save":
            self.send_error(404)
            return
        if not self._local_only():
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 512 * 1024:
                raise ValueError("payload too large")
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
            edits = payload.get("edits") or {}
            if not isinstance(edits, dict) or not edits:
                raise ValueError("no edits")
            with build_lock:
                written = write_blocks(edits)
                rebuild(edit=True)
            body = {"ok": True, "written": len(written), "blocks": written}
            code = 200
            print("  saved %d block(s): %s" % (len(written), ", ".join(written)))
        except Exception as e:
            body = {"ok": False, "error": str(e)}
            code = 400
            print("  save failed: %s" % e)
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def end_headers(self):
        # preview must never serve stale HTML after a rebuild
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass          # keep the console for build output only

def main():
    edit = "--no-edit" not in sys.argv
    print("building%s…" % ("" if edit else " (production mode, no editor)"))
    print(" ", rebuild(edit=edit).replace("\n", "\n  "))
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("\n  site        http://127.0.0.1:%d/" % PORT)
    print("  proofread   http://127.0.0.1:%d/proofread.html" % PORT)
    print("  editing     %s" % ("ON — click Edit at the bottom of the page"
                                if edit else "OFF"))
    print("\nCtrl-C to stop.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")

if __name__ == "__main__":
    main()
