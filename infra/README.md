# Retrieval service

`model-service/` is the organizer's unchanged Docker recipe from commit `88abda0d1882eb56a5cd78bc226f1fbc929cc33b` of https://github.com/october-18-hackathon/nemotron-agentic-ai-challenge . It serves the required pinned Embed VL and Rerank VL models. It does not contain model weights.

Build on the team's Linux amd64 GPU VM with at least 60 GB free build/cache space:

```sh
docker buildx build --platform linux/amd64 --load -t nemotron-challenge-models:local infra/model-service
```

Follow [the setup guide](../docs/setup.md) for runtime arguments, readiness and the real GPU smoke check. The transport tests in this directory use stubs; they do not prove GPU execution. Upstream MIT and model notices remain in the directory.
