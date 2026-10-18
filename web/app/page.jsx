'use client';
import { useEffect } from 'react';

export default function Home() {
  useEffect(() => {
    if (window.__tlInit) return undefined;
    window.__tlInit = true;
(function(){
  "use strict";
  var YEAR_MIN = 1770, YEAR_MAX = 2025;

  /* cover art — fade in if present, keep the dark room if not */
  var cov = document.getElementById("coverImg");
  if (cov) {
    cov.addEventListener("load", function(){ cov.classList.add("on"); });
    cov.addEventListener("error", function(){ cov.style.display = "none"; });
    if (cov.complete && cov.naturalWidth) cov.classList.add("on");
  }

    /* ================= live results — nothing hand-authored ================= */
  var LIVE = {};
  var mainEl = document.querySelector('main');

/* ================= dom ================= */
  var track    = document.getElementById('railTrack');
  var fill     = document.getElementById('railFill');
  var lens     = document.getElementById('lens');
  var lensYear = document.getElementById('lensYear');
  var yearOut  = document.getElementById('yearReadout');
  var editionEl= document.getElementById('editionLabel');
  var pill     = document.getElementById('statusPill');
  var pillText = document.getElementById('statusText');
  var deck     = document.getElementById('deck');
  var stage    = document.getElementById('stage');
  var stageCapKind = document.getElementById('stageCapKind');
  var stageCapText = document.getElementById('stageCapText');
  var entryName= document.getElementById('entryName');
  var entryDef = document.getElementById('entryDef');
  var titleWord= document.getElementById('titleWord');
  var titleSub = document.getElementById('titleSub');
  var specimen = document.getElementById('specimen');
  var specFrame= document.getElementById('specFrame');
  var specImg  = document.getElementById('specImg');
  var specCap  = document.getElementById('specCap');
  var artStrip = document.getElementById('artStrip');
  if (specFrame) specFrame.addEventListener('click', function(){ specFrame.classList.toggle('zoomed'); });
  var urlForm  = document.getElementById('urlForm');
  var urlInput = document.getElementById('urlInput');
  var urlBar   = document.getElementById('urlBar');
  var barMiss  = document.getElementById('barMiss');

  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ================= state ================= */
  var STOPS = [], stopsPos = [], panels = [], stageItems = [], stopEls = [];
  var pos = 0, target = 0, vel = 0;
  var dragging = false;
  var tweening = false, twFrom = 0, twTo = 0, twStart = 0, twDur = 0;
  var lastT = performance.now();
  var lastYearShown = -1, lastStopIdx = -1;

  function clamp(v, a, b){ return v < a ? a : v > b ? b : v; }
  function smooth(t){ return t * t * (3 - 2 * t); }
  function easeOut(t){ return 1 - Math.pow(1 - t, 3); }

  /* ================= build rail ticks (once) ================= */
  var MAJORS = [1770, 1800, 1850, 1900, 1950, 2000];
  for (var y = 1770; y <= 2020; y += 10) {
    var t = document.createElement('span');
    var major = MAJORS.indexOf(y) !== -1;
    t.className = 'tick' + (major ? ' major' : '');
    t.style.left = ((y - YEAR_MIN) / (YEAR_MAX - YEAR_MIN) * 100) + '%';
    track.insertBefore(t, lens);
    if (major) {
      var tl = document.createElement('span');
      tl.className = 'tick-label' + ((y === 1770 || y === 2000) ? '' : ' hide-sm');
      tl.style.left = t.style.left;
      tl.textContent = y;
      track.insertBefore(tl, lens);
    }
  }

  /* ================= topic loading ================= */
  function loadTopic(key, scroll){
    var T = LIVE[key]; if (!T) return;
    if (mainEl) mainEl.classList.remove('idle');
    barMiss.classList.remove('show');
    urlInput.value = T.wikiPath;

    entryName.innerHTML = T.word + '.<span class="def" id="entryDef">' + T.def + '</span>';
    if (titleSub) titleSub.textContent = '— the lens, applied to ' + T.word.toLowerCase() + '.';

    STOPS = T.stops;
    stopsPos = STOPS.map(function(s){ return (s.year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN); });

    /* rebuild stop buttons */
    stopEls.forEach(function(el){ el.remove(); });
    stopEls = STOPS.map(function(s, i){
      var el = document.createElement('button');
      el.type = 'button';
      el.className = 'stop' + (s.cls === 'settled' ? ' settled' : '');
      el.style.left = (stopsPos[i] * 100) + '%';
      el.setAttribute('aria-label', 'Jump to ' + s.year + ' — ' + s.label);
      el.innerHTML = '<span class="slabel">' + s.label + '</span><i></i>';
      el.addEventListener('click', function(){ goTo(i); });
      track.insertBefore(el, lens);
      return el;
    });

    /* rebuild stage items (keep frame marks + cap) */
    stageItems.forEach(function(n){ n.remove(); });
    stageItems = STOPS.map(function(s){
      var el;
      if (s.img) {
        el = document.createElement('img');
        el.className = 'stage-item' + (s.img.indexOf('scan') !== -1 || s.img.indexOf('record') !== -1 ? ' scan' : '');
        el.src = s.img; el.alt = s.alt || '';
        el.addEventListener('error', function(){
          el.dataset.broken = '1'; el.style.opacity = 0; el.style.display = 'none';
          if (stageItems.every(function(i){ return i.dataset.broken; })) stage.style.display = 'none';
        });
        if (el.complete && el.naturalWidth === 0) { el.dataset.broken = '1'; }
      } else {
        el = document.createElement('div');
        el.className = 'stage-item plate-item';
        el.innerHTML = '<div class="ptitle">' + (s.plate && s.plate.title || '') + '</div>' + (s.plate && s.plate.sub || '') + '</div>';
      }
      stage.insertBefore(el, stage.querySelector('.cap'));
      return el;
    });
    if (stageItems.length && stageItems.every(function(i){ return i.dataset.broken; })) stage.style.display = 'none';
    else stage.style.display = '';

    /* rebuild panels */
    deck.innerHTML = '';
    panels = STOPS.map(function(s){
      var p = document.createElement('article');
      p.className = 'panel';
      p.innerHTML = s.html;
      deck.appendChild(p);
      return p;
    });

    /* specimen — the matched page under glass */
    var scanImg = T.scan || null;
    if (!scanImg) STOPS.forEach(function(s){ if (!scanImg && s.img && /scan|record/.test(s.img)) scanImg = s.img; });
    if (scanImg) {
      specImg.src = scanImg;
      specCap.textContent = T.scanCap || 'original scan — the historical page under the lens';
      specimen.style.display = '';
    } else {
      specimen.style.display = 'none';
    }
    specFrame.classList.remove('zoomed');
    if (artStrip) artStrip.innerHTML = '';

    lastStopIdx = -1;
    var s0 = T.start || 0;
    pos = stopsPos[s0]; target = pos; vel = 0; tweening = false;
    if (scroll) {
      document.querySelector('.exhibit-head').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
    }
  }

  /* ================= url routing — every lookup hits the real pipeline ================= */
  function topicFrom(raw){
    var s = (raw || '').trim();
    if (!s) return null;
    s = s.replace(/^https?:\/\//, '').replace(/^(www\.)?timelens\.to\/?/i, '').replace(/\/+$/, '');
    var m = s.match(/wiki\/(.+)/i);
    var slug = (m ? m[1] : s.split('/').pop()).replace(/_/g, ' ').replace(/%20/g, ' ');
    try { slug = decodeURIComponent(slug); } catch(e) {}
    slug = slug.replace(/\(.*?\)/g, '').trim();
    return slug || null;
  }
  var barBusy = document.getElementById('barBusy');
  function liveTopic(d){
    var yr = d.page.editionYear || 1823;
    var ed = (d.page.edition ? d.page.edition + ' edition' : 'historical edition');
    var diverged = !d.exhibit || d.exhibit.verdict === 'diverged';
    var thenHead = diverged
      ? 'The retriever surfaced the wrong page — honest failure, kept visible.'
      : 'What the page says.';
    var thenHtml = '<span class="plate-no">i.</span><h3>' + thenHead + '</h3>'
      + '<blockquote class="quote">\u201c' + (d.exhibit && d.exhibit.quote || d.thenText.slice(0,160).replace(/"/g,'')) + '\u201d</blockquote>'
      + (d.exhibit && d.exhibit.then_line ? '<p>' + d.exhibit.then_line + '</p>' : '')
      + '<div class="chips"><span class="chip">rerank score <b>' + (d.match.rerankScore != null ? d.match.rerankScore.toFixed(2) : '—') + '</b></span>'
      + '<span class="chip">source <b>' + d.page.sourceId.split(':')[0] + '</b></span>'
      + (diverged ? '<span class="chip hot"><b>no confident match — nearest page shown</b></span>' : '') + '</div>'
      + '<p class="smallprint">live retrieval — quote shown as returned by Super VL against the page text; the scan below is the ground truth</p>';
    var nowTitle = (d.wiki && d.wiki.title) || 'Wikipedia';
    var nowHtml = '<span class="plate-no">ii.</span><h3>' + (d.exhibit && d.exhibit.verdict === 'diverged' ? 'Diverged.' : d.exhibit && d.exhibit.verdict === 'superseded' ? 'Superseded.' : d.exhibit && d.exhibit.verdict === 'open' ? 'Still open.' : 'Today.') + '</h3>'
      + '<blockquote class="quote">\u201c' + ((d.wiki && d.wiki.excerpt || '').slice(0,180).replace(/["\u201c\u201d]/g,'')) + '\u2026\u201d</blockquote>'
      + (d.exhibit && d.exhibit.now_line ? '<p>' + d.exhibit.now_line + '</p>' : '')
      + (d.exhibit && d.exhibit.note ? '<div class="chips"><span class="chip hot"><b>' + d.exhibit.note + '</b></span></div>' : '')
      + '<p class="smallprint">' + nowTitle + ' · ' + (d.wiki && d.wiki.url || 'shared index') + '</p>';
    return {
      word: (d.topic || 'Topic'), def: diverged ? 'no match in the archive — nearest page shown' : 'retrieved live from the archive',
      titleSub: 'live — embedded, reranked, and read by Nemotron.',
      wikiPath: 'wikipedia.org/wiki/' + (d.wiki ? d.wiki.title.replace(/ /g,'_') : d.topic),
      scan: '/scans/' + d.page.id + '.jpg',
      scanCap: 'original scan · ' + d.page.sourceId + ' · Britannica, ' + ed + ' · the exact page LanceDB + Rerank VL returned',
      start: 0,
      stops: [
        { year: yr, label: 'then', status: 'Live match — ' + ed, cls: 'record',
          edition: 'Britannica, ' + ed,
          capKind: 'AI engraving', cap: 'as the old page understood it',
          plate: { title: d.page.headword || d.topic, sub: ed + ' · rendered live' },
          html: thenHtml },
        { year: 2025, label: 'now', status: 'Now — ' + nowTitle, cls: 'settled',
          edition: 'Wikipedia, live revision',
          capKind: 'AI photograph', cap: 'as we understand it now',
          plate: { title: nowTitle, sub: 'wikipedia · live revision' },
          html: nowHtml }
      ]
    };
  }
  function fetchArt(d){
    var shots = (d.art || []).filter(function(s){
      return s && s.prompt && (s.role === 'then' || s.role === 'now');
    }).slice(0, 2);
    if (!shots.length) return Promise.resolve();
    var artRow = document.createElement('div');
    artRow.className = 'ls run'; artRow.dataset.s = 'art';
    artRow.innerHTML = '<i></i><span>FLUX — drawing the plates</span><em></em>';
    barBusy.appendChild(artRow);
    return fetch('/api/art', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompts: shots })
    }).then(function(r){ return r.json(); }).then(function(res){
      var pending = [];
      (res.art || []).forEach(function(a){
        if (!a.url) return;
        var im = document.createElement('img');
        im.alt = 'AI illustration — generated live';
        if (a.role === 'then' || a.role === 'now') {
          var idx = a.role === 'now' ? stageItems.length - 1 : 0;
          im.className = 'stage-item';
          pending.push(new Promise(function(ok){
            im.addEventListener('load', function(){
              var old = stageItems[idx];
              if (old && old !== im) { stage.insertBefore(im, old); old.remove(); stageItems[idx] = im; }
              ok();
            });
            im.addEventListener('error', ok); /* plate stays if the art 404s */
          }));
          im.src = a.url;
        } else {
          im.className = 'art-thumb';
          pending.push(new Promise(function(ok){
            im.addEventListener('load', ok);
            im.addEventListener('error', function(){ im.remove(); ok(); });
          }));
          if (artStrip) artStrip.appendChild(im);
          im.src = a.url;
        }
      });
      artRow.classList.remove('run'); artRow.classList.add('done');
      artRow.querySelector('em').textContent = (res.art || []).filter(function(a){ return a.url; }).length + ' plates';
      return Promise.race([Promise.all(pending), new Promise(function(ok){ setTimeout(ok, 20000); })]);
    }).catch(function(){ /* plates render without art */ });
  }
  var LENS_STEPS = [
    ['start', 'Opening the archive'],
    ['wikipedia', 'Wikipedia — resolving the modern article'],
    ['embed', 'Nemotron Embed VL — topic to a 2,048-dim vector'],
    ['lance_candidates', 'LanceDB — evidence regions shortlisted'],
    ['rerank', 'Nemotron Rerank VL — weighing the pages'],
    ['super_vl', 'Nemotron Super VL — verdict + art direction'],
    ['art', 'FLUX — drawing the plates']
  ];
  function lensStepsReset(){
    barBusy.innerHTML = '<span class="busy-title">Reading the archive</span>'
      + LENS_STEPS.slice(0, 6).map(function(s){
          return '<div class="ls" data-s="' + s[0] + '"><i></i><span>' + s[1] + '</span><em></em></div>';
        }).join('');
    document.body.classList.add('loading');
    var first = barBusy.querySelector('.ls'); if (first) first.classList.add('run');
  }
  function lensStep(name, detail){
    var rows = barBusy.querySelectorAll('.ls'), hit = false;
    rows.forEach(function(r){
      if (r.dataset.s === name) { r.classList.remove('run'); r.classList.add('done'); hit = true;
        if (detail) r.querySelector('em').textContent = detail;
      }
      else if (!hit && r.classList.contains('run')) { r.classList.remove('run'); r.classList.add('done'); }
    });
    var next = barBusy.querySelector('.ls:not(.done)');
    if (next) next.classList.add('run');
  }
  function lensStepDetail(ev){
    if (ev.title) return ev.title;
    if (ev.top) return ev.top + (ev.score != null ? ' · ' + ev.score.toFixed(2) : '');
    if (ev.pages) return ev.pages.length + ' pages';
    if (ev.topic) return ev.topic;
    return '';
  }
  function fetchLive(raw){
    var topic = topicFrom(raw);
    if (!topic) { barMiss.classList.add('show'); return; }
    barMiss.classList.remove('show');
    lensStepsReset();
    fetch('/api/lens?topic=' + encodeURIComponent(topic))
      .then(function(r){
        if (!r.ok || !r.body) throw r.status;
        var reader = r.body.getReader(), dec = new TextDecoder(), buf = '';
        function pump(){
          return reader.read().then(function(res){
            if (res.done) return;
            buf += dec.decode(res.value, { stream: true });
            var lines = buf.split('\n'); buf = lines.pop();
            lines.forEach(function(l){
              if (!l.trim()) return;
              var ev = JSON.parse(l);
              if (ev.step) lensStep(ev.step, lensStepDetail(ev));
              if (ev.error) throw ev.error;
              if (ev.done) {
                lensStep('super_vl');
                var key = 'live:' + topic;
                LIVE[key] = liveTopic(ev.data);
                loadTopic(key, false);
                fetchArt(ev.data).then(function(){
                  document.body.classList.remove('loading');
                  var eh = document.querySelector('.exhibit-head');
                  if (eh) eh.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
                });
              }
            });
            return pump();
          });
        }
        return pump();
      })
      .catch(function(){
        document.body.classList.remove('loading');
        urlBar.classList.remove('shake'); void urlBar.offsetWidth; urlBar.classList.add('shake');
        barMiss.classList.add('show');
      });
  }
  if (mainEl) mainEl.classList.add('idle');
  urlForm.addEventListener('submit', function(e){
    e.preventDefault();
    var raw = urlInput.value.trim();
    if (raw) fetchLive(raw);
  });
  Array.prototype.forEach.call(document.querySelectorAll('.bar-miss .go'), function(b){
    b.addEventListener('click', function(){ fetchLive(b.dataset.topic); });
  });
  try {
    var qp = new URLSearchParams(location.search).get('wiki') || new URLSearchParams(location.search).get('q');
    var hk = location.hash.replace('#','');
    var pathRaw = location.pathname.replace(/^\/+/, '');
    var raw0 = qp || pathRaw || hk;
    if (raw0) { document.body.classList.add('deep'); fetchLive(raw0); }
  } catch(e) {}

  /* ================= motion ================= */
  function posFromEvent(e){
    var r = track.getBoundingClientRect();
    return clamp((e.clientX - r.left) / r.width, 0, 1);
  }
  function nearestStop(p){
    var best = 0, bd = Infinity;
    for (var i = 0; i < stopsPos.length; i++) {
      var d = Math.abs(stopsPos[i] - p);
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }
  function goTo(i){
    tweening = true; twFrom = pos; twTo = stopsPos[i];
    twStart = performance.now(); twDur = reduced ? 0 : 520;
    vel = 0;
  }

  var lastX = 0, lastMoveT = 0;
  lens.addEventListener('pointerdown', function(e){
    dragging = true; tweening = false; vel = 0;
    lens.setPointerCapture(e.pointerId);
    lastX = e.clientX; lastMoveT = performance.now();
    e.preventDefault();
  });
  track.addEventListener('pointerdown', function(e){
    if (e.target === lens || lens.contains(e.target)) return;
    if (e.target.closest && e.target.closest('.stop')) return;
    dragging = true; tweening = false; vel = 0;
    target = posFromEvent(e);
    lastX = e.clientX; lastMoveT = performance.now();
    lens.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  window.addEventListener('pointermove', function(e){
    if (!dragging) return;
    var now = performance.now();
    var r = track.getBoundingClientRect();
    var newTarget = clamp((e.clientX - r.left) / r.width, 0, 1);
    var dt = (now - lastMoveT) / 1000;
    if (dt > 0.005) {
      vel = vel * 0.5 + ((newTarget - target) / dt) * 0.5;
      lastMoveT = now;
    }
    target = newTarget;
    lastX = e.clientX;
  });
  window.addEventListener('pointerup', function(){
    if (!dragging) return;
    dragging = false;
    vel = clamp(vel, -1.6, 1.6);
  });

  lens.addEventListener('keydown', function(e){
    var i = nearestStop(pos);
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp')   { goTo(Math.min(i + 1, STOPS.length - 1)); e.preventDefault(); }
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowDown') { goTo(Math.max(i - 1, 0)); e.preventDefault(); }
    if (e.key === 'Home') { goTo(0); e.preventDefault(); }
    if (e.key === 'End')  { goTo(STOPS.length - 1); e.preventDefault(); }
  });

  function focusAmount(w){ return (1 - w) * 3.2; }

  function render(){
    if (!isFinite(pos)) pos = stopsPos[0] || 0;
    var year = Math.round(YEAR_MIN + pos * (YEAR_MAX - YEAR_MIN));
    lens.style.left = (pos * 100) + '%';
    fill.style.width = (pos * 100) + '%';
    if (year !== lastYearShown) {
      lastYearShown = year;
      lensYear.textContent = year;
      yearOut.textContent = year;
      lens.setAttribute('aria-valuenow', year);
    }
    var ni = nearestStop(pos);
    if (ni !== lastStopIdx) {
      lastStopIdx = ni;
      var s = STOPS[ni];
      pillText.textContent = s.status;
      editionEl.textContent = s.edition;
      pill.className = 'status ' + s.cls;
      lens.setAttribute('aria-valuetext', year + ' — ' + s.edition);
      stageCapKind.textContent = s.capKind;
      stageCapKind.style.color = s.capKind === 'AI photograph' || s.capKind === 'AI engraving' ? '#cf5a30' : '#7fa08b';
      stageCapText.textContent = s.cap;
    }
    stopEls.forEach(function(el, i){ el.classList.toggle('active', i === ni); });

    for (var i = 0; i < panels.length; i++) {
      var w = 0;
      if (pos <= stopsPos[i] && i === 0) w = pos <= stopsPos[0] ? 1 : 0;
      if (i > 0 && pos <= stopsPos[i] && pos >= stopsPos[i - 1]) {
        w = smooth((pos - stopsPos[i - 1]) / (stopsPos[i] - stopsPos[i - 1]));
      }
      if (i < panels.length - 1 && pos >= stopsPos[i] && pos <= stopsPos[i + 1]) {
        w = 1 - smooth((pos - stopsPos[i]) / (stopsPos[i + 1] - stopsPos[i]));
      }
      if (i === panels.length - 1 && pos >= stopsPos[i]) w = 1;
      w = clamp(w, 0, 1);
      var p = panels[i];
      p.style.opacity = w;
      p.style.transform = 'translateY(' + ((1 - w) * 12) + 'px)';
      p.classList.toggle('front', w > 0.6);
      p.style.visibility = w < 0.02 ? 'hidden' : 'visible';
      if (stageItems[i] && !stageItems[i].dataset.broken) {
        stageItems[i].style.opacity = w;
        stageItems[i].style.filter = 'blur(' + focusAmount(w).toFixed(2) + 'px) brightness(' + (0.82 + w * 0.18).toFixed(3) + ')';
      }
    }
  }

  function frame(now){
    var dt = Math.min((now - lastT) / 1000, 0.05);
    lastT = now;
    if (tweening) {
      var k = twDur === 0 ? 1 : clamp((now - twStart) / twDur, 0, 1);
      pos = twFrom + (twTo - twFrom) * easeOut(k);
      if (k >= 1) { tweening = false; pos = twTo; }
    } else if (dragging) {
      pos += (target - pos) * (reduced ? 1 : Math.min(1, dt * 18));
    } else {
      if (Math.abs(vel) > 0.02) {
        pos = clamp(pos + vel * dt, 0, 1);
        if (pos === 0 || pos === 1) vel = 0;
        vel *= Math.pow(0.06, dt);
      } else if (stopsPos.length) {
        var ns = stopsPos[nearestStop(pos)];
        var d = ns - pos;
        if (Math.abs(d) > 0.0004) pos += d * Math.min(1, dt * 7);
        else pos = ns;
      }
    }
    render();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  /* ================= scroll reveal ================= */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduced) {
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function(el){ io.observe(el); });
  } else {
    revealEls.forEach(function(el){ el.classList.add('in'); });
  }
})();
    return undefined;
  }, []);

  return (
<>
{/* ============ fullscreen pipeline loader ============ */}
<div className="loader" id="loader">
  <div className="loader-box">
    <div className="bar-miss show" id="barBusy"></div>
  </div>
</div>

{/* ============ the cover ============ */}
<div className="cover">
  <img className="cover-img" id="coverImg" src="/assets/hero.png" alt="" />
  <div className="cover-scrim" />

  <div className="cover-inner">
    <div className="cover-kicker reveal">TimeLens</div>
    <h1 className="cover-title reveal">Pull history<br />into focus.</h1>
    <p className="cover-line reveal">Prefix any Wikipedia URL — <code>timelens.to/</code> reads the topic across 250 years of encyclopedias.</p>

    <div className="barzone">
      <div className="bar" id="urlBar">
        <span className="dots" aria-hidden="true"><i></i><i></i><i></i></span>
        <form className="url" id="urlForm" autoComplete="off" spellCheck="false">
          <span className="mag" aria-hidden="true">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.6 15.6 21 21"/></svg>
          </span>
          <label className="field" htmlFor="urlInput">
            <span className="dom">timelens.to/</span><input className="path" id="urlInput" defaultValue="wikipedia.org/wiki/Basalt" aria-label="Wikipedia URL or topic" />
          </label>
        </form>
        <span className="yrs">250 yrs of revisions</span>
      </div>
      <div className="bar-miss" id="barMiss">
        <span>No reliable match came back — try one of these:</span>
        <button className="go" data-topic="basalt">Basalt</button>
        <button className="go" data-topic="electricity">Electricity</button>
        <button className="go" data-topic="cloud">Cloud</button>
        <button className="go" data-topic="chocolate">Chocolate</button>
      </div>
    </div>
    <p className="cover-sub" id="titleSub">— type a topic, or paste a Wikipedia URL.</p>
  </div>

  <div className="cover-scroll"><span>the record</span><i /></div>
</div>

<div className="wrap">
  {/* exhibit */}
  <main>
    <div className="exhibit-head">
      <div className="entry reveal" id="entryName">—
        <span className="def" id="entryDef"></span>
      </div>
      <div className="yearbox reveal">
        <div className="year" id="yearReadout"></div>
        <div className="edition" id="editionLabel"></div>
        <span className="status record" id="statusPill"><span className="dot"></span><span id="statusText"></span></span>
      </div>
    </div>

    {/* the object under the lens */}
    <div className="stage reveal" id="stage" aria-hidden="true">
      <span className="frame-mark fm-tl"></span><span className="frame-mark fm-tr"></span>
      <span className="frame-mark fm-bl"></span><span className="frame-mark fm-br"></span>
      <span className="cap"><b id="stageCapKind">Lens</b><span className="sep">·</span><span id="stageCapText">awaiting the archive</span></span>
    </div>

    {/* instrument rail */}
    <div className="rail reveal" id="timeline">
      <div className="rail-track" id="railTrack">
        <div className="rail-line"></div>
        <div className="rail-fill" id="railFill"></div>
        <div className="lens" id="lens" role="slider" tabIndex="0"
             aria-label="Timeline year" aria-valuemin="1770" aria-valuemax="2025" aria-valuenow="1810"
             aria-valuetext="1810 — Britannica, Fourth Edition">
          <span className="ret" aria-hidden="true"></span>
          <span className="lyr" id="lensYear">1810</span>
        </div>
      </div>
      <div className="rail-hint">drag the lens through 250 years — <kbd>←</kbd> <kbd>→</kbd> to step between editions</div>
    </div>

    {/* era plates */}
    <div className="deck" id="deck"></div>

    {/* the page under glass — the matched scan, inspectable */}
    <section className="block specimen" id="specimen" style={{ display: 'none' }}>
      <div className="sec-head reveal">
        <h2>The page, <em>under glass.</em></h2>
        <p className="margin-note note">— the actual matched scan. Tap to enlarge.</p>
      </div>
      <figure className="spec-frame" id="specFrame">
        <img id="specImg" alt="Matched Britannica scan" />
        <figcaption id="specCap"></figcaption>
      </figure>
    </section>

  </main>

  {/* colophon */}
  <footer>
    <div className="pipeline reveal">
      <span className="pipe">Nemotron Parse 3.5</span>
      <span className="pipe-arrow">→</span>
      <span className="pipe">Embed VL</span>
      <span className="pipe-arrow">→</span>
      <span className="pipe">Rerank VL <span className="sub">· RTX PRO 6000</span></span>
      <span className="pipe-arrow">→</span>
      <span className="pipe">Super VL agent</span>
    </div>
    <p className="colophon reveal"><b>timelens.to</b> — prepend it to anything we thought we knew.</p>
  </footer>
</div>
</>
  );
}
