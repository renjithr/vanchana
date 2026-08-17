/* Preview-only inline editor for communistvanchana.com.

   Loaded solely by an edit build (CMS_EDIT=1). Clicking any outlined block makes
   it editable; Save posts the changed blocks to the local CMS server, which
   rewrites content/ml.txt and rebuilds the site.

   Text only. Blocks are read back with innerText and sent as plain strings, so
   pasting styled text from elsewhere cannot inject markup into the source. */
(function () {
  'use strict';
  var d = document, editing = false, dirty = {};

  var bar = d.createElement('div');
  bar.className = 'cms-bar';
  bar.innerHTML =
    '<span class="cms-badge">Preview</span>' +
    '<span class="cms-hint" id="cmsHint">Edit mode is off &mdash; the page behaves normally</span>' +
    '<span class="cms-sp"></span>' +
    '<span class="cms-count" id="cmsCount"></span>' +
    '<button id="cmsToggle">Edit</button>' +
    '<button id="cmsSave" class="save" disabled>Save</button>';
  d.body.appendChild(bar);

  var toggle = d.getElementById('cmsToggle'),
      saveBtn = d.getElementById('cmsSave'),
      hint = d.getElementById('cmsHint'),
      counter = d.getElementById('cmsCount');

  function blocks() { return [].slice.call(d.querySelectorAll('[data-cms]')); }

  function count() {
    var n = Object.keys(dirty).length;
    counter.textContent = n ? n + (n === 1 ? ' change' : ' changes') : '';
    saveBtn.disabled = !n;
  }

  function toast(msg, isErr) {
    var t = d.createElement('div');
    t.className = 'cms-toast' + (isErr ? ' err' : '');
    t.textContent = msg;
    d.body.appendChild(t);
    setTimeout(function () { t.remove(); }, isErr ? 6000 : 2600);
  }

  function setEditing(on) {
    editing = on;
    d.documentElement.classList.toggle('cms-on', on);
    toggle.classList.toggle('on', on);
    toggle.textContent = on ? 'Done' : 'Edit';
    hint.innerHTML = on
      ? 'Click any outlined text to edit it, then Save'
      : 'Edit mode is off &mdash; the page behaves normally';
    blocks().forEach(function (el) {
      if (!on) {
        el.removeAttribute('contenteditable');
      }
    });
    // everything must be reachable, so open all chapters while editing
    var all = d.getElementById('expandAll');
    if (on && all && all.textContent === all.dataset.open) all.click();
  }

  toggle.addEventListener('click', function () { setEditing(!editing); });

  /* Capture phase: the story headings sit inside the accordion buttons, so the
     click has to be stopped before site.js sees it and toggles the chapter. */
  d.addEventListener('click', function (e) {
    if (!editing) return;
    var el = e.target.closest && e.target.closest('[data-cms]');
    if (!el) return;
    e.preventDefault();
    e.stopPropagation();
    if (el.getAttribute('contenteditable') === 'true') return;
    el.setAttribute('contenteditable', 'true');
    el.dataset.cmsOrig = el.innerText;
    el.focus();
  }, true);

  d.addEventListener('input', function (e) {
    var el = e.target.closest && e.target.closest('[data-cms]');
    if (!el || !editing) return;
    var now = el.innerText.replace(/\s+/g, ' ').trim();
    var was = (el.dataset.cmsOrig || '').replace(/\s+/g, ' ').trim();
    if (now && now !== was) {
      dirty[el.dataset.cms] = now;
      el.classList.add('dirty');
    } else {
      delete dirty[el.dataset.cms];
      el.classList.remove('dirty');
    }
    count();
  });

  // Escape reverts the block being edited
  d.addEventListener('keydown', function (e) {
    if (!editing) return;
    var el = e.target.closest && e.target.closest('[data-cms]');
    if (!el) return;
    if (e.key === 'Escape') {
      el.innerText = el.dataset.cmsOrig;
      delete dirty[el.dataset.cms];
      el.classList.remove('dirty');
      el.removeAttribute('contenteditable');
      count();
    }
  });

  saveBtn.addEventListener('click', function () {
    var edits = dirty;
    if (!Object.keys(edits).length) return;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving…';
    fetch('/__cms/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ edits: edits })
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok || !res.j.ok) throw new Error(res.j.error || 'save failed');
        toast('Saved ' + res.j.written + ' block' + (res.j.written === 1 ? '' : 's') + ' — reloading');
        setTimeout(function () { location.reload(); }, 700);
      })
      .catch(function (err) {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save';
        toast('Could not save: ' + err.message, true);
      });
  });

  // don't lose work to an accidental navigation
  window.addEventListener('beforeunload', function (e) {
    if (Object.keys(dirty).length) { e.preventDefault(); e.returnValue = ''; }
  });
})();
