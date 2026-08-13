"""Oppositional cases that 0.2.0 still fails — stamp pollution, no-op accepts, bad utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from loop.edits import apply_bounded_edits_detailed, rank_edits, strip_audit_stamps
from loop.optimize import Article, run_loop
from loop.paths import PathSafetyError, resolve_output
from loop.scorers import HeuristicChecklistScorer, SkillAwareMockScorer


def _articles(n: int = 5) -> list[Article]:
    return [Article(id=f"a{i}", content=f"Article {i} about evidence and examples.") for i in range(n)]


def test_missed_edits_cannot_invent_a_gain():
    """A candidate with zero successful edits must not beat the current skill."""
    skill = "unchanged skill body\n"
    result = run_loop(
        skill,
        _articles(),
        SkillAwareMockScorer(seed=99),
        epochs=3,
        train_n=3,
        selection_n=2,
        propose=lambda _s, _e: [{"type": "delete", "old_text": "DOES-NOT-EXIST", "utility": 1}],
    )
    assert all(not rec.accepted for rec in result.epochs)
    assert all(rec.success_count == 0 for rec in result.epochs)
    assert all(rec.current_score == rec.candidate_score for rec in result.epochs)
    assert "skillopt-content-edit" not in result.best_skill
    assert strip_audit_stamps(result.best_skill) == strip_audit_stamps(skill)


def test_loop_does_not_accumulate_audit_stamps():
    skill = Path("skill_template.md").read_text(encoding="utf-8")
    result = run_loop(
        skill,
        _articles(),
        SkillAwareMockScorer(seed=2),
        epochs=3,
        train_n=3,
        selection_n=2,
    )
    assert result.best_skill.count("skillopt-content-edit") == 0


def test_non_numeric_utility_is_treated_as_zero():
    ranked = rank_edits(
        [
            {"type": "delete", "old_text": "a", "utility": "nope"},
            {"type": "delete", "old_text": "b", "utility": 1},
        ],
        1,
    )
    assert ranked[0]["old_text"] == "b"


def test_relative_path_escape_is_refused(tmp_path: Path):
    with pytest.raises(PathSafetyError):
        resolve_output(Path("../outside.md"), cwd=tmp_path, allow_absolute=False)


def test_heuristic_token_window_is_order_stable():
    skill = "zeta alpha beta gamma delta epsilon theta"
    article = "alpha beta gamma"
    s = HeuristicChecklistScorer(max_tokens=3)
    scores = [s.score(article, "id", skill) for _ in range(8)]
    assert len(set(scores)) == 1


def test_strip_audit_stamps_removes_only_our_comments():
    body = "hello\n\n<!-- skillopt-content-edit 2026-08-13T12:00Z: add:append -->\nkeep"
    assert "skillopt-content-edit" not in strip_audit_stamps(body)
    assert "hello" in strip_audit_stamps(body)
    assert "keep" in strip_audit_stamps(body)


def test_stamped_apply_is_opt_in():
    result = apply_bounded_edits_detailed(
        "hello",
        [{"type": "add", "new_text": "x", "utility": 1}],
        1,
        stamp=False,
    )
    assert "skillopt-content-edit" not in result.text
    stamped = apply_bounded_edits_detailed(
        "hello",
        [{"type": "add", "new_text": "x", "utility": 1}],
        1,
        stamp=True,
    )
    assert "skillopt-content-edit" in stamped.text
