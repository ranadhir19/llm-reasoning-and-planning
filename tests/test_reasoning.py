"""Tests for the reasoning tasks (R1-R4). Run: python3 -m unittest discover tests"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from problems import PROBLEMS, solve  # noqa: E402
from toy_reasoner import direct_answer, sample_chain  # noqa: E402
import r1_direct_vs_cot as r1  # noqa: E402
import r2_self_consistency as r2  # noqa: E402
import r3_verifier as r3  # noqa: E402
import r4_tree_search as r4  # noqa: E402


class TestProblems(unittest.TestCase):
    def test_gold_is_last_step(self):
        for p in PROBLEMS:
            values, answer = solve(p)
            self.assertEqual(answer, values[-1], p["id"])
            self.assertGreaterEqual(len(values), 1)

    def test_no_answer_leaks_into_direct_reach(self):
        # The designed trap: total chairs (224) is not a text number, so the
        # shortcut solver cannot use it and must fail p02.
        p02 = next(p for p in PROBLEMS if p["id"] == "p02_hall_chairs")
        _, gold = solve(p02)
        self.assertNotEqual(direct_answer(p02), gold)

    def test_direct_can_do_one_step(self):
        p10 = next(p for p in PROBLEMS if p["id"] == "p10_aquarium_tickets")
        _, gold = solve(p10)
        self.assertEqual(direct_answer(p10), gold)


class TestR1(unittest.TestCase):
    def test_chain_beats_direct_at_fixed_seed(self):
        res = r1.run_toy(seed=18)
        self.assertEqual(res["direct_correct"], 1)
        self.assertGreaterEqual(res["chain_correct"], 11)
        self.assertGreater(res["chain_correct"], res["direct_correct"])


class TestR2(unittest.TestCase):
    def test_vote_at_least_single(self):
        res = r2.run(k=9, seed=11)
        self.assertEqual(res["vote_correct"], 14)
        self.assertGreaterEqual(res["vote_correct"], res["single_correct"])


class TestR3(unittest.TestCase):
    def test_verifier_at_least_first(self):
        res = r3.run(n=8, seed=23)
        self.assertEqual(res["best_correct"], 14)
        self.assertGreater(res["best_correct"], res["first_correct"])

    def test_verify_scores_perfect_chain_highest(self):
        p = PROBLEMS[0]
        _, gold = solve(p)
        perfect = [{"desc": s["desc"], "claimed": v, "gold": v}
                   for s, v in zip(p["steps"], solve(p)[0])]
        self.assertEqual(r3.verify(perfect), (True, len(p["steps"])))


class TestR4(unittest.TestCase):
    def test_greedy_fails_tree_solves(self):
        solved_g, _ = r4.greedy_chain()
        self.assertFalse(solved_g)
        path, _ = r4.tree_search()
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 7)

    def test_chain_sampler_is_deterministic_per_seed(self):
        p = PROBLEMS[4]
        a1, _ = sample_chain(p, random.Random(5))
        a2, _ = sample_chain(p, random.Random(5))
        self.assertEqual(a1, a2)


if __name__ == "__main__":
    unittest.main()
