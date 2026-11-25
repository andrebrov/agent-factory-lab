# Finding 82: Clean Untrusted Text + AGENTS.md Enforcement Hook

## Idea

Strip invisible Unicode and hidden HTML from issue/PR/README text before
an agent reads it. Log what was removed. Add a hook enforcing a small set
of deterministic AGENTS.md rules.

## Experiment Design

Sanitizer tested on a held-out corpus (visible text, invisible Unicode,
mixed). The hook enforces predefined rules (forbidden paths, banned
commands, required test count) on held-out diffs.

**Both are deterministic text-processing/rule checks, not models.
Limitation: fully visible malicious instructions pass the sanitizer.**
