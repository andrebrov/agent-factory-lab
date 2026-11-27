# Finding 87: Per-Pane Notes + Commit Trailers

## Sources

- <https://x.com/pradyum1916/status/2125982914110459937>
- <https://x.com/prathamesh2_/status/2125990476473913366>

## Idea

Each helper writes its own notes file. Only the lead merges verified facts
into the shared file. Every commit carries Agent/Prompt-Hash trailers.
Prevents one agent's wrong guess from spreading.

## Experiment Design

Test on real git commits: (a) wrong fact stays in helper notes, not shared;
(b) commits attributed by trailer; (c) shared-notes baseline leaks the
wrong fact.

**Real git operations. No live herdr session needed.**
