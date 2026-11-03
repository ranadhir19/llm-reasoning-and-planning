# LLM Reasoning and Planning — the Part 2 Lab

The runnable companion to **"Demystifying LLM Reasoning, Part 2: From
Reasoning to Planning"** by Ranadhir Ghosh.

**Part 1** of the series went *inside* the machine — how a transformer
turns the words "20% discount" into the mathematical object 0.8P, tested
with probes, ablations and activation patching on Qwen2.5-0.5B-Instruct:

- Part 1 article (LinkedIn): https://www.linkedin.com/feed/update/urn:li:activity:7522610307488272384/
- Part 1 lab: https://github.com/ranadhir19/llm-reasoning-demystified

**Part 2** steps outside the network. Part 1's machine only predicts the
next token: it has no built-in search, no state tracker, no memory, no
checker. This lab shows how those missing organs are supplied *around*
the model — and measures what each one buys. Reasoning (deriving a
conclusion) and planning (sequencing actions toward a goal) are treated
as the two different jobs they are, each with runnable tasks.

Everything runs on CPU, with no API keys and no downloads. The core lab
uses only the Python standard library.

## The tasks

### Reasoning

| Task | Run | Concept | Measured result (this repo's captured run) |
|---|---|---|---|
| R1 | `python3 src/r1_direct_vs_cot.py` | Chain-of-thought vs direct answer | Direct **1/14 (7%)**; chain-of-thought **13/14 (93%)** on 14 word problems (fixed seed 18; across seeds 1–40 the chain scores 9–13 of 14) |
| R2 | `python3 src/r2_self_consistency.py` | Self-consistency (majority vote) | Single chain **12/14 (86%)**; majority of 9 chains **14/14 (100%)** |
| R3 | `python3 src/r3_verifier.py` | Verifier reranking (best-of-n) | First sample **9/14 (64%)**; exact step-checker best-of-8 **14/14 (100%)**, rescuing 5 problems |
| R4 | `python3 src/r4_tree_search.py` | Tree search / backtracking | Greedy chain **fails** the river crossing in 3 moves; BFS tree search **solves it in 7 crossings**, expanding 10 nodes |

### Planning

| Task | Run | Concept | Measured result |
|---|---|---|---|
| P1 | `python3 src/p1_classical_planner.py` | Classical planning (state, preconditions, effects, search) | Blocks world solved in **6 steps**; BFS expands 62 nodes, A\* 21; plan **validated by simulation** |
| P2 | `python3 src/p2_replan_gridworld.py` | Plan–execute–monitor–replan | Plan: 17 steps. Blind executor **fails** at the closed corridor; monitoring executor replans once and **succeeds in 21 steps** |
| P3 | `python3 src/p3_episodic_memory.py` | Episodic memory (Reflexion pattern) | Attempt 1 **fails** at the locked gate; attempt 2 with one stored episode **succeeds**; no-memory control **fails again, identically** |
| P4 | `python3 src/p4_plan_graph.py` | Plans as graphs | Fair-prep plan: **16 h sequential vs 5 h** on the critical path; one broken task invalidates exactly **4 of 9** tasks, not all 9 |

Captured outputs live in `results/` (per-task `.txt` plus `summary.json`).

## An honesty note about R1–R3

The word-problem tasks need something to do the reasoning. Downloading a
real model would break the "runs anywhere in seconds" property, so the
default engine is a **toy reasoner** (`src/toy_reasoner.py`): a small,
fully inspectable stand-in whose failure modes are modelled on documented
LLM behaviour — a shortcut mode that pattern-matches on surface numbers
(the way one-shot answers fail), and a chain mode that decomposes into
steps but slips occasionally, with slips propagating as real errors do.
The subject of these tasks is the *techniques* and their measured effect,
not the toy. Every number above is the toy's real measured output at the
stated fixed seeds, and the seeds are in the code for you to vary.

For the genuine article, `--llm` on any of R1–R3 runs all 14 problems
through a real **Qwen2.5-0.5B-Instruct** on CPU — the same model and
pattern as Part 1's experiments — once you install the optional
dependencies (see `requirements.txt`). One sampling pass is shared by
all three tasks (per problem: a greedy direct answer plus 9 sampled
chains), so the direct, vote and verifier numbers describe the same
generations; outputs land in `results/llm_*`. The first run downloads
the model (~1 GB); nothing else in the lab needs it. The same pass runs
in GitHub Actions (`.github/workflows/run-experiments.yml`, manual
trigger), which commits the `results/llm_*` files back to this repo.

### Real-model results (CI)

Produced by the “Run experiments” GitHub Actions workflow (run
41367851053; results committed as 3673982121f5aeb5db34ba09737a04a74592e62d),
model Qwen/Qwen2.5-0.5B-Instruct, seed 1234, temperature 0.7:

| Engine | Direct | Single chain | Majority vote (k=9) | Verifier best-of-9 |
|---|---|---|---|---|
| Toy reasoner (fixed seeds) | 1/14 (7%) | 13/14 (93%) | 14/14 (100%) | 14/14 (100%) |
| Qwen2.5-0.5B-Instruct (CI run, seed 1234) | 0/14 | 6/14 | 9/14 | 5/14 |

The vote rescued p01_print_shop, p03_bookbinder and p08_library_net;
the verifier rescued none and fell below the single chain — its
stated-arithmetic checker is not the toy's exact decomposition
checker. Unparseable outputs: 0 direct, 0 of 126 chains.

## Validate

```
python3 validate.py     # compile, imports, unit tests, results, reference scan
python3 -m unittest discover tests
```

## Layout

```
PLAN.md                  the build plan: article outline + concept-to-task map
src/problems.py          the 14 word problems + exact solver (ground truth)
src/toy_reasoner.py      direct / chain generators with seeded slip model
src/llm_backend.py       optional Qwen2.5-0.5B-Instruct backend (--llm)
src/r1..r4_*.py          reasoning tasks
src/planner.py           shared classical-planner core (BFS / A* / simulate)
src/p1..p4_*.py          planning tasks
tests/                   unit tests for all eight tasks
results/                 captured outputs of the runs quoted above
```
