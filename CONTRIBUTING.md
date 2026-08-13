# Contributing

Thanks for helping harden `skillopt-content`.

## Ground rules

1. **No private org policy in defaults.** Voice, privacy, CTAs, and rosters belong in `profiles/` (private) or stay out of git.
2. **Do not claim SkillOpt paper results** from the bundled mock scorers.
3. **Tests first** for loop / edit / scorer changes. `pytest` must stay green.
4. **Keep the gate honest.** A candidate may be accepted only when the held-out score of the *candidate skill text* is strictly greater than the score of the current skill text.

## Dev setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check loop tests
```

## Pull requests

- One concern per PR.
- Include a short rationale in the description (what was broken, why this fix).
- Update `CHANGELOG.md` under Unreleased.
- Do not commit `.env`, `best_skill.md`, or `profiles/private/`.

## Release

Maintainers tag `vX.Y.Z` after CI is green on `main` and CHANGELOG is updated.
