"""
Scorers for the skillopt-content loop.

IMPORTANT: DeterministicMockScorer exists only so the control loop can be
exercised offline. It is NOT a research evaluator and must not be presented
as SkillOpt paper evaluation.
"""

from __future__ import annotations

import hashlib
from typing import Protocol


class Scorer(Protocol):
    def score(self, article: str, article_id: str, skill_version: str = "v0") -> float:
        ...


class DeterministicMockScorer:
    """
    Plumbing-only scorer: stable floats from content hash + optional version bonus.

    DO NOT use this to claim real content quality improvements.
    """

    def __init__(self, seed: int = 42, version_bonus: float = 0.5):
        self.seed = seed
        self.version_bonus = version_bonus

    def score(self, article: str, article_id: str, skill_version: str = "v0") -> float:
        h = hashlib.sha256((article + str(self.seed)).encode()).hexdigest()
        base = 6.5 + (int(h[:4], 16) / 0xFFFF) * 2.5  # ~6.5–9.0
        bonus = self.version_bonus if skill_version == "v1" else 0.0
        return round(base + bonus, 2)


class ConstantScorer:
    """Always returns the same score (useful for gate tests)."""

    def __init__(self, value: float = 7.0):
        self.value = value

    def score(self, article: str, article_id: str, skill_version: str = "v0") -> float:
        return self.value
