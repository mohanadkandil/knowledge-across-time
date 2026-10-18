# Test the baseline

## Open the current workspace

```sh
cd knowledge-across-time
uv sync --python 3.12 --extra dev --frozen
uv run kat serve
```

Open http://127.0.0.1:8130. If the server is already running, open that address directly.

1. Select row57 in the left list.
2. Inspect the original scan and extracted text. Click a region outline to jump to its extracted text. Coordinates and OCR are unreviewed.
3. Open the static archive and the compiled LaTeX PDF. The LaTeX source remains editable.
4. Inspect row1261. Its Parse failure is retained; the program does not invent a transcription for it.

Match, Compare and Ask require the remaining services. They stay unavailable until their settings are present. Placeholder answers are not supplied.

## Run the software checks

```sh
uv run pytest -q
uv run kat status
uv run kat doctor --live
```

The tests exercise actual local LanceDB and mocked service contracts. They do not establish model quality or count as agent cases. The doctor currently reports the missing Token Factory key and GPU retrieval service; that is expected until setup is complete.

## Enable one complete comparison

Put your Token Factory key in `SUPER_API_KEY` in the local `.env`. Deploy the official retrieval container on your Nebius GPU VM and forward its port to the laptop. Set:

```dotenv
RETRIEVAL_BASE_URL=http://127.0.0.1:8000/v1
```

Restart the local server after changing `.env`. Follow [setup.md](setup.md) for Hermes paths and the exact Docker recipe. Check the GPU service before running a comparison:

```sh
curl --fail http://127.0.0.1:8000/ready
uv run kat doctor --live --inference --page 57
uv run kat match 57
uv run kat compare 57
uv run kat ask "Which parts of this entry report observations and which parts are conjecture? Compare with the modern evidence." --page 57
```

Inspect the model calls, returned source IDs, exact quotes and final answer. A model quotation matching OCR still needs comparison with the original scan. The evaluation guide proposes six questions; none are claimed to have passed before a live run.

## Cover all pages and export

```sh
uv run kat batch --stage compare
uv run kat archive
uv run kat export --output submission.zip
```

The batch keeps every selected page and its failures. Review three successful and three clear failure cases from actual Hermes runs using the interface or `kat review`. Inspect `submission/checklist.json` in the export. The three-minute video is a separate deliverable.

The tracked `site/` directory is the initial static snapshot. To refresh it for a later submission, copy the newly generated `data/site/` into it and inspect the changed files before committing.
