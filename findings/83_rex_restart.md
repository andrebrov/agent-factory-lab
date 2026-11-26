# Finding 83: Rex Restart-Resume Drill

## Source

<https://x.com/mitchellh/status/2125713695233970521>

Rex can resume programs after its server restarts, built on a new terminal
protocol (OSC 7577) written with the herdr team. Once herdr supports
OSC 7577, the same drill applies there.

## Experiment Status: COULD NOT RUN

Neither Rex nor herdr is installed on this VM (same as exp 79). No Claude
CLI. No API keys. Building a toy process manager and calling it a Rex or
herdr result would be dishonest.

**Requirements to run:** Rex installed + running, agent panes mid-task,
ability to restart Rex server and verify job reattachment via OSC 7577.
