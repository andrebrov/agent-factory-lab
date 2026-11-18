# Finding 60: Watcher Pane as Done-Gate + Tab Resume

## Sources

- <https://x.com/tilakmadichetti/status/2123004900993118471>
- <https://x.com/thrawn01/status/2122689273514098828>

## Idea

(a) Before marking done, read the recent output of a dev-server or test-
watcher pane. Fail on new errors or stack traces. Include tricky edge cases.

(b) Save per-tab resume info and test restoring sessions after a simulated
restart (overlaps with exp 54 but adds watcher-specific checks).

## Experiment Design

Build labeled watcher output samples (errors, warnings, clean, tricky).
Measure caught false-done claims and false blocks.

**Measured: pattern detection on labeled samples. Real tmux for resume.**
