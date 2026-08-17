"""Download Google Fonts woff2 files for self-hosting and rewrite the CSS to local paths.

Self-hosting matters here for three reasons: it removes a render-blocking third-party
request (Core Web Vitals feed into ranking), it avoids sending visitor IPs to Google,
and it means the site keeps working if fonts.googleapis.com is blocked.

Google's own CSS already splits each family into unicode-range subsets, so we keep that
splitting rather than re-subsetting ourselves -- important for Malayalam, where naive
subsetting breaks conjunct clusters.
"""
import os, re, urllib.request

ROOT = "/Users/apple/Commie/communistvanchana"
FONTDIR = os.path.join(ROOT, "assets/fonts")
os.makedirs(FONTDIR, exist_ok=True)

# Modern UA is required or Google serves ttf instead of woff2
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

FAMILIES = [
    # Latin display + body, taken from the mockups
    ("bricolage", "Bricolage+Grotesque:opsz,wght@12..96,400..800"),
    ("archivo",   "Archivo:wght@400;500;600;700"),
    # Malayalam display + body. The mockup fonts carry no Malayalam glyphs at all,
    # so the story pages need their own pair.
    ("anek",      "Anek+Malayalam:wght@400..800"),
    ("manjari",   "Manjari:wght@400;700"),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read()

all_css = []
seen = {}
for slug, spec in FAMILIES:
    css = fetch("https://fonts.googleapis.com/css2?family=%s&display=swap" % spec).decode()
    urls = re.findall(r"url\((https://[^)]+\.woff2)\)", css)
    for u in urls:
        if u in seen:
            continue
        name = "%s-%d.woff2" % (slug, len([k for k in seen.values() if k.startswith(slug)]))
        with open(os.path.join(FONTDIR, name), "wb") as f:
            f.write(fetch(u))
        seen[u] = name
    for u, name in seen.items():
        css = css.replace(u, "/assets/fonts/" + name)
    all_css.append("/* %s */\n%s" % (slug, css.strip()))

out = "\n\n".join(all_css)
with open(os.path.join(ROOT, "assets/fonts.css"), "w") as f:
    f.write(out + "\n")

total = sum(os.path.getsize(os.path.join(FONTDIR, n)) for n in os.listdir(FONTDIR))
print("font files: %d" % len(os.listdir(FONTDIR)))
print("total woff2: %.0f KB" % (total / 1024))
for fam in ("Bricolage", "Archivo", "Anek", "Manjari"):
    print("  %-12s %d faces" % (fam, out.count("font-family: '%s" % fam)))
