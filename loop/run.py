#!/usr/bin/env python3
"""
CLI for the minimal SkillOpt-style content-skill loop.

Default scorer is DeterministicMockScorer (plumbing only).
Wire a real scorer before claiming quality gains.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Allow `python -m loop.run` from repo root
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from loop.edits import apply_bounded_edits
from loop.scorers import DeterministicMockScorer


def load_articles(articles_dir: Path, limit: int = 8) -> List[Dict[str, str]]:
    paths = sorted(articles_dir.glob("*.md"))[:limit]
    out = []
    for p in paths:
        out.append({"id": p.stem, "content": p.read_text(encoding="utf-8", errors="replace")})
    return out


def default_proposals(skill: str) -> List[Dict[str, Any]]:
    """Example proposals — replace with LLM reflection in production."""
    return [
        {
            "type": "replace",
            "old_text": (
                "You are a senior editor triaging article improvements.\n"
                "Select the highest-impact hypotheses to implement in this revision pass.\n"
                "Be ruthless: it is better to implement 2 hypotheses well than 4 poorly.\n"
                "Prefer edits that strengthen argumentative rigor and insight novelty over cosmetic polish.\n"
                "Do NOT include Python code or pseudocode."
            ),
            "new_text": (
                "You are a senior editor triaging article improvements.\n"
                "Select the highest-impact hypotheses to implement in this revision pass.\n"
                "Be ruthless: it is better to implement 2 hypotheses well than 4 poorly.\n"
                "Prefer edits that strengthen argumentative rigor and insight novelty over cosmetic polish.\n"
                "When two hypotheses conflict, choose the one with clearer evidence requirements.\n"
                "Do NOT include Python code or pseudocode."
            ),
            "utility": 0.18,
        },
        {
            "type": "add",
            "after": "No placeholders. No \"[write X here]\".",
            "new_text": "Prefer one concrete example or counterexample over vague claims.",
            "utility": 0.12,
        },
    ]


def mean_score(scorer, articles: List[Dict], skill_version: str) -> float:
    if not articles:
        return 0.0
    scores = [scorer.score(a["content"], a["id"], skill_version) for a in articles]
    return round(sum(scores) / len(scores), 2)


def main() -> None:
    ap = argparse.ArgumentParser(description="SkillOpt-style content skill loop (minimal)")
    ap.add_argument("--skill", default="skill_template.md", help="Path to skill markdown")
    ap.add_argument("--articles", default="examples/articles", help="Directory of .md articles")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=int, default=2, help="Textual learning rate (max edits per step)")
    ap.add_argument("--train-n", type=int, default=3)
    ap.add_argument("--selection-n", type=int, default=2)
    ap.add_argument("--out", default="best_skill.md", help="Export path for best skill")
    args = ap.parse_args()

    skill_path = Path(args.skill)
    articles_dir = Path(args.articles)
    if not skill_path.is_file():
        raise SystemExit(f"Skill not found: {skill_path}")
    if not articles_dir.is_dir():
        raise SystemExit(f"Articles dir not found: {articles_dir}")

    scorer = DeterministicMockScorer()
    print(
        "[skillopt-content] scorer=DeterministicMockScorer "
        "(plumbing only — not SkillOpt paper evaluation)"
    )
    print(f"[skillopt-content] start {datetime.now(timezone.utc).isoformat()}")

    articles = load_articles(articles_dir, limit=args.train_n + args.selection_n)
    print(f"[data] {len(articles)} articles from {articles_dir}")
    train = articles[: args.train_n]
    selection = articles[args.train_n : args.train_n + args.selection_n]

    current = skill_path.read_text(encoding="utf-8")
    best = current
    best_score = 0.0
    version = "v0"
    rejected: List[Dict] = []

    for epoch in range(args.epochs):
        print(f"\n=== Epoch {epoch + 1}/{args.epochs} ===")
        train_scores = [scorer.score(a["content"], a["id"], version) for a in train]
        print(f"[rollout] train scores: {train_scores}")

        edits = default_proposals(current)
        candidate = apply_bounded_edits(current, edits, args.lr)

        cand_score = mean_score(scorer, selection, "v1")
        cur_score = mean_score(scorer, selection, version)
        print(f"[gate] current={cur_score:.2f} candidate={cand_score:.2f}")

        if cand_score > cur_score:
            current = candidate
            version = "v1"
            if cand_score > best_score:
                best_score = cand_score
                best = candidate
            print(f"[accept] best={best_score:.2f}")
        else:
            rejected.append({"epoch": epoch + 1, "drop": round(cur_score - cand_score, 2)})
            print(f"[reject] drop={cur_score - cand_score:.2f}")

    Path(args.out).write_text(best, encoding="utf-8")
    print(f"\n[done] wrote {args.out} (best_score={best_score:.2f}, rejected={len(rejected)})")


if __name__ == "__main__":
    main()
