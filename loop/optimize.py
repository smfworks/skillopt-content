"""Core SkillOpt-style optimization loop (testable, no I/O besides optional log)."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from loop.edits import apply_bounded_edits_detailed

ProposalFn = Callable[[str, int], list[dict[str, Any]]]


@dataclass
class Article:
    id: str
    content: str


@dataclass
class EpochRecord:
    epoch: int
    train_scores: list[float]
    current_score: float
    candidate_score: float
    accepted: bool
    applied: list[str]
    success_count: int
    drop: float | None = None


@dataclass
class LoopResult:
    best_skill: str
    best_score: float
    current_skill: str
    epochs: list[EpochRecord] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    articles_used: int = 0
    started_at: str = ""
    finished_at: str = ""
    scorer: str = ""

    def to_json(self) -> str:
        payload = asdict(self)
        payload["best_skill"] = f"<omitted {len(self.best_skill)} chars>"
        payload["current_skill"] = f"<omitted {len(self.current_skill)} chars>"
        return json.dumps(payload, indent=2)


def mean_score(scorer, articles: Sequence[Article], skill_text: str) -> float:
    if not articles:
        return 0.0
    scores = [float(scorer.score(a.content, a.id, skill_text)) for a in articles]
    return round(sum(scores) / len(scores), 2)


def split_articles(
    articles: Sequence[Article], train_n: int, selection_n: int
) -> tuple[list[Article], list[Article]]:
    if train_n < 0 or selection_n < 0:
        raise ValueError("train_n and selection_n must be >= 0")
    if not articles:
        raise ValueError("no articles loaded")
    if train_n + selection_n > len(articles):
        raise ValueError(
            f"need {train_n + selection_n} articles, only {len(articles)} available"
        )
    if selection_n == 0:
        raise ValueError("selection_n must be >= 1 so the validation gate can run")
    return list(articles[:train_n]), list(articles[train_n : train_n + selection_n])


def default_proposals(skill: str, epoch: int = 0) -> list[dict[str, Any]]:
    """
    Deterministic example proposals.

    Production callers should replace this with an LLM reflection step.
    The second proposal varies by epoch so later epochs are not no-ops
    after the first accept.
    """
    evidence_line = (
        "When two hypotheses conflict, choose the one with clearer evidence requirements."
    )
    proposals: list[dict[str, Any]] = [
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
                f"{evidence_line}\n"
                "Do NOT include Python code or pseudocode."
            ),
            "utility": 0.18,
        },
        {
            "type": "add",
            "after": 'No placeholders. No "[write X here]".',
            "new_text": (
                "Prefer one concrete example or counterexample over vague claims."
                if epoch == 0
                else f"Epoch {epoch + 1}: prefer named sources over unsourced authority."
            ),
            "utility": 0.12,
        },
    ]
    return proposals


def run_loop(
    skill_text: str,
    articles: Sequence[Article],
    scorer,
    *,
    epochs: int = 2,
    lr: int = 2,
    train_n: int = 3,
    selection_n: int = 2,
    propose: ProposalFn | None = None,
    event_log: TextIO | None = None,
    scorer_name: str = "",
) -> LoopResult:
    if epochs < 1:
        raise ValueError("epochs must be >= 1")
    if lr < 0:
        raise ValueError("lr must be >= 0")
    if not skill_text.strip():
        raise ValueError("skill text is empty")

    train, selection = split_articles(articles, train_n, selection_n)
    propose = propose or default_proposals
    started = datetime.now(timezone.utc).isoformat()

    current = skill_text
    best = skill_text
    best_score = mean_score(scorer, selection, current)
    records: list[EpochRecord] = []
    rejected: list[dict[str, Any]] = []

    def emit(event: dict[str, Any]) -> None:
        if event_log is None:
            return
        event_log.write(json.dumps(event, default=str) + "\n")
        event_log.flush()

    emit({"event": "start", "articles": len(articles), "train": len(train), "selection": len(selection)})

    for epoch in range(epochs):
        train_scores = [float(scorer.score(a.content, a.id, current)) for a in train]
        edits = propose(current, epoch)
        result = apply_bounded_edits_detailed(current, edits, lr)
        candidate = result.text
        cur_score = mean_score(scorer, selection, current)
        cand_score = mean_score(scorer, selection, candidate)
        accepted = cand_score > cur_score
        drop = None if accepted else round(cur_score - cand_score, 2)

        record = EpochRecord(
            epoch=epoch + 1,
            train_scores=train_scores,
            current_score=cur_score,
            candidate_score=cand_score,
            accepted=accepted,
            applied=list(result.applied),
            success_count=result.hit_count,
            drop=drop,
        )
        records.append(record)
        emit({"event": "epoch", **asdict(record)})

        if accepted:
            current = candidate
            if cand_score > best_score:
                best_score = cand_score
                best = candidate
        else:
            rejected.append(
                {
                    "epoch": epoch + 1,
                    "drop": drop,
                    "applied": list(result.applied),
                }
            )

    finished = datetime.now(timezone.utc).isoformat()
    emit({"event": "done", "best_score": best_score, "rejected": len(rejected)})
    return LoopResult(
        best_skill=best,
        best_score=best_score,
        current_skill=current,
        epochs=records,
        rejected=rejected,
        articles_used=len(train) + len(selection),
        started_at=started,
        finished_at=finished,
        scorer=scorer_name or type(scorer).__name__,
    )


def load_articles(articles_dir: Path, limit: int | None = None) -> list[Article]:
    paths = sorted(articles_dir.glob("*.md"))
    if limit is not None:
        paths = paths[:limit]
    return [
        Article(id=p.stem, content=p.read_text(encoding="utf-8", errors="replace"))
        for p in paths
    ]
