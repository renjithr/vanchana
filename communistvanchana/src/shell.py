# -*- coding: utf-8 -*-
"""Shared HTML shell: head, SEO metadata, structured data, nav, footer."""
import json, html, os
from content_ml import SITE, NAV, FOOTER, CREDIT

DOMAIN = SITE["domain"]
# Sangeeth's page; he gathered the documents. Credited on every page.
CREDIT_URL = "https://www.facebook.com/keraleyam"
WIDTH_FALLBACK = 400

# Preview-only inline editor. Set by the CMS server; a normal build never sees
# it, so production HTML contains no editor markup, CSS or script at all.
EDIT = os.environ.get("CMS_EDIT") == "1"

def esc(s):
    return html.escape(s or "", quote=True)

def cite(n, label=None):
    """Inline citation linking a claim to the document that supports it."""
    if not n:
        return ""
    return ('<a class="cite" href="/archive/doc-%s/" title="രേഖ %s കാണുക">%s</a>'
            % (esc(n), esc(n), esc(label or ("രേഖ " + n))))

def picture(slug, imgs, alt, sizes, cls="", loading="lazy", w=800):
    """<picture> with WebP + JPEG fallback and explicit dimensions.

    Width/height are always emitted: without them the page reflows as each scan
    arrives, which Google measures as Cumulative Layout Shift and penalises.
    """
    e = imgs.get(slug.replace("doc-", ""))
    if not e:
        return ""
    # JSON round-trips dict keys to strings
    src = e["sources"]
    d = src.get(str(w)) or src.get(w) or src[str(WIDTH_FALLBACK)]
    return (
        '<picture>'
        '<source type="image/webp" srcset="/assets/scans/%s-400.webp 400w, /assets/scans/%s-800.webp 800w" sizes="%s">'
        '<img src="/assets/scans/%s-%d.jpg" alt="%s" width="%d" height="%d" '
        'loading="%s" decoding="async" class="%s">'
        '</picture>'
    ) % (slug, slug, sizes, slug, w, esc(alt), d["w"], d["h"], loading, cls)

def head(title, desc, path, lang="ml", og_type="article", jsonld=None, extra="",
         alts=None):
    url = DOMAIN + path
    locale = "ml_IN" if lang == "ml" else "en_IN"
    # hreflang: tells search engines these are the same page in two languages,
    # so neither is treated as duplicate content and each is served to the right
    # audience. x-default points at the Malayalam, which is the canonical home.
    for hl, hp in (alts or []):
        extra += '<link rel="alternate" hreflang="%s" href="%s%s">' % (hl, DOMAIN, hp)
    if alts:
        extra += '<link rel="alternate" hreflang="x-default" href="%s/">' % DOMAIN
    blocks = ""
    for block in (jsonld or []):
        blocks += ('<script type="application/ld+json">%s</script>'
                   % json.dumps(block, ensure_ascii=False, separators=(",", ":")))
    return """<!doctype html>
<html lang="%s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta property="og:type" content="%s">
<meta property="og:site_name" content="%s">
<meta property="og:locale" content="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="%s/assets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%s">
<meta name="twitter:description" content="%s">
<meta name="twitter:image" content="%s/assets/og.jpg">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preload" href="/assets/fonts/bricolage-0.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/site.css">
%s%s
</head>
<body>
<a class="skip" href="#main">ഉള്ളടക്കത്തിലേക്ക് പോകുക</a>
""" % (lang, esc(title), esc(desc), url, og_type, esc(SITE["name"]), locale,
       esc(title), esc(desc), url, DOMAIN, esc(title), esc(desc), DOMAIN,
       blocks, extra)

def nav(current, lang="ml"):
    from content_en import NAV_EN, SITE_EN
    items = NAV_EN if lang == "en" else NAV
    brand_a = SITE_EN["brand_a"] if lang == "en" else SITE["brand_a"]
    brand_b = SITE_EN["brand_b"] if lang == "en" else SITE["brand_b"]
    home = "/en/" if lang == "en" else "/"
    # the toggle is a plain link between the two URLs, not a script: it works
    # with JavaScript off and search engines can follow it
    other = ('<a class="langtog" href="/" hreflang="ml" lang="ml">മലയാളം</a>'
             if lang == "en" else
             '<a class="langtog" href="/en/" hreflang="en" lang="en">English</a>')
    links = ""
    for href, label in items:
        cur = ' aria-current="page"' if href == current else ""
        links += '<a href="%s"%s>%s</a>' % (href, cur, esc(label))
    return ("""<header class="mast">
<div class="navbar">
<a class="brand" href="%s">%s<span>&thinsp;/&thinsp;</span>%s</a>
<nav class="navlinks" aria-label="Menu">%s</nav>
%s</div>
</header>
<main id="main">""" % (home, esc(brand_a), esc(brand_b), links, other))

def footer(dark=True, lang="ml"):
    from content_en import NAV_EN, FOOTER_EN, SITE_EN, CREDIT_EN
    items = NAV_EN if lang == "en" else NAV
    note = FOOTER_EN["note"] if lang == "en" else FOOTER["note"]
    credit = CREDIT_EN if lang == "en" else CREDIT
    brand_a = SITE_EN["brand_a"] if lang == "en" else SITE["brand_a"]
    brand_b = SITE_EN["brand_b"] if lang == "en" else SITE["brand_b"]
    links = "".join('<a href="%s">%s</a>' % (h, esc(l)) for h, l in items)
    cls = "slab-ink" if dark else ""
    return """</main>
<footer class="site %s">
<div class="inner">
<div>
<div class="mark">%s<span style="color:var(--amber)">&thinsp;/&thinsp;</span>%s</div>
<p>%s</p>
<p style="font-size:13.5px;opacity:.75">%s</p>
<p style="font-size:13.5px">%s &middot; <a href="%s" rel="noopener" style="color:var(--amber)">Keraleyam</a></p>
</div>
<nav aria-label="Menu">%s</nav>
</div>
</footer>
<script src="/assets/site.js" defer></script>
%s</body>
</html>
""" % (cls, esc(brand_a), esc(brand_b), esc(note), esc(SOURCE_LINE_EN if lang == "en" else SOURCE_LINE_ML),
       esc(credit["footer"]), CREDIT_URL, links, CMS_ASSETS)

SOURCE_LINE_ML = ("രേഖകളുടെ ഉറവിടം: National Archives of India, India Office Records, "
                  "The Collected Works of Mahatma Gandhi.")
SOURCE_LINE_EN = ("Documents from the National Archives of India, the India Office Records, "
                  "and The Collected Works of Mahatma Gandhi.")

CMS_ASSETS = ('<link rel="stylesheet" href="/assets/cms.css">'
              '<script src="/assets/cms.js" defer></script>') if EDIT else ""

def breadcrumb(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             "item": DOMAIN + u} for i, (n, u) in enumerate(items)
        ],
    }

WEBSITE_LD = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": SITE["name"],
    "alternateName": "Communist Vanchana",
    "url": DOMAIN,
    "inLanguage": ["ml", "en"],
    "description": ("ക്വിറ്റ് ഇന്ത്യ സമരകാലത്തെ ഇന്ത്യൻ കമ്മ്യൂണിസ്റ്റ് പാർട്ടിയുടെ "
                    "നിലപാട് — ബ്രിട്ടീഷ് ആഭ്യന്തര വകുപ്പിന്റെ 41 രേഖകളിൽ നിന്ന്."),
}
