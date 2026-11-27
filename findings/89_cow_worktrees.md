# Finding 89: Copy-on-Write Worktrees (git-cow)

## Source

<https://x.com/edwardsanchez/status/2125842324437766488>

## Tool: git-cow

Three implementations found:
- **gabrielkoerich/git-cow** (crates.io, 0.4.0): keeps an extra checkout per
  repo; new worktrees are CoW clones of it. Supports APFS (clonefile), btrfs,
  XFS (reflink=1), ZFS 2.2+. MIT license. `cargo install git-cow`.
- **onnimonni/git-cow**: similar approach, APFS+btrfs+XFS. Wraps `git worktree
  add --no-checkout` then clones the directory tree.
- **Roasbeef/git-cow**: adds a `copy` mode (independent repo for untrusted
  code) and an `add` mode (linked worktree). Go implementation.

All use `clonefile(2)` on macOS APFS, `FICLONE` ioctl on Linux btrfs/XFS.
Tracked files AND gitignored build caches (node_modules, target/, _build/)
are cloned. .venv is excluded by default (absolute paths break on clone).

## Experiment Design

The lab VM is Linux ext4 (no reflink). A 2GB XFS loopback image with
reflink=1 was created for testing. `cp --reflink=always` works within it.

Measure: disk space (via df, not du), wall time, correctness (git status,
worktree list, commits, isolation, remove+prune), dependency folder handling.

**MEASURED on XFS reflink loopback. Not APFS — Mac results would need
verification on Andrei's MacBook.**
