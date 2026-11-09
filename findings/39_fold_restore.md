# Finding 39: Fold-and-Restore Compaction (billion-context)

## Sources

- billion-context: <https://x.com/RoundtableSpace/status/2119554368580223071>
- <https://x.com/krip_tom/status/2119715174156239237>
- Repo: <https://github.com/ranxianglei/billion-context>
- Paper: model-driven-incremental-hierarchical-compression (in repo)

## Repo Status

The repo is real, has 775+ files, a TypeScript build system, and 100+ test
files. However:
- It's an API proxy that intercepts Claude/Codex calls — requires API keys
  and a running model to test meaningfully.
- `npm test` hangs (likely needs a running proxy or mock server).
- The paper's claims (94.2% cache hit rate, 70x fold ratio, months-long
  sessions) are the authors' own production measurements, **not independently
  verified**.

## Idea

Keep the recent window (~50K tokens) raw. Fold finished subtasks into
restorable summaries placed at the head of the conversation. Key properties:
- **Incremental:** only the newly consumed slice is folded, not the whole
  history.
- **Reversible:** any folded block can be decompressed back to full text.
- **Cache-friendly:** folds deactivate suffix ranges without touching the
  prefix, so the prompt cache stays warm.

Contrast with hard compaction (summarize-and-discard): hard compaction
invalidates the entire cache prefix and loses detail permanently.

## Experiment Design

**What can be tested:** Build a minimal fold-and-restore prototype in Python.
Compare tokens and information retention against hard compaction over a
simulated multi-task session.

**What requires the full billion-context proxy:** Actual cache-hit rate
measurements, real model interactions, production session data.
