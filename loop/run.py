#!/usr/bin/env python3
"""
CLI for the SkillOpt-style content-skill loop.

Default scorer is SkillAwareMockScorer (plumbing + honest gate).
Wire a real scorer before claiming quality gains.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from loop.optimize import load_articles, run_loop
from loop.paths import PathSafetyError, resolve_existing, resolve_output
from loop.scorers import get_scorer


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="SkillOpt-style content skill loop",
        epilog=(
            "Default scorer is skill-aware mock plumbing. "
            "Do not publish quality claims from mock scores."
        ),
    )
    ap.add_argument("--skill", default="skill_template.md", help="Path to skill markdown")
    ap.add_argument("--articles", default="examples/articles", help="Directory of .md articles")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=int, default=2, help="Textual learning rate (max edits per step)")
    ap.add_argument("--train-n", type=int, default=3)
    ap.add_argument("--selection-n", type=int, default=2)
    ap.add_argument("--out", default="best_skill.md", help="Export path for best skill")
    ap.add_argument(
        "--scorer",
        default="skill-aware",
        help="mock | skill-aware | heuristic | constant",
    )
    ap.add_argument("--log-jsonl", default="", help="Optional JSONL event log path")
    ap.add_argument("--rejected-jsonl", default="", help="Optional rejected-edit dump")
    ap.add_argument("--allow-absolute", action="store_true", help="Allow absolute output paths")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true", help="Print LoopResult summary as JSON")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        skill_path = resolve_existing(Path(args.skill), must_be_file=True)
        articles_dir = resolve_existing(Path(args.articles), must_be_dir=True)
        out_path = resolve_output(Path(args.out), allow_absolute=args.allow_absolute)
        scorer = get_scorer(args.scorer)
    except (FileNotFoundError, PathSafetyError, ValueError) as exc:
        print(f"[skillopt-content] error: {exc}", file=sys.stderr)
        return 2

    articles = load_articles(articles_dir, limit=args.train_n + args.selection_n)
    if not articles:
        print(f"[skillopt-content] error: no .md articles in {articles_dir}", file=sys.stderr)
        return 3

    if not args.quiet:
        print(
            f"[skillopt-content] scorer={type(scorer).__name__} "
            "(not SkillOpt paper evaluation)"
        )
        print(f"[skillopt-content] start {datetime.now(timezone.utc).isoformat()}")
        print(f"[data] {len(articles)} articles from {articles_dir}")

    log_handle = None
    try:
        if args.log_jsonl:
            log_path = resolve_output(Path(args.log_jsonl), allow_absolute=args.allow_absolute)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = log_path.open("w", encoding="utf-8")

        result = run_loop(
            skill_path.read_text(encoding="utf-8"),
            articles,
            scorer,
            epochs=args.epochs,
            lr=args.lr,
            train_n=args.train_n,
            selection_n=args.selection_n,
            event_log=log_handle,
            scorer_name=type(scorer).__name__,
        )
    except ValueError as exc:
        print(f"[skillopt-content] error: {exc}", file=sys.stderr)
        return 2
    finally:
        if log_handle is not None:
            log_handle.close()

    if not args.quiet:
        for rec in result.epochs:
            print(f"\n=== Epoch {rec.epoch}/{args.epochs} ===")
            print(f"[rollout] train scores: {rec.train_scores}")
            print(f"[gate] current={rec.current_score:.2f} candidate={rec.candidate_score:.2f}")
            if rec.accepted:
                print(f"[accept] applied={rec.success_count} best={result.best_score:.2f}")
            else:
                print(f"[reject] drop={rec.drop:.2f} applied={rec.success_count}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result.best_skill, encoding="utf-8")
    if not args.quiet:
        print(
            f"\n[done] wrote {out_path} "
            f"(best_score={result.best_score:.2f}, rejected={len(result.rejected)})"
        )

    if args.rejected_jsonl:
        rej_path = resolve_output(Path(args.rejected_jsonl), allow_absolute=args.allow_absolute)
        rej_path.parent.mkdir(parents=True, exist_ok=True)
        with rej_path.open("w", encoding="utf-8") as fh:
            for item in result.rejected:
                fh.write(json.dumps(item) + "\n")

    if args.json:
        print(result.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
