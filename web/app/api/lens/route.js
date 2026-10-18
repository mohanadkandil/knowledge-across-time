import { NextResponse } from 'next/server';
import fs from 'node:fs';
import path from 'node:path';
import { ART_STYLE } from '../art-direction.mjs';

export const runtime = 'nodejs';
export const maxDuration = 60;

const LENS_API_URL = process.env.LENS_API_URL || 'https://surf-ties-christopher-mortgage.trycloudflare.com';
const WIKI_API_URL = process.env.WIKIPEDIA_API_URL || 'https://port8000-rks0xavparpzq59.tunnel.applications.uk-south2.nebius.cloud';
const TF_BASE_URL = process.env.TOKEN_FACTORY_BASE_URL || 'https://api.tokenfactory.nebius.com/v1';
const TF_KEY = process.env.TOKEN_FACTORY_API_KEY || '';
const EMBED_MODEL = 'nvidia/llama-nemotron-embed-vl-1b-v2';
const RERANK_MODEL = 'nvidia/llama-nemotron-rerank-vl-1b-v2';
const SUPER_MODEL = process.env.SUPER_MODEL || 'nvidia/Nemotron-3.5-Super-VL';

const EDITION_YEAR = [
  [/first/i, 1771], [/second/i, 1778], [/third|3rd|suppl/i, 1797],
  [/fourth/i, 1810], [/fifth/i, 1817], [/sixth/i, 1823], [/seventh/i, 1842], [/eighth/i, 1860],
];

let _index = null;
async function loadIndex(origin) {
  if (_index) return _index;
  const dir = path.join(process.cwd(), 'public/data');
  let meta, bytes;
  try {
    meta = JSON.parse(fs.readFileSync(path.join(dir, 'index.json'), 'utf8'));
    const bin = fs.readFileSync(path.join(dir, 'index.i8'));
    bytes = new Uint8Array(bin.buffer, bin.byteOffset, bin.length);
  } catch {
    const [m, b] = await Promise.all([
      fetch(`${origin}/data/index.json`).then((r) => r.json()),
      fetch(`${origin}/data/index.i8`).then((r) => r.arrayBuffer()),
    ]);
    meta = m; bytes = new Uint8Array(b);
  }
  const i8 = new Int8Array(bytes.buffer, bytes.byteOffset, bytes.length);
  const vectors = [];
  for (let i = 0; i < meta.n; i++) vectors.push(i8.subarray(i * meta.dims, (i + 1) * meta.dims));
  _index = { meta, vectors };
  return _index;
}

async function cosineTopK(qvec, k, origin) {
  const { meta, vectors } = await loadIndex(origin);
  const scores = new Float32Array(meta.n);
  for (let i = 0; i < meta.n; i++) {
    const v = vectors[i];
    let s = 0;
    for (let j = 0; j < qvec.length; j++) s += qvec[j] * v[j];
    scores[i] = s; // row scale is a positive constant per row — ranking preserved
  }
  const order = [...scores.keys()].sort((a, b) => scores[b] - scores[a]).slice(0, k);
  return order.map((i) => ({ i, score: scores[i], row: meta.rows[i] }));
}

async function jpost(url, body, headers = {}, ms = 25000) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(ms),
  });
  if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
  return res.json();
}

function parseFirstJson(raw) {
  const start = (raw || '').indexOf('{');
  if (start < 0) return null;
  let depth = 0, inStr = false, esc = false;
  for (let i = start; i < raw.length; i++) {
    const c = raw[i];
    if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; continue; }
    if (c === '"') inStr = true;
    else if (c === '{') depth++;
    else if (c === '}') { if (--depth === 0) { try { return JSON.parse(raw.slice(start, i + 1)); } catch { return null; } } }
  }
  return null;
}

const pageIdOf = (sourceId) => sourceId.split(':')[0];
const editionYear = (title) => {
  for (const [re, y] of EDITION_YEAR) if (re.test(title || '')) return y;
  return 1823;
};
const headword = (text) => {
  const m = (text || '').match(/^[\s*_]*([A-Z][A-Z' -]{2,40})[.,]/);
  return m ? m[1].trim() : null;
};

export async function GET(request) {
  const enc = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const send = (o) => controller.enqueue(enc.encode(JSON.stringify(o) + '\n'));
      try {
        const data = await run(request, send);
        send(data ? { done: true, data } : { error: 'no_match' });
      } catch (e) {
        send({ error: String(e.message || e) });
      }
      controller.close();
    },
  });
  return new Response(stream, {
    headers: { 'Content-Type': 'application/x-ndjson', 'Cache-Control': 'no-store' },
  });
}

async function run(request, send) {
  const topic = (new URL(request.url).searchParams.get('topic') || '').trim();
  if (!topic || topic.length > 120) throw new Error('topic_required');

  const trace = { steps: [] };
  const t = (name, extra = {}) => { trace.steps.push({ name, ...extra }); send({ step: name, ...extra }); };

  // 1. Wikipedia — modern side. Real REST summary first (canonical article),
  //    organizer shared BM25 corpus as fallback.
  send({ step: 'start', topic });
  let wiki = null;
  try {
    const r = await fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topic.replace(/ /g, '_'))}`,
      { signal: AbortSignal.timeout(10000), headers: { Accept: 'application/json' } }
    );
    if (r.ok) {
      const j = await r.json();
      if (j.title && j.extract && j.type !== 'disambiguation') {
        wiki = { title: j.title, url: j.content_urls?.desktop?.page, excerpt: j.extract, source: 'wikipedia.org' };
      }
    }
  } catch {}
  if (!wiki) try {
    const s = await jpost(`${WIKI_API_URL}/v1/search`, { query: topic, top_k: 8, excerpt_chars: 1000 });
    const hits = s.hits || [];
    const bad = /disambiguation|^(lists?|outline|index|glossary) of|\bdeity\b|mytholog|religion/i;
    wiki = hits.find((h) => h.title?.toLowerCase() === topic.toLowerCase() && !bad.test(h.title || ''))
        || hits.find((h) => h.title?.toLowerCase().split(/[(—–]/)[0].trim() === topic.toLowerCase() && !bad.test(h.title || ''))
        || hits.find((h) => !bad.test(h.title || ''))
        || hits[0] || null;
    if (wiki) wiki.source = 'shared-corpus';
  } catch (e) { t('wikipedia_error', { message: String(e.message) }); }
  t('wikipedia', { title: wiki?.title, source: wiki?.source });

  // 2. Embed VL query (Nebius GPU VM via public tunnel)
  const queryText = wiki ? `${wiki.title}. ${wiki.excerpt.slice(0, 700)}` : topic;
  const emb = await jpost(`${LENS_API_URL}/v1/embeddings`, {
    model: EMBED_MODEL, input: [queryText.slice(0, 2000)], input_type: 'query',
  }, {}, 30000);
  const qvec = emb?.data?.[0]?.embedding;
  if (!qvec || qvec.length !== 2048) throw new Error('embedder returned no vector');
  t('embed', { model: EMBED_MODEL });

  // 3. LanceDB-exported evidence vectors — nearest Britannica regions only
  const origin = new URL(request.url).origin;
  const top = await cosineTopK(qvec, 400, origin);
  const perPage = new Map();
  for (const c of top) {
    if (!c.row.id.startsWith('bri-')) continue;
    const pid = pageIdOf(c.row.id);
    if (!perPage.has(pid)) perPage.set(pid, c);
    if (perPage.size >= 12) break;
  }
  const cands = [...perPage.values()];
  t('lance_candidates', { pages: cands.map((c) => pageIdOf(c.row.id)) });

  // 4. Rerank VL — the pinned reranker scores the candidates
  const rer = await jpost(`${LENS_API_URL}/v1/rerank`, {
    model: RERANK_MODEL, query: `${topic}: ${wiki ? wiki.title : ''}`.slice(0, 1990),
    documents: cands.map((c) => c.row.text.slice(0, 1800)), top_n: 6,
  }, {}, 30000);
  const ranked = (rer.results || []).map((r) => ({ ...cands[r.index], rerank: r.relevance_score }));
  const best = ranked[0];
  if (!best) return null;
  const pageId = pageIdOf(best.row.id);
  t('rerank', { model: RERANK_MODEL, top: pageId, score: best.rerank });

  // 5. Super VL (Token Factory) — grounded then/now reading
  let exhibit = null;
  if (TF_KEY) {
    try {
      const sys = `You are TimeLens, comparing a historical encyclopedia page with modern knowledge. Reply with ONLY compact JSON, no markdown: {"then_line": one short sentence of what the old page claims, "now_line": one short sentence of the modern position, "quote": one VERBATIM phrase (max 18 words) copied from the OLD PAGE TEXT, "verdict": one of settled|superseded|diverged|open, "note": max 12 words on what changed, "shots": [ {"role": "then", "prompt": scene description}, {"role": "now", "prompt": scene description} ]}.
Art direction: exactly two coordinated illustrations, both in this SAME visual language: ${ART_STYLE}
Design the pair together. Repeat the same subject, viewpoint, framing, subject scale and placement in both self-contained scene descriptions. Change only the evidence-supported understanding of the subject, not the artistic medium. Never switch the modern image to photography.
Then depicts what the OLD PAGE actually describes; now depicts what the MODERN ARTICLE supports. Do not invent a visual difference when the sources agree. Choose a concrete specimen, apparatus or observable phenomenon; do not use unrelated props or historical costumes as filler.
For invisible mechanisms, explicitly describe a schematic illustration rather than pretending particles or fields can be photographed. Do not turn a fluid theory into literal liquid or invent glowing wires, decorative lightning or impossible apparatus. Each scene must explain the comparison through a small number of clear visual details, not just illustrate the topic generically. No text or labels in either image.`;
      const user = `TOPIC: ${topic}\n\nOLD PAGE TEXT (historical, possibly OCR-noisy):\n${best.row.text.slice(0, 2400)}\n\nMODERN ARTICLE EXCERPT (${wiki ? wiki.title : 'unknown'}):\n${(wiki?.excerpt || '').slice(0, 1200)}`;
      const r = await jpost(`${TF_BASE_URL}/chat/completions`, {
        model: SUPER_MODEL, temperature: 0.2, max_tokens: 3000,
        messages: [{ role: 'system', content: sys }, { role: 'user', content: user }],
      }, { Authorization: `Bearer ${TF_KEY}` }, 45000);
      const msg = r.choices?.[0]?.message || {};
      let raw = msg.content || '';
      if (!raw.trim() && typeof msg.reasoning_content === 'string') {
        const rm = msg.reasoning_content.match(/\{[\s\S]*\}/);
        raw = rm ? rm[0] : '';
      }
      exhibit = parseFirstJson(raw);
      t('super_vl', { model: SUPER_MODEL, ok: !!exhibit, raw: raw.slice(0, 240), finish: r.choices?.[0]?.finish_reason });
    } catch (e) { t('super_vl_error', { message: String(e.message) }); }
  }

  return {
    topic,
    wiki: wiki && { title: wiki.title, url: wiki.url, excerpt: wiki.excerpt },
    page: {
      id: pageId,
      scan: `/scans/${pageId}.jpg`,
      edition: best.row.text.match(/first|second|third|fourth|fifth|sixth|seventh|eighth/i)?.[0] || null,
      editionYear: editionYear(best.row.text),
      headword: headword(best.row.text),
      sourceId: best.row.id,
    },
    match: { rerankScore: best.rerank, candidates: ranked.slice(0, 5).map((r) => ({ page: pageIdOf(r.row.id), score: r.rerank })) },
    thenText: best.row.text.slice(0, 1500),
    exhibit,
    art: Array.isArray(exhibit?.shots) ? exhibit.shots.slice(0, 2) : [],
    trace,
  };
}
