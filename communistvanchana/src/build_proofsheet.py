# -*- coding: utf-8 -*-
"""Generate build/proofread.html — an editable sheet for checking the Malayalam.

The point is that a proofreader needs no repo, no Python and no terminal. They open
one page, read every Malayalam string with its context and the English it came from,
type corrections, and click Download. What comes out is a complete content/ml.txt,
which drops straight back into the project.

Work is kept in the browser's localStorage, so closing the tab does not lose it.
"""
import json, os, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mltext, content_ml, ml_labels as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")

# where each string appears, so the proofreader can go and look at it in place
def page_for(path):
    top = path.split(".")[0]
    if top in ("DOC_ML", "DOC_DESC"):
        return "/archive/doc-%s/" % path.split(".", 1)[1]
    if top == "CHAPTERS":
        try:
            return "/#ch-%s" % content_ml.CHAPTERS[int(path.split(".")[1])]["n"]
        except Exception:
            return "/"
    if top == "CONCLUSION":
        return "/#ch-end"
    return "/"

SECTION_TITLE = {
    "SITE": "Site name and wordmark",
    "NAV": "Navigation labels",
    "FOOTER": "Footer (every page)",
    "HOME": "Home page — headline, hook and introduction",
    "CHAPTERS": "The 36 story chapters",
    "CONCLUSION": "Closing section",
    "NOTES": "Small reusable notices",
    "DOC_ML": "Archive — short title for each document",
    "DOC_DESC": "Archive — one-line description for each document",
}

def english_for(path):
    """Context line shown above a block: which chapter it belongs to."""
    try:
        if path.startswith("CHAPTERS."):
            c = content_ml.CHAPTERS[int(path.split(".")[1])]
            field = path.split(".")[2]
            label = {"title": "chapter title", "paras": "body text"}.get(field, field)
            return "Chapter %s — %s" % (c["n"], label)
    except Exception:
        pass
    return ""

def main():
    entries = mltext.parse(open(mltext.MLFILE, encoding="utf-8").read())
    # preserve file order
    order = [ln[1:-1] for ln in open(mltext.MLFILE, encoding="utf-8").read().splitlines()
             if ln.startswith("[") and ln.endswith("]")]
    items = []
    for p in order:
        if p not in entries:
            continue
        items.append({"id": p, "text": entries[p], "en": english_for(p),
                      "page": page_for(p), "group": p.split(".")[0]})

    groups = []
    seen = set()
    for it in items:
        if it["group"] not in seen:
            seen.add(it["group"])
            groups.append(it["group"])

    data = json.dumps(items, ensure_ascii=False)
    gjson = json.dumps([{"k": g, "t": SECTION_TITLE.get(g, g)} for g in groups], ensure_ascii=False)

    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Proofread the Malayalam — communistvanchana.com</title>
<meta name="robots" content="noindex, nofollow">
<link rel="stylesheet" href="/assets/fonts.css">
<style>
:root{--cream:#FFF7EA;--ink:#141019;--amber:#FFA51E;--red:#E23E2C;--blue:#3B2FD9;
--blue-pale:#EDE9FF;--grey:#5C5468;--rule:#E6DFD0;--white:#fff;--teal:#12A4A0;
--ml:'Anek Malayalam','Manjari',sans-serif;--ui:'Archivo',system-ui,sans-serif;
--disp:'Bricolage Grotesque',sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--ui);font-size:15px}
header{position:sticky;top:0;z-index:10;background:var(--ink);color:var(--cream);padding:16px 26px;
display:flex;gap:18px;align-items:center;flex-wrap:wrap;box-shadow:0 6px 20px rgba(0,0,0,.18)}
h1{font-family:var(--disp);font-size:19px;margin:0;letter-spacing:-.02em}
.spacer{flex:1}
button{font-family:var(--ui);font-size:13px;font-weight:600;cursor:pointer;border-radius:999px;
padding:10px 18px;border:1px solid transparent}
.primary{background:var(--amber);color:var(--ink)}
.ghost{background:transparent;color:var(--cream);border-color:rgba(255,255,255,.35)}
.stat{font-family:var(--disp);font-size:13px;color:var(--amber)}
#search{font-family:var(--ui);font-size:13px;padding:9px 14px;border-radius:999px;border:0;min-width:200px}
.wrap{max-width:1100px;margin:0 auto;padding:28px 26px 120px}
.intro{background:var(--blue-pale);border-left:4px solid var(--blue);padding:20px 24px;
border-radius:0 14px 14px 0;margin-bottom:30px;line-height:1.65}
.intro b{display:block;font-family:var(--disp);font-size:17px;margin-bottom:8px}
h2{font-family:var(--disp);font-size:15px;letter-spacing:.1em;text-transform:uppercase;
color:var(--grey);margin:38px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--rule)}
.row{background:var(--white);border:1px solid var(--rule);border-radius:14px;padding:18px 20px;margin-bottom:12px}
.row.changed{border-color:var(--teal);box-shadow:0 0 0 3px rgba(18,164,160,.12)}
.row.hidden{display:none}
.meta{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
.id{font-family:ui-monospace,monospace;font-size:11px;color:var(--grey);background:var(--cream);
padding:3px 9px;border-radius:6px}
.see{font-size:12px;color:var(--blue);text-decoration:none}
.tag{font-size:10.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
color:var(--teal);margin-left:auto}
.en{font-size:13.5px;line-height:1.6;color:var(--grey);font-style:italic;
border-left:3px solid var(--rule);padding-left:12px;margin:0 0 12px}
textarea{width:100%;font-family:var(--ml);font-size:17px;line-height:1.9;color:var(--ink);
background:var(--cream);border:1px solid var(--rule);border-radius:10px;padding:14px 16px;resize:vertical}
textarea:focus{outline:none;border-color:var(--blue);background:#fff}
.orig{font-family:var(--ml);font-size:14px;line-height:1.8;color:var(--grey);margin:10px 0 0;display:none}
.row.changed .orig{display:block}
.orig b{font-family:var(--ui);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--red)}
footer{position:fixed;bottom:0;left:0;right:0;background:var(--ink);color:var(--cream);
padding:14px 26px;display:flex;gap:16px;align-items:center;justify-content:center;font-size:13px}
</style>
</head>
<body>
<header>
<h1>Proofread the Malayalam</h1>
<span class="stat" id="stat"></span>
<span class="spacer"></span>
<input id="search" type="search" placeholder="Search…" aria-label="Search the strings">
<button class="ghost" id="onlyChanged">Show changed only</button>
<button class="primary" id="download">Download ml.txt</button>
</header>
<div class="wrap">
<div class="intro">
<b>What to do</b>
Read each Malayalam block and correct it directly in the box. Everything you type is saved
in this browser as you go, so you can close the tab and come back.
When you are finished, click <b style="display:inline">Download ml.txt</b> and send the
file back — it replaces <code>content/ml.txt</code> in the project, and the site rebuilds from it.
<br><br>
The grey italic lines are the original English a passage was translated from, where there is one.
“See in place” opens the page the text appears on. You cannot break anything here.
</div>
<div id="rows"></div>
</div>
<footer><span id="foot">—</span></footer>
<script>
var ITEMS = __DATA__, GROUPS = __GROUPS__, KEY = 'cv-proof-v1';
var saved = JSON.parse(localStorage.getItem(KEY) || '{}');
var rows = document.getElementById('rows'), out = [];

GROUPS.forEach(function (g) {
  var mine = ITEMS.filter(function (i) { return i.group === g.k; });
  if (!mine.length) return;
  out.push('<h2>' + g.t + '</h2>');
  mine.forEach(function (it) {
    var cur = saved[it.id] !== undefined ? saved[it.id] : it.text;
    var chg = cur !== it.text;
    out.push(
      '<div class="row' + (chg ? ' changed' : '') + '" data-id="' + it.id + '" data-q="' +
      (it.id + ' ' + it.text).toLowerCase().replace(/"/g, '') + '">' +
      '<div class="meta"><span class="id">' + it.id + '</span>' +
      '<a class="see" href="' + it.page + '" target="_blank" rel="noopener">See in place &nearr;</a>' +
      '<span class="tag">' + (chg ? 'edited' : '') + '</span></div>' +
      (it.en ? '<p class="en">' + it.en.replace(/</g, '&lt;') + '</p>' : '') +
      '<textarea rows="1">' + cur.replace(/</g, '&lt;') + '</textarea>' +
      '<p class="orig"><b>Original:</b> ' + it.text.replace(/</g, '&lt;') + '</p>' +
      '</div>');
  });
});
rows.innerHTML = out.join('');

function autosize(t) { t.style.height = 'auto'; t.style.height = (t.scrollHeight + 4) + 'px'; }
[].forEach.call(document.querySelectorAll('textarea'), autosize);

function count() {
  var n = ITEMS.filter(function (i) {
    return saved[i.id] !== undefined && saved[i.id] !== i.text;
  }).length;
  document.getElementById('stat').textContent = n + ' edited of ' + ITEMS.length;
  document.getElementById('foot').textContent = n
    ? n + ' change' + (n === 1 ? '' : 's') + ' saved in this browser — click Download ml.txt when finished'
    : ITEMS.length + ' Malayalam blocks to review';
}
count();

rows.addEventListener('input', function (e) {
  if (e.target.tagName !== 'TEXTAREA') return;
  var row = e.target.closest('.row'), id = row.dataset.id;
  var it = ITEMS.find(function (x) { return x.id === id; });
  saved[id] = e.target.value;
  localStorage.setItem(KEY, JSON.stringify(saved));
  var chg = e.target.value !== it.text;
  row.classList.toggle('changed', chg);
  row.querySelector('.tag').textContent = chg ? 'edited' : '';
  autosize(e.target);
  count();
});

document.getElementById('search').addEventListener('input', function (e) {
  var t = e.target.value.trim().toLowerCase();
  [].forEach.call(document.querySelectorAll('.row'), function (r) {
    r.classList.toggle('hidden', !!t && r.dataset.q.indexOf(t) === -1);
  });
});

var only = false;
document.getElementById('onlyChanged').addEventListener('click', function () {
  only = !only;
  this.textContent = only ? 'Show all' : 'Show changed only';
  [].forEach.call(document.querySelectorAll('.row'), function (r) {
    r.classList.toggle('hidden', only && !r.classList.contains('changed'));
  });
});

document.getElementById('download').addEventListener('click', function () {
  var head = __HEADER__;
  var body = '', group = null;
  ITEMS.forEach(function (it) {
    if (it.group !== group) {
      group = it.group;
      var g = GROUPS.find(function (x) { return x.k === group; });
      body += '\\n# ' + Array(75).join('-') + '\\n# ' + (g ? g.t : group) + '\\n\\n';
    }
    var v = saved[it.id] !== undefined ? saved[it.id] : it.text;
    body += '[' + it.id + ']\\n' + v + '\\n\\n';
  });
  var blob = new Blob([head + body], { type: 'text/plain;charset=utf-8' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'ml.txt';
  document.body.appendChild(a); a.click(); a.remove();
});
</script>
</body>
</html>"""
    page = (page.replace("__DATA__", data)
                .replace("__GROUPS__", gjson)
                .replace("__HEADER__", json.dumps(mltext.HEADER, ensure_ascii=False)))
    os.makedirs(BUILD, exist_ok=True)
    open(os.path.join(BUILD, "proofread.html"), "w", encoding="utf-8").write(page)
    print("proofread.html: %d strings" % len(items))

if __name__ == "__main__":
    main()
