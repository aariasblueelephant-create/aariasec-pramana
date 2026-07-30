# Seasons v1 and v2 are WITHDRAWN — 2026-07-29

**If you saw a PRAMANA v1 or v2 score anywhere, it does not mean what it appeared to
mean. Both seasons were defective. Every figure measured against them is void,
including our own.**

This is not the same as a season being *retired*. A retired season is sound — its
labels are published so anyone can re-score it, and it remains a valid reference.
A **withdrawn** season was broken as an evaluation and should not be used for
anything.

Season **v3** replaces both. It is built by the same pipeline with the defect fixed and
a guard that would have caught it.

---

## What was wrong

Both seasons could be solved almost perfectly by a single field comparison:

| one-line detector | v1 | v2 |
|---|---|---|
| `response_length == 0` | balanced **0.9936** | balanced **1.0000** |

For comparison, our own detector scored 0.8126 on v1 and 0.9811 on v2. **A one-line
detector beat every real one on the board, including ours.** Any ranking those seasons
produced was measuring an artifact.

## Why it happened

The corpus is assembled from two independent generators — one producing benign agent
telemetry, one producing compromised-agent telemetry. Combining them means the two
populations must be indistinguishable except by behaviour. Twice they were not:

1. **The field *set* was the label** (found and fixed 2026-07-28). The attack generator
   emitted fields the benign one did not, so `"app_name" in trace` scored perfectly.
   Fixed by union-filling every event to a common key set.

2. **The field *values* were the label** (this defect). The fix for (1) filled an absent
   field with a type default, so an absent `int` became `0`. The benign generator emits
   `response_length` on every event; the attack generator emits request-side events,
   where `response_length` is legitimately `0` because no response exists yet. Result:
   every attack event carried `response_length == 0` and no benign event did.

The second defect was introduced by the fix for the first. Same failure both times —
one field separates the classes — approached as two unrelated bugs.

## What changed in v3

- **`direction` and `response_length` are not published.** The attack generators emit
  request-side events and the benign generator does not, so those two fields are drawn
  from different event populations and cannot be compared across classes. Filling
  cannot fix that, and neutralising them to one value would leave `response_length`
  still marking every compromise event. Dropping them is the honest option.

  Cost, stated plainly: `response_length` is one of six fields our fleet-drift detector
  reads, so it runs on five here. The other ~37 fields are unaffected.

- **A build-time guard.** The builder now searches every field for the strongest
  single-field rule — every observed value as an equality test, every numeric value as
  a threshold — and **refuses to emit a corpus** where any single field exceeds 0.85
  balanced. v3's strongest is `tool_call_count > 4` at **0.5673**, against 0.5 for
  chance. A field carrying *some* signal is expected; a field carrying *all* of it is
  the defect.

  The guard was verified by re-running it against the old fill, where it fires.

- **`agent_role` neutralised.** `'orchestrator'` appeared only in attack traces. Found
  by the same guard.

## v3 reference scores

Measured on the held-out split. The spread is the point — a benchmark where everything
scores the same, or where a triviality tops the board, measures nothing.

| detector | balanced | recall | FP |
|---|---|---|---|
| `always-benign` | 0.5000 | 0.0000 | 0.0000 |
| `always-attack` | 0.5000 | 1.0000 | 1.0000 |
| `naive-egress` | 0.6577 | 0.7769 | 0.4615 |
| `sigma-3` | 0.7968 | 0.6704 | 0.0769 |
| `drift-tail` | 0.9115 | 0.9846 | 0.1615 |
| AariaSec 3.0.0 | 0.9505 | 0.9471 | 0.0462 |

## Why you are reading this rather than nothing

The defect was found by us, before any third party had submitted a score — repository
traffic across the whole period was 0 page views and 0 forks. It would have been
possible to replace the seasons quietly and say nothing.

A benchmark's only asset is that its numbers mean what they claim. A vendor who
silently swaps out a corpus after publishing scores against it has nothing worth
citing. The correction is louder than the original announcement on purpose.

If you did download v1 or v2, discard them. Nothing built on those numbers holds.
