"""Loop + CLI oppositional tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from loop.optimize import Article, default_proposals, run_loop, split_articles
from loop.paths import PathSafetyError, resolve_output
from loop.run import main
from loop.scorers import ConstantScorer, SkillAwareMockScorer


def _articles(n: int = 5) -> list[Article]:
    return [Article(id=f"a{i}", content=f"Article {i} about evidence and examples.") for i in range(n)]


def test_split_requires_selection_and_enough_rows():
    arts = _articles(4)
    train, sel = split_articles(arts, 2, 2)
    assert len(train) == 2 and len(sel) == 2
    with pytest.raises(ValueError, match="selection_n"):
        split_articles(arts, 2, 0)
    with pytest.raises(ValueError, match="need"):
        split_articles(arts, 3, 3)
    with pytest.raises(ValueError, match="no articles"):
        split_articles([], 1, 1)


def test_empty_skill_rejected():
    with pytest.raises(ValueError, match="empty"):
        run_loop("   ", _articles(), ConstantScorer(), epochs=1, train_n=2, selection_n=2)


def test_constant_scorer_never_accepts():
    skill = "You are a senior editor.\nNo placeholders. No \"[write X here]\"."
    result = run_loop(
        skill,
        _articles(),
        ConstantScorer(7.0),
        epochs=2,
        train_n=3,
        selection_n=2,
        scorer_name="constant",
    )
    assert all(not rec.accepted for rec in result.epochs)
    assert len(result.rejected) == 2
    assert result.best_score == 7.0
    assert result.best_skill == skill


def test_gate_uses_skill_text_not_fake_version():
    """Regression: old CLI scored candidates as version='v1' and always 'won'."""
    skill = Path("skill_template.md").read_text(encoding="utf-8")
    result = run_loop(
        skill,
        _articles(),
        SkillAwareMockScorer(seed=1),
        epochs=2,
        train_n=3,
        selection_n=2,
        propose=lambda _s, _e: [{"type": "add", "new_text": "unused-token-xyz", "utility": 1}],
    )
    # Either accept or reject is fine; scores must differ only if text differs.
    for rec in result.epochs:
        assert rec.current_score != rec.candidate_score or rec.success_count == 0


def test_default_proposals_vary_by_epoch():
    p0 = default_proposals("x", 0)
    p1 = default_proposals("x", 1)
    assert p0[1]["new_text"] != p1[1]["new_text"]


def test_cli_dry_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    out = tmp_path / "best.md"
    log = tmp_path / "events.jsonl"
    rc = main(
        [
            "--skill",
            "skill_template.md",
            "--articles",
            "examples/articles",
            "--epochs",
            "1",
            "--out",
            str(out),
            "--log-jsonl",
            str(log),
            "--allow-absolute",
            "--quiet",
        ]
    )
    assert rc == 0
    assert out.is_file()
    assert "skillopt-content-edit" in out.read_text(encoding="utf-8") or out.stat().st_size > 10
    assert log.read_text(encoding="utf-8").count("\n") >= 2


def test_cli_missing_skill(tmp_path: Path):
    rc = main(["--skill", str(tmp_path / "nope.md"), "--articles", str(tmp_path)])
    assert rc == 2


def test_cli_empty_articles(tmp_path: Path):
    skill = tmp_path / "s.md"
    skill.write_text("# skill\n", encoding="utf-8")
    arts = tmp_path / "arts"
    arts.mkdir()
    rc = main(["--skill", str(skill), "--articles", str(arts), "--allow-absolute"])
    assert rc == 3


def test_refuse_absolute_output_by_default(tmp_path: Path):
    with pytest.raises(PathSafetyError):
        resolve_output(tmp_path / "out.md", cwd=Path.cwd(), allow_absolute=False)
