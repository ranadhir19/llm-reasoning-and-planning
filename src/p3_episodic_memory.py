"""P3 -- Episodic memory: the depot gate, learned across attempts.

Concept (article Part 2, Section 10): the Reflexion pattern (Shinn et al.,
2023). An agent tries a task, fails, converts the failure into a verbal
*episode* stored in memory, and on the next attempt retrieves the episode
and behaves differently. The critique is anchored to something real -- the
environment's refusal -- not to the agent's opinion of itself.

The task: a depot worker must leave through the east gate. The gate is
locked; the key hangs in a side pocket of the depot. The agent's planner is
deliberately naive: its internal model treats the gate as an ordinary
door, so it plans the beeline. Watch:

* Attempt 1 (no memory): beeline to the gate -> "locked" -> attempt fails.
  The failure is written into episodic memory as a verbal lesson plus the
  structured fact the planner can use (gate needs key; key location).
* Attempt 2 (with memory): the planner consults memory *before* planning,
  routes via the key, unlocks the gate, succeeds.
* Control (attempt 2, memory wiped): the same naive planner fails in
  exactly the same way again. Memory, not luck, made the difference.

Run:  python3 src/p3_episodic_memory.py
"""

from __future__ import annotations

import heapq

# Depot: 5 rows x 9 cols. The key hangs in a side pocket at (3, 4);
# the locked gate is the east opening at (2, 8).
GRID = [
    ".........",
    ".##.##.#.",
    ".#.......",
    ".#.#..##.",
    ".........",
]
START = (4, 0)
KEY = (3, 4)
GATE = (2, 8)
STEP_BUDGET = 40


def parse_walls(grid):
    return {(r, c) for r, row in enumerate(grid)
            for c, ch in enumerate(row) if ch == "#"}


def shortest_path(start, goal, walls, rows, cols):
    def h(x):
        return abs(x[0] - goal[0]) + abs(x[1] - goal[1])

    heap = [(h(start), 0, start, [start])]
    best = {start: 0}
    while heap:
        _, g, cell, path = heapq.heappop(heap)
        if cell == goal:
            return path
        if g > best.get(cell, float("inf")):
            continue
        r, c = cell
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            n = (r + dr, c + dc)
            if 0 <= n[0] < rows and 0 <= n[1] < cols and n not in walls:
                ng = g + 1
                if ng < best.get(n, float("inf")):
                    best[n] = ng
                    heapq.heappush(heap, (ng + h(n), ng, n, path + [n]))
    return None


class EpisodicMemory:
    """A tiny episodic store: verbal lessons + the structured facts."""

    def __init__(self):
        self.episodes = []

    def store(self, text, facts):
        self.episodes.append({"text": text, "facts": facts})

    def recall(self, key, default=None):
        for ep in self.episodes:
            if key in ep["facts"]:
                return ep["facts"][key]
        return default


def attempt(memory, walls, rows, cols):
    """One attempt. Returns (success, steps_taken, events)."""
    events = []
    knows_key = memory.recall("gate_needs_key", False) if memory else False
    key_at = memory.recall("key_at", None) if memory else None
    waypoints = ([key_at] if knows_key and key_at else []) + [GATE]
    pos, steps, has_key = START, 0, False
    for target in waypoints:
        path = shortest_path(pos, target, walls, rows, cols)
        for cell in path[1:]:
            pos, steps = cell, steps + 1
            if steps > STEP_BUDGET:
                return False, steps, events + ["out of steps"]
            # The key is collected only on a deliberate detour to fetch it
            # (this leg's target), not by wandering past the pocket.
            if pos == KEY and target == KEY and not has_key:
                has_key = True
                events.append(f"step {steps}: picked up the key at {KEY}")
    if pos == GATE and not has_key:
        events.append(f"step {steps}: arrived at the gate -- LOCKED. "
                      f"The environment refuses the action 'exit'.")
        return False, steps, events
    events.append(f"step {steps}: unlocked the gate and exited")
    return True, steps, events


def reflect(success, events):
    """Turn an observed failure into a stored verbal episode."""
    if success:
        return None
    return ("Episode: I walked the beeline to the east gate and it was "
            "LOCKED -- the action failed. The key hangs in the side "
            f"pocket at {KEY}. Next time: fetch the key first, then go "
            "to the gate.",
            {"gate_needs_key": True, "key_at": KEY})


def run():
    walls = parse_walls(GRID)
    rows, cols = len(GRID), len(GRID[0])
    print("P3 -- episodic memory across attempts (Reflexion in miniature)")
    print(f"Depot: start {START}, key at {KEY}, locked gate at {GATE}, "
          f"step budget {STEP_BUDGET}")

    memory = EpisodicMemory()
    ok1, steps1, ev1 = attempt(memory, walls, rows, cols)
    print(f"\nAttempt 1 (memory empty): success={ok1}, steps={steps1}")
    for e in ev1:
        print(f"    {e}")
    episode = reflect(ok1, ev1)
    if episode:
        memory.store(*episode)
        print(f"    Stored episode: \"{episode[0]}\"")

    ok2, steps2, ev2 = attempt(memory, walls, rows, cols)
    print(f"\nAttempt 2 (with memory): success={ok2}, steps={steps2}")
    for e in ev2:
        print(f"    {e}")

    wiped = EpisodicMemory()
    okc, stepsc, evc = attempt(wiped, walls, rows, cols)
    print(f"\nControl -- attempt 2 with memory wiped: success={okc}, "
          f"steps={stepsc}")
    for e in evc:
        print(f"    {e}")
    print("\nSame planner, same world. The only difference between the "
          "second attempt and the control is one stored sentence, written "
          "from a real failure and read before planning.")
    return {"attempt1": (ok1, steps1), "attempt2_memory": (ok2, steps2),
            "control_no_memory": (okc, stepsc)}


if __name__ == "__main__":
    run()
