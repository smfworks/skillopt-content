"""Minimal SkillOpt-style loop for content skills."""

from loop.edits import (
    AppliedEdit,
    ApplyResult,
    EditError,
    EditResult,
    apply_bounded_edits,
    apply_bounded_edits_detailed,
    validate_edit,
)
from loop.optimize import Article, LoopResult, load_articles, run_loop
from loop.scorers import (
    ConstantScorer,
    DeterministicMockScorer,
    HeuristicChecklistScorer,
    SkillAwareMockScorer,
    get_scorer,
)

__version__ = "0.2.0"

__all__ = [
    "Article",
    "AppliedEdit",
    "ApplyResult",
    "ConstantScorer",
    "DeterministicMockScorer",
    "EditError",
    "EditResult",
    "HeuristicChecklistScorer",
    "LoopResult",
    "SkillAwareMockScorer",
    "apply_bounded_edits",
    "apply_bounded_edits_detailed",
    "get_scorer",
    "load_articles",
    "run_loop",
    "validate_edit",
    "__version__",
]
