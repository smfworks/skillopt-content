"""Bounded text edits for skill documents (add / delete / replace)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def apply_bounded_edits(skill: str, edits: List[Dict[str, Any]], lr: int) -> str:
    """
    Apply top-Lt ranked edits to a skill document.

    Edit schema:
      type: "replace" | "add" | "delete"
      utility: float (higher = applied first)
      replace: old_text, new_text
      add: new_text, optional after=marker
      delete: old_text
    """
    ranked = sorted(edits, key=lambda e: e.get("utility", 0), reverse=True)[: max(lr, 0)]
    out = skill
    applied: List[str] = []

    for e in ranked:
        etype = e.get("type")
        if etype == "replace":
            old = e.get("old_text") or ""
            new = e.get("new_text", "")
            if old and old in out:
                out = out.replace(old, new, 1)
                applied.append(f"replace:{old[:40]!r}")
            else:
                applied.append(f"replace-miss:{old[:40]!r}")
        elif etype == "add":
            after = e.get("after")
            block = e.get("new_text", "")
            if after and after in out:
                idx = out.find(after) + len(after)
                out = out[:idx] + "\n" + block + out[idx:]
                applied.append(f"add-after:{after[:30]!r}")
            else:
                out = out.rstrip() + "\n\n" + block + "\n"
                applied.append("add:append")
        elif etype == "delete":
            old = e.get("old_text") or ""
            if old and old in out:
                out = out.replace(old, "", 1)
                applied.append(f"delete:{old[:40]!r}")
            else:
                applied.append(f"delete-miss:{old[:40]!r}")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    out = out.rstrip() + f"\n\n<!-- skillopt-content-edit {stamp}: {', '.join(applied)} -->\n"
    return out
