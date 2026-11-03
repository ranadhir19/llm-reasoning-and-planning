# ARTICLE UPDATE PLAN — Part 2 article, real-model numbers

**Do not edit the article until the GitHub Actions run has completed and
`results/llm_summary.json` exists in this repo.** Until then the only
real-model statement the article may make is the one it already makes
(the mode exists). Every placeholder below is filled from that one JSON
file plus `results/llm_examples.md` — no number is ever typed from
memory or from the workflow log.

Article: `~/workspace/your_files/Demystifying_LLM_Reasoning_Part2_Reasoning_and_Planning.md`
(681 lines, 6,099 words at plan time; line numbers below refer to that
version and will drift as edits land — each item also names its section
and quotes its first words so it can be found after drift.)

## Inputs the editor needs, and where each value lives

From `results/llm_summary.json` (written by the CI run):

| Placeholder | JSON field |
|---|---|
| `<MODEL>` | `model` |
| `<SEED>` | `seed` |
| `<K>` | `k` (9) |
| `<TEMP>` | `temperature` (0.7) |
| `<LLM_DIRECT>` / `<LLM_DIRECT_PCT>` | `r1.direct_correct` / 14 |
| `<LLM_SINGLE>` / `<LLM_SINGLE_PCT>` | `r1.single_chain_correct` / 14 (equals `r2.single_correct`) |
| `<LLM_VOTE>` / `<LLM_VOTE_PCT>` | `r2.vote_correct` / 14 |
| `<LLM_BEST>` / `<LLM_BEST_PCT>` | `r3.best_correct` / 14 |
| `<LLM_FIRST>` | `r3.first_correct` / 14 (same generations as `<LLM_SINGLE>`) |
| `<UNPARSE_DIRECT>`, `<UNPARSE_CHAINS>` | `unparseable.direct`, `unparseable.chains` of `unparseable.chains_total` |
| `<VOTE_RESCUES>` | `r2.vote_rescues` (problem ids) |
| `<VERIFIER_RESCUES>` | `r3.verifier_rescues` (problem ids) |
| per-problem detail (any anecdote) | `per_problem[]`: `direct_answer`, `chain_answers`, `vote_distribution`, `verifier_scores`, `verifier_pick_index` |

From `results/llm_examples.md`: the verbatim chains under its four
headings (direct-failure/CoT-success, vote rescue, verifier rescue,
honest failure — only headings that actually occurred are present).

Provenance values, from the GitHub UI after the run:
`<RUN_DATE>`, `<RUN_URL>` =
`https://github.com/ranadhir19/llm-reasoning-and-planning/actions/runs/<RUN_ID>`,
`<RESULTS_COMMIT_SHA>` = the bot commit the workflow pushed
("Experiment run <RUN_ID>: …").

## The framing decision (applies to every edit below)

The toy-reasoner numbers **stay** — they are the controlled experiment:
exact seeds, exact checker, reproducible in seconds. The real-model
numbers are **added alongside** as the ecological-validity check: same
14 problems, same three techniques, a real (small) model. Neither set
replaces the other; each edit below says which voice it is in. R4 and
P1–P4 are symbolic by design and are **not** touched anywhere.

## Change list

### 1. Introduction — the "simplification" paragraph (lines 62–76)

Current text says every number below is reproducible, describes the toy
reasoner, and ends: "An optional mode runs the same problems through a
real Qwen2.5-0.5B-Instruct — Part 1's model — for readers who want the
genuine article."

Change: after that sentence, add that the mode has now been run — in
GitHub Actions, on the repo's own runners — and that Sections 2–4 quote
its results next to the toy's. Insert the provenance line (item 8)
here or in Section 12. The sentence "Every number quoted below is the
output of a run you can reproduce" stays true and stays.

### 2. Section 2 (R1) — engine description (lines ~146–160)

Current text introduces "Two engines" (toy direct / toy chain) and the
15% slip model. Change: add a third short paragraph introducing the
real-model pass in the same terms the reader has just learned — one
greedy direct answer and `<K>` sampled chains per problem, temperature
`<TEMP>`, seed `<SEED>` — noting R2 and R3 reuse the identical chains,
so the three sections' real-model numbers are one experiment, not
three.

### 3. Section 2 (R1) — measured-result sentence (line 162)

Current: "**direct answers score 1/14 (7%); chain-of-thought scores
13/14 (93%)**" plus the seeds-1–40 range sentence (toy only — keep,
labelled as the toy's).

Add immediately after, in the real-model voice:

> The real model, same 14 problems: **direct answers score
> `<LLM_DIRECT>`/14 (`<LLM_DIRECT_PCT>`); a single sampled chain scores
> `<LLM_SINGLE>`/14 (`<LLM_SINGLE_PCT>`)**. `<UNPARSE_CHAINS>` of the
> `<K*14>` sampled chains and `<UNPARSE_DIRECT>` direct answers yielded
> no parseable number at all and are counted wrong — a failure mode the
> toy, which always answers, does not have.

Then check the p02 "up close" walkthrough that follows (direct answers
132; 224; 76): those are the *toy's* numbers. Keep the walkthrough in
the toy voice, but if `<LLM direct on p02>` also fails, add one sentence
saying what the real model answered on p02 (from `per_problem`) — and
if the direct-failure/CoT-success example in `llm_examples.md` is a
different problem, prefer quoting that verbatim chain here instead
(see item 7).

### 4. Section 3 (R2) — measured-result sentence (lines 204–205)

Current: "**a single chain scores 12/14 (86%); the majority vote scores
14/14 (100%)**", followed by two toy-run anecdotes (warehouse problem:
eight different answers, correct answer won with two votes; courier
problem: vote recovered 6–3).

Add the real-model sentence:

> The real model's vote: **single chain `<LLM_SINGLE>`/14; majority of
> `<K>` chains `<LLM_VOTE>`/14 (`<LLM_VOTE_PCT>`)**, rescuing
> `<VOTE_RESCUES>` — the problems where the first chain was wrong and
> the crowd was right.

Then replace or supplement at least one anecdote with a real vote
distribution from `per_problem[].vote_distribution` (pick the most
scattered one — it makes the same "slips scatter, truth concentrates"
point with real data). Also check the section's closing warning
(systematic error ⇒ confidently wrong majority): if any problem in
`per_problem` has `vote_answer != gold` with a decisive margin, cite it
by name as the real-model instance; if none occurred, leave the warning
as a design statement, unamended.

### 5. Section 4 (R3) — how many candidates, and which checker (lines ~246–252)

Two factual adjustments for the real-model voice:

- Current text says "Eight candidate chains are generated per problem"
  (toy best-of-8). The real-model pass reranks the same `<K>`=9 chains
  as R2 — say so explicitly; do not quietly change the toy's 8.
- The verifier description ("an exact step-checker … recomputes each
  step independently") is exact for the toy. For free text there is no
  ground-truth decomposition to recompute against, so the real-model
  checker (`verify_text_chain`) verifies the arithmetic of every
  computation the chain *states* (`a × b = c` claims) — and cannot judge
  whether the chain chose the right steps. Add that limit in the
  article's own voice; it strengthens, and must not be hidden by, the
  gold-standard paragraph.

Measured sentence (lines 251–252), current: "**the first sample scores
9/14 (64%); best-of-8 under the verifier scores 14/14 (100%)**,
rescuing five problems…". Add:

> On the real model's chains: **first sample `<LLM_FIRST>`/14;
> best-of-`<K>` under the text step-checker `<LLM_BEST>`/14
> (`<LLM_BEST_PCT>`)**, rescuing `<VERIFIER_RESCUES>`.

### 6. Section 12 — command list (lines 613–615)

The three comment lines quote toy scores; keep them, and add a second
block:

```
python3 src/r1_direct_vs_cot.py --llm   # the real model: <LLM_DIRECT> direct vs <LLM_SINGLE> single chain
python3 src/r2_self_consistency.py --llm  # the real vote: <LLM_VOTE>/14
python3 src/r3_verifier.py --llm          # the real checker: <LLM_BEST>/14 best-of-<K>
```

plus one line noting the same commands run in GitHub Actions
(workflow "Run experiments") for readers without a local torch install.

### 7. Verbatim example chains — insertion points

From `results/llm_examples.md`, quote **at most** these, each trimmed
only by the article's usual ellipsis convention, never silently edited:

| Example (llm_examples.md heading) | Insert in | Replaces / supplements |
|---|---|---|
| "Direct answer fails, chain-of-thought succeeds" | Section 2, after the p02 walkthrough | Supplements the toy walkthrough with one real chain |
| "Self-consistency rescue…" | Section 3, beside the vote-distribution anecdote | Supplements item 4's real distribution |
| "Verifier rescue…" | Section 4, after the real measured sentence | New: shows the checker picking among real chains |
| "An honest failure…" | Section 4 end or Section 12 limits | New: the article's honesty beat, in the model's own words |

If a heading is absent from `llm_examples.md`, that example did not
happen in this run — skip the row; do not substitute a near-miss.

### 8. Provenance line — new, one place only (end of Section 12)

Template:

> *Real-model results were produced by the lab's own GitHub Actions
> workflow ("Run experiments") on `<RUN_DATE>`: run `<RUN_URL>`, which
> committed `results/llm_*` back to the repository as commit
> `<RESULTS_COMMIT_SHA>`. Model `<MODEL>`, seed `<SEED>`, temperature
> `<TEMP>`, `<K>` sampled chains per problem plus one greedy direct
> answer; unparseable outputs counted as wrong (`<UNPARSE_DIRECT>`
> direct, `<UNPARSE_CHAINS>` of `<K*14>` chains).*

### 9. Section 12 — limits paragraph (lines 634–646)

Current text: the toy "is a *model of failure modes*, not a model … —
which is why the lab also carries the optional real-model mode … and
why the article has leaned, for every claim about real systems, on the
published measurements of PlanBench, Tree of Thoughts, process-verifier
and Reflexion research rather than on the toy."

Change the last movement: the real-model mode has now run (item 8's
provenance), so for R1–R3 the article leans on the lab's own two
engines — toy for exactness, real model for ecological validity — and
on published measurements for everything beyond a 0.5B model on 14
problems. Keep the "what scales is the architecture, not the numbers"
close unchanged.

### 10. Real-model results table — new (end of Section 4 or start of Section 5)

```markdown
| Engine | Direct | Single chain | Majority vote (k=`<K>`) | Verifier best-of-`<K>` |
|---|---|---|---|---|
| Toy reasoner (fixed seeds) | 1/14 (7%) | 13/14 (93%) | 14/14 (100%) | 14/14 (100%) |
| Qwen2.5-0.5B-Instruct (CI run, seed `<SEED>`) | `<LLM_DIRECT>`/14 | `<LLM_SINGLE>`/14 | `<LLM_VOTE>`/14 | `<LLM_BEST>`/14 |
```

Notes on reading the table, to write honestly from the actual numbers:
whether the ordering (direct < single < vote ≲ verifier) held for the
real model; the unparseable counts; and that the toy's verifier is an
exact decomposition checker while the real model's is a stated-arithmetic
checker (item 5) — the two "verifier" cells are not the same instrument.

### 11. Companion change in this repo (not the article)

`README.md`'s R1–R3 table quotes toy numbers only. Add a short
"Real-model results (CI)" table under the honesty note, filled from
the same placeholders, so repo and article agree.

## After the edits

1. Regenerate the PDF from the edited Markdown with the same reportlab
   pipeline used for the original Part 2 PDF; verify page count and
   spot-check the new table renders.
2. Re-run `python3 validate.py` in this repo (the article edit does not
   touch the lab, but the README change in item 11 does touch a file
   the harness's reference scan stage checks).
3. Nothing about R4 / P1–P4 numbers changes; if any toy number in the
   article differs from a fresh `python3 run_all.py` regeneration,
   stop — that is a lab problem, not an article edit.
