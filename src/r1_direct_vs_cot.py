"""R1 -- Direct answer vs chain-of-thought.

Concept (article Part 2, Section 3): a one-shot answer must do all its
arithmetic inside a single forward sweep; writing the steps externalises
intermediate quantities, so each step is small and checkable. Here both
modes run over the same 14 word problems and we count who is right.

Engines: the toy reasoner by default (see toy_reasoner.py for exactly what
it does and does not claim). With --llm, a real Qwen2.5-0.5B-Instruct runs
all 14 problems -- one greedy direct answer and k=9 sampled chains each --
in the sampling pass shared with R2 and R3 (see llm_experiment.py), so
the three tasks' real-model numbers describe the same generations.

Run:  python3 src/r1_direct_vs_cot.py [--llm] [--seed 7]
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from problems import PROBLEMS, solve  # noqa: E402
from toy_reasoner import direct_answer, format_trace, sample_chain  # noqa: E402


def run_toy(seed: int = 18, slip_rate: float = 0.15):
    rng = random.Random(seed)
    rows, d_ok, c_ok = [], 0, 0
    showcase = None
    for p in PROBLEMS:
        _, gold = solve(p)
        d = direct_answer(p)
        c, trace = sample_chain(p, rng, slip_rate=slip_rate)
        d_ok += d == gold
        c_ok += c == gold
        if p["id"] == "p02_hall_chairs":
            showcase = (p, d, c, trace, gold)
        rows.append((p["id"], gold, d, c))
    n = len(PROBLEMS)
    print("R1 -- direct answer vs chain-of-thought (toy reasoner, "
          f"seed={seed}, slip_rate={slip_rate})")
    print(f"{'problem':24s} {'gold':>7s} {'direct':>8s} {'chain':>8s}")
    for pid, gold, d, c in rows:
        print(f"{pid:24s} {gold:>7} {d:>8} {c:>8}")
    print(f"\nDirect accuracy : {d_ok}/{n} = {d_ok / n:.1%}")
    print(f"Chain accuracy  : {c_ok}/{n} = {c_ok / n:.1%}")
    if showcase:
        p, d, c, trace, gold = showcase
        print("\nThe designed failure, up close -- p02_hall_chairs:")
        print(f"  {p['text']}")
        print(f"  Direct mode grabs the two largest numbers it can see (148 and "
              f"16) and answers {d}. The quantity it needs -- total chairs, "
              f"{gold + 148} -- appears nowhere in the text; it has to be "
              f"*constructed*.")
        print("  Chain mode constructs it:")
        print(format_trace(p, trace, c))
    return {"direct_correct": d_ok, "chain_correct": c_ok, "n": n}


def run_llm():
    """Real-model mode: direct vs single-chain over the shared sampling
    pass (see llm_experiment.py). R2 votes and R3 reranks the very same
    chains this function reports."""
    from llm_experiment import run_all_llm

    try:
        a = run_all_llm()
    except RuntimeError as exc:
        print(f"R1 --llm: {exc} The toy-reasoner run above is the lab's "
              "core result.")
        return None
    n = a["n_problems"]
    print(f"R1 -- direct answer vs chain-of-thought, REAL MODEL "
          f"({a['model']}, CPU; seed={a['seed']}, "
          f"temperature={a['temperature']})")
    print(f"{'problem':24s} {'gold':>7s} {'direct':>8s} {'chain#1':>8s}")
    for pp in a["per_problem"]:
        print(f"{pp['id']:24s} {pp['gold']:>7} "
              f"{pp['direct_answer']!s:>8} {pp['chain_answers'][0]!s:>8}")
    print(f"\nDirect accuracy       : {a['r1']['direct_correct']}/{n} = "
          f"{a['r1']['direct_correct'] / n:.1%}")
    print(f"Single-chain accuracy : {a['r1']['single_chain_correct']}/{n} "
          f"= {a['r1']['single_chain_correct'] / n:.1%}")
    print(f"Unparseable: {a['unparseable']['direct']} direct answers, "
          f"{a['unparseable']['chains']} of {a['unparseable']['chains_total']}"
          " chains (counted wrong)")
    print("Full detail: results/llm_r1_direct_vs_cot.txt; verbatim chains:"
          " results/llm_examples.md")
    return a["r1"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=18)
    ap.add_argument("--llm", action="store_true")
    a = ap.parse_args()
    run_toy(seed=a.seed)
    if a.llm:
        print()
        run_llm()
