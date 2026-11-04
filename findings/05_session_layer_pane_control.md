# Finding 5: Native Pane/Tab Control & Durable Session Layer

## Sources

- Native pane/tab control for Rex: <https://x.com/dani_avila7/status/2116352019564777669>
- herdr-core as durable session layer: <https://x.com/herdrdev/status/2115841099575222765>
- herdr multi-agent orchestration: <https://x.com/nicoritschel/status/2116931517415141724>

## Idea

Two related ideas:

### 5a: Native Pane/Tab Control

Give the coding agent (Rex) the ability to programmatically create, switch, and
manage terminal panes and editor tabs. Instead of working in a single terminal,
the agent can:
- Open a pane for running tests while editing in another.
- Split the view to monitor logs while coding.
- Manage multiple worktrees across tabs.

This turns the editor from a passive tool into an active workspace the agent
controls, mimicking how experienced developers use tmux/screen splits.

### 5b: Durable Session Layer (herdr-core)

herdr-core provides a persistent session layer that survives disconnections and
process restarts. Agent state, conversation history, and task progress are
durably stored so that:
- An interrupted session resumes exactly where it left off.
- Multiple agents can share session state.
- The orchestrator can checkpoint and restore sub-agent work.

## Proposal for Rex and Gwaihir

1. **Rex pane control skill:** Add a tool/skill that wraps tmux (or the
   editor's native pane API) to let Rex:
   - Create named panes (`test-runner`, `dev-server`, `logs`).
   - Send commands to specific panes.
   - Read output from panes.
   - Close panes when done.
2. **herdr-core integration in Gwaihir:** Use herdr-core's durable sessions
   to persist Gwaihir's orchestrator state, enabling:
   - Resume after crash/disconnect.
   - Hand-off between agents (writer finishes, reviewer picks up the
     same session).
   - Audit trail of all agent actions.

## Experiment Design

**Goal:** Demonstrate and measure the value of multi-pane execution and session
durability.

**Setup (pane control):**
- Build a small tmux-based pane manager in Python.
- Run a simulated agent workflow: edit code in pane 1, run tests in pane 2,
  monitor logs in pane 3.
- Compare sequential (one pane) vs. parallel (multi-pane) execution time.

**Setup (durable sessions):**
- Implement a minimal session store (JSON file) that checkpoints agent state.
- Simulate a session interruption and resumption.
- Measure state loss (if any) and recovery time.

**Metrics:**
- Wall-clock time: sequential vs. parallel pane execution
- Session recovery: time to resume, state fidelity
- Complexity: lines of code for pane manager

**What can be tested in-sandbox:**
- tmux pane management — fully runnable.
- Session checkpoint/restore — fully runnable.

**What requires real Rex/herdr:**
- Integration with Rex's actual tool calling and herdr-core's session API.
- Protocol for integration testing provided.
