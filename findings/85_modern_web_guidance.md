# Finding 85: Load Modern Web Guidance for Web Tasks

## Source

<https://x.com/0xpipimd/status/2125918742572052788>

Google's Modern Web Guidance (GoogleChrome/modern-web-guidance): curated web
skills for coding agents. Their eval (229 tasks, Playwright graders) reports
Claude Code (Opus 5.5) going from 54% → 94% (+40pp) with guidance loaded.

## Experiment Status: COULD NOT RUN (eval)

No Claude Code CLI, no API keys, no Playwright test infrastructure. The eval
requires running a real coding agent on web apps and grading with Playwright.

**What was done:** Fetched the repo, measured the guidance content's token
footprint, documented loading conditions. The 54%→94% claim is Google's own
published result, NOT verified by this lab.
