# Submissions

One file per submission, named `<detector>-<season>.jsonl`.

Each line:

```json
{"trace_id": "t_0f3c9a...", "verdict": "attack", "score": 0.91}
```

- `verdict` — **required**, exactly `"attack"` or `"benign"`
- `score` — optional confidence in `[0,1]`. Informational; not ranked.

Open a pull request adding your file.

**Season v1 is retired** — its labels are in `corpus/v1/holdout_labels.jsonl`, so
you can score yourself before submitting, and CI re-runs the same command and
comments the result. Nothing here relies on trusting us.

**Season v2 is live** — labels withheld, so a maintainer scores it and posts the
result. A few days, not minutes. Not automated on purpose: auto-scoring a live
holdout would let a submitter recover one label per submission and eventually the
whole answer key.

**We never execute submitted code.** Run your detector on your own hardware and
send the predictions. No sandbox, no compute budget, no liability — for anyone.

Unanswered traces count as `benign`: skipping the hard cases must not raise a score.
