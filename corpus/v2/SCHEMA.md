# PRAMANA v2 — sequence schema

v2 changes the **trace unit**. In v1 a trace was one event, which measured
per-event discrimination and not the longitudinal behaviour behavioural detection
is actually about. In v2 a trace is an **ordered sequence of events, possibly
spanning several agents**.

The submission format is unchanged: one verdict per `trace_id`.

**No prompt or response text, anywhere.** Content is SHA-256 hashed at capture and
the raw bytes never retained, so there was nothing to redact.

---

## What changed, and why

| | v1 | v2 |
|---|---|---|
| `trace_unit` | `"event"` | `"sequence"` |
| `schema_version` | `1` | `2` |
| Trace shape | one event | `events[]`, ordered, `step`-indexed |
| Agents per trace | 1 | 1, 2 or 4 |
| Baselines | `baseline` | `baselines` keyed by `agent_id` |

**Temporal.** An attack trace is healthy for its first several events and then
deviates. That prefix is what makes deviation measurable rather than absolute — the
question becomes "did this agent stop behaving like itself", not "is this value
large".

**Structural.** Coordinated archetypes span multiple agents, because some attacks
do not exist inside a single agent. `attack_class_10` is the clearest case: any one
of its events is just a fast, small request; the attack is many agents doing it at
once to corrupt the swarm centroid.

## Trace fields

```json
{
  "trace_id": "t_…", "schema_version": 2, "trace_unit": "sequence",
  "agent_count": 4,
  "events": [ { "step": 0, "agent_id": "…", "latency_ms": 812, … }, … ],
  "baselines": { "<agent_id>": { "latency_ms_mean": …, "latency_ms_std": …, … } }
}
```

Event fields are as v1, plus `step` (0-based position) and `agent_id`. Every trace
has exactly **12** events.

`baselines` is keyed by `agent_id` — each agent carries the behavioural baseline of
its own healthy self. Read it: behavioural detection is relative, and a detector
that thresholds on absolute values scores far worse.

## The shortcut this corpus refuses to reward

If attack traces were longer, or were the only multi-agent ones, you could score
well by counting events or agents and detecting nothing. Two structural defences:

- **Every trace has exactly 12 events**, attack and benign alike.
- **Benign agent-counts match the attack marginal exactly.** The attack
  distribution is tallied first, then benign traces are assigned counts from that
  same tally — identical by construction, not approximately.

Measured on the published v2 holdout:

| Shortcut detector | balanced |
|---|---|
| flag if `agent_count > 1` | 0.4821 |
| flag if `agent_count == 4` | 0.4927 |
| flag if `len(events) != 12` | 0.5000 |

All at or below chance. Structure alone buys nothing.

## What v2 demonstrates

Reference results on the published holdout (all run by AariaSec, reproducible with
`score_pramana.py`):

| Detector | balanced | recall | FP | `attack_class_10` |
|---|---|---|---|---|
| `drift-tail` — tail vs prefix, longitudinal | **0.9308** | 1.000 | 0.139 | **1.000** |
| AariaSec 3.0.0 rule engine | 0.8538 | 0.923 | 0.215 | **0.000** |
| `sigma-3` — per-event, baseline-relative | 0.8139 | 0.744 | 0.116 | 0.100 |
| `naive-egress` — two field checks | 0.6846 | 0.806 | 0.437 | 0.100 |
| `always-benign` / `always-attack` | 0.5000 | 0.000 / 1.000 | 0.000 / 1.000 | — |

Two things worth stating plainly, neither flattering to us:

1. **A longitudinal method beats every per-event method**, including ours. That is
   the point of v2 — order carries signal a per-event corpus cannot express.
2. **AariaSec scores 0.000 on `attack_class_10` while `drift-tail` scores 1.000.** In
   v1 that zero was ambiguous: corpus limitation, or real gap? It is now
   unambiguous. The signal is present and a forty-line baseline finds all of it.
   That is a detection gap in our product, published here because a benchmark that
   only embarrasses other people is marketing.

## Leakage: what was wrong, and what it cost

An audit on 2026-07-28 found the corpus was **trivially gameable**. The two
generators emitted different field sets, so the *schema itself* was the label —
nine fields separated the classes at accuracy 1.00, and `app_name` embedded the
scenario and archetype name verbatim. A submitter would have scored perfectly with
`"app_name" in trace`.

Three fixes, all structural rather than remembered:

- **Union-fill.** Every event carries the same key set; absentees are filled with
  type-appropriate benign defaults. Presence carries no information; *values* still
  do, which is correct — a benign agent really does have `scan_burst_count: 0`.
- **Opaque identifiers.** Participant and session identifiers are drawn from one
  namespace shared by both classes. They previously named the archetype.
- **Stratified split.** Marginals were matched during generation but the holdout was
  an independent random draw, which reintroduced skew (attack `{1:86, 2:32, 4:11}`
  against benign `{1:96, 2:25, 4:10}`). Splitting within each (label, participant
  count) stratum makes them identical in the *published* partition, which is where
  the property has to hold.

Verified after: `"app_name" in trace` and any class-name substring match both score
exactly **0.5000** on both seasons.

Worth noting the fix did *not* move our own numbers materially (v1 0.8142 → 0.8126,
v2 0.8394 → 0.8538). The reference detectors never read the leaky fields, so the
published figures were never inflated — the corpus was simply exploitable by
someone who looked.

`drift-tail` is also a cautionary tale about calibration. Its first version
compared tail-mean to prefix-mean against one prefix standard deviation and scored
a 0.92 false-positive rate — a 1σ threshold on a mean of four samples is roughly
two standard errors, and a four-sample standard deviation underestimates spread
anyway. Scaling from the supplied baseline and testing against three standard
errors of the tail mean took it from 0.5382 to 0.9008. If your longitudinal
detector scores near chance, check the threshold before the method.
