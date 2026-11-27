#!/usr/bin/env python3
"""ПР11: табличное Q-learning для LaneEnv из course kit (rl_intro/lane_env.py).

Запуск из корня репозитория:
    PYTHONPATH=.course-kit/v1/rl_intro python3 -B labs/pr11/train.py \
        --output evidence/pr11/q-table.json
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
from random import Random
from typing import Sequence

from lane_env import ACTIONS, LANE_LIMIT, LaneEnv, ROUTE_LENGTH

ALPHA = 0.20
GAMMA = 0.95
EPISODES = 2000
ACTION_SEED = 12
EPSILON_MIN = 0.05
EPSILON_DECAY_EPISODES = 1200

QTable = list[list[list[float]]]
State = tuple[int, int]


def zero_table() -> QTable:
    """Нулевая таблица 8 × 7 × 4: [remaining - 1][offset + 3][действие]."""
    return [[[0.0] * len(ACTIONS) for _ in range(2 * LANE_LIMIT + 1)]
            for _ in range(ROUTE_LENGTH)]


def row(table: QTable, state: State) -> list[float]:
    """Строка оценок для состояния (offset, remaining)."""
    offset, remaining = state
    return table[remaining - 1][offset + LANE_LIMIT]


def epsilon_for(episode: int) -> float:
    """ε = max(0.05, 1 − i/1200) для эпизода с номером i."""
    return max(EPSILON_MIN, 1.0 - episode / EPSILON_DECAY_EPISODES)


def greedy_index(scores: Sequence[float]) -> int:
    """Индекс максимального Q; при равенстве — первое действие по порядку ACTIONS."""
    best = 0
    for index in range(1, len(scores)):
        if scores[index] > scores[best]:
            best = index
    return best


def choose_action(scores: Sequence[float], epsilon: float, rng: Random) -> int:
    """ε-жадный выбор: с вероятностью ε случайное действие, иначе жадное."""
    if rng.random() < epsilon:
        return rng.randrange(len(scores))
    return greedy_index(scores)


def td_target(reward: float, next_max: float, terminated: bool,
              gamma: float = GAMMA) -> float:
    """Цель обновления: r при terminated, иначе r + γ·max Q(s′, ·) (в т.ч. при truncated)."""
    if terminated:
        return reward
    return reward + gamma * next_max


def updated_q(q: float, reward: float, next_max: float, terminated: bool,
              alpha: float = ALPHA, gamma: float = GAMMA) -> float:
    """Q(s,a) ← Q(s,a) + α·(цель − Q(s,a))."""
    return q + alpha * (td_target(reward, next_max, terminated, gamma) - q)


def next_max_q(table: QTable, next_state: State) -> float:
    """max Q(s′, ·); для состояний вне таблицы (финиш, сход) — 0."""
    offset, remaining = next_state
    if remaining < 1 or abs(offset) > LANE_LIMIT:
        return 0.0
    return max(row(table, next_state))


def train(episodes: int = EPISODES, action_seed: int = ACTION_SEED) -> QTable:
    """Обучить Q-таблицу на эпизодах среды с seed 0…episodes−1."""
    table = zero_table()
    rng = Random(action_seed)
    env = LaneEnv()
    for episode in range(episodes):
        state, _ = env.reset(seed=episode)
        epsilon = epsilon_for(episode)
        while True:
            scores = row(table, state)
            action = choose_action(scores, epsilon, rng)
            next_state, reward, terminated, truncated, _ = env.step(ACTIONS[action])
            scores[action] = updated_q(
                scores[action], reward, next_max_q(table, next_state), terminated)
            if terminated or truncated:
                break
            state = next_state
    return table


def save_table(table: QTable, path: Path) -> None:
    """Сохранить {"schema_version": 1, "q": ...}; все оценки конечны."""
    if not all(isfinite(v) for d in table for o in d for v in o):
        raise ValueError('в Q-таблице есть нечисловые значения')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'schema_version': 1, 'q': table}, allow_nan=False) + '\n',
                    encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='куда сохранить JSON')
    parser.add_argument('--episodes', type=int, default=EPISODES)
    args = parser.parse_args()
    table = train(args.episodes)
    save_table(table, args.output)
    print(f'Q-таблица {ROUTE_LENGTH}×{2 * LANE_LIMIT + 1}×{len(ACTIONS)} '
          f'после {args.episodes} эпизодов сохранена в {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
