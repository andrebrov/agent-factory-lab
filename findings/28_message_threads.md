# Finding 28: Anthropic Message Threads Beta

## Source

<https://x.com/BretKerr/status/2117730735637282840>

## Official Documentation

- Docs: <https://platform.claude.com/docs/en/build-with-claude/message-threads>
- Blog: <https://claude.com/resources/articles/message-threads>
- Release notes: November 2, 2026
- Beta header: `message-threads-2026-08-12`

## Idea

Message threads keep a conversation on the server so you don't re-upload
the full history on every turn. After the first (create) request, subsequent
turns send only new messages plus the previous response ID.

Key properties:
- **~35% lower median TTFT** on 500K–1M-token requests (Anthropic's claim)
- **Same token usage** — Claude still reads the full conversation
- **Same cost** — this is a latency optimization, not a cost optimization
- **5-minute expiry** — threads expire after 5 min of inactivity, then the
  client replays the full conversation in a new create request
- **Append-only** — can't edit earlier messages; branch by starting a new thread

## Proposal for Gwaihir

1. Enable message threads for all long-running agent sessions.
2. Combined with prompt caching (Finding 4), threads reduce both TTFT
   (threads handle upload/validation) and input cost (caching handles
   model processing).
3. Implement the 5-minute keepalive or the SDK's automatic replay fallback.

## Experiment Design

**What can be tested:** A simulation of the payload-size reduction over a
multi-turn session (real tiktoken token counts on payloads with and without
threads).

**What requires an API key:** Actual TTFT measurement with the
`message-threads-2026-08-12` beta header.
