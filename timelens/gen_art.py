"""Generate TimeLens timeline illustrations with the BFL FLUX API.

Reads the key from BFL_API_KEY (or .env), POSTs to api.bfl.ai, polls until
Ready, and saves PNGs into timelens/assets/ with a prompt manifest.
Generated art is an illustration aid, never presented as historical imagery.
"""

import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "assets"
API = "https://api.bfl.ai"

ENV = pathlib.Path(__file__).resolve().parents[1] / ".env"
KEY = os.environ.get("BFL_API_KEY", "")
if not KEY and ENV.is_file():
    for line in ENV.read_text().splitlines():
        if line.startswith("BFL_API_KEY="):
            KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
if not KEY:
    raise SystemExit("Set BFL_API_KEY in .env or the environment.")

STYLE = (
    "Late-18th-century copperplate encyclopedia engraving style: fine burin "
    "hatching, sepia ink on warm ivory paper, subtle plate wear, museum "
    "archive feel. Elegant, restrained, historically suggestive but clearly "
    "an engraved illustration. No text, no lettering, no captions, no UI."
)

JOBS = [
    {
        "name": "hero",
        "endpoint": "flux-3-image",
        "prompt": (
            "16:9 landscape, extremely minimal surreal illustration of a tiny "
            "glowing brass hand-lens hovering alone near the lower third of an "
            "enormous deep midnight-indigo landscape, the lens casting a small "
            "warm pool of golden candlelight onto an open antique encyclopedia "
            "page resting on a dark hill below it, almost the entire frame is "
            "empty deep blue-black night sky, one extremely soft hill silhouette "
            "along the bottom edge, tiny scattered stars barely visible, subtle "
            "atmospheric haze, dense fine film grain and speckled analog "
            "texture, muted dreamy colors, lonely peaceful mood, strange scale "
            "relationship, experimental editorial. No text, no lettering, no UI."
        ),
    },
    {
        "name": "war",
        "endpoint": "flux-3-image",
        "prompt": (
            STYLE + " Scene: two natural philosophers in 1790s dress arguing "
            "over a large sketch of hexagonal basalt columns pinned to a "
            "table. Behind the scholar on the left, engraved storm waves and "
            "a primordial ocean recede; behind the scholar on the right, a "
            "small erupting volcano glows. Dramatic chiaroscuro, single "
            "wide composition, both figures in profile dispute."
        ),
    },
    {
        "name": "verdict",
        "endpoint": "flux-3-image",
        "prompt": (
            STYLE + " Scene: the interior of Fingal's Cave on Staffa — "
            "towering hexagonal basalt columns rendered in dense engraved "
            "hatching, sea water entering at the cave mouth, a tiny rowboat "
            "with two figures for scale, a faint volcanic glow deep in the "
            "cavern suggesting fiery origin. Wide composition."
        ),
    },
    {
        "name": "today",
        "endpoint": "flux-3-image",
        "prompt": (
            "Photoreal wide photograph of the Giant's Causeway at golden "
            "hour: interlocking hexagonal basalt columns stepping into the "
            "sea, low warm light raking across the stone tops, gentle surf, "
            "a few distant visitors for scale, natural color, high detail, "
            "no text or watermark."
        ),
    },
    {
        "name": "rumford-then",
        "endpoint": "flux-3-image",
        "prompt": (
            STYLE + " Scene: inside a Munich arsenal workshop in 1798 — "
            "workmen boring a large brass cannon barrel mounted on a "
            "wooden frame, the blunt borer driven by horse gearing, metal "
            "curls flying, the barrel glowing warm where friction acts; a "
            "gentleman observer in a long coat watches the brass cannon "
            "half-submerged in a water trough. Wide composition, workshop "
            "atmosphere."
        ),
    },
    {
        "name": "rumford-now",
        "endpoint": "flux-3-image",
        "prompt": (
            "Clean modern scientific visualization on an ivory background: "
            "a cross-section of a copper cylinder being bored, the metal "
            "atoms rendered as small vibrating spheres glowing warm at the "
            "boring interface, motion lines radiating outward as heat, "
            "minimal editorial physics-illustration aesthetic, warm copper "
            "and charcoal palette. No text, no labels, no arrows, no UI."
        ),
    },
    {
        "name": "electricity-now",
        "endpoint": "flux-3-image",
        "prompt": (
            "Photoreal macro photograph of a crackling electric arc leaping "
            "between two brass electrodes on a dark laboratory bench, "
            "violet-blue plasma streamers and fine branching filaments, "
            "deep shadows, warm rim light on the brass, high detail, "
            "moody museum-dark background. No text, no watermark."
        ),
    },
    {
        "name": "cloud-now",
        "endpoint": "flux-3-image",
        "prompt": (
            "Photoreal aerial photograph above a field of towering white "
            "cumulus clouds at late afternoon, sunlit crowns with soft "
            "warm light, deep blue atmosphere at the horizon, high detail, "
            "natural color. No text, no watermark."
        ),
    },
    {
        "name": "chlamys-now",
        "endpoint": "flux-3-image",
        "prompt": (
            "Photoreal museum-still photograph of a single fan-shaped "
            "scallop shell (living bivalve) resting on dark charcoal "
            "velvet, ridged surface catching a soft warm side light, "
            "shallow depth of field, high detail, quiet archival mood. "
            "No text, no watermark."
        ),
    },
    {
        "name": "chocolate-now",
        "endpoint": "flux-3-image",
        "prompt": (
            "Photoreal close photograph of broken dark chocolate pieces "
            "with visible snap texture and a few cacao nibs scattered on "
            "dark slate, warm side lighting, rich browns against deep "
            "shadow, high detail, editorial food photography. "
            "No text, no watermark."
        ),
    },
]


def request(url, data=None, auth=True):
    headers = {"Accept": "application/json"}
    if auth:
        headers["x-key"] = KEY
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), r.headers.get("Content-Type", "")


def main():
    OUT.mkdir(exist_ok=True)
    only = set(sys.argv[1:])
    manifest = []
    for job in JOBS:
        if only and job["name"] not in only:
            continue
        payload = {
            "prompt": job["prompt"],
            "aspect_ratio": "16:9",
            "resolution": "1k",
        }
        result_raw, _ = request(f"{API}/v1/{job['endpoint']}", payload)
        result = json.loads(result_raw)
        job_id = result.get("id")
        print(f"{job['name']}: submitted id={job_id} cost={result.get('cost')}", flush=True)
        for _ in range(120):
            time.sleep(2)
            status_raw, _ = request(result["polling_url"])
            status = json.loads(status_raw)
            state = status.get("status")
            if state == "Ready":
                url = status["result"]["sample"]
                content, ctype = request(url, auth=False)
                ext = ".png" if "png" in ctype else ".jpg"
                path = OUT / (job["name"] + ext)
                path.write_bytes(content)
                print(f"{job['name']}: saved {path.name} ({len(content)} bytes)", flush=True)
                manifest.append({
                    "name": job["name"], "endpoint": job["endpoint"],
                    "file": path.name, "id": job_id,
                    "prompt": job["prompt"], "cost": result.get("cost"),
                })
                break
            if state in {"Error", "Failed", "Request Moderated", "Content Moderated"}:
                raise RuntimeError(f"{job['name']} ended: {state}")
        else:
            print(f"{job['name']}: poll timeout id={job_id}", flush=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("manifest written")


if __name__ == "__main__":
    main()
