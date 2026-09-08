# Submissions

One file per submission, named `<detector>-<season>.jsonl`.

Each line:

```json
{"trace_id": "t_0f3c9a...", "verdict": "attack", "score": 0.91}
```

- `verdict` — **required**, exactly `"attack"` or `"benign"`
- `score` — optional confidence in `[0,1]`. Informational; not ranked.

Open a pull request adding your file.

**Seasons v1 and v2 are WITHDRAWN** — both were defective as evaluations (see
[`../WITHDRAWN.md`](../WITHDRAWN.md)); any score against them, ours included, is void.

**Season v3 is live** — labels withheld, so a maintainer scores it and posts the
result. A few days, not minutes. Not automated on purpose: auto-scoring a live
holdout would let a submitter recover one label per submission and eventually the
whole answer key.

Don't want to hand-format the JSONL yourself? [`../submit_helper.py`](../submit_helper.py)
wraps your detector function and writes a correctly-formatted `<name>-v3.jsonl` for
you — still runs entirely on your own hardware, still your PR to open.

**We never execute submitted code.** Run your detector on your own hardware and
send the predictions. No sandbox, no compute budget, no liability — for anyone.

Unanswered traces count as `benign`: skipping the hard cases must not raise a score.
