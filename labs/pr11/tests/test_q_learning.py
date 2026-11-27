"""Тесты обновления Q и ε-жадного выбора (unittest, без сторонних библиотек)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lane_env import ACTIONS, LaneEnv  # noqa: E402
import train  # noqa: E402


class UpdateTest(unittest.TestCase):
    """Q(s,a)=1, r=2, max Q(s′,a′)=4, α=0.2, γ=0.95."""

    def test_terminated_ignores_next_state(self):
        self.assertAlmostEqual(train.updated_q(1.0, 2.0, 4.0, terminated=True), 1.20, places=9)

    def test_truncated_bootstraps_from_next_state(self):
        self.assertAlmostEqual(train.updated_q(1.0, 2.0, 4.0, terminated=False), 1.96, places=9)

    def test_terminal_and_truncated_differ(self):
        self.assertNotAlmostEqual(train.updated_q(1.0, 2.0, 4.0, True),
                                  train.updated_q(1.0, 2.0, 4.0, False))


class EnvTransitionTest(unittest.TestCase):

    def test_first_transition_seed_12(self):
        env = LaneEnv()
        state, _ = env.reset(seed=12)
        next_state, reward, terminated, truncated, _ = env.step('straight')
        self.assertEqual((state, next_state), ((1, 8), (1, 7)))
        self.assertAlmostEqual(reward, 0.85)
        self.assertFalse(terminated or truncated)

    def test_limit_truncates_without_termination(self):
        env = LaneEnv()
        env.reset(seed=0)
        for _ in range(13):
            *_, terminated, truncated, _ = env.step('stop')
            self.assertFalse(terminated or truncated)
        *_, terminated, truncated, _ = env.step('stop')
        self.assertFalse(terminated)
        self.assertTrue(truncated)


class PolicyTest(unittest.TestCase):

    def test_greedy_tie_takes_first_action(self):
        self.assertEqual(train.greedy_index([0.0, 0.0, 0.0, 0.0]), 0)
        self.assertEqual(train.greedy_index([0.0, 2.0, 2.0, 1.0]), 1)

    def test_epsilon_schedule(self):
        self.assertEqual(train.epsilon_for(0), 1.0)
        self.assertAlmostEqual(train.epsilon_for(600), 0.5)
        self.assertEqual(train.epsilon_for(1999), 0.05)

    def test_epsilon_zero_is_greedy(self):
        rng = Random(1)
        self.assertEqual({train.choose_action([0, 5, 1, 0], 0.0, rng) for _ in range(50)}, {1})

    def test_epsilon_one_explores_all_actions(self):
        rng = Random(1)
        picks = {train.choose_action([0, 5, 1, 0], 1.0, rng) for _ in range(200)}
        self.assertEqual(picks, set(range(len(ACTIONS))))


class TableTest(unittest.TestCase):

    def test_saved_table_shape_and_finiteness(self):
        table = train.train(episodes=50)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'q.json'
            train.save_table(table, path)
            spec = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(spec['schema_version'], 1)
        q = spec['q']
        self.assertEqual((len(q), len(q[0]), len(q[0][0])), (8, 7, 4))

    def test_training_is_deterministic(self):
        self.assertEqual(train.train(episodes=100), train.train(episodes=100))


if __name__ == '__main__':
    unittest.main()
