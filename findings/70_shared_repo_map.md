# Finding 70: Shared Repo Map for Rex Lanes (with Real File Reads)

## Idea

Write a saved, git-tracked map of the code once per repo. Every lane reads
the map before starting instead of re-reading the full codebase. Corrects
exp 66's gap: the baseline and treatment must both include real file-content
reads, not just file name/size lists.

## Experiment Design

Measure tokens when N lanes each read the actual files vs when they read a
detailed repo map (with function signatures and key patterns) and only read
the specific files their task requires. The map must contain enough detail
to route correctly — not just names and sizes.

**Measured: real tiktoken on actual file contents and a detailed map.**
