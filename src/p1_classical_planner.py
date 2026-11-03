"""P1 -- A miniature classical planner: blocks world.

Concept (article Part 2, Section 8): planning as search over an exact
model. Four blocks start as two stacks of two; the goal is one tower of
four. Every action is specified by preconditions and effects, the planner
applies only actions whose preconditions hold, tracks the state exactly,
and the resulting plan is *validated by simulation* -- each step's
preconditions re-checked at the moment it executes. That validation step
is the whole point: it is the check a fluent text itinerary never gets.

Both breadth-first search (guaranteed shortest) and A* (guided by a crude
heuristic) solve the same problem, so the cost of *direction* is measured.

Run:  python3 src/p1_classical_planner.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from planner import Action, astar_plan, bfs_plan, simulate  # noqa: E402

BLOCKS = ("A", "B", "C", "D")


def blocks_actions():
    acts = []
    for x in BLOCKS:
        acts.append(Action(
            name=f"pickup({x})",
            pre_pos=frozenset({f"ontable({x})", f"clear({x})", "handempty"}),
            add=frozenset({f"holding({x})"}),
            delete=frozenset({f"ontable({x})", f"clear({x})", "handempty"})))
        acts.append(Action(
            name=f"putdown({x})",
            pre_pos=frozenset({f"holding({x})"}),
            add=frozenset({f"ontable({x})", f"clear({x})", "handempty"}),
            delete=frozenset({f"holding({x})"})))
        for y in BLOCKS:
            if x == y:
                continue
            acts.append(Action(
                name=f"stack({x},{y})",
                pre_pos=frozenset({f"holding({x})", f"clear({y})"}),
                add=frozenset({f"on({x},{y})", f"clear({x})", "handempty"}),
                delete=frozenset({f"holding({x})", f"clear({y})"})))
            acts.append(Action(
                name=f"unstack({x},{y})",
                pre_pos=frozenset({f"on({x},{y})", f"clear({x})",
                                   "handempty"}),
                add=frozenset({f"holding({x})", f"clear({y})"}),
                delete=frozenset({f"on({x},{y})", f"clear({x})",
                                  "handempty"})))
    return acts


INITIAL = frozenset({
    "on(B,A)", "ontable(A)", "on(D,C)", "ontable(C)",
    "clear(B)", "clear(D)", "handempty",
})
GOAL = frozenset({"on(D,C)", "on(C,B)", "on(B,A)"})  # tower A-B-C-D


def run():
    actions = blocks_actions()
    print("P1 -- classical planning in blocks world")
    print("Initial: B on A, D on C (two stacks of two)")
    print("Goal   : one tower -- D on C on B on A")
    results = {}
    for label, fn in (("BFS ", bfs_plan), ("A*  ", astar_plan)):
        plan, expanded = fn(INITIAL, GOAL, actions)
        ok, end = simulate(INITIAL, plan)
        valid = ok and GOAL <= end
        results[label.strip()] = {"plan_length": len(plan),
                                  "nodes_expanded": expanded,
                                  "validated": valid}
        print(f"\n{label}: plan length {len(plan)}, "
              f"nodes expanded {expanded}, "
              f"simulation-validated: {valid}")
        for i, a in enumerate(plan, 1):
            print(f"    {i:2d}. {a.name}")
    return results


if __name__ == "__main__":
    run()
