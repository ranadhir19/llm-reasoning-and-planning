"""P2 -- Plan, execute, monitor, REPLAN: the courier whose road closes.

Concept (article Part 2, Section 9): a plan is a hypothesis about the
world. A courier plans the shortest route across a depot yard; partway
through the run, a forklift blocks the corridor the route depends on.
Two executors:

* blind executor -- follows the plan without checking it against the
  world. It walks up to the closure and the delivery fails.
* monitoring executor -- before every step it compares the world with
  what the plan assumed. The moment they disagree it stops, and replans
  from the *actual* current state (the closed cell now marked). The
  delivery takes longer than planned -- and succeeds.

The yard has exactly two crossings from the west side to the east side:
the short middle corridor (which the original plan uses) and a long
southern bridge (which only the replan uses).

Run:  python3 src/p2_replan_gridworld.py
"""

from __future__ import annotations

import heapq

# 9 wide x 6 tall. '#' wall, '.' open, 'S' start, 'G' goal.
GRID = [
    ".........",
    ".###.##.#",
    ".#.....#.",
    ".#.###.#.",
    ".#...#...",
    ".###....G",
]
START = (4, 0)   # (row, col)
GOAL = (5, 8)
# The closure: after 3 executed steps, this corridor cell becomes blocked.
# The executors discover it only when their plan meets it.
CLOSURE_AFTER_STEPS = 3
CLOSURE_CELLS = {(2, 5)}


def parse_walls(grid):
    return {(r, c) for r, row in enumerate(grid)
            for c, ch in enumerate(row) if ch == "#"}


def neighbours(cell, walls, rows, cols):
    r, c = cell
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        n = (r + dr, c + dc)
        if 0 <= n[0] < rows and 0 <= n[1] < cols and n not in walls:
            yield n


def astar(start, goal, walls, rows, cols):
    def h(x):
        return abs(x[0] - goal[0]) + abs(x[1] - goal[1])

    open_heap = [(h(start), 0, start, [start])]
    best = {start: 0}
    while open_heap:
        _, g, cell, path = heapq.heappop(open_heap)
        if cell == goal:
            return path
        if g > best.get(cell, float("inf")):
            continue
        for n in neighbours(cell, walls, rows, cols):
            ng = g + 1
            if ng < best.get(n, float("inf")):
                best[n] = ng
                heapq.heappush(open_heap, (ng + h(n), ng, n, path + [n]))
    return None


def draw(grid, extra_walls, path, mark):
    rows = [list(r) for r in grid]
    for (r, c) in extra_walls:
        rows[r][c] = "X"
    for (r, c) in path:
        if rows[r][c] == ".":
            rows[r][c] = mark
    rows[START[0]][START[1]] = "S"
    rows[GOAL[0]][GOAL[1]] = "G"
    return "\n".join("".join(r) for r in rows)


def run():
    rows_n, cols_n = len(GRID), len(GRID[0])
    walls = parse_walls(GRID)
    plan = astar(START, GOAL, walls, rows_n, cols_n)
    print("P2 -- plan, execute, monitor, replan (courier grid)")
    print(f"\nOriginal plan: {len(plan) - 1} steps "
          f"(through the middle corridor, cell (2, 5))")
    print(draw(GRID, set(), plan, "*"))

    # Blind executor: walks the plan, never checks the world.
    blind_steps, blind_failed_at = 0, None
    for nxt in plan[1:]:
        world_now = walls | (CLOSURE_CELLS
                             if blind_steps >= CLOSURE_AFTER_STEPS else set())
        if nxt in world_now:
            blind_failed_at = nxt
            break
        blind_steps += 1
    print(f"\nBlind executor: took {blind_steps} steps, then its next planned "
          f"cell {blind_failed_at} was blocked. It has no procedure for "
          f"this. Delivery FAILED.")

    # Monitoring executor: checks each next cell; replans on disagreement.
    pos, walked, replans = START, [START], 0
    current_plan = plan
    while pos != GOAL:
        closure_live = (len(walked) - 1) >= CLOSURE_AFTER_STEPS
        blocked = walls | (CLOSURE_CELLS if closure_live else set())
        nxt = current_plan[1]
        if nxt in blocked:
            replans += 1
            print(f"\nMonitor: at step {len(walked) - 1}, position {pos} -- "
                  f"the planned next cell {nxt} is blocked in the real "
                  f"world (corridor closed). Replanning from the actual "
                  f"position.")
            current_plan = astar(pos, GOAL, blocked, rows_n, cols_n)
            print(f"New plan: {len(current_plan) - 1} steps remaining, "
                  f"via the southern bridge.")
            nxt = current_plan[1]
        walked.append(nxt)
        current_plan = current_plan[1:]
        pos = nxt
    print(f"\nMonitoring executor: delivery SUCCEEDED in "
          f"{len(walked) - 1} steps ({replans} replan), versus "
          f"{len(plan) - 1} planned.")
    print(draw(GRID, CLOSURE_CELLS, walked, "+"))
    return {"planned_steps": len(plan) - 1,
            "blind_failed": blind_failed_at is not None,
            "blind_steps": blind_steps,
            "monitor_steps": len(walked) - 1, "replans": replans}


if __name__ == "__main__":
    run()
