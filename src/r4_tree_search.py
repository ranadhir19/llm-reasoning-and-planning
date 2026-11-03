"""R4 -- Tree search over reasoning steps: the river-crossing puzzle.

Concept (article Part 2, Section 6): a chain commits to its first path and
cannot take a step back. Some problems *require* an apparent step backwards.
The classic river crossing is the smallest such problem: a farmer must ferry
a wolf, a goat and a cabbage across a river, one item at a time; left alone
together, the wolf eats the goat and the goat eats the cabbage. The only
solution includes carrying the goat *back* once -- a move any "always make
progress" chain refuses to make.

Two solvers:
* greedy chain -- at each step takes the first legal move from a fixed
  preference order, but never carries an item back toward the start bank
  (its "no backwards steps" rule). It walks into a corner and stops.
* tree search -- breadth-first search over states, with a visited set and
  backtracking. It explores the fork in the road instead of betting on it.

Run:  python3 src/r4_tree_search.py
"""

from __future__ import annotations

from collections import deque

ITEMS = ("wolf", "goat", "cabbage")
EATS = {("wolf", "goat"), ("goat", "cabbage")}


def safe(bank: frozenset, farmer_present: bool) -> bool:
    if farmer_present:
        return True
    return not any(a in bank and b in bank for a, b in EATS)


def moves(state):
    """Yield (description, next_state). State = (farmer_side, near, far)."""
    side, near, far = state
    here, there = (near, far) if side == 0 else (far, near)
    options = [None] + [x for x in ITEMS if x in here]
    for item in options:
        new_here = here - {item} if item else here
        new_there = there | {item} if item else there
        if not safe(new_here, False) or not safe(new_there, True):
            continue
        nxt = (1 - side, new_here, new_there) if side == 0 else \
            (1 - side, new_there, new_here)
        desc = (f"farmer crosses {'with ' + item if item else 'alone'} "
                f"to the {'far' if side == 0 else 'near'} bank")
        yield desc, nxt


START = (0, frozenset(ITEMS), frozenset())
GOAL = (1, frozenset(), frozenset(ITEMS))


def greedy_chain(max_steps: int = 30):
    """Linear solver with a no-backwards rule. Returns (solved, path)."""
    state, path, seen = START, [], {START}
    for _ in range(max_steps):
        if state == GOAL:
            return True, path
        side = state[0]
        advanced = False
        for desc, nxt in moves(state):
            carrying_back = side == 1 and nxt[2] != state[2] and \
                len(nxt[1]) > len(state[1])
            if carrying_back:
                continue  # the rule: never carry anything back
            if nxt in seen:
                continue
            path.append(desc)
            seen.add(nxt)
            state = nxt
            advanced = True
            break
        if not advanced:
            return False, path
    return state == GOAL, path


def tree_search():
    """Breadth-first search. Returns (solution_path, nodes_expanded)."""
    frontier = deque([(START, [])])
    seen = {START}
    expanded = 0
    while frontier:
        state, path = frontier.popleft()
        expanded += 1
        if state == GOAL:
            return path, expanded
        for desc, nxt in moves(state):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append((nxt, path + [desc]))
    return None, expanded


def run():
    solved_g, path_g = greedy_chain()
    path_t, expanded = tree_search()
    print("R4 -- river crossing: greedy chain vs tree search")
    print(f"\nGreedy chain (no backwards steps): solved={solved_g} "
          f"after {len(path_g)} moves")
    for d in path_g:
        print(f"    {d}")
    if not solved_g:
        print("    ...stuck: every remaining legal move either revisits a "
              "state or carries an item back -- and its one rule forbids "
              "exactly the move the solution needs.")
    print(f"\nTree search (BFS): solved={path_t is not None} "
          f"nodes_expanded={expanded} solution_length={len(path_t)}")
    for i, d in enumerate(path_t, 1):
        print(f"    {i}. {d}")
    back = sum(1 for d in path_t if "to the near bank" in d and
               any(x in d for x in ITEMS))
    print(f"\nThe solution contains {back} 'backwards' item-carrying move(s) "
          "-- the goat must be ferried back once. A linear chain that "
          "refuses to retreat can never find it; search can, because "
          "retreating is just another branch.")
    return {"greedy_solved": solved_g, "greedy_moves": len(path_g),
            "tree_solved": path_t is not None, "nodes_expanded": expanded,
            "solution_length": len(path_t)}


if __name__ == "__main__":
    run()
