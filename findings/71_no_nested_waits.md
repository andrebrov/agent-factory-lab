# Finding 71: No Nested Background Waits

## Idea

Workers wait on builds/tests with ONE blocking command with a timeout, never
a background job started from a background subagent. Also flag turns where
the worker reads >200K cached tokens but writes <20 output tokens (idle-wait
quota leak: a subagent watching a job, repeatedly waking for empty turns).

## Experiment Design

Simulate worker turns with and without the rule. Include idle-wait leak
scenarios. Measure leak prevention and flag accuracy on a labeled set.

**Measured: flag logic on labeled turns. Simulated: worker behavior model.**
