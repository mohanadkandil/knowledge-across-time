# Real Hermes baseline

`kat.hermes_bridge.run_hermes` runs **NousResearch's real `AIAgent` conversation loop**, using the supplied model, endpoint and key. It does not replace missing Hermes with a home-grown or alternative framework agent. An unavailable installation returns `error.code=hermes_unavailable` and an empty answer.

## Pinned upstream and runtime

Inspected pin: **`354ad3d48786f2978c49be88f28c13d78fa0b6e0`**, upstream commit dated 2026-10-18. Hermes package version at this pin is `0.0.0`; the commit is the useful version identifier. Source: [AIAgent](https://github.com/NousResearch/hermes-agent/blob/354ad3d48786f2978c49be88f28c13d78fa0b6e0/run_agent.py), [registry](https://github.com/NousResearch/hermes-agent/blob/354ad3d48786f2978c49be88f28c13d78fa0b6e0/tools/registry.py), [dependency manifest](https://github.com/NousResearch/hermes-agent/blob/354ad3d48786f2978c49be88f28c13d78fa0b6e0/pyproject.toml).

The current upstream runtime expects Python **3.14**; its dependency declarations are conditional on Python >=3.14. Installing it under the application's Python3.12 can leave required dependencies uninstalled. Use a separate interpreter. From the project root:

```sh
git clone https://github.com/NousResearch/hermes-agent.git .vendor/hermes-agent
git -C .vendor/hermes-agent checkout 354ad3d48786f2978c49be88f28c13d78fa0b6e0
uv venv --python 3.14 .venv-hermes
uv pip install --python .venv-hermes/bin/python -e .vendor/hermes-agent
export HERMES_REPO_PATH="$PWD/.vendor/hermes-agent"
export HERMES_PYTHON="$PWD/.venv-hermes/bin/python"
```

No terminal, browser, MCP, vector-store or other provider extras are required. The exact direct dependency pins live in the pinned upstream manifest; use upstream's committed `uv.lock` with `uv sync --frozen --no-dev` for its fully locked environment, then point `HERMES_PYTHON` to that environment. The editable-install command above was used for the isolated adapter smoke test. Do not commit `.vendor`, virtual environments or credentials.

An already installed, compatible Hermes is also supported: omit `HERMES_REPO_PATH` and point `HERMES_PYTHON` at its interpreter. Its package version is returned, with an unknown commit. A git checkout with a different HEAD is explicitly rejected to prevent silently drifting APIs.

## Interface

```python
result = run_hermes(
    question,
    model=required_token_factory_model,
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=provider_api_key,
    search=lambda query, limit=6: corpus.search(query, limit),
    read=lambda source_id: corpus.read(source_id),
    compare=lambda page: corpus.compare(page),
    max_iterations=12,
)
```

The callbacks run synchronously **in the parent app** and return JSON-compatible objects. Their keyword arguments are part of the contract:

- `search(query: str, limit: int = 6)` corresponds to `search_sources`.
- `read(source_id: str)` corresponds to `read_source`.
- `compare(page: str)` corresponds to `compare_page`.

Wrap existing corpus functions in lambdas if they use different parameter names. The bridge cannot access arbitrary paths or URLs through a tool schema; callbacks must retain their own source-ID validation and local-corpus boundary.

Result keys: `answer`, `messages`, `tool_trace`, `model`, `framework="hermes"`, `framework_version`, `framework_commit`, `api_calls`, `completed`. Each trace entry records the actual callback name, arguments, result, status and duration. Structured errors contain `error={code,message}`; the caller should show an unavailable/failed baseline rather than score the empty answer as a valid completed run. The returned messages are Hermes's actual conversation, not a reconstructed transcript. No chain-of-thought needs to be rendered in the UI.

## Tool isolation and concurrency

Each run launches a separate Python subprocess with a temporary `HERMES_HOME` and runtime directory. This isolates Hermes's module caches/global tool registry, profile, memory, plugin configuration and persistence from concurrent baseline runs and the user's personal profile. The subprocess uses the real upstream registry signature `register(name, toolset, schema, handler, ...)`; handlers accept an arguments dictionary and return JSON strings.

Only the three source schemas are exposed. Both the initial tool surface and subsequent schema refreshes are restricted; the generic tool-dispatch entry point is also restricted to the same names. Upstream's framework remains responsible for model calls and its conversation loop. A worker lock pairs tool requests/replies even when Hermes dispatches multiple tool calls concurrently. No fallback model or provider is configured.

This is an application capability boundary, not an operating-system sandbox for untrusted Python dependencies. The Hermes runtime is trusted code. The bridge never asks it to run terminal/browser tools. Provider credentials travel over stdin, not process arguments; known provider keys and credential fields are removed from returned traces/messages/errors. Worker stderr is captured temporarily and is not returned to clients. Framework memory, background review, context-file loading and trajectory saving are disabled.

The parent has a240-second worker deadline; Hermes has a180-second turn budget and at most12 tool iterations by default. Source callbacks should have their own timeouts because a blocking Python callback runs in the parent. The bridge kills an unfinished worker when returning.

## What still needs a live credential check

The adapter supports any actual supplied OpenAI-compatible model; it does not assert that a particular Token Factory account has access. Validate the required model's exact catalog ID, tool calling and endpoint availability with the real hackathon key. Integration against a local fake provider verifies framework wiring and callback transport, not the remote model's quality or access.

This upstream commit enforces a minimum64K model context window. A local fake provider advertising32K was rejected during initialization; advertising131K passed. Use a genuinely supported model context rather than overriding metadata to defeat that check.

Verified locally on2026-10-18: real Hermes import/registration and its conversation loop against a local OpenAI-compatible fake provider, running search→read→compare→cited answer across four provider requests. Assertions checked the exact supplied model on every request, exactly the three permitted tool schemas on every request, all three actual callback traces, and absence of the fake API key in the returned JSON. The adapter also passes Python3.12 compilation; Hermes worker used CPython3.14.7. The temporary test fixture is `/tmp/kat-test-hermes.py`; it is intentionally outside the application's corpus and runtime.
