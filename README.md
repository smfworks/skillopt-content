# skillopt-content

**SkillOpt-style training loop for agent content skills** — bounded `add` / `delete` / `replace` edits, a held-out validation gate, and a rejected-edit buffer. Optimize writing and edit-planning skills **without changing model weights**.

> This is an **applied pattern kit**, not a reimplementation of Microsoft’s SkillOpt paper or a drop-in for their forthcoming release.  
> Paper: [SkillOpt (arXiv:2605.23904)](https://arxiv.org/abs/2605.23904) · Related: [Bilevel-Autoresearch](https://github.com/EdwardOptimization/Bilevel-Autoresearch)

---

## What you get

| Path | Purpose |
|------|---------|
| `skill_template.md` | Generic edit-planning skill (trainable text artifact) |
| `checklists/public-content.md` | Pre-publish triage checklist (any public longform) |
| `loop/` | Minimal SkillOpt-style loop: bounded edits + gate + audit stamp |
| `examples/` | Before/after sketch of a skill document after one accepted update |
| `profiles/` | Optional org profiles (empty by default; see below) |

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
python3 -m venv .venv && source .venv/bin/activate  # optional
pip install -r requirements.txt  # empty / minimal today

# Dry-run the loop with the built-in deterministic scorer (for plumbing only)
python -m loop.run --skill skill_template.md --articles examples/articles --epochs 2
```

### Important honesty note

The default scorer in this kit is a **deterministic hash-based mock** so the control loop can be exercised offline. **It is not a research-grade evaluator and not the SkillOpt paper’s evaluation stack.** Wire your own scorer (LLM rubric, human scores, or product metrics) via `--scorer custom` / `loop/scorers.py` before claiming real quality gains.

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

## Attribution

- **SkillOpt:** Yang et al., *SkillOpt: Executive Strategy for Self-Evolving Agent Skills*, arXiv:2605.23904  
- **Bilevel Autoresearch:** mechanism-level outer loops for autoresearch (inspiration for treating process as optimizable)  
- **This kit:** SMF Works — applied content-skill loop for multi-agent writing systems  

---

## License

MIT — see [LICENSE](./LICENSE).

## Contributing

PRs welcome for: better scorers, multi-skill batches, clearer examples.  
Please do **not** open PRs that hard-code private org policies into the default skill path.
