# Finding 76: Lane Safety in Rex

## Idea

Lock files prevent one lane from removing another's worktree. Each lane gets
scoped credentials. A status view shows idle/working/waiting + handles stale
sessions from crashes.

## Experiment Design

Real filesystem lock tests (concurrent access). Credential scope isolation.
Status detection on labeled states including a crash/stale case.

**Locks and credentials: MEASURED (real filesystem). Status: logic on labeled
states. Completion sound: stubbed (not human-tested).**
