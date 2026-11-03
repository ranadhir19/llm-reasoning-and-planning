# PLAN — llm-reasoning-and-planning (Part 2 lab + article)

**Series:** Demystifying LLM Reasoning
**Part 1:** "From Language to Mathematical Constructs" — LinkedIn https://www.linkedin.com/feed/update/urn:li:activity:7522610307488272384/ · repo https://github.com/ranadhir19/llm-reasoning-demystified
**Part 2 (this build):** "From Reasoning to Planning" — repo https://github.com/ranadhir19/llm-reasoning-and-planning
**Source concepts:** `~/workspace/your_files/Reasoning_vs_Planning_in_AI_Models_2026-11-01.md`

## Design principles

- CPU-only, $0, no API keys. Pure Python for the symbolic / search / memory machinery.
- The word-problem tasks (R1–R3) need a "reasoner" to reason *with*. Two engines:
  1. **Toy reasoner (default, fast, deterministic).** A small stochastic solver that
     mimics documented LLM failure modes: in *direct* mode it uses surface shortcuts
     (grab two prominent numbers, apply the most salient operation) and slips on
     multi-step problems; in *chain* mode it decomposes into steps with a small
     per-step slip probability. It exists so the *techniques* (CoT, voting,
     verification, search) can be measured exactly, with fixed seeds, in seconds.
     The article states plainly that this is a stand-in with LLM-like failure
     modes, and that the techniques — not the toy — are the subject.
  2. **Real model (optional, `--llm`).** Qwen2.5-0.5B-Instruct via transformers on
     CPU, following Part 1's experiment pattern, for readers who want the genuine
     article on a small problem subset. Core suite never requires it.
- **Different examples from the research report** (no bakery, no Chicago trip):
  word problems about a print shop, a community hall, a bookbinder, a courier;
  river-crossing puzzle; blocks world; a courier grid-world; a key-and-gate depot;
  a community-fair task graph.
- Every demo prints honest measured outcomes; all outputs captured to `results/`.
  Failures stay in the record.

## Repo layout

```
llm-reasoning-and-planning/
  PLAN.md  README.md  validate.py  requirements.txt
  src/
    problems.py        word-problem set + exact solver (ground truth)
    toy_reasoner.py    direct / chain generators with seeded slip model
    llm_backend.py     optional Qwen2.5-0.5B-Instruct backend (--llm)
    r1_direct_vs_cot.py
    r2_self_consistency.py
    r3_verifier.py
    r4_tree_search.py      river crossing: greedy chain vs tree search
    planner.py             shared classical-planner core (state/actions/BFS/A*)
    p1_classical_planner.py  blocks world
    p2_replan_gridworld.py   courier grid, obstacle appears mid-execution
    p3_episodic_memory.py    key-and-gate depot, Reflexion-style loop
    p4_plan_graph.py         causal graph of a plan + fair-prep task DAG
  tests/
    test_reasoning.py  test_planning.py
  results/   (captured outputs, .txt + .json)
```

## Task list — concept → runnable demo → what is measured

| Task | Concept (report ref) | Demo | Measured outcome |
|---|---|---|---|
| R1 | Chain-of-thought (§3.1) | direct vs step-by-step on 14 word problems | accuracy of each mode; the designed failure problem |
| R2 | Self-consistency (§3.3) | k sampled chains, majority vote | vote accuracy vs single chain; vote distribution |
| R3 | Verifiers, best-of-n (§3.4) | exact step-checker reranks n candidates | best-of-n with verifier vs first-sample vs single |
| R4 | Tree of Thoughts / search (§3.6) | river crossing: greedy linear chain vs BFS tree search | nodes expanded, solution found/missed, plan length |
| P1 | Classical planning (§4.2–4.3) | blocks world, BFS + A* over PDDL-style actions | plan length, nodes expanded, plan validated by simulation |
| P2 | Plan–execute–monitor–replan (§4.7) | courier grid; road closes mid-route | original vs replanned length, detection point, total steps |
| P3 | Episodic memory / Reflexion (§3.5, Part 5) | key-and-gate depot across attempts, ± memory | success per attempt, steps, control (no memory) fails again |
| P4 | Graph engineering (Part 7) | causal graph of P1 plan + fair-prep DAG | parallel levels vs sequential length; invalidated subgraph size vs total |

## Article outline — "Demystifying LLM Reasoning, Part 2: From Reasoning to Planning"

1. **Opening / bridge from Part 1.** Recap: Part 1 asked how "20% discount" becomes
   0.8P inside the network (behavioural / representational / causal evidence on
   Qwen2.5-0.5B). Part 2 steps outside the network: given that the machine only
   predicts the next token, how do we *organise* its output into reasoning, and
   into the harder thing — planning? Links to Part 1 (LinkedIn + repo) and to
   this repo. The lab as the article's experiments section.
2. **Two jobs, one machine.** Reasoning = deriving conclusions; planning =
   sequencing actions under preconditions toward a goal. The contrast table.
   Why planning is harder for a next-token machine (state it cannot see,
   preconditions it can hallucinate, no backtracking, compounding error).
   → sets up why the article has two halves.
3. **Making it reason (i): write the steps.** Chain-of-thought; tokens as
   computation and scratchpad (echoes Part 1 §2). → **R1** with measured numbers.
4. **Making it reason (ii): vote.** Self-consistency; generation is cheap and
   unreliable, aggregation buys reliability. → **R2**.
5. **Making it reason (iii): check the work.** Verifiers; checking is easier
   than doing; outcome vs process verification. → **R3**.
6. **Making it reason (iv): search.** When a chain forks: tree search,
   backtracking; the moment reasoning becomes planning. → **R4**.
7. **Interlude: why fluent plans fail.** PlanBench in brief (~12% executable;
   Mystery Blocksworld collapse; approximate retrieval vs search). Motivation
   for machinery.
8. **Planning properly: state, actions, search.** Classical planning miniature;
   "a planner refuses to write a step it cannot justify." → **P1**.
9. **Planning in a world that changes: the replan loop.** Plan–execute–monitor–
   replan. → **P2**.
10. **Planning that learns: episodic memory.** Reflexion pattern; memory gated
    by real failure; the no-memory control. → **P3**.
11. **Plans as graphs.** Causal structure, parallelism, precise invalidation —
    what a graph buys that a list cannot. → **P4**.
12. **The improvement roadmap.** Five rungs: prompting → sampling/verification →
    search → systems (loops, memory, graphs, hybrids) → training (RLVR, process
    supervision, distillation of search into weights). Where planning's roadmap
    lags reasoning's, and why (verification is harder for plans).
13. **What to try yourself.** Repo walkthrough: commands per task, what to vary
    (seeds, slip rates, grid size), what to watch for. Honest limits.
14. **Links & further reading.** Part 1 (LinkedIn, repo), this repo, key papers.

## Build order

1. Core library (`problems.py`, `toy_reasoner.py`, `planner.py`).
2. R1–R4, P1–P4 modules; run each; capture `results/`.
3. Optional `--llm` backend for R1 (run on a subset if the model cache is warm).
4. Tests; `validate.py`; reference scan of the exact tree.
5. Article MD quoting the measured results; PDF via reportlab; verify PDF.
6. STOP before GitHub creation/push — parent pushes after review.
