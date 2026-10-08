# -*- coding: utf-8 -*-
"""Build communistvanchana.com — Malayalam story + English archive, static HTML."""
import json, os, re, shutil, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shell import (head, nav, footer, esc, picture, breadcrumb, WEBSITE_LD,
                   DOMAIN, EDIT, CREDIT_URL)
import content_en
import content_ml, ml_labels as L, mltext, entext

# content/ml.txt is the proofreader's copy and wins over the defaults in code
_applied, _skipped = mltext.override([content_ml.NS,
                                      {"DOC_ML": L.DOC_ML, "DOC_DESC": L.DOC_DESC}])
if _skipped:
    print("  note: %d entries in content/ml.txt matched nothing and were ignored" % _skipped)
# rewrite ml.txt from the values now in memory: edits already applied above are
# preserved, and any copy newly added in code appears for the proofreader
mltext.dump([content_ml.NS, {"DOC_ML": L.DOC_ML, "DOC_DESC": L.DOC_DESC}])

# same treatment for the English: content/en.txt wins, then is rewritten so new
# copy shows up for whoever edits it
_ea, _es = entext.override([content_en.NS_EN])
if _es:
    print("  note: %d entries in content/en.txt matched nothing and were ignored" % _es)
entext.dump([content_en.NS_EN])

from content_ml import SITE, HOME, CHAPTERS, CONCLUSION, CONTEXT_NOTE, NAV

# Preview CMS: map a rendered string back to its block in content/ml.txt, so the
# inline editor knows which entry a click is editing. Empty on a normal build.
CMS_INDEX = mltext.index([content_ml.NS,
                          {"DOC_ML": L.DOC_ML, "DOC_DESC": L.DOC_DESC}]) if EDIT else {}
# English blocks live in content/en.txt and are indexed the same way
EN_INDEX = entext.index([content_en.NS_EN]) if EDIT else {}
CMS_INDEX.update({k: v for k, v in EN_INDEX.items() if k not in CMS_INDEX})

UI = {
 "ml": {"chapters": "അധ്യായങ്ങൾ", "results": "ഫലം",
        "expand": "എല്ലാം തുറക്കുക", "collapse": "എല്ലാം അടയ്ക്കുക",
        "next": "അടുത്ത അധ്യായം ↓", "docs": "ആധാരമായ രേഖ",
        "search": "സംഭവങ്ങളിൽ തിരയുക — പേര്, സ്ഥലം, വാക്ക്…",
        "clear": "തിരച്ചിൽ മായ്ക്കുക",
        "empty": "ഈ വാക്ക് കണ്ടെത്തിയില്ല.", "menu": "മെനു"},
 "en": content_en.UI_EN,
}

# a chapter that exists in one language must exist in the other
_ml_ns = [c["n"] for c in content_ml.CHAPTERS]
_en_ns = list(content_en.CHAPTERS_EN)
assert _ml_ns == _en_ns, ("chapter numbers differ between languages: ml=%s en=%s"
                          % (set(_ml_ns) ^ set(_en_ns), ""))

def cms(value):
    """data-cms attribute naming the editable block, or nothing outside preview."""
    if not EDIT:
        return ""
    paths = CMS_INDEX.get(value)
    return ' data-cms="%s"' % ",".join(paths) if paths else ""

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
DOCS = json.load(open(os.path.join(ROOT, "data/docs.json")))
IMGS = json.load(open(os.path.join(ROOT, "data/images.json")))
PEOPLE = json.load(open(os.path.join(ROOT, "data/people.json")))
BY_NO = {d["archival_no"]: d for d in DOCS}
TODAY = datetime.date.today().isoformat()

def w(path, content):
    p = os.path.join(BUILD, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(content)

def alt_for(d):
    return ("Scan of document %s: %s, %s"
            % (d["archival_no"], d["title"], d.get("date", "").split("[")[0].strip()))

def parse_sigs(d):
    raw = (d.get("signatories") or "").strip()
    if not raw or raw.lower().startswith("none"):
        return []
    out = []
    for s in raw.split(";;"):
        parts = [p.strip() for p in s.split("|")]
        while len(parts) < 3:
            parts.append("")
        out.append(parts[:3])
    return out

# ============================================================ home

def doc_chips(nums, lang):
    """Chips that open the scan + transcript in the slide-in panel.

    The href stays a real archive URL, so with JavaScript off (or if the fetch
    fails) the chip is an ordinary working link rather than a dead button.
    """
    if not nums:
        return ""
    chips = ""
    for n in nums:
        d = BY_NO.get(n)
        if not d:
            continue
        label = d["title"] if lang == "en" else L.DOC_ML.get(n, d["title"])
        chips += ('<a class="dchip" href="/archive/doc-%s/" data-doc="%s">'
                  '<span class="dchip-n">%s</span><span class="dchip-t">%s</span></a>'
                  % (esc(n), esc(n), esc(n), esc(label[:52])))
    return ('<div class="ch-docs"><span class="ch-docs-l">%s</span>'
            '<div class="ch-chips">%s</div></div>' % (esc(UI[lang]["docs"]), chips))

def chapter(c, idx, lang):
    """One chapter card. Structure and citations come from the Malayalam entry;
    only the words switch language."""
    if lang == "en":
        src = content_en.CHAPTERS_EN[c["n"]]
        note_text = content_en.CONTEXT_NOTE_EN
    else:
        src = c
        note_text = CONTEXT_NOTE
    body = "".join('<p%s>%s</p>' % (cms(p), esc(p)) for p in src["paras"])
    note = (('<p class="ch-context"%s>%s</p>' % (cms(note_text), esc(note_text)))
            if c.get("context") else "")
    kind = "ch-ctx" if c.get("context") else "ch-doc"
    return (
        '<article class="ch %s" id="ch-%s">'
        '<h2 class="ch-head">'
        '<button class="ch-btn" aria-expanded="false" aria-controls="chb-%s" id="chh-%s">'
        '<span class="ch-n">%s</span>'
        '<span class="ch-t"%s>%s</span>'
        '<span class="ch-mark" aria-hidden="true"></span>'
        '</button></h2>'
        '<div class="ch-body" id="chb-%s" role="region" aria-labelledby="chh-%s" hidden>'
        '<div class="ch-inner">%s%s%s'
        '<div class="ch-foot">'
        '<button class="ch-next" data-next="%s">%s</button>'
        '</div></div></div></article>'
    ) % (kind, esc(c["n"]), esc(c["n"]), esc(c["n"]), esc(c["n"]),
         cms(src["title"]), esc(src["title"]),
         esc(c["n"]), esc(c["n"]), note, body, doc_chips(c.get("docs", []), lang),
         esc(str(idx + 1)), esc(UI[lang]["next"]))

def build_home(lang="ml"):
    en = lang == "en"
    H = content_en.HOME_EN if en else HOME
    C = content_en.CONCLUSION_EN if en else CONCLUSION
    u = UI[lang]
    path = "/en/" if en else "/"
    out = "en/index.html" if en else "index.html"

    chapters = "".join(chapter(c, i, lang) for i, c in enumerate(CHAPTERS))
    concl = (
        '<article class="ch ch-end" id="ch-end">'
        '<h2 class="ch-head">'
        '<button class="ch-btn" aria-expanded="false" aria-controls="chb-end" id="chh-end">'
        '<span class="ch-n">&#9679;</span><span class="ch-t"%s>%s</span>'
        '<span class="ch-mark" aria-hidden="true"></span></button></h2>'
        '<div class="ch-body" id="chb-end" role="region" aria-labelledby="chh-end" hidden>'
        '<div class="ch-inner">%s%s</div></div></article>'
    ) % (cms(C["title"]), esc(C["title"]),
         "".join('<p%s>%s</p>' % (cms(p), esc(p)) for p in C["paras"]),
         doc_chips(CONCLUSION.get("docs", []), lang))

    body = (
        '<section class="hero hero-amber">'
        '<div class="blob" style="right:-120px;top:-90px;width:520px;height:520px;background:var(--amber-lt)"></div>'
        '<div class="blob" style="right:60px;bottom:-190px;width:340px;height:340px;background:var(--red);opacity:.9"></div>'
        '<div class="hero-inner">'
        '<p class="tag"><span class="dot"></span><span%s>%s</span></p>'
        '<h1%s>%s</h1>'
        '<p class="hook"%s>%s</p>'
        '<p class="standfirst" style="color:var(--on-amber)"%s>%s</p>'
        '<p class="howto"%s>%s</p>'
        '</div></section>'
        '<section class="sec story">'
        '<div class="storybar">'
        '<div class="chsearch">'
        '<svg class="chsearch-i" viewBox="0 0 20 20" aria-hidden="true" focusable="false">'
        '<circle cx="9" cy="9" r="6.2" fill="none" stroke="currentColor" stroke-width="2"/>'
        '<path d="M13.6 13.6 18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
        '</svg>'
        '<input id="chq" type="search" autocomplete="off" placeholder="%s" aria-label="%s">'
        '<button id="chclear" class="chsearch-x" type="button" aria-label="%s" hidden>&times;</button>'
        '</div>'
        '<span class="storybar-c" id="chCount" data-unit="%s" data-results="%s">%d %s</span>'
        '<button id="expandAll" class="storybar-b" data-open="%s" data-close="%s">%s</button>'
        '</div>'
        '<div class="chapters" id="chapters">%s%s</div>'
        '<p class="ch-empty" id="chEmpty" hidden>%s</p>'
        '</section>'
        '%s'
        '<section class="sec"><div class="cards-wide">'
        '<a class="linkcard" style="background:var(--ink)" href="/archive/">'
        '<span class="t" style="color:var(--cream)">The Archive<br>'
        '<span style="font-size:.6em">41 documents</span></span>'
        '<span class="b"><span style="color:var(--grey-pale)">Scans and full transcripts, in English</span>'
        '<span class="arrow" style="color:var(--amber)">&rarr;</span></span></a>'
        '<a class="linkcard" style="background:var(--blue-pale);border:2px solid var(--blue)" href="/aadharam/">'
        '<span class="t" style="color:var(--blue-ink)">%s</span>'
        '<span class="b"><span style="color:var(--blue-mid)">%s</span>'
        '<span class="arrow" style="color:var(--blue)">&rarr;</span></span></a>'
        '</div></section>'
    ) % (cms(H["tag"]), esc(H["tag"]),
         cms(H["h1"]), esc(H["h1"]),
         cms(H["hook"]), esc(H["hook"]),
         cms(H["standfirst"]), esc(H["standfirst"]),
         cms(H["howto"]), esc(H["howto"]),
         esc(u["search"]), esc(u["search"]), esc(u["clear"]),
         esc(u["chapters"]), esc(u["results"]), len(CHAPTERS), esc(u["chapters"]),
         esc(u["expand"]), esc(u["collapse"]), esc(u["expand"]),
         chapters, concl, esc(u["empty"]),
         credit_section(lang),
         "Sources" if en else "ആധാരം",
         ("Where the documents come from, and what they do not prove" if en
          else "രേഖകൾ എവിടെ നിന്ന്, എന്ത് തെളിയിക്കുന്നില്ല"))

    alts = [("ml", "/"), ("en", "/en/")]
    ld = [WEBSITE_LD, breadcrumb([(H["h1"], path)]), {
        "@context": "https://schema.org", "@type": "Article",
        "headline": H["h1"], "description": H["meta"], "inLanguage": lang,
        "datePublished": TODAY, "dateModified": TODAY,
        "articleSection": [(content_en.CHAPTERS_EN[c["n"]]["title"] if en else c["title"])
                           for c in CHAPTERS],
        "isBasedOn": [DOMAIN + "/archive/doc-%s/" % n
                      for c in CHAPTERS for n in c.get("docs", [])][:20],
        "about": [{"@type": "Thing", "name": "Quit India Movement"},
                  {"@type": "Thing", "name": "Communist Party of India"}],
        "contributor": {"@type": "Person", "name": "Sangeeth", "url": CREDIT_URL},
    }]
    w(out, head(H["title"], H["meta"], path, lang, "article", ld, alts=alts)
      + nav(path, lang) + body + doc_panel() + footer(lang=lang))

def credit_section(lang, tone="ink"):
    """Thanks to Sangeeth, who gathered the documents and gave them freely.

    Ink on the home page; amber on the sources page, which already ends on an
    ink slab right above the (ink) footer.
    """
    C = content_en.CREDIT_EN if lang == "en" else content_ml.CREDIT
    ink = tone == "ink"
    tag_style = ' style="background:var(--amber);color:var(--ink)"' if ink else ""
    p_style = "" if ink else ' style="color:var(--on-amber)"'
    paras = "".join('<p%s%s>%s</p>' % (p_style, cms(p), esc(p)) for p in C["paras"])
    return (
        '<section class="slab %s" id="credit">'
        '<div class="hero-inner">'
        '<p class="tag"%s><span%s>%s</span></p>'
        '<h2 style="margin-top:24px;max-width:24ch;color:var(--%s)"%s>%s</h2>'
        '<div class="prose" style="margin-top:28px;max-width:62ch">%s</div>'
        '<div class="btnrow" style="margin-top:32px">'
        '<a class="btn %s" href="%s" rel="noopener"><span%s>%s</span> &rarr;</a>'
        '</div></div></section>'
    ) % ("slab-ink" if ink else "slab-amber",
         tag_style, cms(C["tag"]), esc(C["tag"]),
         "cream" if ink else "ink", cms(C["title"]), esc(C["title"]),
         paras,
         "btn-amber" if ink else "btn-ink", CREDIT_URL, cms(C["link"]), esc(C["link"]))

def doc_panel():
    """Empty shell the slide-in panel fills from /d/<no>.json."""
    return (
        '<div class="dp" id="dp" hidden>'
        '<div class="dp-scrim" data-close></div>'
        '<aside class="dp-sheet" role="dialog" aria-modal="true" aria-labelledby="dp-title">'
        '<header class="dp-top">'
        '<span class="dp-no" id="dp-no"></span>'
        '<button class="dp-close" data-close aria-label="അടയ്ക്കുക">&times;</button>'
        '</header>'
        '<div class="dp-scroll" id="dp-scroll">'
        '<h2 id="dp-title"></h2>'
        '<div id="dp-meta"></div>'
        '<div id="dp-img"></div>'
        '<div id="dp-extra"></div>'
        '<pre id="dp-tr"></pre>'
        '<a class="dp-full" id="dp-full" href="/archive/">പൂർണ്ണ താളിലേക്ക് &rarr;</a>'
        '</div></aside></div>'
    )

# ============================================================ sources

def build_sources():
    prov = [
        ("National Archives of India", "വാട്ടർമാർക്ക് ഉള്ള പകർപ്പുകൾ", "13, 14, 12, 10"),
        ("India Office Records, London", "രജിസ്ട്രി മുദ്രകൾ: POL 4737 1942", "1"),
        ("The Collected Works of Mahatma Gandhi", "അച്ചടിച്ച പുസ്തകത്തിന്റെ താൾ", "21"),
    ]
    rows = "".join('<div class="prow"><div class="pname">%s<span>%s</span></div>'
                   '<div class="pdocs">%s</div></div>'
                   % (esc(a), esc(b),
                      " ".join('<a href="/archive/doc-%s/">%s</a>' % (x.strip(), x.strip())
                               for x in c.split(",")))
                   for a, b, c in prov)

    ctx = [c for c in CHAPTERS if c.get("context")]
    ctx_list = "".join("<li>അധ്യായം %s — %s</li>" % (esc(c["n"]), esc(c["title"])) for c in ctx)

    body = (
        '<section class="hero hero-violet">'
        '<div class="blob" style="right:-120px;top:-130px;width:440px;height:440px;background:var(--blue-pale2)"></div>'
        '<div class="hero-inner">'
        '<p class="tag" style="background:var(--blue);color:var(--cream)">Reference</p>'
        '<h1 style="color:var(--blue-ink)">ആധാരം</h1>'
        '<p class="standfirst" style="color:#3B3357">'
        'ഈ സൈറ്റ് ഒരു പക്ഷം പിടിക്കുന്നു. അതുകൊണ്ടുതന്നെ ഉറവിടങ്ങളുടെ കാര്യത്തിൽ '
        'കൂടുതൽ കർശനമായിരിക്കേണ്ടതുണ്ട്.</p>'
        '</div></section>'
        '<section class="sec"><div class="cards-wide">'
        '<div class="card" style="background:var(--red);color:var(--cream)">'
        '<h3 style="color:var(--cream)">തർക്കമില്ലാത്തത്</h3>'
        '<p style="color:var(--red-tint)">ഈ 41 രേഖകൾ യഥാർത്ഥമാണ്. അവയുടെ സ്കാൻ ഇവിടെയുണ്ട്. '
        'പകർപ്പുകൾ അക്ഷരാർത്ഥത്തിലുള്ളതാണ് — അക്ഷരത്തെറ്റുകൾ പോലും തിരുത്തിയിട്ടില്ല.</p></div>'
        '<div class="card"><h3>തർക്കമുള്ളത്</h3>'
        '<p>ഈ നിലപാട് ഒറ്റുകൊടുക്കലായിരുന്നോ എന്നത്. രേഖകൾ എന്ത് പറയുന്നു എന്നത് '
        'വസ്തുതയാണ്; അതിന്റെ അർത്ഥം എന്താണ് എന്നത് വ്യാഖ്യാനമാണ്.</p></div>'
        '<div class="card" style="background:var(--ink);color:var(--cream)">'
        '<h3 style="color:var(--amber)">വായിക്കേണ്ട വിധം</h3>'
        '<p style="color:var(--grey-pale)">സ്കാനുകളുടെ റെസല്യൂഷൻ കുറവാണ്; ചില താളുകൾ '
        'മങ്ങിയതാണ്. വായിക്കാൻ ഉറപ്പില്ലാത്ത വാക്കുകൾ ആർക്കൈവിൽ അടയാളപ്പെടുത്തിയിട്ടുണ്ട്.</p></div>'
        '</div></section>'
        '<section class="sec"><h2>രേഖകൾ എവിടെ നിന്ന്</h2>'
        '<p class="lead">ഇവ ഒരൊറ്റ ശേഖരത്തിൽ നിന്നുള്ളതല്ല.</p>'
        '<div class="people">%s</div></section>'
        '%s'
        '<section class="slab slab-ink"><div class="hero-inner">'
        '<h2>ഞങ്ങളുടെ രേഖകളിൽ ഇല്ലാത്തത്</h2>'
        '<p class="lead lead-dark">താഴെപ്പറയുന്ന അധ്യായങ്ങൾ പൊതുചരിത്രത്തെ ആശ്രയിക്കുന്നു. '
        'അവയ്ക്ക് ആധാരമായ രേഖ ഞങ്ങളുടെ ശേഖരത്തിലില്ല, അത് ഓരോ അധ്യായത്തിലും '
        'അടയാളപ്പെടുത്തിയിട്ടുമുണ്ട്.</p>'
        '<ul class="notlist">%s'
        '<li>1942 ജൂലൈ 22: നിരോധനം ഔദ്യോഗികമായി നീക്കിയ തീയതി — ഞങ്ങളുടെ രേഖ (16) '
        'ജൂലൈ 13-ലെ മന്ത്രിസഭാ തീരുമാനം മാത്രമാണ് കാണിക്കുന്നത്</li></ul>'
        '<p class="lead lead-dark" style="margin-top:26px">ഒരു രേഖ തെറ്റായി '
        'വായിച്ചിട്ടുണ്ടെങ്കിൽ, അത് തിരുത്തേണ്ടതുണ്ട്. സ്കാൻ ഓരോ താളിലും '
        'ഉള്ളതുകൊണ്ട് ആർക്കും പരിശോധിക്കാം.</p>'
        '</div></section>'
    ) % (rows, credit_section("ml", "amber"), ctx_list)

    ld = [breadcrumb([("സംഭവങ്ങൾ", "/"), ("ആധാരം", "/aadharam/")])]
    w("aadharam/index.html",
      head("ആധാരം — രേഖകൾ എവിടെ നിന്ന്",
           "41 രേഖകളുടെ ഉറവിടം, പകർത്തിയെഴുത്തിന്റെ രീതി, ഞങ്ങളുടെ ശേഖരത്തിൽ ഇല്ലാത്തത്.",
           "/aadharam/", "ml", "article", ld)
      + nav("/aadharam/") + body + footer())
