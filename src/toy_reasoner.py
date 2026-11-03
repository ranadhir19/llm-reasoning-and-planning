"""A toy reasoner with LLM-like failure modes.

This is NOT a language model. It is a small, fully inspectable stand-in whose
failure modes are modelled on the ones documented for LLMs in the literature
(see the companion article): it lets the lab measure *techniques* --
chain-of-thought, self-consistency, verification -- exactly and quickly,
with fixed seeds, on CPU, with no downloads.

Two generators:

* ``direct_answer`` -- the "shortcut" generator. It mimics surface
  pattern-matching: it grabs the two largest numbers in the problem text and
  combines them with one operation chosen from a cue word in the question
  (``left/remain/...`` -> subtract, ``per/each/...`` -> divide, otherwise
  multiply). It never constructs an intermediate quantity, so any problem
  whose answer needs one is out of reach -- the same structural reason a
  one-shot LLM answer fails on multi-step problems.

* ``sample_chain`` -- the "chain-of-thought" generator. It follows the
  problem's true step decomposition, but at each step it may *slip* with
  probability ``slip_rate``: either an arithmetic slip (the step's value is
  perturbed) or an operand slip (it uses a salient number from the text
  instead of the intermediate result it should have used). Slips propagate:
  later steps build on the slipped value, as real reasoning errors do.
  Different seeds slip at different steps, so sampled chains disagree --
  which is exactly the raw material self-consistency and verifiers exploit.

For readers who want the genuine article, ``src/llm_backend.py`` runs the
same problems through a real Qwen2.5-0.5B-Instruct behind a flag.
"""

from __future__ import annotations

import random

from problems import evaluate_step, solve, text_numbers

_SUB_CUES = ("left", "remain", "empty", "change", "still need", "more books are out")
_DIV_CUES = ("per box", "per tray", "each box", "split equally", "how many hours",
             "how many trips", "how many cartons")


def direct_answer(problem):
    """Shortcut answer: combine the two largest text numbers by a cue op."""
    nums = sorted(text_numbers(problem), reverse=True)
    if len(nums) < 2:
        return nums[0]
    a, b = nums[0], nums[1]
    q = problem["text"].lower()
    if any(cue in q for cue in _SUB_CUES):
        out = a - b
    elif any(cue in q for cue in _DIV_CUES):
        out = a / b if b else a
    else:
        out = a * b
    return int(out) if float(out).is_integer() else out


def sample_chain(problem, rng: random.Random, slip_rate: float = 0.15):
    """Generate one reasoning chain. Returns (answer, trace).

    trace is a list of dicts: {desc, claimed, gold} per step, so a checker
    can see exactly where the chain left the rails.
    """
    gold_values, _ = solve(problem)
    values, trace = [], []
    salient = text_numbers(problem)
    for i, st in enumerate(problem["steps"]):
        true_here = evaluate_step(st, values)
        claimed = true_here
        if rng.random() < slip_rate:
            kind = rng.random()
            if kind < 0.5:
                # arithmetic slip: small perturbation of the true value
                claimed = true_here + rng.choice([-10, -2, -1, 1, 2, 10])
            else:
                # operand slip: rebuild the step with a salient text number
                # standing in for one of its arguments
                args = []
                for knd, ref in st["args"]:
                    if knd == "s" and salient and rng.random() < 0.8:
                        args.append(("n", rng.choice(salient)))
                    else:
                        args.append((knd, ref))
                try:
                    claimed = evaluate_step({**st, "args": args}, values)
                except ZeroDivisionError:
                    claimed = true_here + 1
        values.append(claimed)
        trace.append({"desc": st["desc"], "claimed": claimed,
                      "gold": gold_values[i]})
    return values[-1], trace


def format_trace(problem, trace, answer):
    lines = [f"  step {i + 1}: {t['desc']} = {t['claimed']}"
             for i, t in enumerate(trace)]
    lines.append(f"  Answer: {answer}")
    return "\n".join(lines)
