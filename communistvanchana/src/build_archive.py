# -*- coding: utf-8 -*-
"""English archive: index plus one page per document, and final site assets."""
import json, os, re, shutil, datetime
from shell import head, nav, footer, esc, picture, breadcrumb, DOMAIN
from build_site import (ROOT, BUILD, DOCS, IMGS, PEOPLE, BY_NO, TODAY,
                        w, alt_for, parse_sigs, build_home, build_sources)
import ml_labels as L

ORDER = [d["archival_no"] for d in DOCS]

def cat_of(n):
    base = int(re.match(r"\d+", n).group())
    if base == 21: return "Published source"
    if base in (12, 13, 14): return "Provincial report"
    if base in (10, 11, 15, 17, 18, 19): return "Communist Party"
    return "Government"

def en_footer():
    return footer()

# ------------------------------------------------------------------ index

def build_archive_index():
    rows = ""
    for d in DOCS:
        n = d["archival_no"]
        date = d.get("date", "").split("[")[0].strip().rstrip("(").strip() or "n.d."
        frm = re.sub(r"\[.*?\]", "", d.get("from", "")).split(",")[0].strip() or "—"
        q = " ".join([n, d["title"], frm, date, cat_of(n)]).lower()
        rows += (
            '<tr class="fa-row" data-q="%s" data-cat="%s" data-signed="%s">'
            '<td class="fa-no"><a href="/archive/doc-%s/">%s</a></td>'
            '<td class="fa-date">%s</td>'
            '<td class="fa-title"><a href="/archive/doc-%s/">%s</a></td>'
            '<td class="fa-from">%s</td>'
            '<td class="fa-sig">%s</td></tr>'
        ) % (esc(q), esc(cat_of(n)), "y" if parse_sigs(d) else "n",
             esc(n), esc(n), esc(date), esc(n), esc(d["title"]), esc(frm),
             "●" if parse_sigs(d) else "·")

    people = ""
    for name, role, hits in PEOPLE:
        links = "".join('<a href="/archive/doc-%s/">%s</a>' % (esc(h), esc(h)) for h in hits)
        people += ('<div class="prow"><div class="pname">%s<span>%s</span></div>'
                   '<div class="pdocs">%s</div></div>' % (esc(name), esc(role or ""), links))

    signed = sum(1 for d in DOCS if parse_sigs(d))
    body = (
        '<section class="hero hero-violet">'
        '<div class="blob" style="right:-120px;top:-130px;width:440px;height:440px;background:var(--blue-pale2)"></div>'
        '<div class="hero-inner">'
        '<p class="tag" style="background:var(--blue);color:var(--cream)">Reference archive</p>'
        '<h1 style="color:var(--blue-ink)">The archive</h1>'
        '<p class="standfirst" style="color:#3B3357">Forty-one sheets from the Government of India, '
        'Home Department (Political) files on the Communist Party of India, 1940&ndash;1944. '
        'Every sheet transcribed verbatim, with its signatories, annotations and physical '
        'condition recorded, and the original scan beside each transcript.</p>'
        '<div class="facts">'
        '<div class="fact"><b>41</b><span>Documents</span></div>'
        '<div class="fact"><b>1940&ndash;44</b><span>Date range</span></div>'
        '<div class="fact"><b>%d</b><span>Bearing signatures</span></div>'
        '<div class="fact"><b>1</b><span>Sheet missing (18e)</span></div>'
        '</div></div></section>'
        '<div class="controls"><div class="wrap cinner">'
        '<div class="searchbox">'
        '<input id="q" type="search" placeholder="Search titles, names, file references…" '
        'aria-label="Search the archive" autocomplete="off">'
        '</div>'
        '<div class="filters" role="group" aria-label="Filter by category">'
        '<button data-f="all" aria-pressed="true">All</button>'
        '<button data-f="Government" aria-pressed="false">Government</button>'
        '<button data-f="Communist Party" aria-pressed="false">Communist Party</button>'
        '<button data-f="signed" aria-pressed="false">Signed</button>'
        '</div><span class="count" id="count"></span>'
        '</div></div>'
        '<section class="sec"><div class="tablewrap"><table>'
        '<thead><tr><th>No.</th><th>Date</th><th>Document</th><th>From</th><th>Sig.</th></tr></thead>'
        '<tbody id="fa">%s</tbody></table></div>'
        '<p class="empty" id="empty">No document matches that search.</p></section>'
        '<section class="sec"><h2 class="rise">Index of persons</h2>'
        '<p class="lead rise">Everyone named in the transcripts, with the documents they appear in.</p>'
        '<div class="people rise">%s</div></section>'
    ) % (signed, rows, people)

    ld = [breadcrumb([("സംഭവങ്ങൾ", "/"), ("Archive", "/archive/")]), {
        "@context": "https://schema.org", "@type": "Collection",
        "name": "Communist Vanchana Archive",
        "description": "41 Government of India Home Department documents on the Communist Party of India, 1940–1944.",
        "url": DOMAIN + "/archive/", "inLanguage": "en",
        "numberOfItems": len(DOCS),
    }]
    w("archive/index.html",
      head("The Archive — 41 Home Department documents, 1940–1944",
           "Verbatim transcripts and scans of 41 Government of India Home Department "
           "documents on the Communist Party of India, 1940–1944, with signatories and provenance.",
           "/archive/", "en", "website", ld)
      + nav("/archive/") + body + en_footer())

# ------------------------------------------------------------------ one doc

def build_doc(d, i):
    n = d["archival_no"]
    slug = "doc-" + n
    img = IMGS.get(n, {})
    prev_n = ORDER[i - 1] if i > 0 else None
    next_n = ORDER[i + 1] if i < len(ORDER) - 1 else None

    meta = ""
    for k, v in [("Date", d.get("date")), ("From", d.get("from")), ("To", d.get("to")),
                 ("Classification", d.get("classification")), ("File reference", d.get("file_ref")),
                 ("Page", d.get("page")), ("Document type", d.get("doc_type"))]:
        if v and v.lower() not in ("none", "n/a", "none marked"):
            meta += '<div class="mrow"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v))

    sigs = parse_sigs(d)
    if sigs:
        items = "".join('<li><span class="sg-name">%s</span>%s<span class="sg-note">%s</span></li>'
                        % (esc(a), '<span class="sg-role">%s</span>' % esc(b) if b else "", esc(c))
                        for a, b, c in sigs)
        sig_html = '<div class="sigs"><h2>Signatories</h2><ul>%s</ul></div>' % items
    else:
        sig_html = ('<div class="sigs unsigned"><h2>Signatories</h2>'
                    '<p>None — this sheet bears no signature.</p></div>')

    marg = ""
    mg = d.get("marginalia", "")
    if mg and not mg.lower().startswith("none"):
        marg = '<div class="marg"><h2>Marginalia &amp; annotations</h2><p>%s</p></div>' % esc(mg)

    enh = ""
    if "enhanced" in img:
        enh = ('<button class="enh-btn" id="enh" data-src="/assets/scans/%s-enhanced.jpg" '
               'aria-pressed="false">Improve legibility</button>'
               '<p class="enh-note">Contrast-enhanced derivative. The scan shown by default is '
               'the unmodified original, so any reading can be checked honestly.</p>') % slug

    ml_note = ""
    if n in L.DOC_ML:
        ml_note = ('<aside class="mlnote" lang="ml"><span class="mlnote-l">മലയാളത്തിൽ</span>'
                   '<b>%s</b><p>%s</p><a href="/">വാദം വായിക്കുക &rarr;</a></aside>'
                   % (esc(L.DOC_ML[n]), esc(L.DOC_DESC.get(n, ""))))

    nav_lr = '<nav class="docnav">'
    nav_lr += ('<a href="/archive/doc-%s/">&larr; %s</a>' % (esc(prev_n), esc(prev_n))
               if prev_n else '<span></span>')
    nav_lr += '<a href="/archive/">All documents</a>'
    nav_lr += ('<a href="/archive/doc-%s/">%s &rarr;</a>' % (esc(next_n), esc(next_n))
               if next_n else '<span></span>')
    nav_lr += '</nav>'

    body = (
        '<article class="docpage">'
        '<div class="wrap">'
        '<nav class="crumb" aria-label="Breadcrumb"><a href="/">%s</a> / '
        '<a href="/archive/">Archive</a> / <span>%s</span></nav>'
        '<div class="dochead"><div class="crayon">%s</div>'
        '<div><h1 class="doctitle">%s</h1>'
        '<p class="chips"><span class="chip c-cat">%s</span>%s</p></div></div>'
        '<div class="docgrid">'
        '<figure class="docscan">'
        '<a href="/assets/scans/%s-full.jpg" id="zoom">%s</a>'
        '<figcaption>%s</figcaption>%s</figure>'
        '<div class="docmeta"><dl class="meta">%s</dl>%s%s%s</div>'
        '</div>'
        '<section class="transcript-block"><h2>Transcript <span class="verbatim">verbatim</span></h2>'
        '<div class="tscroll"><pre>%s</pre></div></section>'
        '%s</div></article>'
    ) % (esc("സംഭവങ്ങൾ"), esc(n), esc(n), esc(d["title"]), esc(cat_of(n)),
         ('<span class="chip c-secret">%s</span>' % esc(d["classification"]))
         if d.get("classification", "").lower() not in ("none marked", "none", "") and not d.get("classification", "").startswith("[") else "",
         slug,
         picture(slug, IMGS, alt_for(d), "(max-width:900px) 92vw, 520px", loading="eager", w=800),
         esc(d.get("condition", "")), enh, meta, sig_html, marg, ml_note,
         esc(d["transcript"]), nav_lr)

    ld = [breadcrumb([("സംഭവങ്ങൾ", "/"), ("Archive", "/archive/"),
                      ("Document " + n, "/archive/doc-%s/" % n)]), {
        "@context": "https://schema.org", "@type": "ArchiveComponent",
        "name": d["title"], "identifier": "Archival no. " + n,
        "inLanguage": "en", "url": DOMAIN + "/archive/doc-%s/" % n,
        "text": d["transcript"][:600],
        "holdingArchive": {"@type": "ArchiveOrganization", "name": "National Archives of India"},
        "isPartOf": {"@type": "Collection", "name": "Communist Vanchana Archive",
                     "url": DOMAIN + "/archive/"},
        "about": [{"@type": "Thing", "name": "Communist Party of India"},
                  {"@type": "Thing", "name": "Quit India Movement"}],
        "image": DOMAIN + "/assets/scans/%s-800.jpg" % slug,
    }]
    desc = (L.DOC_DESC.get(n) or d.get("condition", ""))[:150]
    title = "Document %s: %s — Archive" % (n, d["title"][:70])
    w("archive/doc-%s/index.html" % n,
      head(title, desc, "/archive/doc-%s/" % n, "en", "article", ld)
      + nav("/archive/") + body + en_footer())

# ------------------------------------------------------------------ assets

def build_doc_json(d):
    """Small payload the home-page panel fetches, so opening a document costs
    ~3KB instead of loading a whole page."""
    n = d["archival_no"]
    img = IMGS.get(n, {})
    meta = [(k, v) for k, v in
            [("Date", d.get("date")), ("From", d.get("from")), ("To", d.get("to")),
             ("Classification", d.get("classification")), ("File reference", d.get("file_ref")),
             ("Page", d.get("page"))]
            if v and v.lower() not in ("none", "n/a", "none marked")]
    payload = {
        "n": n, "title": d["title"], "ml": L.DOC_ML.get(n, ""),
        "mlDesc": L.DOC_DESC.get(n, ""),
        "meta": meta,
        "sigs": parse_sigs(d),
        "condition": d.get("condition", ""),
        "marginalia": ("" if (d.get("marginalia","").lower().startswith("none"))
                       else d.get("marginalia", "")),
        "transcript": d["transcript"],
        "alt": alt_for(d),
        "img": {"w": img.get("sources", {}).get("800", {}).get("w", 0),
                "h": img.get("sources", {}).get("800", {}).get("h", 0)},
        "url": "/archive/doc-%s/" % n,
    }
    w("d/%s.json" % n, json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

def build_icon():
    """apple-touch-icon: the wordmark's V on the ink ground."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (180, 180), "#141019")
    dr = ImageDraw.Draw(im)
    dr.polygon([(38, 48), (62, 48), (90, 106), (118, 48), (142, 48),
                (100, 134), (80, 134)], fill="#FFA51E")
    im.save(os.path.join(BUILD, "assets/icon-180.png"))

def build_og():
    """Share card. Latin text only.

    Pillow here has no raqm/HarfBuzz, so it cannot shape Malayalam -- conjuncts
    and chillu would come out as broken glyph soup. Rather than ship mangled
    Malayalam to every social preview, the card carries a real scan and Latin
    type, which is more striking in a feed anyway.
    """
    from PIL import Image, ImageDraw, ImageFont
    T = os.path.join(ROOT, "src/ttf")
    def f(name, size):
        return ImageFont.truetype(os.path.join(T, name), size)

    im = Image.new("RGB", (1200, 630), "#FFA51E")
    dr = ImageDraw.Draw(im)
    dr.ellipse((820, -200, 1420, 400), fill="#FFB84D")

    # a genuine document, tilted into the corner
    scan_p = os.path.join(ROOT, "assets/scans/doc-5-800.jpg")
    if os.path.exists(scan_p):
        s = Image.open(scan_p).convert("RGB")
        s.thumbnail((430, 430))
        s = s.rotate(-6, expand=True, fillcolor="#FFA51E", resample=Image.BICUBIC)
        im.paste(s, (742, 96))

    dr.rectangle((0, 470, 1200, 630), fill="#141019")
    dr.text((68, 120), "Communist", font=f("bricolage.ttf", 96), fill="#141019")
    dr.text((68, 218), "Vanchana", font=f("bricolage.ttf", 96), fill="#141019")
    dr.text((72, 344), "The betrayal of 1942, in the Government's own files",
            font=f("archivo.ttf", 27), fill="#3A2A12")
    dr.text((68, 512), "communistvanchana.com", font=f("bricolage.ttf", 40), fill="#FFA51E")
    dr.text((70, 566), "41 Home Department documents  ·  1940–1944  ·  scans + full transcripts",
            font=f("archivo.ttf", 22), fill="#CFC8D8")
    im.save(os.path.join(BUILD, "assets/og.jpg"), quality=86, optimize=True)

FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="14" fill="#141019"/>'
           '<path d="M14 46V18h8.5l9.5 18 9.5-18H50v28h-7V31l-8 15h-6l-8-15v15z" fill="#FFA51E"/>'
           '</svg>')

def finalize():
    # assets
    dst = os.path.join(BUILD, "assets")
    os.makedirs(dst, exist_ok=True)
    for item in ("fonts", "scans"):
        s = os.path.join(ROOT, "assets", item)
        t = os.path.join(dst, item)
        if os.path.isdir(t):
            shutil.rmtree(t)
        shutil.copytree(s, t)
    shutil.copy(os.path.join(ROOT, "assets/fonts.css"), dst)
    # one stylesheet request instead of two
    base = open(os.path.join(ROOT, "src/site.css"), encoding="utf-8").read()
    comp = open(os.path.join(ROOT, "src/components.css"), encoding="utf-8").read()
    open(os.path.join(dst, "site.css"), "w", encoding="utf-8").write(base + "\n" + comp)
    shutil.copy(os.path.join(ROOT, "src/site.js"), dst)
    # preview editor assets: copied only for an edit build, and any stale copy
    # from a previous edit build is removed so production never carries them
    from shell import EDIT
    for f in ("cms.css", "cms.js"):
        target = os.path.join(dst, f)
        if EDIT:
            shutil.copy(os.path.join(ROOT, "src", f), target)
        elif os.path.exists(target):
            os.remove(target)
    open(os.path.join(dst, "favicon.svg"), "w").write(FAVICON)
    build_og()
    build_icon()

    # Cloudflare Pages serves /404.html automatically for unmatched routes
    w("404.html", head("താൾ കണ്ടെത്തിയില്ല — " + "കമ്മ്യൂണിസ്റ്റ് വഞ്ചന",
                       "ഈ വിലാസത്തിൽ ഒരു താളില്ല.", "/404.html", "ml", "website", [])
      + nav("") +
      '<section class="hero hero-amber"><div class="hero-inner">'
      '<p class="tag"><span class="dot"></span>404</p>'
      '<h1>ഈ താൾ ഇല്ല</h1>'
      '<p class="standfirst" style="color:var(--on-amber)">'
      'വിലാസം തെറ്റിയതാകാം. 41 രേഖകളും ആർക്കൈവിൽ ലഭ്യമാണ്.</p>'
      '<div class="btnrow" style="margin-top:32px">'
      '<a class="btn btn-ink" href="/">വാദത്തിലേക്ക്</a>'
      '<a class="btn btn-out" href="/archive/">Browse the archive</a>'
      '</div></div></section>' + en_footer())

    urls = ["/", "/en/", "/aadharam/", "/archive/"]
    urls += ["/archive/doc-%s/" % d["archival_no"] for d in DOCS]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">'.replace("sitemap.org", "sitemaps.org")]
    for u in urls:
        pri = "1.0" if u == "/" else ("0.8" if u.count("/") <= 2 else "0.6")
        sm.append("<url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
                  % (DOMAIN, u, TODAY, pri))
    sm.append("</urlset>")
    w("sitemap.xml", "\n".join(sm))

    w("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % DOMAIN)

    w("_headers", """/assets/fonts/*
  Cache-Control: public, max-age=31536000, immutable
  Access-Control-Allow-Origin: *
/assets/scans/*
  Cache-Control: public, max-age=31536000, immutable
/assets/*.css
  Cache-Control: public, max-age=604800
/assets/*.js
  Cache-Control: public, max-age=604800
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: geolocation=(), microphone=(), camera=()
""")
    w("_redirects", "/index.html / 301\n"
                "/kaalarekha/* / 301\n"
                "/rekhakal/* /archive/ 301\n")

    # Host config for both targets, so one build can deploy either way.
    # Cloudflare reads _headers/_redirects and ignores CNAME/.nojekyll;
    # GitHub Pages reads CNAME/.nojekyll and ignores _headers/_redirects.
    w("CNAME", DOMAIN.split("//")[-1] + "\n")
    w(".nojekyll", "")          # stop Jekyll eating paths that begin with _

    # GitHub Pages cannot redirect at all, so the stub page has to do it
    # itself. On Cloudflare the 301 in _redirects wins and this is never hit.
    for path, dest in (("kaalarekha/index.html", "/"),
                       ("rekhakal/index.html", "/archive/")):
        w(path, redirect_stub(dest))

def redirect_stub(dest):
    """Stand-in for a 301 on hosts that have no redirect support.

    Canonical for crawlers, meta refresh for browsers, and a plain link for
    anyone both of those fail. A real 301 is better; this is what is available
    when the host offers nothing.
    """
    return ("<!doctype html>\n<html lang=\"ml\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<link rel=\"canonical\" href=\"" + DOMAIN + dest + "\">\n"
            "<meta http-equiv=\"refresh\" content=\"0; url=" + dest + "\">\n"
            "<title>Moved</title>\n</head>\n<body>\n"
            "<p>This page has moved. <a href=\"" + dest + "\">Continue</a>.</p>\n"
            "</body>\n</html>\n")

def main():
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(BUILD)
    build_home('ml'); build_home('en'); build_sources()
    build_archive_index()
    for i, d in enumerate(DOCS):
        build_doc(d, i)
        build_doc_json(d)
    finalize()
    import build_proofsheet; build_proofsheet.main()

    pages = sum(len([f for f in fs if f.endswith(".html")]) for _, _, fs in os.walk(BUILD))
    size = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(BUILD) for f in fs)
    print("pages: %d" % pages)
    print("total: %.1f MB" % (size / 1e6))

if __name__ == "__main__":
    main()
