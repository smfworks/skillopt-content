# Architecture

`skillopt-content` is a **textual learning-rate loop** for markdown skills. It does not train model weights.

```
articles/*.md ──► split (train / selection)
                      │
skill.md ──► rollout on train ──► propose edits
                      │
                      ▼
              apply at most Lt edits
                      │
                      ▼
         score(selection, current) vs score(selection, candidate)
                      │
            accept iff candidate > current
                      │
                      ▼
                 best_skill.md + rejected buffer
```

## Why the gate must see skill text

v0.1 scored `DeterministicMockScorer.score(article, id, version)` and the CLI always passed `"v1"` for the candidate. The mock added a flat +0.5 bonus for `v1`. That made the gate a coin with two heads.

v0.2 scores `scorer.score(article, id, skill_text)`. A candidate that does not change the skill cannot invent a gain on `SkillAwareMockScorer`. `DeterministicMockScorer` still ignores skill text on purpose, so it is no longer the default.

## Modules

| Module | Responsibility |
|--------|----------------|
| `loop/edits.py` | Validate and apply bounded add/delete/replace |
| `loop/scorers.py` | Pluggable scorers + registry |
| `loop/optimize.py` | Epoch loop, splits, proposals, `LoopResult` |
| `loop/paths.py` | Output path sandbox |
| `loop/run.py` | CLI only |

## Failure modes we test

- Empty skill / empty article dir / too-small split
- `lr = 0` (no-op)
- Missing replace/delete targets
- Unknown edit types (skip vs raise)
- Constant scorer never accepts
- Absolute `--out` refused without `--allow-absolute`
- **Missed edits cannot invent a gain** (no audit-stamp scoring)
- Non-numeric utility does not crash ranking

## What this is not

- Not the SkillOpt paper’s evaluator
- Not a multi-skill batch trainer
- Not a publisher (it writes a markdown file; you load it in your harness)
