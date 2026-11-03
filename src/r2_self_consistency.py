"""R2 -- Self-consistency: sample many chains, take the majority answer.

Concept (article Part 2, Section 4): generation is cheap and unreliable;
aggregation buys reliability. A single chain slips somewhere with some
probability, but independent slips scatter across many different wrong
answers, while correct chains all land on the same number. The majority
vote therefore finds the right answer far more often than one chain does --
unless the reasoner misunderstands the problem *systematically*, in which
case the majority is confidently wrong (the demo prints vote distributions
so you can see both regimes).

Run:  python3 src/r2_self_consistency.py [--k 9] [--seed 11] [--llm]

With --llm, the vote runs over the real model's k=9 sampled chains --
the same generations R1 and R3 measure (see llm_experiment.py).
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from problems import PROBLEMS, solve  # noqa: E402
from toy_reasoner import sample_chain  # noqa: E402


def run(k: int = 9, seed: int = 11, slip_rate: float = 0.15):
    rng = random.Random(seed)
    single_ok = vote_ok = 0
    print(f"R2 -- self-consistency (k={k} chains per problem, seed={seed}, "
          f"slip_rate={slip_rate})")
    for p in PROBLEMS:
        _, gold = solve(p)
        answers = [sample_chain(p, rng, slip_rate=slip_rate)[0]
                   for _ in range(k)]
        first, votes = answers[0], Counter(answers)
        winner, winner_votes = votes.most_common(1)[0]
        single_ok += first == gold
        vote_ok += winner == gold
        print(f"  {p['id']:24s} gold={gold:<7} single={first!s:<8} "
              f"vote={winner!s:<7} ({winner_votes}/{k})  "
              f"distribution={dict(votes)}")
    n = len(PROBLEMS)
    print(f"\nSingle chain accuracy : {single_ok}/{n} = {single_ok / n:.1%}")
    print(f"Majority vote accuracy: {vote_ok}/{n} = {vote_ok / n:.1%}")
    return {"single_correct": single_ok, "vote_correct": vote_ok, "n": n, "k": k}


def run_llm():
    """Real-model mode: majority vote over the shared sampled chains
    (see llm_experiment.py), against the first chain as the single."""
    from llm_experiment import run_all_llm

    try:
        a = run_all_llm()
    except RuntimeError as exc:
        print(f"R2 --llm: {exc} The toy-reasoner run above is the lab's "
              "core result.")
        return None
    n = a["n_problems"]
    print(f"R2 -- self-consistency, REAL MODEL ({a['model']}, CPU; "
          f"shared generations, k={a['k']}, seed={a['seed']}, "
          f"temperature={a['temperature']})")
    for pp in a["per_problem"]:
        print(f"  {pp['id']:24s} gold={pp['gold']:<7} "
              f"single={pp['chain_answers'][0]!s:<8} "
              f"vote={pp['vote_answer']!s:<7} ({pp['vote_votes']}/{a['k']})"
              f"  distribution={pp['vote_distribution']}")
    print(f"\nSingle chain accuracy : {a['r2']['single_correct']}/{n} = "
          f"{a['r2']['single_correct'] / n:.1%}")
    print(f"Majority vote accuracy: {a['r2']['vote_correct']}/{n} = "
          f"{a['r2']['vote_correct'] / n:.1%}")
    print("Full detail: results/llm_r2_self_consistency.txt")
    return a["r2"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=9)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--llm", action="store_true")
    a = ap.parse_args()
    run(k=a.k, seed=a.seed)
    if a.llm:
        print()
        run_llm()
