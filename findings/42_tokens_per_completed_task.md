# Finding 42: Tokens per Completed Task — The Right Metric + Efficiency Stack

## Sources

- <https://x.com/Phantomstone2/status/2120040685529354494>
- <https://x.com/CodetocashAi/status/2120061472151667028>

## Idea

Measure **tokens per successfully completed task** — not tokens per request or
per session — as the primary efficiency metric. Pair it with an efficiency
stack:

1. **Content-hash file-read cache:** Don't re-read a file whose content hash
   hasn't changed since the last read.
2. **Step checkpointing:** On failure/retry, resume from the last completed
   step (like Finding 25) instead of re-running everything.
3. **Stable cacheable prompt prefix:** Keep the system prompt static so the
   LLM's prompt cache works (like Finding 34).

Combined, these make retries cheap and the metric (tokens/completed task)
stays low even under failures.

## Proposal for Gwaihir / Landroval

1. Track tokens/completed-task as the primary cost metric.
2. Before every file read, check a content-hash cache; skip reads for
   unchanged files.
3. On retry, resume from the step-log checkpoint.
4. Keep the prompt prefix stable (no timestamps/UUIDs).

## Experiment Design

**What can be tested:** Measure tokens/completed task with and without the
efficiency stack, including under injected failures.

**Real token counting (tiktoken) + real file hashing.**
