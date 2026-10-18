import { NextResponse } from 'next/server';

// Server-side BFL generation for live exhibits. Prompts arrive already
// art-directed by Super VL in /api/lens; this route just runs FLUX.
export const maxDuration = 120;

const BFL = 'https://api.bfl.ai';
const BFL_KEY = process.env.BFL_API_KEY || '';

async function generate(prompt) {
  const sub = await fetch(`${BFL}/v1/flux-3-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-key': BFL_KEY },
    body: JSON.stringify({ prompt, aspect_ratio: '16:9', resolution: '1k' }),
  });
  const sd = await sub.json();
  if (!sd.polling_url) return null;
  for (let i = 0; i < 50; i++) {
    await new Promise((r) => setTimeout(r, 2000));
    const st = await fetch(sd.polling_url).then((r) => r.json());
    if (st.status === 'Ready') return st.result?.sample || null;
    if (['Error', 'Failed', 'Request Moderated', 'Content Moderated'].includes(st.status)) return null;
  }
  return null;
}

export async function POST(req) {
  if (!BFL_KEY) return NextResponse.json({ error: 'no_bfl_key' }, { status: 501 });
  const { prompts } = await req.json().catch(() => ({}));
  const jobs = (prompts || []).filter((p) => p && p.prompt).slice(0, 5);
  const art = await Promise.all(
    jobs.map(async (j) => ({ role: j.role, url: await generate(j.prompt).catch(() => null) }))
  );
  return NextResponse.json({ art });
}
