"""Shared real-model experiment for R1-R3 (``--llm`` mode).

One sampling pass, three measurements. For each of the 14 word problems
the real model (Qwen2.5-0.5B-Instruct, CPU) generates:

* 1 direct answer -- greedy decoding, "answer with just the number";
* k=9 chains-of-thought -- sampled at temperature 0.7 under fixed,
  per-chain seeds, "think step by step, then 'Answer: <number>'".

R1, R2 and R3 then measure *the same generations*:

* R1: direct accuracy vs single-chain accuracy (the first sampled chain);
* R2: majority-vote accuracy over the 9 extracted chain answers;
* R3: best-of-9 accuracy when the step-verifier (``r3_verifier``'s text
  checker) reranks the same 9 chains.

Generations are cached in ``results/llm_generations.json`` (keyed by the
full run configuration), so running all three tasks costs one generation
pass; delete the cache -- or pass ``--force`` -- to regenerate. Every run
(re)writes the ``llm_*`` result files: ``llm_summary.json``,
``llm_r1_direct_vs_cot.txt``, ``llm_r2_self_consistency.txt``,
``llm_r3_verifier.txt`` and ``llm_examples.md`` (full example chains for
the companion article to quote). The toy-reasoner results are separate
files and are never touched by this module.

Run via any of:
    python3 src/r1_direct_vs_cot.py --llm
    python3 src/r2_self_consistency.py --llm
    python3 src/r3_verifier.py --llm
or all of it at once:
    python3 src/llm_experiment.py [--force]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from problems import PROBLEMS, solve  # noqa: E402

RESULTS = Path(__file__).parent.parent / "results"

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
SEED = 1234
K = 9
TEMPERATURE = 0.7
MAX_NEW_TOKENS = 256        # per sampled chain
DIRECT_MAX_NEW_TOKENS = 48  # the direct prompt asks for just the number

DIRECT_SUFFIX = "\nAnswer with just the number."
COT_SUFFIX = ("\nThink step by step, then finish with the line "
              "'Answer: <number>'.")

CONFIG = {
    "model": MODEL_ID,
    "seed": SEED,
    "k": K,
    "temperature": TEMPERATURE,
    "max_new_tokens": MAX_NEW_TOKENS,
    "direct_max_new_tokens": DIRECT_MAX_NEW_TOKENS,
    "direct_prompt_suffix": DIRECT_SUFFIX,
    "cot_prompt_suffix": COT_SUFFIX,
    "problems": [p["id"] for p in PROBLEMS],
}


# --------------------------------------------------------------------------
# Answer extraction
# --------------------------------------------------------------------------

_NUM = r"-?\d[\d,]*\.?\d*"


def _to_number(text):
    try:
        v = float(text.replace(",", ""))
    except ValueError:
        return None
    return int(v) if v.is_integer() else v


def extract_answer(text):
    """Extract the final numeric answer from a model completion.

    Preference order: the number on the last ``Answer:`` line; otherwise
    the last number anywhere in the text. Returns None when the text holds
    no number at all -- callers count that as *unparseable*, i.e. wrong,
    and tally it separately so the failure mode stays visible.
    """
    if not text:
        return None
    answer_lines = [ln for ln in text.splitlines() if "answer" in ln.lower()]
    for ln in reversed(answer_lines):
        m = re.findall(_NUM, ln)
        if m:
            return _to_number(m[-1])
    m = re.findall(_NUM, text)
    return _to_number(m[-1]) if m else None


# --------------------------------------------------------------------------
# Generation (cached)
# --------------------------------------------------------------------------

def _chain_seed(problem_index, chain_index):
    return SEED + problem_index * 1000 + chain_index


def _generate_all():
    from llm_backend import generate, sample

    gens = []
    for i, p in enumerate(PROBLEMS):
        _, gold = solve(p)
        direct_raw = generate(p["text"] + DIRECT_SUFFIX,
                              max_new_tokens=DIRECT_MAX_NEW_TOKENS)
        chains = []
        for j in range(K):
            raw = sample(p["text"] + COT_SUFFIX, temperature=TEMPERATURE,
                         seed=_chain_seed(i, j),
                         max_new_tokens=MAX_NEW_TOKENS)
            chains.append({"raw": raw, "answer": extract_answer(raw)})
        gens.append({
            "id": p["id"],
            "text": p["text"],
            "gold": gold,
            "direct": {"raw": direct_raw,
                       "answer": extract_answer(direct_raw)},
            "chains": chains,
        })
        print(f"  [llm] {p['id']}: generated 1 direct + {K} chains",
              file=sys.stderr)
    return {"config": CONFIG, "problems": gens}


def ensure_generations(results_dir=None, force=False):
    """Return the generations dict, generating (and caching) if needed."""
    results_dir = Path(results_dir) if results_dir else RESULTS
    cache = results_dir / "llm_generations.json"
    if cache.exists() and not force:
        try:
            data = json.loads(cache.read_text())
            if data.get("config") == CONFIG:
                return data
        except (ValueError, OSError):
            pass  # fall through and regenerate
    data = _generate_all()
    results_dir.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, indent=2) + "\n")
    return data


# --------------------------------------------------------------------------
# Analysis: R1 / R2 / R3 over the same generations
# --------------------------------------------------------------------------

def analyze(data):
    from r3_verifier import verify_text_chain

    per_problem = []
    d_ok = single_ok = vote_ok = first_ok = best_ok = 0
    unparseable_direct = unparseable_chains = 0
    vote_rescues, verifier_rescues = [], []
    for g in data["problems"]:
        gold = g["gold"]
        answers = [c["answer"] for c in g["chains"]]
        scores = [verify_text_chain(c["raw"]) for c in g["chains"]]
        direct_ans = g["direct"]["answer"]
        first_ans = answers[0]

        parseable = Counter(a for a in answers if a is not None)
        if parseable:
            winner, winner_votes = parseable.most_common(1)[0]
        else:
            winner, winner_votes = None, 0
        ranked = sorted(range(len(answers)),
                        key=lambda j: (scores[j][0], scores[j][1],
                                       answers[j] is not None),
                        reverse=True)
        pick = ranked[0]
        pick_ans = answers[pick]

        d_ok += direct_ans == gold
        single_ok += first_ans == gold
        vote_ok += winner == gold
        first_ok += first_ans == gold
        best_ok += pick_ans == gold
        unparseable_direct += direct_ans is None
        unparseable_chains += sum(a is None for a in answers)
        if first_ans != gold and winner == gold:
            vote_rescues.append(g["id"])
        if first_ans != gold and pick_ans == gold:
            verifier_rescues.append(g["id"])
        per_problem.append({
            "id": g["id"],
            "gold": gold,
            "direct_answer": direct_ans,
            "chain_answers": answers,
            "single_chain_correct": first_ans == gold,
            "vote_answer": winner,
            "vote_votes": winner_votes,
            "vote_distribution": {str(a): n for a, n in
                                  Counter(answers).items()},
            "verifier_scores": [list(s) for s in scores],
            "verifier_pick_index": pick,
            "verifier_pick_answer": pick_ans,
        })
    n = len(data["problems"])
    return {
        **data["config"],
        "n_problems": n,
        "r1": {"direct_correct": d_ok, "single_chain_correct": single_ok,
               "n": n},
        "r2": {"single_correct": single_ok, "vote_correct": vote_ok,
               "n": n, "k": data["config"]["k"],
               "vote_rescues": vote_rescues},
        "r3": {"first_correct": first_ok, "best_correct": best_ok,
               "n_problems": n, "candidates": data["config"]["k"],
               "verifier_rescues": verifier_rescues},
        "unparseable": {"direct": unparseable_direct,
                        "chains": unparseable_chains,
                        "chains_total": n * data["config"]["k"]},
        "per_problem": per_problem,
    }


# --------------------------------------------------------------------------
# Result files
# --------------------------------------------------------------------------

def _header(title, a):
    return (f"{title} -- REAL MODEL ({a['model']}, CPU)\n"
            f"seed={a['seed']}, k={a['k']} chains/problem, "
            f"temperature={a['temperature']}, "
            f"max_new_tokens={a['max_new_tokens']}\n"
            f"Generations are shared across R1/R2/R3 (one sampling pass).\n")


def _txt_r1(a):
    lines = [_header("R1 -- direct answer vs chain-of-thought", a),
             f"{'problem':24s} {'gold':>7s} {'direct':>8s} {'chain#1':>8s}"]
    for pp in a["per_problem"]:
        lines.append(f"{pp['id']:24s} {pp['gold']:>7} "
                     f"{pp['direct_answer']!s:>8} "
                     f"{pp['chain_answers'][0]!s:>8}")
    n = a["n_problems"]
    lines.append(f"\nDirect accuracy       : {a['r1']['direct_correct']}/{n}"
                 f" = {a['r1']['direct_correct'] / n:.1%}")
    lines.append(f"Single-chain accuracy : {a['r1']['single_chain_correct']}"
                 f"/{n} = {a['r1']['single_chain_correct'] / n:.1%}")
    lines.append(f"Unparseable direct answers: {a['unparseable']['direct']}")
    return "\n".join(lines) + "\n"


def _txt_r2(a):
    lines = [_header("R2 -- self-consistency (majority vote)", a)]
    for pp in a["per_problem"]:
        lines.append(f"  {pp['id']:24s} gold={pp['gold']:<7} "
                     f"single={pp['chain_answers'][0]!s:<8} "
                     f"vote={pp['vote_answer']!s:<7} "
                     f"({pp['vote_votes']}/{a['k']})  "
                     f"distribution={pp['vote_distribution']}")
    n = a["n_problems"]
    lines.append(f"\nSingle chain accuracy : {a['r2']['single_correct']}/{n}"
                 f" = {a['r2']['single_correct'] / n:.1%}")
    lines.append(f"Majority vote accuracy: {a['r2']['vote_correct']}/{n}"
                 f" = {a['r2']['vote_correct'] / n:.1%}")
    lines.append("Problems rescued by the vote (first chain wrong, "
                 f"majority right): {a['r2']['vote_rescues']}")
    return "\n".join(lines) + "\n"


def _txt_r3(a):
    lines = [_header("R3 -- verifier reranking (best-of-n)", a)]
    for pp in a["per_problem"]:
        pick = pp["verifier_pick_index"]
        lines.append(f"  {pp['id']:24s} gold={pp['gold']:<7} "
                     f"first={pp['chain_answers'][0]!s:<8} "
                     f"best-of-{a['k']}={pp['verifier_pick_answer']!s:<7} "
                     f"(chain #{pick}, score="
                     f"{tuple(pp['verifier_scores'][pick])})")
        lines.append(f"      scores per chain: "
                     f"{[tuple(s) for s in pp['verifier_scores']]}")
    n = a["n_problems"]
    lines.append(f"\nFirst-sample accuracy        : "
                 f"{a['r3']['first_correct']}/{n} = "
                 f"{a['r3']['first_correct'] / n:.1%}")
    lines.append(f"Verifier best-of-{a['k']} accuracy : "
                 f"{a['r3']['best_correct']}/{n} = "
                 f"{a['r3']['best_correct'] / n:.1%}")
    lines.append("Problems rescued by the verifier (first chain wrong, "
                 f"verifier pick right): {a['r3']['verifier_rescues']}")
    return "\n".join(lines) + "\n"


def _pick_examples(data, a):
    """Choose full chains for the article, labelled by what actually
    happened. Returns a list of (heading, problem_dict, body_text)."""
    by_id = {g["id"]: g for g in data["problems"]}
    info = {pp["id"]: pp for pp in a["per_problem"]}
    used = set()
    out = []

    def chain_block(g, j, note):
        return (f"{note}\n\n> Problem: {g['text']}\n>\n"
                f"> Chain #{j} (extracted answer: "
                f"{g['chains'][j]['answer']!s}; gold: {g['gold']}):\n\n"
                f"```text\n{g['chains'][j]['raw'].strip()}\n```\n")

    # 1. Direct fails, chain-of-thought succeeds.
    for pp in a["per_problem"]:
        g = by_id[pp["id"]]
        if pp["direct_answer"] != pp["gold"] and pp["chain_answers"][0] == pp["gold"]:
            out.append(("Direct answer fails, chain-of-thought succeeds",
                        g,
                        f"Direct output (greedy, extracted answer: "
                        f"{pp['direct_answer']!s}; gold: {pp['gold']}):\n\n"
                        f"```text\n{g['direct']['raw'].strip()}\n```\n\n"
                        + chain_block(g, 0, "The first sampled chain:")))
            used.add(pp["id"])
            break

    # 2. Vote rescue: first chain wrong, majority right.
    for pid in a["r2"]["vote_rescues"]:
        if pid in used:
            continue
        g, pp = by_id[pid], info[pid]
        right_j = next(j for j, ans in enumerate(pp["chain_answers"])
                       if ans == pp["gold"])
        out.append(("Self-consistency rescue: the first chain is wrong, "
                    "the majority is right", g,
                    f"Vote distribution over the {a['k']} extracted "
                    f"answers: {pp['vote_distribution']} -- the majority "
                    f"answer is {pp['vote_answer']!s} ({pp['vote_votes']}/"
                    f"{a['k']}), which is correct.\n\n"
                    + chain_block(g, 0, "The first chain (wrong):")
                    + "\n"
                    + chain_block(g, right_j, "A chain that got it right:")))
        used.add(pid)
        break

    # 3. Verifier rescue: first chain wrong, verifier pick right.
    for pid in a["r3"]["verifier_rescues"]:
        if pid in used:
            continue
        g, pp = by_id[pid], info[pid]
        pick = pp["verifier_pick_index"]
        out.append(("Verifier rescue: the step-checker picks the right "
                    "chain", g,
                    f"Verifier scores per chain (all steps arithmetically "
                    f"exact?, # exact steps): "
                    f"{[tuple(s) for s in pp['verifier_scores']]}. The "
                    f"checker picks chain #{pick}.\n\n"
                    + chain_block(g, 0, "The first chain (wrong):")
                    + "\n"
                    + chain_block(g, pick, "The verifier's pick:")))
        used.add(pid)
        break

    # 4. Honest failure: every method wrong on this problem.
    for pp in a["per_problem"]:
        if pp["id"] in used:
            continue
        if (pp["direct_answer"] != pp["gold"]
                and pp["vote_answer"] != pp["gold"]
                and pp["verifier_pick_answer"] != pp["gold"]):
            g = by_id[pp["id"]]
            out.append(("An honest failure: direct, vote and verifier all "
                        "miss", g,
                        f"Gold answer: {pp['gold']}. Direct answered "
                        f"{pp['direct_answer']!s}; the majority vote was "
                        f"{pp['vote_answer']!s}; the verifier's pick was "
                        f"{pp['verifier_pick_answer']!s}. Wrong chains are "
                        f"data too -- this is what the failure looks like "
                        f"from inside.\n\n"
                        + chain_block(g, pp["verifier_pick_index"],
                                      "The verifier's (wrong) pick:")))
            used.add(pp["id"])
            break

    if len(out) < 3:
        out.append(("Note", None,
                    "Fewer than three of the four canonical example "
                    "categories occurred in this run; the file reports "
                    "only categories that actually happened, with the "
                    "labels above stating exactly what occurred."))
    return out


def _examples_md(data, a):
    lines = ["# Real-model example chains (verbatim)",
             "",
             f"Model: {a['model']} on CPU. Seed {a['seed']}, temperature "
             f"{a['temperature']}, k={a['k']} sampled chains per problem, "
             f"greedy direct answers. Extracted answers are the lab's "
             f"parser's reading of each completion; unparseable counts as "
             f"wrong. Headline results: direct "
             f"{a['r1']['direct_correct']}/{a['n_problems']}, single chain "
             f"{a['r1']['single_chain_correct']}/{a['n_problems']}, "
             f"majority vote {a['r2']['vote_correct']}/{a['n_problems']}, "
             f"verifier best-of-{a['k']} {a['r3']['best_correct']}/"
             f"{a['n_problems']}.",
             ""]
    for heading, _g, body in _pick_examples(data, a):
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(body)
    return "\n".join(lines) + "\n"


def write_outputs(data, a, results_dir=None):
    results_dir = Path(results_dir) if results_dir else RESULTS
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "llm_summary.json").write_text(
        json.dumps(a, indent=2) + "\n")
    (results_dir / "llm_r1_direct_vs_cot.txt").write_text(_txt_r1(a))
    (results_dir / "llm_r2_self_consistency.txt").write_text(_txt_r2(a))
    (results_dir / "llm_r3_verifier.txt").write_text(_txt_r3(a))
    (results_dir / "llm_examples.md").write_text(_examples_md(data, a))


def run_all_llm(results_dir=None, force=False):
    """Generate (or reuse the cache), analyse, write all llm_* files.

    Returns the analysis dict. Raises RuntimeError if the real-model
    backend is unavailable -- callers decide how to present that.
    """
    from llm_backend import available

    ok, why = available()
    if not ok:
        raise RuntimeError(f"real-model backend unavailable ({why})")
    data = ensure_generations(results_dir=results_dir, force=force)
    a = analyze(data)
    write_outputs(data, a, results_dir=results_dir)
    return a


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="ignore the generation cache and regenerate")
    args = ap.parse_args()
    try:
        result = run_all_llm(force=args.force)
    except RuntimeError as exc:
        print(f"llm_experiment: {exc}")
        sys.exit(1)
    print(_txt_r1(result))
    print(_txt_r2(result))
    print(_txt_r3(result))
