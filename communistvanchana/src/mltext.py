# -*- coding: utf-8 -*-
"""Keep every Malayalam string in one plain text file that a non-programmer can edit.

The prose still *lives* in content_ml.py / ml_labels.py as defaults, but any string
containing Malayalam characters is exposed in content/ml.txt under a stable path.
On build, ml.txt wins. So:

  - a proofreader edits content/ml.txt (or the web sheet, which exports the same file)
  - nobody has to touch Python, or worry about quotes and commas breaking a build
  - if ml.txt is missing or only half-filled, the defaults still render

Detection is automatic: anything in the Malayalam Unicode block (U+0D00-U+0D7F) is
picked up, so new copy never needs registering by hand.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MLFILE = os.path.join(ROOT, "content/ml.txt")
MAL = re.compile(r"[ഀ-ൿ]")

def is_ml(s):
    return isinstance(s, str) and bool(MAL.search(s))

def walk(obj, path=""):
    """Yield (path, string) for every Malayalam string, depth-first."""
    if isinstance(obj, str):
        if is_ml(obj):
            yield path, obj
    elif isinstance(obj, dict):
        for k in obj:
            if isinstance(k, str) and k.startswith("_"):
                continue
            for p, s in walk(obj[k], "%s.%s" % (path, k) if path else str(k)):
                yield p, s
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            for p, s in walk(v, "%s.%d" % (path, i)):
                yield p, s

def _step(cur, part):
    # dict keys may themselves be numeric strings ("1", "18c"), so only treat a
    # numeric path segment as an index when the container is actually a sequence
    if isinstance(cur, (list, tuple)) and part.isdigit():
        return cur[int(part)]
    return cur[part]

def get_at(root, path):
    cur = root
    for part in path.split("."):
        cur = _step(cur, part)
    return cur

def set_at(root, path, value):
    parts = path.split(".")
    cur = root
    for part in parts[:-1]:
        cur = _step(cur, part)
    last = parts[-1]
    key = int(last) if (isinstance(cur, (list, tuple)) and last.isdigit()) else last
    if isinstance(cur, tuple):        # paras are tuples; caller converts them to lists
        raise TypeError("cannot assign into a tuple at %s" % path)
    cur[key] = value

# ---------------------------------------------------------------- dump

HEADER = """# ============================================================================
#  communistvanchana.com  —  MALAYALAM TEXT
#
#  HOW TO EDIT
#    Change only the text BELOW each [id] line. Leave the [id] lines alone.
#    A block runs until the next [id] line, so paragraphs can span lines.
#    Lines starting with # are comments and are ignored.
#    Save the file, then run:  ./preview.sh
#
#  You cannot break the build by editing text here. Quotes, commas and
#  apostrophes are all safe. If a block is deleted, the original wording
#  is used instead.
# ============================================================================

"""

SECTION_NOTES = {
    "SITE": "Site name and wordmark",
    "NAV": "Navigation labels",
    "FOOTER": "Footer, appears on every page",
    "HOME": "Home page — headline, hook and introduction",
    "CHAPTERS": "The 36 story chapters",
    "CONCLUSION": "Closing section",
    "NOTES": "Small reusable notices",
    "DOC_ML": "Short title shown for each document",
    "DOC_DESC": "One-line description shown for each document",
}

def dump(namespaces):
    """Write content/ml.txt from the current defaults."""
    os.makedirs(os.path.dirname(MLFILE), exist_ok=True)
    out, seen_top = [HEADER], set()
    for ns in namespaces:
        for path, s in walk(ns):
            top = path.split(".")[0]
            if top not in seen_top:
                seen_top.add(top)
                note = SECTION_NOTES.get(top, "")
                out.append("\n# %s\n# %s\n" % ("-" * 74, note or top))
            out.append("[%s]\n%s\n\n" % (path, s))
    open(MLFILE, "w", encoding="utf-8").write("".join(out))
    return sum(1 for ns in namespaces for _ in walk(ns))

# ---------------------------------------------------------------- load

def parse(text):
    entries, key, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^\[([^\]]+)\]\s*$", line)
        if m:
            if key:
                entries[key] = "\n".join(buf).strip()
            key, buf = m.group(1), []
        elif key is not None:
            if line.startswith("#"):
                continue
            buf.append(line)
    if key:
        entries[key] = "\n".join(buf).strip()
    return {k: v for k, v in entries.items() if v}

def override(namespaces):
    """Apply content/ml.txt over the defaults. Returns (applied, skipped)."""
    if not os.path.exists(MLFILE):
        return 0, 0
    entries = parse(open(MLFILE, encoding="utf-8").read())
    applied = skipped = 0
    for path, value in entries.items():
        for ns in namespaces:
            try:
                if get_at(ns, path) == value:
                    applied += 1          # already identical; nothing to do
                    break
                set_at(ns, path, value)
                applied += 1
                break
            except (KeyError, IndexError, TypeError, ValueError):
                continue
        else:
            skipped += 1
    return applied, skipped

def index(namespaces):
    """value -> [ml.txt paths], so a rendered string can be mapped back to the
    block(s) that produced it. Used only by the preview CMS.

    A value can legitimately live at more than one path -- the site name and the
    home headline are the same words -- so every match is recorded and the editor
    updates all of them. Silently picking one would let an edit to the headline
    rewrite the site name instead."""
    idx = {}
    for ns in namespaces:
        for path, s in walk(ns):
            idx.setdefault(s, [])
            if path not in idx[s]:
                idx[s].append(path)
    return idx
