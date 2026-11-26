# Finding 84: Plan Around the 5-Minute Anthropic Prompt Cache

## Sources

- <https://x.com/EveSjr/status/2125939555195138408>
- <https://x.com/eren_cndn/status/2125598276128755813>

## Idea

Anthropic's prompt cache lasts 5 min (default) or 1 hour (2x write cost).
After a break, the next turn rewrites the whole context at 1.25x. Policy:
use the 1-hour cache or compact before idle gaps. Weekly log report shows
cache-read share, rewrites after idle, and repeated file reads.

## Experiment Design

No real Claude session logs or live Anthropic cache. Build a log parser and
cache policy tested against constructed fixtures with known timestamps and
cache events. Results are FIXTURE/MODELED, not production measurements.
