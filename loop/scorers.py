"""
Scorers for the skillopt-content loop.

DeterministicMockScorer is plumbing-only. SkillAwareMockScorer makes the
validation gate honest: the score depends on skill text + article, so an
edit that does not change the skill cannot invent a gain.

None of these are the SkillOpt paper's evaluation stack. Wire a real
scorer (LLM rubric, human scores, product metrics) before claiming
quality gains.
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol


class Scorer(Protocol):
    def score(self, article: str, article_id: str, skill_text: str = "") -> float: ...


class DeterministicMockScorer:
    """
    Plumbing-only scorer: stable floats from article hash.

    Ignores skill_text. Do not use this to claim content quality gains.
    Kept so old plumbing demos stay reproducible.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def score(self, article: str, article_id: str, skill_text: str = "") -> float:
        payload = f"{article}\0{self.seed}\0{article_id}"
        h = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
        return round(6.5 + (int(h[:4], 16) / 0xFFFF) * 2.5, 2)


class SkillAwareMockScorer:
    """
    Offline mock whose score *does* change when the skill text changes.

    Still not a research evaluator. Use it to test the gate, not to
    publish quality claims.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def score(self, article: str, article_id: str, skill_text: str = "") -> float:
        payload = f"{article}\0{skill_text}\0{self.seed}\0{article_id}"
        h = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
        return round(6.0 + (int(h[:6], 16) / 0xFFFFFF) * 3.5, 2)


class HeuristicChecklistScorer:
    """
    Lightweight heuristic: reward articles that mention concrete tokens
    extracted from the skill (headers, imperative verbs, checklist words).

    Honest about being a heuristic. Useful as a smoke test that a skill
    and a corpus are talking about the same things.
    """

    TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{3,}")

    def __init__(self, max_tokens: int = 40) -> None:
        self.max_tokens = max_tokens

    def _tokens(self, text: str) -> set[str]:
        return {m.group(0).lower() for m in self.TOKEN_RE.finditer(text or "")}

    def score(self, article: str, article_id: str, skill_text: str = "") -> float:
        if not article.strip():
            return 0.0
        skill_tokens = sorted(self._tokens(skill_text))[: self.max_tokens]
        if not skill_tokens:
            return 5.0
        article_tokens = self._tokens(article)
        hits = sum(1 for t in skill_tokens if t in article_tokens)
        coverage = hits / max(len(skill_tokens), 1)
        length_bonus = min(len(article.split()) / 400.0, 1.0) * 1.5
        return round(4.0 + coverage * 4.5 + length_bonus, 2)


class ConstantScorer:
    """Always returns the same score (useful for gate tests)."""

    def __init__(self, value: float = 7.0) -> None:
        self.value = value

    def score(self, article: str, article_id: str, skill_text: str = "") -> float:
        return self.value


SCORERS = {
    "mock": DeterministicMockScorer,
    "skill-aware": SkillAwareMockScorer,
    "heuristic": HeuristicChecklistScorer,
    "constant": ConstantScorer,
}


def get_scorer(name: str, **kwargs):
    key = (name or "skill-aware").strip().lower()
    if key not in SCORERS:
        known = ", ".join(sorted(SCORERS))
        raise ValueError(f"unknown scorer {name!r}; choose one of: {known}")
    return SCORERS[key](**kwargs)
