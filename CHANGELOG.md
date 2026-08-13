# Changelog

All notable changes to this project are documented here.

## [0.2.1] — 2026-08-13

Oppositional pass on 0.2.0.

### Fixed

- **Audit stamps were scored.** The loop stamped every candidate by default, so `SkillAwareMockScorer` hashed a timestamp even when every edit missed. A no-op could invent a gain. The loop now applies edits with `stamp=False`, strips existing audit comments before scoring, and **refuses to accept a candidate with zero successful edits**.
- **Non-numeric `utility` crashed ranking.** Invalid utilities now coerce to `0.0`.
- **Heuristic token window depended on set iteration order.** Tokens are sorted before the max-token window.
- **Partial writes.** CLI now writes `best_skill` via a temp file + `replace`.

### Added

- `strip_audit_stamps()` and oppositional tests in `tests/test_oppositional.py`.
- Rejected-edit records now include the proposed `edits` payload.
- Finite-score check in `mean_score`.

## [0.2.0] — 2026-08-13

Production-hardening pass (Harry / SMF Works Grok 4.6 sprint).

### Fixed

- **Validation gate was fake.** The CLI scored candidates with a hardcoded `skill_version="v1"`, so the mock scorer awarded a version bonus whether or not the skill text changed. The gate now scores the **candidate skill text** against the **current skill text**.
- **`best_score` initialized at 0.0**, so the first accept always replaced the original even when the original would have been better under a later scorer. Best now starts as the baseline held-out score.
- **Static proposals every epoch.** Default add-proposal now varies by epoch so later steps are not guaranteed no-ops.

### Added

- Extracted `loop.optimize.run_loop` (testable, no hidden I/O).
- `SkillAwareMockScorer` and `HeuristicChecklistScorer`.
- `--scorer`, `--log-jsonl`, `--rejected-jsonl`, `--json`, `--quiet`, `--allow-absolute`.
- Edit validation (`EditError`) and detailed apply results.
- Output path sandbox (relative to cwd unless `--allow-absolute`).
- pytest suite + GitHub Actions CI on Python 3.10–3.12.
- `pyproject.toml` install (`skillopt-content` CLI).
- CONTRIBUTING, SECURITY, ARCHITECTURE.

### Changed

- Default scorer is `skill-aware` (honest gate). `mock` remains for v0.1 plumbing.
- Package version 0.1.0 → 0.2.0.

## [0.1.0] — 2026-07-11

Initial public kit: bounded edits, mock scorer, skill template, examples.
