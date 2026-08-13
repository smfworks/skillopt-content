# skillopt-content

**SkillOpt-style training loop for agent content skills** — bounded `add` / `delete` / `replace` edits, a held-out validation gate, and a rejected-edit buffer. Optimize writing and edit-planning skills **without changing model weights**.

> This is an **applied pattern kit**, not a reimplementation of Microsoft’s SkillOpt paper or a drop-in for their forthcoming release.
> Paper: [SkillOpt (arXiv:2605.23904)](https://arxiv.org/abs/2605.23904) · Related: [Bilevel-Autoresearch](https://github.com/EdwardOptimization/Bilevel-Autoresearch)

Current kit version: **0.2.1** (oppositional pass: stamps no longer score).

---

## What you get

| Path | Purpose |
|------|---------|
| `skill_template.md` | Generic edit-planning skill (trainable text artifact) |
| `checklists/public-content.md` | Pre-publish triage checklist (any public longform) |
| `loop/` | SkillOpt-style loop: bounded edits + honest gate + JSONL audit |
| `examples/` | Tiny public sample posts for offline plumbing |
| `profiles/` | Optional org profiles (empty by default; see below) |
| `tests/` | Unit + oppositional tests for edits, scorers, CLI |
| `docs/ARCHITECTURE.md` | Control-loop design and failure modes |

**Not in this repo:** private org voice rules, personal/family privacy policies, social CTA conventions, agent rosters, or ops plumbing. Put those in a private profile or keep them out of git.

---

## Core idea (six mechanisms, simplified)

1. **Rollout** — run the current skill on a train split of articles
2. **Reflect** — propose structured `add` / `delete` / `replace` edits
3. **Bounded update** — apply at most `Lt` edits (textual learning rate)
4. **Validation gate** — accept only if held-out score **strictly** improves
5. **Rejected-edit buffer** — keep failed proposals as negative feedback
6. **Slow/meta (optional)** — epoch-level lessons without bloating the deployed skill

Deployed output is a compact skill markdown file you can load in any agent harness.

---

## Quick start

```bash
git clone https://github.com/smfworks/skillopt-content.git
cd skillopt-content
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Honest-gate mock (score depends on skill text + article)
python -m loop.run --skill skill_template.md --articles examples/articles --epochs 2 --scorer skill-aware

# Run the test suite
pytest
```

Installable CLI after `pip install -e .`:

```bash
skillopt-content --help
```

### Important honesty note

Bundled scorers are **offline mocks or heuristics**. They exist so the control loop can be exercised and tested without an LLM. **They are not a research-grade evaluator and not the SkillOpt paper’s evaluation stack.** Wire your own scorer (LLM rubric, human scores, or product metrics) before claiming real quality gains.

| `--scorer` | What it does | Use it for |
|------------|--------------|------------|
| `skill-aware` (default) | Hash of article + skill text | Testing that the gate is honest |
| `mock` | Hash of article only (ignores skill) | Reproducing v0.1 plumbing |
| `heuristic` | Token overlap between skill and article | Smoke-testing a corpus |
| `constant` | Fixed float | Proving the gate can reject |

---

## Using the skill template

1. Copy `skill_template.md` into your agent skill directory.
2. Run triage → plan → apply on real drafts (see checklist).
3. Optionally run the optimization loop when you have a real scorer and a train/selection split.

```
Before publish: 2–3 rigor/novelty edits max → concrete prose → privacy/safety gate → ship.
```

---

## Optional profiles

Organization-specific voice, privacy, or publishing rules **do not belong in the core package**.

```
profiles/
  README.md          # how to add a private profile
  example-org.md     # fictional example only
```

Keep real profiles in a private fork, submodule, or local path that is **not** forced as a default.

---

## Observability

```bash
python -m loop.run --log-jsonl run.jsonl --rejected-jsonl rejected.jsonl --json
```

- `--log-jsonl` writes start / epoch / done events
- `--rejected-jsonl` dumps rejected proposals
- `--json` prints a LoopResult summary (skill bodies omitted)

Absolute output paths are refused unless you pass `--allow-absolute`.

---

## Attribution

- **SkillOpt:** Yang et al., *SkillOpt: Executive Strategy for Self-Evolving Agent Skills*, arXiv:2605.23904
- **Bilevel Autoresearch:** mechanism-level outer loops for autoresearch (inspiration for treating process as optimizable)
- **This kit:** SMF Works — applied content-skill loop for multi-agent writing systems

---

## License

MIT — see [LICENSE](./LICENSE).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). PRs welcome for better scorers, multi-skill batches, and clearer examples.

Please do **not** open PRs that hard-code private org policies into the default skill path.

## Security

See [SECURITY.md](./SECURITY.md).
