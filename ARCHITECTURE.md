# Architecture

## Purpose

A small, inspectable control loop for **editing agent skill markdown** the way SkillOpt describes in spirit: propose bounded textual edits, accept only if a held-out score strictly improves.

This repo is a **kit**, not a reproduction of the SkillOpt paper evaluation stack.

## Components

```
skill markdown ──► proposals ──► apply_bounded_edits (Lt) ──► candidate skill
        ▲                                                      │
        │                                                      ▼
        └── reject / accept ◄── validation gate ◄── scorer(selection, skill)
```

| Module | Responsibility |
|--------|----------------|
| `loop/edits.py` | Rank, validate, and apply `add` / `delete` / `replace`. Optional audit stamp. |
| `loop/scorers.py` | Pluggable scorers. Mock (plumbing), checklist (skill hygiene), constant (tests). |
| `loop/run.py` | CLI: split articles, run epochs, write `best_skill.md` + optional JSON audit. |

## Scoring contract

Every scorer implements:

```python
def score(self, article: str, article_id: str, skill_text: str = "") -> float
```

**v0.1 bug:** the gate passed a hardcoded `skill_version="v1"` and never scored the candidate skill text. A mock bonus made almost every candidate look better. **v0.2** passes the full candidate skill string. Acceptance now depends on the scorer actually seeing the edited document.

## Failure modes we accept

- Default proposals are static examples, not LLM reflection.
- Checklist scorer measures document hygiene, not article quality.
- Mock scorer is hash-based and must not be used in published quality claims.
- No distributed locking; one process, local files only.

## Observability

- stderr logs via `logging` (`[skillopt-content] …`)
- `--audit path.json` writes a structured run record
- `--json` prints the same summary to stdout
- Each accepted/rejected epoch records applied vs missed edits
