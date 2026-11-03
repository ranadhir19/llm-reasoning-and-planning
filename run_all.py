#!/usr/bin/env python3
"""Run the full default (toy-reasoner / symbolic) suite and regenerate
``results/*.txt`` + ``results/summary.json``.

Each task module is run exactly as its own ``__main__`` runs it, with
stdout captured to the task's results file. ``summary.json`` keeps the
shape the article and README quote. The optional real-model pass
(``python3 src/llm_experiment.py``) writes the separate ``llm_*`` files
and is never triggered from here.

Run:  python3 run_all.py
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import p1_classical_planner as p1  # noqa: E402
import p2_replan_gridworld as p2  # noqa: E402
import p3_episodic_memory as p3  # noqa: E402
import p4_plan_graph as p4  # noqa: E402
import r1_direct_vs_cot as r1  # noqa: E402
import r2_self_consistency as r2  # noqa: E402
import r3_verifier as r3  # noqa: E402
import r4_tree_search as r4  # noqa: E402

RESULTS = ROOT / "results"


def capture(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn()
    return result, buf.getvalue()


def main():
    RESULTS.mkdir(exist_ok=True)
    summary = {}

    res, out = capture(lambda: r1.run_toy(seed=18))
    (RESULTS / "r1_direct_vs_cot.txt").write_text(out)
    summary["r1"] = res

    if (RESULTS / "llm_summary.json").exists():
        summary["r1_llm_note"] = ("real-model results captured in "
                                  "llm_summary.json (shared R1-R3 "
                                  "sampling pass)")
    else:
        summary["r1_llm_note"] = "not run in this environment; see README"

    with contextlib.redirect_stdout(io.StringIO()):
        sweep = [r1.run_toy(seed=s)["chain_correct"] for s in range(1, 41)]
    summary["r1_chain_accuracy_across_seeds_1_40"] = {
        "min": min(sweep), "max": max(sweep), "of": res["n"]}

    res, out = capture(lambda: r2.run(k=9, seed=11))
    (RESULTS / "r2_self_consistency.txt").write_text(out)
    summary["r2"] = res

    res, out = capture(lambda: r3.run(n=8, seed=23))
    (RESULTS / "r3_verifier.txt").write_text(out)
    summary["r3"] = res

    res, out = capture(r4.run)
    (RESULTS / "r4_tree_search.txt").write_text(out)
    summary["r4"] = res

    res, out = capture(p1.run)
    (RESULTS / "p1_classical_planner.txt").write_text(out)
    summary["p1"] = res

    res, out = capture(p2.run)
    (RESULTS / "p2_replan_gridworld.txt").write_text(out)
    summary["p2"] = res

    res, out = capture(p3.run)
    (RESULTS / "p3_episodic_memory.txt").write_text(out)
    summary["p3"] = res

    res, out = capture(p4.run)
    (RESULTS / "p4_plan_graph.txt").write_text(out)
    fair = res["fair"]
    summary["p4"] = {
        "p1_steps": res["p1_steps"],
        "p1_layers": res["p1_layers"],
        "p1_invalidated_from_mid": res["p1_invalidated_from_mid"],
        "fair_sequential_hours": fair["sequential_hours"],
        "fair_parallel_hours": fair["parallel_hours"],
        "fair_invalidated": fair["invalidated"],
    }

    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))
    print("run_all: regenerated 8 task outputs + summary.json in results/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
