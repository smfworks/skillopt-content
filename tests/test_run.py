"""CLI smoke tests that match the 0.2 runner (int return codes)."""

from __future__ import annotations

from pathlib import Path

from loop.optimize import load_articles, mean_score
from loop.run import main
from loop.scorers import ConstantScorer


def test_load_articles_returns_article_objects(tmp_path: Path):
    (tmp_path / "b.md").write_text("second")
    (tmp_path / "a.md").write_text("first")
    (tmp_path / "note.txt").write_text("ignored")
    arts = load_articles(tmp_path, limit=8)
    assert [a.id for a in arts] == ["a", "b"]
    assert arts[0].content == "first"


def test_mean_score_empty():
    assert mean_score(ConstantScorer(), [], "skill") == 0.0


def test_cli_missing_skill_returns_2(tmp_path: Path):
    assert main(["--skill", str(tmp_path / "nope.md"), "--articles", str(tmp_path)]) == 2


def test_cli_empty_articles_returns_3(tmp_path: Path):
    skill = tmp_path / "skill.md"
    skill.write_text("# skill\n")
    arts = tmp_path / "arts"
    arts.mkdir()
    assert main(["--skill", str(skill), "--articles", str(arts), "--allow-absolute"]) == 3
