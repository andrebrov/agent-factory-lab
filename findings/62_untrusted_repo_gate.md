# Finding 62: Gate for Untrusted Repos — Injection Scanner + Credential Block

## Source

<https://x.com/yituihi/status/2123273058471330015>

## Idea

For repos not on an allowlist: auto-approve off, CLAUDE.md/AGENTS.md held
until they pass a scan or a human approves, and reads of .env / ~/.ssh
blocked. Extends exp 21 (booby-trap scanner) and exp 56 (harden the judge).

Attack vectors: HTML comments, zero-width/unicode tricks, base64-encoded
instructions, instructions disguised as normal setup steps.

## Experiment Design

Build attack samples SEPARATELY from the scanner (avoid overfitting).
Include clean repos with legitimate setup. Measure injections caught,
false holds, credential read blocks.

**Real execution: file scanning + git.**
