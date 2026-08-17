"""Generate responsive derivatives of the 41 scans.

Emits WebP plus JPEG fallback at 400w and 800w, a full-size original for the lightbox,
and a contrast-enhanced variant used by the "improve legibility" toggle on faded sheets.

Records intrinsic width/height for every file so the templates can set width/height
attributes -- without them the page reflows as scans load, which is a Core Web Vitals
(CLS) penalty and therefore a ranking penalty.
"""
import json, os, subprocess
from PIL import Image

ROOT = "/Users/apple/Commie/communistvanchana"
SCRATCH = ("/private/tmp/claude-501/-Users-apple-Commie/"
           "e3fbc782-6b45-478d-9333-3cf53a55777d/scratchpad/work")
OUT = os.path.join(ROOT, "assets/scans")
os.makedirs(OUT, exist_ok=True)

docs = json.load(open(os.path.join(ROOT, "data/docs.json")))
manifest = {m["id"]: m for m in json.load(open(os.path.join(SCRATCH, "manifest.json")))}

WIDTHS = [400, 800]
index = {}

for d in docs:
    slug = "doc-" + d["archival_no"]
    src = manifest[d["id"]]["src"]
    im = Image.open(src).convert("RGB")
    entry = {"slug": slug, "id": d["id"], "sources": {}}

    for w in WIDTHS:
        # never upscale: the originals are Facebook-compressed and already small
        tw = min(w, im.width)
        r = im.resize((tw, round(im.height * tw / im.width)), Image.LANCZOS) if tw != im.width else im
        jp = os.path.join(OUT, "%s-%d.jpg" % (slug, w))
        wp = os.path.join(OUT, "%s-%d.webp" % (slug, w))
        r.save(jp, quality=72, optimize=True, progressive=True)
        r.save(wp, format="WEBP", quality=70, method=6)
        entry["sources"][w] = {"w": r.width, "h": r.height}

    full = os.path.join(OUT, "%s-full.jpg" % slug)
    im.save(full, quality=84, optimize=True, progressive=True)
    entry["full"] = {"w": im.width, "h": im.height}

    enh_src = os.path.join(SCRATCH, "v3", d["id"] + ".jpg")
    if os.path.exists(enh_src):
        e = Image.open(enh_src).convert("RGB")
        if e.width > 1100:
            e = e.resize((1100, round(e.height * 1100 / e.width)), Image.LANCZOS)
        e.save(os.path.join(OUT, "%s-enhanced.jpg" % slug), quality=78, optimize=True)
        entry["enhanced"] = {"w": e.width, "h": e.height}

    index[d["archival_no"]] = entry

json.dump(index, open(os.path.join(ROOT, "data/images.json"), "w"), indent=1)

files = os.listdir(OUT)
total = sum(os.path.getsize(os.path.join(OUT, f)) for f in files)
print("scan derivatives: %d files, %.1f MB" % (len(files), total / 1e6))
print("webp: %d  jpeg: %d  enhanced: %d"
      % (sum(f.endswith(".webp") for f in files),
         sum(f.endswith(".jpg") and "enhanced" not in f for f in files),
         sum("enhanced" in f for f in files)))
