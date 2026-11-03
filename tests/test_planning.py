"""Tests for the planning tasks (P1-P4). Run: python3 -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from planner import astar_plan, bfs_plan, simulate  # noqa: E402
from p1_classical_planner import GOAL, INITIAL, blocks_actions  # noqa: E402
import p2_replan_gridworld as p2  # noqa: E402
import p3_episodic_memory as p3  # noqa: E402
import p4_plan_graph as p4  # noqa: E402


class TestP1(unittest.TestCase):
    def test_bfs_and_astar_find_valid_shortest_plan(self):
        actions = blocks_actions()
        for fn in (bfs_plan, astar_plan):
            plan, _ = fn(INITIAL, GOAL, actions)
            self.assertEqual(len(plan), 6)
            ok, end = simulate(INITIAL, plan)
            self.assertTrue(ok)
            self.assertTrue(GOAL <= end)

    def test_astar_expands_fewer_nodes(self):
        actions = blocks_actions()
        _, b = bfs_plan(INITIAL, GOAL, actions)
        _, a = astar_plan(INITIAL, GOAL, actions)
        self.assertLess(a, b)


class TestP2(unittest.TestCase):
    def test_blind_fails_monitor_succeeds(self):
        res = p2.run()
        self.assertEqual(res["planned_steps"], 17)
        self.assertTrue(res["blind_failed"])
        self.assertEqual(res["monitor_steps"], 21)
        self.assertEqual(res["replans"], 1)


class TestP3(unittest.TestCase):
    def test_memory_turns_failure_into_success(self):
        res = p3.run()
        self.assertFalse(res["attempt1"][0])
        self.assertTrue(res["attempt2_memory"][0])
        self.assertFalse(res["control_no_memory"][0])


class TestP4(unittest.TestCase):
    def test_fair_graph_numbers(self):
        f = p4.fair_analysis()
        self.assertEqual(f["sequential_hours"], 16)
        self.assertEqual(f["parallel_hours"], 5)
        self.assertEqual(len(f["invalidated"]), 4)
        self.assertEqual(f["n_tasks"], 9)

    def test_p1_causal_graph(self):
        plan, _ = astar_plan(INITIAL, GOAL, blocks_actions())
        edges = p4.causal_graph(INITIAL, plan)
        self.assertEqual(sum(len(v) for v in edges.values()), 8)
        inv = p4.descendants(edges, len(plan) // 2, len(plan))
        self.assertEqual(len(inv), 2)


if __name__ == "__main__":
    unittest.main()
