"""P4 -- Plans as graphs: what a graph buys that a list cannot.

Concept (article Part 2, Section 11): a plan written as a flat list hides
its structure. Drawn as a graph -- steps as nodes, an edge A -> B when B
needs an effect that A produces -- two things become computable:

1. **Parallelism.** Steps in the same layer of the graph have no dependency
   between them and can run at once. The flat list's length is the
   sequential time; the graph's longest path (its *critical path*) is the
   parallel time. The difference is real capacity the list was hiding.

2. **Precise invalidation.** When one step's effect breaks, only its
   *descendants* in the graph are invalidated. A flat list offers two bad
   options: redo everything, or keep everything and risk inconsistency.

Part A builds the causal graph of the actual blocks-world plan from P1.
Part B uses a community-fair preparation plan -- a graph with genuine
branching -- to measure both effects.

Run:  python3 src/p4_plan_graph.py
"""

from __future__ import annotations

import sys
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from p1_classical_planner import GOAL, INITIAL, blocks_actions  # noqa: E402
from planner import apply, astar_plan  # noqa: E402


def causal_graph(initial, plan):
    """Edge i -> j when step j consumes an atom that step i produced."""
    producer = {atom: -1 for atom in initial}  # -1 = the initial state
    edges = defaultdict(set)
    state = set(initial)
    for j, a in enumerate(plan):
        for atom in a.pre_pos:
            if producer.get(atom, -1) >= 0:  # produced by an earlier step
                edges[producer[atom]].add(j)
        state = set(apply(frozenset(state), a))
        for atom in a.add:
            producer[atom] = j
    return edges


def descendants(edges, start, n):
    seen, stack = set(), [start]
    while stack:
        x = stack.pop()
        for y in edges.get(x, ()):
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return seen


def layers(edges, n):
    """Longest-path layering: layer(v) = 1 + max(layer of predecessors)."""
    preds = defaultdict(set)
    for a, bs in edges.items():
        for b in bs:
            preds[b].add(a)
    layer = {}
    order = deque([i for i in range(n) if not preds[i]])
    indeg = {i: len(preds[i]) for i in range(n)}
    succ = defaultdict(set)
    for a, bs in edges.items():
        for b in bs:
            succ[a].add(b)
    while order:
        x = order.popleft()
        layer[x] = 1 + max((layer[p] for p in preds[x]), default=-1)
        for y in succ[x]:
            indeg[y] -= 1
            if indeg[y] == 0:
                order.append(y)
    return layer


# --- Part B: the community-fair prep plan -----------------------------------
# task: (duration_hours, dependencies)
FAIR = {
    "reserve_hall":       (2, []),
    "print_posters":      (3, []),
    "order_food":         (1, []),
    "recruit_volunteers": (4, []),
    "set_up_stage":       (2, ["reserve_hall"]),
    "hang_posters":       (1, ["print_posters", "reserve_hall"]),
    "prep_kitchen":       (2, ["order_food"]),
    "sound_check":        (1, ["set_up_stage"]),
    "open_fair":          (0, ["hang_posters", "prep_kitchen",
                               "sound_check", "recruit_volunteers"]),
}


def fair_analysis():
    # layer by name over the dependency DAG
    name_layer = {}

    def lay(t):
        if t not in name_layer:
            deps = FAIR[t][1]
            name_layer[t] = 0 if not deps else 1 + max(lay(d) for d in deps)
        return name_layer[t]

    for t in FAIR:
        lay(t)
    # critical path: longest duration-weighted path ending anywhere
    best = {}

    def crit(t):
        if t not in best:
            dur, deps = FAIR[t]
            best[t] = dur + max((crit(d) for d in deps), default=0)
        return best[t]

    makespan = max(crit(t) for t in FAIR)
    sequential = sum(d for d, _ in FAIR.values())
    broken = "reserve_hall"
    idx = {t: i for i, t in enumerate(FAIR)}
    name_edges = defaultdict(set)
    for t, (_, deps) in FAIR.items():
        for d in deps:
            name_edges[d].add(t)
    invalidated = descendants(name_edges, broken, len(FAIR))
    return {"layers": name_layer, "sequential_hours": sequential,
            "parallel_hours": makespan,
            "broken": broken, "invalidated": sorted(invalidated),
            "n_tasks": len(FAIR)}


def run():
    print("P4 -- plans as graphs")
    plan, _ = astar_plan(INITIAL, GOAL, blocks_actions())
    edges = causal_graph(INITIAL, plan)
    n = len(plan)
    layer = layers(dict(edges), n)
    n_layers = max(layer.values()) + 1 if layer else 0
    mid = n // 2
    inv = descendants(edges, mid, n)
    print(f"\nPart A -- the P1 blocks-world plan as a causal graph:")
    print(f"  {n} steps; causal edges: "
          f"{sum(len(v) for v in edges.values())}; layers: {n_layers}")
    print(f"  If step {mid + 1} ({plan[mid].name}) breaks, the graph "
          f"invalidates exactly its {len(inv)} descendant step(s); the "
          f"{mid} steps before it provably stand, and only the broken "
          f"step plus its descendants need redoing. A flat list cannot "
          f"tell you that.")

    f = fair_analysis()
    print(f"\nPart B -- community-fair preparation ({f['n_tasks']} tasks):")
    by_layer = defaultdict(list)
    for t, l in f["layers"].items():
        by_layer[l].append(t)
    for l in sorted(by_layer):
        print(f"  layer {l}: {', '.join(sorted(by_layer[l]))}")
    print(f"  Sequential time (the flat list): {f['sequential_hours']} h")
    print(f"  Parallel time (critical path)  : {f['parallel_hours']} h")
    print(f"  If '{f['broken']}' falls through, the graph invalidates "
          f"{len(f['invalidated'])} of {f['n_tasks']} tasks: "
          f"{f['invalidated']}.")
    print(f"  The other {f['n_tasks'] - len(f['invalidated'])} tasks stand "
          f"untouched -- no replanning, no risk of redoing finished work.")
    return {"p1_steps": n, "p1_layers": n_layers,
            "p1_invalidated_from_mid": len(inv), "fair": f}


if __name__ == "__main__":
    run()
