#!/usr/bin/env python3
"""Turn a detector function into a submission-ready PRAMANA v3 file.

Reduces "read SCHEMA.md and hand-format JSON correctly" down to "point this
at your detector function." Runs entirely on YOUR hardware — this script
never uploads anything and we never execute submitted code (see README);
that trust boundary is unchanged, this just automates the formatting on
your side of it.

Usage:
    python3 submit_helper.py --detector mymodule:my_detect_fn --name myvendor

Your function is called once per trace and must return either a verdict
string or a (verdict, score) tuple:

    def my_detect_fn(trace: dict) -> str | tuple[str, float]:
        # trace has: trace_id, schema_version, trace_unit, agent_count,
        # baselines, events — see corpus/v3/SCHEMA.md for the full field list
        ...
        return "attack"        # or:
        return "attack", 0.91  # score is optional, informational, in [0,1]

Writes ``<name>-v3.jsonl`` in the exact format submissions/README.md and
score.py expect, then prints the (still-local, still-manual) next steps to
open a PR. Every trace in holdout.jsonl gets a line — silently skipping a
hard trace is not allowed, matching how missing predictions are already
scored (counted as ``benign``, so skipping never helps a score).
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

HOLDOUT = Path(__file__).resolve().parent / "corpus" / "v3" / "holdout.jsonl"


def _load_detector(spec: str):
    if ":" not in spec:
        raise SystemExit(f"--detector must be 'module:function', got {spec!r}")
    mod_name, fn_name = spec.split(":", 1)
    sys.path.insert(0, str(Path.cwd()))
    mod = importlib.import_module(mod_name)
    try:
        return getattr(mod, fn_name)
    except AttributeError:
        raise SystemExit(f"{mod_name!r} has no function named {fn_name!r}") from None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--detector", required=True, help="module:function to call per trace")
    p.add_argument("--name", required=True, help="your detector's name — used for the output filename")
    p.add_argument(
        "--holdout",
        default=str(HOLDOUT),
        help="path to holdout.jsonl (default: corpus/v3/holdout.jsonl)",
    )
    args = p.parse_args(argv)

    fn = _load_detector(args.detector)
    holdout_path = Path(args.holdout)
    if not holdout_path.exists():
        raise SystemExit(f"holdout file not found: {holdout_path}")

    out_path = Path(f"{args.name}-v3.jsonl")
    seen = 0
    with holdout_path.open(encoding="utf-8") as fin, out_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            trace = json.loads(line)
            result = fn(trace)
            verdict, score = result if isinstance(result, tuple) else (result, None)
            if verdict not in ("attack", "benign"):
                raise SystemExit(
                    f"detector returned invalid verdict {verdict!r} for trace "
                    f"{trace['trace_id']!r} — must be 'attack' or 'benign'"
                )
            row: dict = {"trace_id": trace["trace_id"], "verdict": verdict}
            if score is not None:
                score = float(score)
                if not (0.0 <= score <= 1.0):
                    raise SystemExit(
                        f"score {score!r} for trace {trace['trace_id']!r} out of [0,1] range"
                    )
                row["score"] = score
            fout.write(json.dumps(row) + "\n")
            seen += 1

    print(f"wrote {out_path} — {seen} traces scored\n")
    print("Next step (still local — nothing this script does uploads anything):")
    print(f"  1. git checkout -b submit-{args.name}")
    print(f"  2. mv {out_path} submissions/{out_path}")
    print(f"  3. git add submissions/{out_path} && git commit -m 'submit: {args.name} v3'")
    print("  4. Open a PR. v3 is live (labels withheld), so a maintainer scores it")
    print("     by hand against the held-back labels — expect a few days, not")
    print("     minutes. That's deliberate, not a limitation of this script:")
    print("     see README.md for why auto-scoring a live holdout isn't safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
