# Finding 75: Cache and Compaction Hygiene

## Idea

Keep the system-prompt prefix byte-identical across turns (fixed tool order,
no timestamps/run IDs). Log cache hit rate, flag below ~80%. Compact at
~400K tokens instead of the ~967K default.

## Experiment Design

Byte-comparison of prefix stability with 3 variants. Cache-hit modeling on
synthetic traces. Cost model for 400K vs 967K compaction threshold.

**Prefix stability: MEASURED (byte comparison). Cache hits: MODELED on
synthetic traces. Compaction cost: MODELED. Quality at 400K: UNTESTED.**
