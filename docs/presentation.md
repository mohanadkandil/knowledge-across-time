# Presentation plan: TimeLens

Deadline 18:30 CEST. Five-minute live presentation; three-minute submission video.

## The one-sentence story

Add `timelens.` before any Wikipedia URL and travel back 250 years — then watch
a second Nemotron catch the first one lying about history.

## Why basalt is the hero

Row 2376, Britannica 4th edition, MINERALOGY (scan-verified):

> "No subject, in geological speculation, has produced more controversial
> discussion than the origin of basalt; one party asserting that it is the
> effect of fire, while another contends that it must have been deposited from
> an aqueous solution."

This is the Neptunist–Vulcanist war (Werner vs. Hutton) recorded while it was
still unresolved. The page then admits: "Our limits preclude us even from
barely stating the arguments." An encyclopedia confessing uncertainty in 1810.

Same page, all verified on the scan:

- "Melts very easily before the blowpipe into an opaque black glass which
  acts on the magnet." — their experiment.
- "Many basalts affect the magnetic needle, reversing the poles" — iron.
- "The Giant's Causeway and the rocks about Fairhead… exhibit the finest and
  most extensive ranges of columnar basalt in the world." — the iconic visual
  is inside our own source.
- The very next entries are WACKEN and PHONOLITE — Wernerian Neptunist
  vocabulary, still in the dictionary while the war was being lost.

Today: basalt is the most common volcanic rock on Earth. Columnar jointing =
cooling lava cracking. Ocean floor is mostly basalt. Contested → settled.

## The cross-edition beat (verified live, run question-5906dc16)

The strongest timeline moment is inside our own corpus — same encyclopedia,
~30 years apart, the debate resolves itself:

- **4th ed., row 2376:** the fire/water controversy, unresolved.
- **7th ed., row 966:** tertiary-era rocks "principally trachytes and
  basalts… greatly analogous to, or identical with, products of active
  volcanoes." Britannica has moved on. The verdict is in, in its own pages.

Asked to name the debate's winner, the agent correctly reported the 4th
edition's refusal to settle, then cited the 7th edition's volcanic verdict
and the modern framing (Wikipedia "Scriptural geologist": Werner's primeval
ocean vs. Hutton's fire). It also disclosed that its quotes were cleaned
paraphrases of damaged OCR. The red-team bait became a showcase run.

## The twist (what the mentor praised)

The pipeline hallucinates too, and we documented it:

- **Anachronism injection:** the agent wrote "S. Becquerel" — a scientist
  born in 1852 — into a 1768 page. The real name: S. Beccaria. The AI did
  exactly what the encyclopedists did: filled a gap with the nearest
  plausible name. *Electric fluid was the 18th century's Becquerel.*
- **OCR-faithful, scan-false:** "a small quantity of alcohol" — faithful to
  the transcription; the scan says "olive-oil". Accuracy ≠ truth.
- **False verification:** a guessed correction ("electrified metal dish")
  presented as the verified reading of damaged text.
- **Wrong-sense match:** a CHOCOLATE page that is really about an
  electricity experiment — a matching name is not the same subject (the
  mentor's volcano/mountains case, but real and in our corpus).

Line for the close: "Every encyclopedia is a snapshot of what we were willing
to bet on. Our agent included. So we pointed Nemotron at Nemotron."

## Five-minute live arc

1. **0:00–0:40 — Hook.** Type `timelens.` before `wikipedia.org/wiki/Basalt`.
   The timeline appears. Say the one-sentence story. Do not explain the
   pipeline yet.
2. **0:40–2:00 — The controversy.** 1810 card: read the fire/water quote
   aloud. Point at the scan image (site/pages/bri-2376-*.html) — the words
   are really there. Giant's Causeway named on the same page.
3. **2:00–2:40 — Scrub the timeline.** Drag to today: "common igneous rock."
   One sentence on what changed: not the rock — the explanation.
4. **2:40–3:20 — Not a one-off.** Quick cuts: ELECTRICITY (invisible fluid →
   electrons, row 1776), CLOUD (uncertainty preserved, row 59), CHLAMYS
   (cloak ≠ scallop, row 57). Each one line.
5. **3:20–4:20 — The red team.** The Becquerel anachronism first (it's the
   best), then olive-oil/alcohol, then false verification. These are real
   runs, preserved, hashed, with the original scans next to them.
6. **4:20–5:00 — Pipeline + close.** One diagram: Parse 3.5 → Embed VL →
   Rerank VL (RTX PRO 6000) → Super VL agent → challenger probes. 100 pages,
   every claim cited, failures left visible on purpose. Close on the
   snapshot line.

## Three-minute video shot list

| Time | Shot | Audio |
| --- | --- | --- |
| 0:00–0:15 | Hands typing `timelens.` + wikipedia URL, page resolves to timeline | "One word before any Wikipedia link sends you back 250 years." |
| 0:15–0:45 | Basalt timeline scrub: 1810 card ↔ today card; zoom the scan region | "In 1810 the encyclopedia couldn't decide if rock was born of fire or water." |
| 0:45–1:10 | Giant's Causeway photo/scan detail; blowpipe + needle quotes | "The same page shows their experiments — and admits its limits." |
| 1:10–1:40 | Fast cuts: electricity, cloud, chlamys exhibits in the archive UI | "It works on any topic we index — every claim cites both sources." |
| 1:40–2:20 | Failure cards: Becquerel/Beccaria side-by-side, olive-oil/alcohol, electrified dish | "Then we turned the model on itself. It put a scientist born in 1852 into a 1768 page." |
| 2:20–2:45 | Pipeline diagram, /ready output, casebook page | "Parse, embed, rerank on a Blackwell GPU; every run preserved with its sources." |
| 2:45–3:00 | Back to the timeline, scrub slowly to today | "Knowledge isn't a list of facts. It's a trail of bets. We made the trail visible — and audited it." |

## Demo fallback

If the tunnel or GPU drops during the live demo: the static archive
(`python3 -m http.server 8131 --directory site`) and the timelens page work
offline; the preserved run JSONs in evidence/live-agent-cases prove the live
runs. Say so on camera; an outage is not a hallucination case.
