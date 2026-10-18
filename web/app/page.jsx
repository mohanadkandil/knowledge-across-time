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

  /* ================= exhibits — real indexed pages ================= */
  var TOPICS = {
    basalt: {
      word: "Basalt", def: "the rock geology fought a war over",
      titleSub: "a rock, probably — an argument, certainly.",
      wikiPath: "wikipedia.org/wiki/Basalt",
      start: 1,
      stops: [
        {
          year: 1795, label: "the war", status: "Disputed — water vs. fire", cls: "contested",
          edition: "The field, mid-argument",
          capKind: "AI engraving", cap: "how the fight was pictured",
          img: "/assets/war.png", alt: "Engraving-style AI illustration: two 1790s natural philosophers disputing whether basalt came from ocean or fire",
          html: '<span class="plate-no">i.</span><h3>Geology\u2019s civil war.</h3><div class="versus"><div class="side water"><div class="flag">Neptunists</div><h4>water</h4><p>every rock precipitated from a universal ocean — Werner, Freiberg.</p></div><div class="side fire"><div class="flag">Vulcanists</div><h4>fire</h4><p>basalt injected molten into older strata — Hutton.</p></div></div>'
        },
        {
          year: 1810, label: "the record", status: "Disputed — on the record", cls: "record",
          edition: "Britannica, Fourth Edition",
          capKind: "Original scan", cap: "the actual fourth-edition page",
          img: "/assets/record.jpg", alt: "Original scanned page: Britannica fourth edition, MINERALOGY, containing the unresolved basalt controversy",
          html: '<span class="plate-no">ii.</span><h3>The encyclopedia refuses to pick.</h3><blockquote class="quote">\u201cNo subject in geological speculation has produced more controversy than the origin of basalt \u2026 our limits preclude us even from literally stating the arguments.\u201d</blockquote><div class="chips"><span class="chip">blowpipe \u2192 <b>opaque black glass</b></span><span class="chip"><b>affects the magnetic needle</b></span><span class="chip"><b>rings</b> under the hammer</span><span class="chip"><b>columns</b> — Staffa, Giant\u2019s Causeway</span></div><p class="smallprint">fourth-edition page, lightly cleaned OCR · bri-2376-3186638c36ec</p>'
        },
        {
          year: 1835, label: "the verdict", status: "Verdict — in fact volcanic", cls: "record",
          edition: "Britannica, Seventh Edition",
          capKind: "AI engraving", cap: "the verdict, as they came to see it",
          img: "/assets/verdict.png", alt: "Engraving-style AI illustration of Fingal's Cave basalt columns with a volcanic glow",
          html: '<span class="plate-no">iii.</span><h3>The same book changes its mind.</h3><blockquote class="quote">Basalts \u201cidentical with <em>products of active volcanoes</em>.\u201d</blockquote><div class="chips"><span class="chip hot"><b>Britannica vs. Britannica</b> — settled in print</span></div><p class="smallprint">seventh-edition page · bri-0966-64586d30c5c9</p>'
        },
        {
          year: 2025, label: "today", status: "Settled — igneous", cls: "settled",
          edition: "Wikipedia, live revision",
          capKind: "AI photograph", cap: "the settled view",
          img: "/assets/today.png", alt: "AI-generated photoreal Giant's Causeway at golden hour",
          html: '<span class="plate-no">iv.</span><h3>Fire won.</h3><blockquote class="quote">\u201cBasalt is a common igneous rock.\u201d</blockquote><div class="chips"><span class="chip"><b>cooled lava</b></span><span class="chip"><b>aphanitic</b> — grains too fine to see</span><span class="chip"><b>columnar jointing</b></span><span class="chip">the <b>ocean floor</b> is mostly basalt</span></div>'
        }
      ]
    },

    electricity: {
      word: "Electricity", def: "a fluid they could not weigh",
      titleSub: "the invisible substance that became a swarm of particles.",
      wikiPath: "wikipedia.org/wiki/Fluid_theory_of_electricity",
      start: 0,
      stops: [
        {
          year: 1797, label: "then", status: "Fluid theory — held", cls: "record",
          edition: "Britannica, Suppl. to the 3rd ed.",
          capKind: "Original scan", cap: "the actual supplement page",
          img: "/assets/scan-1776.jpg", alt: "Original scanned page: Britannica supplement electricity entry",
          html: '<span class="plate-no">i.</span><h3>One fluid, or two?</h3><blockquote class="quote">\u201c\u2026the distribution of the <em>electric fluid</em> in bodies, in various circumstances.\u201d</blockquote><div class="chips"><span class="chip"><b>a substance</b>, in excess or deficit</span><span class="chip">points, sparks, the <b>electrical chain</b></span><span class="chip">no electrons — not named until <b>1891</b></span></div><p class="smallprint">bri-1776-5ed864a29d36 · supplement to the third edition</p>'
        },
        {
          year: 2025, label: "now", status: "Superseded — archived", cls: "settled",
          edition: "Wikipedia, live revision",
          capKind: "Plate", cap: "the superseded model, on file",
          plate: { title: "Fluid theory of electricity", sub: "wikipedia · superseded model" },
          html: '<span class="plate-no">ii.</span><h3>The fluid becomes a museum piece.</h3><blockquote class="quote">\u201cFluid theory of electricity\u201d — a superseded model.</blockquote><div class="chips"><span class="chip"><b>du Fay</b> — two fluids</span><span class="chip"><b>Franklin</b> — one</span><span class="chip"><b>electron</b> — the replacement</span></div>'
        }
      ]
    },

    cloud: {
      word: "Cloud", def: "vapour, and a question left open",
      titleSub: "they measured the electricity — and still asked which caused which.",
      wikiPath: "wikipedia.org/wiki/Cloud",
      start: 0,
      stops: [
        {
          year: 1823, label: "then", status: "Open question — on the record", cls: "record",
          edition: "Britannica, Sixth Edition",
          capKind: "Original scan", cap: "the actual sixth-edition page",
          img: "/assets/scan-59.jpg", alt: "Original scanned page: Britannica sixth edition CLOUD entry",
          html: '<span class="plate-no">i.</span><h3>Vapour, measured — not explained.</h3><blockquote class="quote">\u201ca collection of <em>vapours</em> suspended in the atmosphere\u201d \u2026 \u201cwhether electricity is the cause or the effect hath <em>not yet been ascertained</em>.\u201d</blockquote><div class="chips"><span class="chip"><b>Beccaria\u2019s rods</b> draw charge from passing clouds</span><span class="chip">cause, or effect? <b>left open</b></span></div><p class="smallprint">bri-0059-891965a7ca3e · the model later wrote \u201cBecquerel\u201d here — see incidents</p>'
        },
        {
          year: 2025, label: "now", status: "Settled definition — old question kept", cls: "settled",
          edition: "Wikipedia, live revision",
          capKind: "Plate", cap: "the modern definition",
          plate: { title: "Cloud", sub: "wikipedia · live revision" },
          html: '<span class="plate-no">ii.</span><h3>Droplets, not vapour.</h3><blockquote class="quote">\u201ca visible mass of condensed droplets or frozen crystals.\u201d</blockquote><div class="chips"><span class="chip"><b>condensate</b>, not vapour</span><span class="chip">charge separation: <b>still researched</b></span><span class="chip">the open question <b>outlived the edition</b></span></div>'
        }
      ]
    },

    chlamys: {
      word: "Chlamys", def: "a cloak that became a scallop",
      titleSub: "the same word, filed under a different world.",
      wikiPath: "wikipedia.org/wiki/Chlamys_(bivalve)",
      start: 0,
      stops: [
        {
          year: 1823, label: "then", status: "A garment — on the record", cls: "record",
          edition: "Britannica, Sixth Edition",
          capKind: "Original scan", cap: "the actual sixth-edition page",
          img: "/assets/scan-57.jpg", alt: "Original scanned page: Britannica sixth edition CHLAMYS entry",
          html: '<span class="plate-no">i.</span><h3>An item of clothing.</h3><blockquote class="quote">\u201ca <em>military cloak</em>, worn over the tunic \u2026 the emperors\u2019 were purple, and bordered with gold.\u201d</blockquote><div class="chips"><span class="chip"><b>cloak</b> — Greek, martial</span><span class="chip">same page as CHOCOLATE — literally</span></div><p class="smallprint">bri-0057-7d7650d5d60f</p>'
        },
        {
          year: 2025, label: "now", status: "Diverged — same name, different subject", cls: "settled",
          edition: "Wikipedia, live revision",
          capKind: "Plate", cap: "the living chlamys",
          plate: { title: "Chlamys (bivalve)", sub: "wikipedia · genus of scallops" },
          html: '<span class="plate-no">ii.</span><h3>A shell wearing the cloak\u2019s name.</h3><blockquote class="quote">\u201cChlamys\u201d — a genus of small scallops.</blockquote><div class="chips"><span class="chip">named <b>after the cloak</b></span><span class="chip hot"><b>name match \u2260 subject match</b></span></div>'
        }
      ]
    },

    chocolate: {
      word: "Chocolate", def: "a medicine, briefly electrical",
      titleSub: "before it was dessert, it was an experiment.",
      wikiPath: "wikipedia.org/wiki/Chocolate",
      start: 0,
      stops: [
        {
          year: 1823, label: "then", status: "Remedy & curiosity — on the record", cls: "record",
          edition: "Britannica, Sixth Edition",
          capKind: "Original scan", cap: "the actual sixth-edition page",
          img: "/assets/scan-57.jpg", alt: "Original scanned page: Britannica sixth edition CHOCOLATE entry",
          html: '<span class="plate-no">i.</span><h3>Medicine — and one forgotten experiment.</h3><blockquote class="quote">Mr. Heily electrifies chocolate; the effect dies unless the mixture holds <em>\u201ca small quantity of olive-oil.\u201d</em></blockquote><div class="chips"><span class="chip"><b>olive-oil</b> — the scan</span><span class="chip hot"><b>alcohol</b> — what the OCR, then the agent, said</span></div><p class="smallprint">bri-0057-7d7650d5d60f · produced the \u201cscan-false\u201d incident below</p>'
        },
        {
          year: 2025, label: "now", status: "A food — the experiment forgotten", cls: "settled",
          edition: "Wikipedia, live revision",
          capKind: "Plate", cap: "the modern article",
          plate: { title: "Chocolate", sub: "wikipedia · live revision" },
          html: '<span class="plate-no">ii.</span><h3>Dessert.</h3><blockquote class="quote">\u201ca food product made from roasted and ground cacao seeds.\u201d</blockquote><div class="chips"><span class="chip"><b>Theobroma cacao</b></span><span class="chip">the experiment: <b>not retained</b></span><span class="chip">knowledge doesn\u2019t only accumulate — it <b>sheds</b></span></div>'
        }
      ]
    }
  };

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
  var wipeEl   = document.getElementById('wipe');
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
    var T = TOPICS[key]; if (!T) return;
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
    artStrip.innerHTML = '';

    lastStopIdx = -1;
    var s0 = T.start || 0;
    pos = stopsPos[s0]; target = pos; vel = 0; tweening = false;
    if (scroll) {
      document.querySelector('.exhibit-head').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
    }
  }

  /* ================= url routing ================= */
  function resolveInput(v){
    var s = v.trim().toLowerCase();
    if (!s) return null;
    s = s.replace(/^https?:\/\//, '').replace(/^timelens\.to\/?/, '').replace(/\/+$/, '');
    var m = s.match(/wiki\/(.+)/);
    var slug = (m ? m[1] : s.split('/').pop()).replace(/_/g, ' ').replace(/%20/g, ' ');
    slug = decodeURIComponent(slug).replace(/\(.*?\)/g, '').trim();
    for (var k in TOPICS) {
      if (TOPICS.hasOwnProperty(k) && (slug.indexOf(k) !== -1 || TOPICS[k].word.toLowerCase().indexOf(slug) !== -1)) return k;
    }
    if (slug.indexOf('fluid') !== -1 || slug.indexOf('electric') !== -1) return 'electricity';
    if (slug.indexOf('bivalve') !== -1 || slug.indexOf('scallop') !== -1) return 'chlamys';
    return null;
  }
  var barBusy = document.getElementById('barBusy');
  function liveTopic(d){
    var yr = d.page.editionYear || 1823;
    var ed = (d.page.edition ? d.page.edition + ' edition' : 'historical edition');
    var thenHtml = '<span class="plate-no">i.</span><h3>What the page says.</h3>'
      + '<blockquote class="quote">\u201c' + (d.exhibit && d.exhibit.quote || d.thenText.slice(0,160).replace(/"/g,'')) + '\u201d</blockquote>'
      + (d.exhibit && d.exhibit.then_line ? '<p>' + d.exhibit.then_line + '</p>' : '')
      + '<div class="chips"><span class="chip">rerank score <b>' + (d.match.rerankScore != null ? d.match.rerankScore.toFixed(2) : '—') + '</b></span>'
      + '<span class="chip">source <b>' + d.page.sourceId.split(':')[0] + '</b></span></div>'
      + '<p class="smallprint">live retrieval — quote shown as returned by Super VL against the page text; original scan above is the ground truth</p>';
    var nowTitle = (d.wiki && d.wiki.title) || 'Wikipedia';
    var nowHtml = '<span class="plate-no">ii.</span><h3>' + (d.exhibit && d.exhibit.verdict === 'diverged' ? 'Diverged.' : d.exhibit && d.exhibit.verdict === 'superseded' ? 'Superseded.' : d.exhibit && d.exhibit.verdict === 'open' ? 'Still open.' : 'Today.') + '</h3>'
      + '<blockquote class="quote">\u201c' + ((d.wiki && d.wiki.excerpt || '').slice(0,180).replace(/["\u201c\u201d]/g,'')) + '\u2026\u201d</blockquote>'
      + (d.exhibit && d.exhibit.now_line ? '<p>' + d.exhibit.now_line + '</p>' : '')
      + (d.exhibit && d.exhibit.note ? '<div class="chips"><span class="chip hot"><b>' + d.exhibit.note + '</b></span></div>' : '')
      + '<p class="smallprint">' + nowTitle + ' · ' + (d.wiki && d.wiki.url || 'shared index') + '</p>';
    return {
      word: (d.topic || 'Topic'), def: 'retrieved live from the archive',
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
    var shots = (d.art || []).filter(function(s){ return s && s.prompt; }).slice(0, 4);
    if (!shots.length) { barBusy.classList.remove('show'); return; }
    var artRow = document.createElement('div');
    artRow.className = 'ls run'; artRow.dataset.s = 'art';
    artRow.innerHTML = '<i></i><span>FLUX — drawing the plates</span><em></em>';
    barBusy.appendChild(artRow);
    fetch('/api/art', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompts: shots })
    }).then(function(r){ return r.json(); }).then(function(res){
      (res.art || []).forEach(function(a){
        if (!a.url) return;
        if (a.role === 'then' || a.role === 'now') {
          var idx = a.role === 'now' ? stageItems.length - 1 : 0;
          var im = document.createElement('img');
          im.className = 'stage-item';
          im.src = a.url; im.alt = 'AI illustration — generated live';
          var old = stageItems[idx];
          if (old) { stage.insertBefore(im, old); old.remove(); stageItems[idx] = im; }
        } else {
          var th = document.createElement('img');
          th.src = a.url; th.className = 'art-thumb'; th.alt = 'AI illustration — generated live';
          artStrip.appendChild(th);
        }
      });
      artRow.classList.remove('run'); artRow.classList.add('done');
      artRow.querySelector('em').textContent = (res.art || []).filter(function(a){ return a.url; }).length + ' plates';
      setTimeout(function(){ barBusy.classList.remove('show'); }, 1600);
    }).catch(function(){ barBusy.classList.remove('show'); });
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
    barBusy.classList.add('show');
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
    barMiss.classList.remove('show');
    lensStepsReset();
    var s = raw.replace(/^https?:\/\//, '').replace(/^timelens\.to\/?/, '').replace(/\/+$/, '');
    var mm = s.match(/wiki\/(.+)/);
    var topic = decodeURIComponent((mm ? mm[1] : s.split('/').pop()).replace(/_/g,' ').replace(/%20/g,' ').replace(/\(.*?\)/g,'').trim());
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
                TOPICS[key] = liveTopic(ev.data);
                loadTopic(key, true);
                fetchArt(ev.data);
              }
            });
            return pump();
          });
        }
        return pump();
      })
      .catch(function(){
        barBusy.classList.remove('show');
        urlBar.classList.remove('shake'); void urlBar.offsetWidth; urlBar.classList.add('shake');
        barMiss.classList.add('show');
      });
  }
  urlForm.addEventListener('submit', function(e){
    e.preventDefault();
    var k = resolveInput(urlInput.value);
    if (k) { loadTopic(k, true); return; }
    var raw = urlInput.value.trim();
    if (raw) fetchLive(raw);
  });
  Array.prototype.forEach.call(document.querySelectorAll('.bar-miss .go'), function(b){
    b.addEventListener('click', function(){ loadTopic(b.dataset.topic, true); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('.lrow[data-topic]'), function(a){
    a.addEventListener('click', function(e){ e.preventDefault(); loadTopic(a.dataset.topic, true); });
  });
  try {
    var qp = new URLSearchParams(location.search).get('wiki') || new URLSearchParams(location.search).get('q');
    var hk = location.hash.replace('#','').toLowerCase();
    var pk = qp && resolveInput(qp);
    var pathRaw = location.pathname.replace(/^\/+/, '');
    var pathKey = pathRaw && resolveInput(pathRaw);
    if (pk || pathKey || qp || pathRaw) document.body.classList.add('deep');
    if (pk) loadTopic(pk, false);
    else if (pathKey) loadTopic(pathKey, false);
    else if (qp) fetchLive(qp);
    else if (pathRaw) fetchLive(pathRaw);
    else if (hk && TOPICS[hk]) loadTopic(hk, false);
    else loadTopic('basalt', false);
  } catch(e) { loadTopic('basalt', false); }

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
      } else {
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

  /* ================= before/after wipe ================= */
  if (wipeEl) {
    var wipeImgs = Array.prototype.slice.call(wipeEl.querySelectorAll('img'));
    var wipeBroken = 0;
    wipeImgs.forEach(function(im){
      var broke = function(){ wipeBroken++; if (wipeBroken >= wipeImgs.length) wipeEl.style.display = 'none'; };
      if (im.complete && im.naturalWidth === 0) broke();
      im.addEventListener('error', broke);
    });
    var wipeDrag = false;
    var setCut = function(p){ wipeEl.style.setProperty('--cut', (clamp(p,0,1) * 100) + '%'); };
    var wipeMove = function(e){
      var r = wipeEl.getBoundingClientRect();
      setCut((e.clientX - r.left) / r.width);
    };
    wipeEl.addEventListener('pointerdown', function(e){
      wipeDrag = true; wipeEl.setPointerCapture(e.pointerId);
      wipeMove(e); e.preventDefault();
    });
    window.addEventListener('pointermove', function(e){ if (wipeDrag) wipeMove(e); });
    window.addEventListener('pointerup', function(){ wipeDrag = false; });
    setCut(0.5);
  }

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
      <div className="bar-miss" id="barBusy"><span>Reading the archive — Embed VL → LanceDB → Rerank VL → Super VL…</span></div>
      <div className="bar-miss" id="barMiss">
        <span>Not in the lens's index yet — five of the hundred scanned pages are live exhibits:</span>
        <button className="go" data-topic="basalt">Basalt</button>
        <button className="go" data-topic="electricity">Electricity</button>
        <button className="go" data-topic="cloud">Cloud</button>
        <button className="go" data-topic="chlamys">Chlamys</button>
        <button className="go" data-topic="chocolate">Chocolate</button>
      </div>
    </div>
    <p className="cover-sub" id="titleSub">— the lens, applied to basalt.</p>
  </div>

  <div className="cover-scroll"><span>the record</span><i /></div>
</div>

<div className="wrap">
  {/* exhibit */}
  <main>
    <div className="exhibit-head">
      <div className="entry reveal" id="entryName">Basalt.
        <span className="def" id="entryDef">the rock geology fought a war over</span>
      </div>
      <div className="yearbox reveal">
        <div className="year" id="yearReadout">1810</div>
        <div className="edition" id="editionLabel">Britannica, Fourth Edition</div>
        <span className="status record" id="statusPill"><span className="dot"></span><span id="statusText">Disputed — on the record</span></span>
      </div>
    </div>

    {/* the object under the lens */}
    <div className="stage reveal" id="stage" aria-hidden="true">
      <span className="frame-mark fm-tl"></span><span className="frame-mark fm-tr"></span>
      <span className="frame-mark fm-bl"></span><span className="frame-mark fm-br"></span>
      <span className="cap"><b id="stageCapKind">AI engraving</b><span className="sep">·</span><span id="stageCapText">how the fight was pictured</span></span>
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
      <div className="art-strip" id="artStrip"></div>
    </section>

    {/* ledger of exhibits */}
    <section className="block">
      <div className="sec-head reveal">
        <h2>The same lens, <em>turned elsewhere.</em></h2>
        <p className="margin-note note">— every claim pinned to a real source region; tap a row to pull it under the lens.</p>
      </div>
      <div className="ledger reveal" id="ledger">
        <a className="lrow" href="#" data-topic="electricity">
          <div className="word">Electricity<span>Suppl. 3rd ed. → Wikipedia</span></div>
          <div className="col"><span className="t">then</span><p>“the distribution of the <i>electric fluid</i> in bodies” — an invisible substance, present in excess or deficit.</p></div>
          <div className="col now"><span className="t">now</span><p><i>Fluid theory of electricity</i> — du Fay's two fluids and Franklin's one, catalogued as a superseded model.</p>
            <span className="arrow">under the lens →</span></div>
        </a>
        <a className="lrow" href="#" data-topic="cloud">
          <div className="word">Cloud<span>Sixth ed. → Wikipedia</span></div>
          <div className="col"><span className="t">then</span><p>“a collection of <i>vapours</i> suspended in the atmosphere” — and an open question: electrified before, or after, they form?</p></div>
          <div className="col now"><span className="t">now</span><p>“a visible mass of <i>condensed droplets or frozen crystals</i>” — the definition settled; the old “hath not yet been ascertained” survived with it.</p>
            <span className="arrow">under the lens →</span></div>
        </a>
        <a className="lrow" href="#" data-topic="chlamys">
          <div className="word">Chlamys<span>Sixth ed. → Wikipedia</span></div>
          <div className="col"><span className="t">then</span><p>a <i>military cloak</i> worn over the tunic — the emperors' were purple, bordered in gold.</p></div>
          <div className="col now"><span className="t">now</span><p>a <i>genus of small scallops</i> — named, Wikipedia notes, after the Greek cloak. A matching name is not the same subject.</p>
            <span className="arrow">under the lens →</span></div>
        </a>
        <a className="lrow" href="#" data-topic="chocolate">
          <div className="word">Chocolate<span>Sixth ed. → Wikipedia</span></div>
          <div className="col"><span className="t">then</span><p>a medicinal <i>paste</i> of cacao — and a forgotten experiment on its <i>electrical properties</i>.</p></div>
          <div className="col now"><span className="t">now</span><p>a <i>food product</i> made from roasted Theobroma cacao seeds — the experiment no longer part of the story.</p>
            <span className="arrow">under the lens →</span></div>
        </a>
      </div>
    </section>

    {/* heat: the wipe */}
    <section className="block">
      <div className="sec-head reveal">
        <h2>Heat: <em>fluid, then motion.</em></h2>
        <p className="margin-note note">— the experiment that killed the caloric theory; drag the seam.</p>
      </div>
      <div className="wipe reveal" id="wipe">
        <img className="before" src="/assets/rumford-then.png" alt="AI engraving of the 1798 Munich cannon-boring workshop" />
        <img className="after" src="/assets/rumford-now.png" alt="AI illustration of vibrating copper atoms radiating heat at the boring interface" />
        <div className="cut-line"></div>
        <div className="cut-knob" aria-hidden="true">‹ ›</div>
        <span className="wipe-tag tag-then">1798 · caloric — a fluid</span>
        <span className="wipe-tag tag-now">today · kinetic — motion</span>
      </div>
      <p className="smallprint reveal" style={{marginTop: 18}}>Both images are FLUX illustrations generated for this exhibit — the engraving is not an archival print. In 1798 Benjamin Thompson — Count Rumford — bored cannon at the Munich arsenal and watched the heat come without limit: what a body can furnish inexhaustibly, he argued, cannot be a substance — “except it be MOTION.” Paper: “An Inquiry Concerning the Source of the Heat which is Excited by Friction,” Philosophical Transactions. Expandable-timeline concept follows Suh et al., “KnowledgeTrail,” arXiv:2510.12113.</p>
    </section>

    {/* incident table */}
    <section className="block">
      <div className="sec-head reveal">
        <h2>Caught <em>in the act.</em></h2>
        <p className="margin-note note">— we pointed Nemotron at Nemotron. Real run traces, nothing edited.</p>
      </div>
      <div className="inctable reveal">
        <div className="inc">
          <div className="kind">anachronism</div>
          <div>
            <h4>The nearest famous name</h4>
            <p className="body">In the historical CLOUD entry the scan names <b>S.&nbsp;Beccaria</b>. The OCR garbled it to “S.&nbsp;Bec-certa” — and the agent wrote <b>S.&nbsp;Becquerel</b>, a physicist who would not be born until 1852, into its answer and into an edited quotation. The machine did what the encyclopedists did: filled damaged evidence with the nearest plausible story.</p>
          </div>
          <div className="evi">
            <div className="row"><span className="k">scan</span><span className="v-right">S. Beccaria</span></div>
            <div className="row"><span className="k">ocr</span><span>“S. Bec-certa”</span></div>
            <div className="row"><span className="k">agent</span><span className="v-wrong">S. Becquerel (b. 1852)</span></div>
          </div>
        </div>
        <div className="inc">
          <div className="kind">scan-false</div>
          <div>
            <h4>Faithful to the text, wrong about the page</h4>
            <p className="body">Asked what substance restored chocolate's electrical effect, the agent answered <b>alcohol</b> — faithfully quoting the stored transcription, while openly admitting it had never seen the scan. The scan says <b>olive-oil</b>. A quote can be accurate to the OCR and false to the source.</p>
          </div>
          <div className="evi">
            <div className="row"><span className="k">scan</span><span className="v-right">“a small quantity of olive-oil”</span></div>
            <div className="row"><span className="k">ocr</span><span>“a small quantity of alcohol”</span></div>
            <div className="row"><span className="k">agent</span><span className="v-wrong">alcohol — disclosed, wrong</span></div>
          </div>
        </div>
        <div className="inc">
          <div className="kind">false verification</div>
          <div>
            <h4>A guess promoted to “verified”</h4>
            <p className="body">Faced with “an influential metal difarified with with a elettronter,” the agent declared the answer <b>“Verified original wording”</b> — though it never saw the image. The scan reads “an insulated metal dish furnished with an electrometer.” The warning not to fabricate verified readings was in the prompt. It did not hold.</p>
          </div>
          <div className="evi">
            <div className="row"><span className="k">scan</span><span className="v-right">“an insulated metal dish…”</span></div>
            <div className="row"><span className="k">ocr</span><span>“an influential metal difarified…”</span></div>
            <div className="row"><span className="k">agent</span><span className="v-wrong">“influential metal diffused…” — called verified</span></div>
          </div>
        </div>
      </div>
      <p className="inc-foot reveal">Documented, reproduced, and reported — <b>so the models improve.</b></p>
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
