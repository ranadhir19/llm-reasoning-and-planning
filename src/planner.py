"""A miniature classical planner -- the shared core for P1 and P4.

The classical formulation (STRIPS, Fikes & Nilsson 1971; PDDL, 1998):

* a **state** is a set of true atoms (strings); anything not listed is false;
* an **action** has **preconditions** (atoms that must be true, atoms that
  must be false) and **effects** (atoms added, atoms deleted);
* a **plan** is a sequence of actions whose preconditions hold at the moment
  each is applied, ending in a state that satisfies the goal.

The planner *searches*: it only ever applies actions whose preconditions
currently hold, tracks the state exactly, and backtracks on dead ends --
the three guarantees a text generator does not give you.
"""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Action:
    name: str
    pre_pos: frozenset = frozenset()
    pre_neg: frozenset = frozenset()
    add: frozenset = frozenset()
    delete: frozenset = frozenset()


def applicable(state, action: Action) -> bool:
    return action.pre_pos <= state and not (action.pre_neg & state)


def apply(state, action: Action):
    return (state - action.delete) | action.add


def bfs_plan(initial, goal_pos, actions):
    """Breadth-first search: shortest plan. Returns (plan, nodes_expanded)."""
    goal_pos = frozenset(goal_pos)
    frontier = deque([(frozenset(initial), [])])
    seen = {frozenset(initial)}
    expanded = 0
    while frontier:
        state, plan = frontier.popleft()
        expanded += 1
        if goal_pos <= state:
            return plan, expanded
        for a in actions:
            if applicable(state, a):
                nxt = apply(state, a)
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append((nxt, plan + [a]))
    return None, expanded


def astar_plan(initial, goal_pos, actions):
    """A* with h = number of goal atoms not yet true.

    Returns (plan, nodes_expanded). The goal-count heuristic is crude but
    admissible in domains where one action adds at most one goal atom --
    and the comparison with BFS shows what even a crude sense of direction
    buys in search effort.
    """
    goal_pos = frozenset(goal_pos)

    def h(state):
        return len(goal_pos - state)

    start = frozenset(initial)
    counter = 0
    open_heap = [(h(start), 0, counter, start, [])]
    best_g = {start: 0}
    expanded = 0
    while open_heap:
        _, g, _, state, plan = heapq.heappop(open_heap)
        if g > best_g.get(state, float("inf")):
            continue
        expanded += 1
        if goal_pos <= state:
            return plan, expanded
        for a in actions:
            if applicable(state, a):
                nxt = apply(state, a)
                ng = g + 1
                if ng < best_g.get(nxt, float("inf")):
                    best_g[nxt] = ng
                    counter += 1
                    heapq.heappush(open_heap,
                                   (ng + h(nxt), ng, counter, nxt, plan + [a]))
    return None, expanded


def simulate(initial, plan):
    """Execute a plan, checking every precondition. Returns (ok, end_state)."""
    state = frozenset(initial)
    for a in plan:
        if not applicable(state, a):
            return False, state
        state = apply(state, a)
    return True, state
