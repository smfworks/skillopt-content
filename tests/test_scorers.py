"""Scorer contract tests."""

from __future__ import annotations

import pytest

from loop.scorers import (
    ConstantScorer,
    DeterministicMockScorer,
    HeuristicChecklistScorer,
    SkillAwareMockScorer,
    get_scorer,
)


def test_deterministic_mock_stable_and_ignores_skill():
    s = DeterministicMockScorer(seed=7)
    a = s.score("article text", "id1", "skill A")
    b = s.score("article text", "id1", "skill B")
    assert a == b
    assert 6.5 <= a <= 9.0


def test_skill_aware_changes_when_skill_changes():
    s = SkillAwareMockScorer(seed=7)
    a = s.score("article text", "id1", "skill A")
    b = s.score("article text", "id1", "skill B")
    assert a != b
    assert 6.0 <= a <= 9.5
    assert 6.0 <= b <= 9.5


def test_heuristic_empty_article_is_zero():
    s = HeuristicChecklistScorer()
    assert s.score("   ", "x", "Prefer evidence") == 0.0


def test_heuristic_rewards_overlap():
    s = HeuristicChecklistScorer()
    skill = "Prefer evidence requirements and concrete examples"
    high = s.score("This draft prefers evidence and concrete examples throughout.", "a", skill)
    low = s.score("zzzz qqqq", "b", skill)
    assert high > low


def test_constant_scorer():
    assert ConstantScorer(3.14).score("x", "y", "z") == 3.14


def test_get_scorer_unknown():
    with pytest.raises(ValueError, match="unknown scorer"):
        get_scorer("magic")
    assert isinstance(get_scorer("heuristic"), HeuristicChecklistScorer)
