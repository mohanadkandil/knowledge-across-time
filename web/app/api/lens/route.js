import { NextResponse } from 'next/server';
import fs from 'node:fs';
import path from 'node:path';

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
function loadIndex() {
  if (_index) return _index;
  const dir = path.join(process.cwd(), 'app/data');
  const meta = JSON.parse(fs.readFileSync(path.join(dir, 'index.json'), 'utf8'));
  const bin = fs.readFileSync(path.join(dir, 'index.i8'));
  const i8 = new Int8Array(bin.buffer, bin.byteOffset, bin.length);
  const vectors = [];
  for (let i = 0; i < meta.n; i++) vectors.push(i8.subarray(i * meta.dims, (i + 1) * meta.dims));
  _index = { meta, vectors };
  return _index;
}

function cosineTopK(qvec, k) {
  const { meta, vectors } = loadIndex();
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
  const topic = (new URL(request.url).searchParams.get('topic') || '').trim();
  if (!topic || topic.length > 120) return NextResponse.json({ error: 'topic_required' }, { status: 400 });

  const trace = { steps: [] };
  const t = (name, extra = {}) => trace.steps.push({ name, ...extra });

  // 1. Wikipedia (organizer shared BM25 service) — modern side
  let wiki = null;
  try {
    const s = await jpost(`${WIKI_API_URL}/v1/search`, { query: topic, top_k: 5, excerpt_chars: 1000 });
    const hits = s.hits || [];
    wiki = hits.find((h) => h.title?.toLowerCase() === topic.toLowerCase())
        || hits.find((h) => !/^(lists?|outline|index|glossary) of/i.test(h.title || '') && !/disambiguation/i.test(h.title || ''))
        || hits[0] || null;
    t('wikipedia', { title: wiki?.title, page_id: wiki?.page_id });
  } catch (e) { t('wikipedia_error', { message: String(e.message) }); }

  // 2. Embed VL query (Nebius GPU VM via public tunnel)
  const queryText = wiki ? `${wiki.title}. ${wiki.excerpt.slice(0, 700)}` : topic;
  const emb = await jpost(`${LENS_API_URL}/v1/embeddings`, {
    model: EMBED_MODEL, input: [queryText.slice(0, 2000)], input_type: 'query',
  }, {}, 30000);
  const qvec = emb?.data?.[0]?.embedding;
  if (!qvec || qvec.length !== 2048) throw new Error('embedder returned no vector');
  t('embed', { model: EMBED_MODEL });

  // 3. LanceDB-exported evidence vectors — nearest Britannica regions only
  const top = cosineTopK(qvec, 400);
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
  if (!best) return NextResponse.json({ error: 'no_match', trace }, { status: 404 });
  const pageId = pageIdOf(best.row.id);
  t('rerank', { model: RERANK_MODEL, top: pageId, score: best.rerank });

  // 5. Super VL (Token Factory) — grounded then/now reading
  let exhibit = null;
  if (TF_KEY) {
    try {
      const sys = 'You are TimeLens, comparing a historical encyclopedia page with modern knowledge. Reply with ONLY compact JSON, no markdown: {"then_line": one short sentence of what the old page claims, "now_line": one short sentence of the modern position, "quote": one VERBATIM phrase (max 18 words) copied from the OLD PAGE TEXT, "verdict": one of settled|superseded|diverged|open, "note": max 12 words on what changed, "shots": [ {"role": "then", "prompt": FLUX image prompt}, {"role": "then_detail", "prompt": ...}, {"role": "now", "prompt": ...}, {"role": "now_detail", "prompt": ...} ]}. Art direction rules for shots — depict the TOPIC itself: "then" shots are late-18th-century copperplate encyclopedia engravings, fine burin hatching, sepia ink on warm ivory paper, museum archive feel — show the object or phenomenon AS THE OLD PAGE UNDERSTOOD IT; "now" shots are clean modern photoreal or minimal editorial photographs — the same subject as understood today. Every prompt must be self-contained, visually specific, and contain no text, lettering, captions or UI.';
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
      const m = raw.match(/\{[\s\S]*\}/);
      exhibit = m ? JSON.parse(m[0]) : null;
      t('super_vl', { model: SUPER_MODEL, ok: !!exhibit, raw: raw.slice(0, 240), finish: r.choices?.[0]?.finish_reason });
    } catch (e) { t('super_vl_error', { message: String(e.message) }); }
  }

  return NextResponse.json({
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
    art: Array.isArray(exhibit?.shots) ? exhibit.shots.slice(0, 5) : [],
    trace,
  });
}
