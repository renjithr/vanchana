/* communistvanchana.com */
(function () {
  'use strict';
  var d = document;
  d.documentElement.classList.add('js');

  /* ---- chapter accordion ---------------------------------------------
     One chapter open at a time. The markup ships with every body hidden and
     aria-expanded="false", so with JavaScript off the buttons are inert but
     nothing is lost -- the same text is on the archive pages and in the
     document panel's fallback links.                                      */
  var wrap = d.getElementById('chapters');
  if (wrap) {
    var chapters = [].slice.call(wrap.querySelectorAll('.ch'));
    var expandBtn = d.getElementById('expandAll');
    var allOpen = false;

    function bodyOf(ch) { return ch.querySelector('.ch-body'); }
    function btnOf(ch) { return ch.querySelector('.ch-btn'); }

    function setOpen(ch, open, keepScroll) {
      var body = bodyOf(ch), btn = btnOf(ch);
      if (open) {
        ch.setAttribute('data-open', '');
        body.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
        if (location.hash !== '#' + ch.id) history.replaceState(null, '', '#' + ch.id);
      } else {
        // closing a chapter above the viewport would yank the page upward,
        // so measure first and correct the scroll afterwards
        var before = keepScroll ? ch.getBoundingClientRect().top : 0;
        ch.removeAttribute('data-open');
        body.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
        if (keepScroll) {
          var after = ch.getBoundingClientRect().top;
          window.scrollBy(0, after - before);
        }
      }
    }

    function openOnly(ch) {
      chapters.forEach(function (c) {
        if (c !== ch && c.hasAttribute('data-open')) setOpen(c, false, true);
      });
      setOpen(ch, true);
    }

    chapters.forEach(function (ch) {
      btnOf(ch).addEventListener('click', function () {
        var isOpen = ch.hasAttribute('data-open');
        if (isOpen) {
          setOpen(ch, false);
        } else {
          openOnly(ch);
          // bring the heading just under the sticky nav
          var top = ch.getBoundingClientRect().top + window.pageYOffset - 88;
          window.scrollTo({ top: top, behavior: reduced() ? 'auto' : 'smooth' });
        }
      });
    });

    // "next chapter" closes this one and opens the following one
    wrap.addEventListener('click', function (e) {
      var b = e.target.closest ? e.target.closest('.ch-next') : null;
      if (!b) return;
      var next = chapters[parseInt(b.dataset.next, 10)];
      if (!next) return;
      openOnly(next);
      window.scrollTo({
        top: next.getBoundingClientRect().top + window.pageYOffset - 88,
        behavior: reduced() ? 'auto' : 'smooth'
      });
    });

    if (expandBtn) {
      expandBtn.addEventListener('click', function () {
        allOpen = !allOpen;
        chapters.forEach(function (c) { setOpen(c, allOpen); });
        expandBtn.textContent = allOpen ? expandBtn.dataset.close : expandBtn.dataset.open;
      });
    }

    /* ---- search over the story --------------------------------------
       The index is built from the DOM, not from data- attributes: the chapter
       text is already in the page, and duplicating ~70KB of it into markup
       would be paid by every visitor whether or not they ever search.      */
    var chq = d.getElementById('chq'),
        chclear = d.getElementById('chclear'),
        chCount = d.getElementById('chCount'),
        chEmpty = d.getElementById('chEmpty'),
        // the closing card is searchable but is not one of the 36 chapters
        storyTotal = chapters.filter(function (c) {
          return !c.classList.contains('ch-end');
        }).length,
        searchTimer = null;

    chapters.forEach(function (ch) {
      var t = ch.querySelector('.ch-t');
      ch._title = t.textContent;
      ch._body = ch.querySelector('.ch-inner').textContent.replace(/\s+/g, ' ').trim();
      ch._hay = (ch._title + ' ' + ch._body).toLowerCase();
      ch._t = t;
    });

    function escRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

    /* Malayalam is agglutinative: ഹർത്താൽ, ഹർത്താലുകൾ and ഹർത്താലിനെതിരെ are
       three different strings, so a plain substring search finds one chapter
       and misses the rest. Trim a trailing chillu, anusvara or vowel sign off
       the query to get a stem, then match on that. Capped at two characters
       and never below three, so the stem cannot get short enough to match
       everything.                                                          */
    var TAIL = /[ംാ-്ൗൺ-ൿ]$/, HAS_ML = /[ഀ-ൿ]/;
    function stemOf(q) {
      if (!HAS_ML.test(q)) return q;   // English needs no stemming
      var s = q;
      for (var i = 0; i < 2 && s.length > 3 && TAIL.test(s); i++) s = s.slice(0, -1);
      return s;
    }
    // highlight the whole inflected word, not just the stem that matched
    function wordRe(stem) {
      return new RegExp(escRe(stem) + '[ഀ-ൿ]*', 'gi');
    }
    function escHtml(s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    function markUp(text, re) {
      var out = '', last = 0, m;
      re.lastIndex = 0;
      while ((m = re.exec(text)) !== null) {
        if (!m[0]) { re.lastIndex++; continue; }
        out += escHtml(text.slice(last, m.index)) + '<mark>' + escHtml(m[0]) + '</mark>';
        last = m.index + m[0].length;
      }
      return out ? out + escHtml(text.slice(last)) : null;
    }

    function snipFor(ch, term, re) {
      var i = ch._body.toLowerCase().indexOf(term);
      if (i < 0) return null;
      var from = Math.max(0, i - 60), to = Math.min(ch._body.length, i + term.length + 90);
      // trim to whitespace so we do not cut a word (or a Malayalam cluster) in half
      if (from > 0) { var s = ch._body.indexOf(' ', from); if (s > -1 && s < i) from = s + 1; }
      if (to < ch._body.length) { var e = ch._body.lastIndexOf(' ', to); if (e > i) to = e; }
      var frag = (from > 0 ? '… ' : '') + ch._body.slice(from, to) + (to < ch._body.length ? ' …' : '');
      return markUp(frag, re) || escHtml(frag);
    }

    function clearSearch() {
      chapters.forEach(function (ch) {
        ch.hidden = false;
        ch._t.textContent = ch._title;
        if (ch._snip) { ch._snip.hidden = true; ch._snip.innerHTML = ''; }
      });
      chCount.textContent = storyTotal + ' ' + chCount.dataset.unit;
      chEmpty.hidden = true;
      chclear.hidden = true;
    }

    function runSearch() {
      var raw = chq.value.trim(), term = stemOf(raw).toLowerCase();
      chclear.hidden = !raw;
      if (!term) { clearSearch(); return; }

      var re = wordRe(stemOf(raw)), hits = 0;
      chapters.forEach(function (ch) {
        var match = ch._hay.indexOf(term) > -1;
        ch.hidden = !match;
        if (!match) {
          ch._t.textContent = ch._title;
          if (ch._snip) { ch._snip.hidden = true; ch._snip.innerHTML = ''; }
          return;
        }
        hits++;
        var titled = markUp(ch._title, re);
        if (titled) ch._t.innerHTML = titled;
        else ch._t.textContent = ch._title;

        // if the hit is only in the body, show where, so a collapsed card
        // still explains why it is in the results
        var snip = ch._title.toLowerCase().indexOf(term) > -1 ? null : snipFor(ch, term, re);
        if (snip) {
          if (!ch._snip) {
            ch._snip = d.createElement('p');
            ch._snip.className = 'ch-snip';
            ch.insertBefore(ch._snip, ch.querySelector('.ch-body'));
          }
          ch._snip.innerHTML = snip;
          ch._snip.hidden = false;
        } else if (ch._snip) {
          ch._snip.hidden = true;
          ch._snip.innerHTML = '';
        }
      });
      chCount.textContent = hits + ' ' + chCount.dataset.results;
      chEmpty.hidden = hits > 0;
    }

    if (chq) {
      chq.addEventListener('input', function () {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(runSearch, 120);
      });
      chq.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { chq.value = ''; clearSearch(); chq.blur(); }
      });
      chclear.addEventListener('click', function () {
        chq.value = ''; clearSearch(); chq.focus();
      });
      d.addEventListener('keydown', function (e) {
        var t = e.target.tagName;
        if (t === 'INPUT' || t === 'TEXTAREA') return;
        if (e.key === '/' || ((e.metaKey || e.ctrlKey) && e.key === 'k')) {
          e.preventDefault(); chq.focus(); chq.select();
        }
      });
    }

    // a link like /#ch-14 should land with that chapter open
    (function fromHash() {
      var m = location.hash && d.getElementById(location.hash.slice(1));
      if (m && m.classList.contains('ch')) {
        openOnly(m);
        setTimeout(function () {
          window.scrollTo(0, m.getBoundingClientRect().top + window.pageYOffset - 88);
        }, 0);
      }
    })();
  }

  function reduced() {
    return matchMedia('(prefers-reduced-motion:reduce)').matches;
  }

  /* ---- document panel -------------------------------------------------
     Chips are real links to /archive/doc-N/. We only intercept the click when
     fetch is available; anything that fails falls through to the real page,
     so the record is always reachable.                                    */
  var dp = d.getElementById('dp');
  if (dp && window.fetch) {
    var scroll = d.getElementById('dp-scroll'),
        cache = {}, lastFocus = null;

    function esc(s) {
      return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function render(doc) {
      d.getElementById('dp-no').textContent = 'രേഖ ' + doc.n;
      d.getElementById('dp-title').textContent = doc.ml || doc.title;
      d.getElementById('dp-full').href = doc.url;

      var meta = doc.meta.map(function (kv) {
        return '<div><dt>' + esc(kv[0]) + '</dt><dd>' + esc(kv[1]) + '</dd></div>';
      }).join('');
      d.getElementById('dp-meta').innerHTML =
        (doc.mlDesc ? '<p class="dp-ml">' + esc(doc.mlDesc) + '</p>' : '') +
        '<dl class="dp-meta">' + meta + '</dl>';

      var slug = 'doc-' + doc.n;
      d.getElementById('dp-img').innerHTML =
        '<picture>' +
        '<source type="image/webp" srcset="/assets/scans/' + slug + '-800.webp">' +
        '<img src="/assets/scans/' + slug + '-800.jpg" alt="' + esc(doc.alt) + '"' +
        (doc.img.w ? ' width="' + doc.img.w + '" height="' + doc.img.h + '"' : '') + '>' +
        '</picture>' +
        (doc.condition ? '<p class="dp-cap">' + esc(doc.condition) + '</p>' : '');

      var extra = '';
      if (doc.sigs && doc.sigs.length) {
        extra += '<p class="dp-sec">Signatories</p>';
        doc.sigs.forEach(function (s) {
          extra += '<div class="dp-sig"><b>' + esc(s[0]) + '</b>' +
                   (s[1] ? '<span>' + esc(s[1]) + '</span>' : '') +
                   (s[2] ? '<span>' + esc(s[2]) + '</span>' : '') + '</div>';
        });
      }
      if (doc.marginalia) {
        extra += '<p class="dp-sec">Marginalia</p><p class="dp-marg">' +
                 esc(doc.marginalia) + '</p>';
      }
      extra += '<p class="dp-sec">Transcript &mdash; verbatim</p>';
      d.getElementById('dp-extra').innerHTML = extra;
      d.getElementById('dp-tr').textContent = doc.transcript;
      scroll.scrollTop = 0;
    }

    function open(n, trigger) {
      lastFocus = trigger || null;
      dp.hidden = false;
      // force a reflow so the transition has a start value, then add the class
      // synchronously. requestAnimationFrame is throttled or skipped in some
      // embedded/background contexts, and if it never ran the sheet would stay
      // off-screen behind a dim scrim with scrolling locked.
      void dp.offsetWidth;
      dp.classList.add('on');
      d.body.style.overflow = 'hidden';
      dp.querySelector('.dp-close').focus();
      settle();

      if (cache[n]) { render(cache[n]); return; }
      d.getElementById('dp-extra').innerHTML = '<p class="dp-loading">രേഖ എടുക്കുന്നു…</p>';
      d.getElementById('dp-tr').textContent = '';
      d.getElementById('dp-img').innerHTML = '';
      d.getElementById('dp-meta').innerHTML = '';
      fetch('/d/' + n + '.json')
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function (doc) { cache[n] = doc; render(doc); })
        .catch(function () { location.href = '/archive/doc-' + n + '/'; });
    }

    /* If the slide-in transition has not actually moved the sheet by the time it
       should have finished, drop the transition and snap it open. A panel that
       never arrives would leave the reader looking at a dim screen with the page
       locked behind it -- worse than no animation at all. */
    function settle() {
      var sheet = dp.querySelector('.dp-sheet'), scrim = dp.querySelector('.dp-scrim');
      setTimeout(function () {
        if (!dp.classList.contains('on')) return;
        if (sheet.getBoundingClientRect().left >= window.innerWidth - 4) {
          sheet.style.transition = 'none';
          sheet.style.transform = 'none';
          scrim.style.transition = 'none';
          scrim.style.opacity = '1';
        }
      }, 400);
    }

    function close() {
      var sheet = dp.querySelector('.dp-sheet'), scrim = dp.querySelector('.dp-scrim');
      sheet.style.transition = sheet.style.transform = '';
      scrim.style.transition = scrim.style.opacity = '';
      dp.classList.remove('on');
      d.body.style.overflow = '';
      setTimeout(function () { dp.hidden = true; }, reduced() ? 0 : 280);
      if (lastFocus) lastFocus.focus();
    }

    d.addEventListener('click', function (e) {
      var chip = e.target.closest ? e.target.closest('.dchip') : null;
      if (chip && chip.dataset.doc) {
        e.preventDefault();
        open(chip.dataset.doc, chip);
        return;
      }
      if (e.target.closest && e.target.closest('[data-close]')) close();
    });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !dp.hidden) close();
    });
  }

  /* ---- archive search ---------------------------------------------- */
  var q = d.getElementById('q');
  if (q) {
    var rows = [].slice.call(d.querySelectorAll('.fa-row')),
        count = d.getElementById('count'),
        empty = d.getElementById('empty'),
        btns = [].slice.call(d.querySelectorAll('.filters button')),
        filter = 'all', timer = null;

    function apply() {
      var term = q.value.trim().toLowerCase(), n = 0;
      rows.forEach(function (r) {
        var ok = (!term || r.dataset.q.indexOf(term) > -1) &&
                 (filter === 'all' ||
                  (filter === 'signed' ? r.dataset.signed === 'y' : r.dataset.cat === filter));
        r.style.display = ok ? '' : 'none';
        if (ok) n++;
      });
      count.textContent = n + ' of ' + rows.length;
      empty.classList.toggle('on', n === 0);
    }
    q.addEventListener('input', function () {
      clearTimeout(timer); timer = setTimeout(apply, 120);
    });
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        filter = b.dataset.f;
        btns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
        apply();
      });
    });
    d.addEventListener('keydown', function (e) {
      if (e.target.tagName === 'INPUT') return;
      if (e.key === '/') { e.preventDefault(); q.focus(); q.select(); }
    });
    apply();
  }

  /* ---- contrast toggle on a document page ---------------------------- */
  var enh = d.getElementById('enh');
  if (enh) {
    var fig = d.querySelector('.docscan img'),
        pic = d.querySelector('.docscan picture'),
        original = fig ? fig.currentSrc || fig.src : null,
        srcEls = pic ? [].slice.call(pic.querySelectorAll('source')) : [],
        srcSets = srcEls.map(function (s) { return s.srcset; });
    enh.addEventListener('click', function () {
      var on = enh.getAttribute('aria-pressed') === 'true';
      if (on) {
        srcEls.forEach(function (s, i) { s.srcset = srcSets[i]; });
        fig.src = original;
        enh.setAttribute('aria-pressed', 'false');
        enh.textContent = 'Improve legibility';
      } else {
        srcEls.forEach(function (s) { s.srcset = enh.dataset.src; });
        fig.src = enh.dataset.src;
        enh.setAttribute('aria-pressed', 'true');
        enh.textContent = 'Show the original scan';
      }
    });
  }

  /* ---- lightbox on a document page ---------------------------------- */
  var zoom = d.getElementById('zoom');
  if (zoom) {
    zoom.addEventListener('click', function (e) {
      e.preventDefault();
      var lb = d.createElement('div');
      lb.className = 'lb';
      lb.innerHTML = '<img src="' + zoom.getAttribute('href') + '" alt="">' +
                     '<p class="lb-hint">Click anywhere, or press Escape, to close</p>';
      lb.addEventListener('click', shut);
      d.body.appendChild(lb);
      void lb.offsetWidth;
      lb.classList.add('on');
      function shut() {
        lb.remove();
        d.removeEventListener('keydown', onEsc);
        zoom.focus();
      }
      function onEsc(ev) { if (ev.key === 'Escape') shut(); }
      d.addEventListener('keydown', onEsc);
    });
  }
})();
