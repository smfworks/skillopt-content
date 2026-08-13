# Security Policy

## What this kit is

`skillopt-content` is an offline text-edit loop. It does not call networks by default and has no authentication surface.

## What to watch for

- **Path traversal on `--out` / `--log-jsonl`.** Absolute paths are refused unless `--allow-absolute` is set. Do not disable that check in wrappers that accept untrusted CLI args.
- **Untrusted skill / article files.** Treat them as data. Do not `eval` or execute them.
- **LLM-backed scorers you add yourself.** Keep API keys in the environment, never in the repo. Do not log full prompts that contain private drafts.
- **Rejected-edit buffers.** They may contain sensitive draft fragments. Keep `rejected.jsonl` out of public commits.

## Reporting

Email security issues to **michael@smfworks.com** or open a **private** GitHub security advisory on [smfworks/skillopt-content](https://github.com/smfworks/skillopt-content).

Please do not file public issues that include secrets, private drafts, or personal data.
