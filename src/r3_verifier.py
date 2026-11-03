"""R3 -- Verifiers: generate candidates, grade them, keep the best.

Concept (article Part 2, Section 5): checking is often easier than doing.
Instead of trusting the first chain (or the loudest vote), generate n
candidate chains and let a *verifier* score each one, then answer with the
best-scoring candidate (best-of-n).

Our verifier is the strongest kind: an exact step-checker. Because every
problem in the lab has a known step decomposition, the checker can recompute
each step independently and count how many of the chain's claimed values are
exactly right. Learned verifiers (outcome and process reward models, as in
the article) approximate precisely this judgement when exact checking is
unavailable; where an exact checker exists -- a maths decomposition, a test
suite, a plan validator -- it is the gold standard, and it cannot be
talked into anything.

Run:  python3 src/r3_verifier.py [--n 8] [--seed 23] [--llm]

With --llm, the same idea runs on the real model's sampled chains: the
text step-checker (``verify_text_chain``) reranks the k=9 chains R1/R2
measured (see llm_experiment.py).
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from problems import PROBLEMS, solve  # noqa: E402
from toy_reasoner import sample_chain  # noqa: E402


def verify(trace):
    """Score a chain: (all steps exactly right?, # steps exactly right)."""
    right = sum(1 for t in trace if t["claimed"] == t["gold"])
    return (right == len(trace), right)


# A stated computation in free text: "14 x 16 = 224", "240 * 2 = 480", ...
_CLAIM = re.compile(
    r"(-?\d[\d,]*\.?\d*)\s*([+\-*x\u00d7/\u00f7])\s*"
    r"(-?\d[\d,]*\.?\d*)\s*=\s*(-?\d[\d,]*\.?\d*)")
_TEXT_OPS = {"+" : lambda a, b: a + b, "-": lambda a, b: a - b,
             "*": lambda a, b: a * b, "x": lambda a, b: a * b,
             "\u00d7": lambda a, b: a * b, "/": lambda a, b: a / b,
             "\u00f7": lambda a, b: a / b}


def verify_text_chain(text):
    """Score a free-text chain: (all stated computations exact?,
    # stated computations that are arithmetically exact).

    This is ``verify`` adapted to prose: every ``a <op> b = c`` claim the
    chain states is recomputed independently, exactly as the step-checker
    recomputes the toy reasoner's steps. The honest limit, stated for the
    record: it verifies the arithmetic of the steps the chain *chose* to
    state; it cannot judge whether the chain chose the right steps. That
    is precisely the gap between a process checker with a ground-truth
    decomposition (the toy mode above) and verification of free text.
    """
    claims = _CLAIM.findall(text or "")
    if not claims:
        return (False, 0)
    right = 0
    for a_s, op, b_s, c_s in claims:
        try:
            a_v = float(a_s.replace(",", ""))
            b_v = float(b_s.replace(",", ""))
            c_v = float(c_s.replace(",", ""))
            right += abs(_TEXT_OPS[op](a_v, b_v) - c_v) < 1e-6
        except (ValueError, ZeroDivisionError):
            continue
    return (right == len(claims), right)


def run(n: int = 8, seed: int = 23, slip_rate: float = 0.15):
    rng = random.Random(seed)
    first_ok = best_ok = 0
    rescued = []
    print(f"R3 -- verifier reranking (best-of-{n}, seed={seed}, "
          f"slip_rate={slip_rate})")
    for p in PROBLEMS:
        _, gold = solve(p)
        cands = [sample_chain(p, rng, slip_rate=slip_rate) for _ in range(n)]
        first_ans = cands[0][0]
        ranked = sorted(cands, key=lambda c: verify(c[1]), reverse=True)
        best_ans, best_trace = ranked[0]
        first_ok += first_ans == gold
        best_ok += best_ans == gold
        tag = ""
        if first_ans != gold and best_ans == gold:
            tag = "  <- verifier rescue"
            rescued.append(p["id"])
        print(f"  {p['id']:24s} gold={gold:<7} first={first_ans!s:<8} "
              f"best-of-{n}={best_ans!s:<7} best score={verify(best_trace)}"
              f"{tag}")
    total = len(PROBLEMS)
    print(f"\nFirst-sample accuracy      : {first_ok}/{total} = "
          f"{first_ok / total:.1%}")
    print(f"Verifier best-of-{n} accuracy : {best_ok}/{total} = "
          f"{best_ok / total:.1%}")
    print(f"Problems rescued by the verifier: {rescued}")
    return {"first_correct": first_ok, "best_correct": best_ok,
            "n_problems": total, "candidates": n, "rescued": rescued}


def run_llm():
    """Real-model mode: rerank the shared sampled chains (see
    llm_experiment.py) with ``verify_text_chain`` and report best-of-k
    against the first sample, over the same generations R1/R2 measured."""
    from llm_experiment import run_all_llm

    try:
        a = run_all_llm()
    except RuntimeError as exc:
        print(f"R3 --llm: {exc} The toy-reasoner run above is the lab's "
              "core result.")
        return None
    n = a["n_problems"]
    print(f"R3 -- verifier reranking, REAL MODEL ({a['model']}, CPU; "
          f"shared generations, k={a['k']}, seed={a['seed']})")
    for pp in a["per_problem"]:
        pick = pp["verifier_pick_index"]
        print(f"  {pp['id']:24s} gold={pp['gold']:<7} "
              f"first={pp['chain_answers'][0]!s:<8} "
              f"best-of-{a['k']}={pp['verifier_pick_answer']!s:<7} "
              f"(chain #{pick})")
    print(f"\nFirst-sample accuracy        : {a['r3']['first_correct']}/{n}"
          f" = {a['r3']['first_correct'] / n:.1%}")
    print(f"Verifier best-of-{a['k']} accuracy : {a['r3']['best_correct']}/{n}"
          f" = {a['r3']['best_correct'] / n:.1%}")
    print("Full per-chain scores and rescues: results/llm_r3_verifier.txt")
    return a["r3"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--llm", action="store_true")
    a = ap.parse_args()
    run(n=a.n, seed=a.seed)
    if a.llm:
        print()
        run_llm()
