const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Exercise the actual animation code with an initially empty async result.
// No browser, models, or paid image generation needed for this regression.
const source = fs.readFileSync(`${__dirname}/app/page.jsx`, 'utf8');
const motion = source.slice(source.indexOf('  function focusAmount'), source.indexOf('  /* ================= scroll reveal'));
function element() {
  return { style: {}, dataset: {}, classList: { toggle() {} }, setAttribute() {} };
}

test('animation survives empty results, then renders images and one text panel', () => {
  const frames = [];
  const state = {
    STOPS: [], stopsPos: [], panels: [], stageItems: [], stopEls: [],
    pos: 0, target: 0, vel: 0, lastT: 0, lastYearShown: -1, lastStopIdx: -1,
    tweening: false, dragging: false, reduced: false, YEAR_MIN: 1770, YEAR_MAX: 2025,
    lens: element(), fill: element(), lensYear: element(), yearOut: element(),
    pillText: element(), editionEl: element(), pill: element(),
    stageCapKind: element(), stageCapText: element(),
    clamp: (v, a, b) => Math.min(b, Math.max(a, v)),
    smooth: t => t * t * (3 - 2 * t),
    requestAnimationFrame: fn => frames.push(fn),
    nearestStop: p => state.stopsPos.reduce((best, v, i, a) => Math.abs(v - p) < Math.abs(a[best] - p) ? i : best, 0),
  };
  vm.runInNewContext(motion, state);
  for (let tick = 1; tick <= 3; tick++) {
    frames.shift()(tick * 16);
    assert.equal(frames.length, 1, 'empty results must not stop the next frame');
  }
  state.STOPS = [1797, 2025].map(year => ({
    year, status: 'Ready', edition: String(year), cls: 'record',
    capKind: 'AI engraving', cap: 'generated live',
  }));
  state.stopsPos = state.STOPS.map(s => (s.year - 1770) / 255);
  state.panels = [element(), element()];
  state.stageItems = [element(), element()];
  state.pos = state.stopsPos[0];
  frames.shift()(64);
  assert.equal(state.yearOut.textContent, 1797);
  assert.equal(state.stageItems[0].style.opacity, 1);
  assert.equal(state.panels[1].style.visibility, 'hidden');
  state.pos = 1;
  frames.shift()(80);
  assert.equal(state.yearOut.textContent, 2025);
  assert.equal(state.stageItems[1].style.opacity, 1);
  assert.equal(state.panels[0].style.visibility, 'hidden');
  // At an intermediate position illustrations can blend; text must stay singular.
  state.pos = (state.stopsPos[0] + 1) / 2;
  state.render();
  assert.equal(state.panels.filter(p => p.style.visibility === 'visible').length, 1);
});
