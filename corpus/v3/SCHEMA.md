# PRAMANA v3 — sequence schema

**v3 is the live season. Seasons v1 and v2 are WITHDRAWN — see
[`WITHDRAWN.md`](../../WITHDRAWN.md).** Any v1 or v2 figure you have seen is void,
ours included: a single field comparison scored balanced 1.0000 on v2 and 0.9936 on v1,
beating every real detector on the board. v3 is the same pipeline with that defect fixed
and a build-time guard that refuses to emit a corpus one field can solve.

One trace is an **ordered sequence of events** from one to four agents. Each attack
trace opens with a healthy prefix drawn from the benign generator and then compromises
at some point — so the signal is *deviation from the agent's own recent behaviour*, not
an absolute threshold.

- `holdout.jsonl` — 260 traces, 3120 events, **no labels**. Score against this.
- `holdout_labels.jsonl` — the answer key. Withheld while v3 is the live season.
- Agent counts: 180 single-agent, 60 two-agent, 20 four-agent traces (matched across
  labels, so `agent_count` carries no signal).
- 12 events per trace, every trace, both classes.

## Trace fields

| field | meaning |
|---|---|
| `trace_id` | opaque, stable identifier — return this in your submission |
| `schema_version` | `2` for sequence-valued seasons |
| `trace_unit` | `"sequence"` |
| `agent_count` | how many distinct agents appear in `events` |
| `baselines` | per-`agent_id` behavioural baseline, learned from ~500 warm-up events. Keys are `{field}_mean` / `{field}_std`. |
| `events` | ordered list; each event carries 37 behavioural fields plus `agent_id` and `step` |

Events are content-free by construction. There is no prompt or response text anywhere
in this corpus, because the platform that produced these fields never captures it — only
hashes, counts, lengths, latencies, tool names and destination hostnames. That privacy
constraint is what makes publishing a corpus like this possible at all.

## Two fields are deliberately absent

`direction` and `response_length` are **not published**, and their absence is the v3
fix rather than an oversight.

The corpus combines two independent generators: one producing benign telemetry, one
producing compromised-agent telemetry. The attack generators emit request-side events —
the compromise *is* a request — where `response_length` is legitimately `0` because no
response exists yet. The benign generator emits response events only. Cross-tabulated on
the withdrawn v2:

```
benign  response  response_length != 0   1560
attack  response  response_length != 0    913   <- the healthy prefix of attack traces
attack  request   response_length == 0    635   <- attack-only, structurally
```

So `response_length == 0` and `direction == 'request'` were each a perfect label. That
is not fixable by filling — both classes held genuine values, drawn from different event
populations — and neutralising to a single value would leave `response_length` marking
every compromise event. Dropping them is the honest option.

**Cost, stated:** `response_length` is one of six fields a longitudinal detector would
naturally read. Detectors here work with five. The other 37 fields are unaffected.

**The real fix**, for anyone building something similar: make both generators span both
directions. Then the fields become legitimate signal instead of an answer key.

## The shortcuts this corpus refuses to reward

Presence, identity and naming carry no label. Every event has the same key set;
`app_name`, `framework`, `model`, `is_demo` and `agent_role` are forced to one shared
value; `agent_id`, `session_id` and `prompt_hash` are opaque and drawn from one
namespace shared by both classes; the split is stratified so per-class marginals match.

New in v3, the builder **searches for shortcuts and refuses to emit a corpus that has
one.** For every field it tries each observed value as an equality test and each numeric
value as a threshold, and rejects the build if any single field exceeds 0.85 balanced.

v3's strongest single-field rule is `tool_call_count > 4` at **0.5673**, against 0.5 for
chance. A behavioural field *should* carry some signal; the guard exists to catch a
field carrying all of it.

## v3 reference scores

Held-out split. The spread is the point — these numbers tell you what a score means.

| detector | balanced | recall | FP | note |
|---|---|---|---|---|
| `always-benign` | 0.5000 | 0.0000 | 0.0000 | the floor |
| `always-attack` | 0.5000 | 1.0000 | 1.0000 | cry wolf, scored identically to silence |
| `naive-egress` | 0.6577 | 0.7769 | 0.4615 | two field checks |
| `sigma-3` | 0.7968 | 0.6704 | 0.0769 | classic per-event anomaly detection |
| `drift-tail` | 0.9115 | 0.9846 | 0.1615 | longitudinal: tail vs its own prefix |
| AariaSec 3.0.0 | 0.9505 | 0.9471 | 0.0462 | rules + fleet drift + persistence gate |

Recall and false positives are weighted **equally**: flagging everything and flagging
nothing both score exactly 0.5. A benchmark that rewards sensitivity alone rewards
noise.

Our weakest class in v3 is `attack_class_12` at 0.714 recall, and the coordinated
multi-agent class `attack_class_10` sits at 0.800. Both are published because a
vendor-run benchmark where the vendor is strong everywhere is not worth reading.

## Submitting

One JSON object per line:

```json
{"trace_id": "t_...", "verdict": "attack", "score": 0.91}
```

`score` is optional and informational. Open a pull request adding your file under
`submissions/`. We never execute submitted code — CI parses the `.jsonl` and scores it
with the same `score.py` you have.

While v3 is the live season its labels are withheld, so a maintainer scores it. When v3
retires, its labels are published and scoring becomes self-service.
