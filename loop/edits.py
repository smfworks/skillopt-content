"""Bounded text edits for skill documents (add / delete / replace)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

VALID_TYPES = frozenset({"replace", "add", "delete"})
AUDIT_STAMP_RE = re.compile(
    r"\n*<!-- skillopt-content-edit [^>]*-->\n?",
    re.MULTILINE,
)


def strip_audit_stamps(text: str) -> str:
    """Remove kit audit comments so they cannot change scores."""
    cleaned = AUDIT_STAMP_RE.sub("\n", text or "")
    if (text or "").endswith("\n"):
        return cleaned.rstrip() + "\n"
    return cleaned.rstrip()


def safe_utility(edit: dict[str, Any]) -> float:
    raw = edit.get("utility", 0)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if value != value:  # NaN
        return 0.0
    return value


class EditError(ValueError):
    """Raised when an edit dict is malformed."""


@dataclass
class AppliedEdit:
    kind: str
    detail: str = ""

    def label(self) -> str:
        return f"{self.kind}:{self.detail}" if self.detail else self.kind


@dataclass
class EditResult:
    text: str
    applied: list[AppliedEdit] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(
            1
            for e in self.applied
            if e.kind not in {"invalid", "replace-miss", "delete-miss"}
        )

    @property
    def hit_count(self) -> int:
        return self.success_count

    @property
    def applied_labels(self) -> list[str]:
        return [e.label() for e in self.applied]

    # Backward-compatible alias used in early 0.2 drafts
    @property
    def missed(self) -> list[str]:
        return [e.label() for e in self.applied if e.kind.endswith("-miss") or e.kind == "invalid"]


# Alias kept so older imports keep working
ApplyResult = EditResult


def validate_edit(edit: dict[str, Any]) -> None:
    if not isinstance(edit, dict):
        raise EditError("edit must be a dict")
    etype = edit.get("type")
    if etype not in VALID_TYPES:
        raise EditError(f"unknown edit type: {etype!r}")
    if etype == "replace" and not str(edit.get("old_text") or "").strip():
        raise EditError("replace requires old_text")
    if etype == "add" and not str(edit.get("new_text") or "").strip():
        raise EditError("add requires new_text")
    if etype == "delete" and not str(edit.get("old_text") or "").strip():
        raise EditError("delete requires old_text")


def rank_edits(edits: list[Any], lr: int) -> list[dict[str, Any]]:
    if lr < 0:
        raise ValueError("lr must be >= 0")
    valid = [e for e in edits if isinstance(e, dict)]
    return sorted(valid, key=safe_utility, reverse=True)[:lr]


def apply_bounded_edits(
    skill: str,
    edits: list[dict[str, Any]],
    lr: int,
    *,
    stamp: bool = True,
    skip_invalid: bool = True,
    strict: bool | None = None,
) -> str:
    """
    Apply top-Lt ranked edits to a skill document.

    Edit schema:
      type: "replace" | "add" | "delete"
      utility: float (higher = applied first)
      replace: old_text, new_text
      add: new_text, optional after=marker
      delete: old_text
    """
    return apply_bounded_edits_detailed(
        skill, edits, lr, stamp=stamp, skip_invalid=skip_invalid, strict=strict
    ).text


def apply_bounded_edits_detailed(
    skill: str,
    edits: list[dict[str, Any]],
    lr: int,
    *,
    stamp: bool = True,
    skip_invalid: bool = True,
    strict: bool | None = None,
) -> EditResult:
    if strict is not None:
        skip_invalid = not strict
    if lr < 0:
        raise ValueError("lr must be >= 0")
    if not isinstance(skill, str):
        raise TypeError("skill must be a string")

    ranked = rank_edits(list(edits or []), lr)
    out = skill
    applied: list[AppliedEdit] = []

    for e in ranked:
        try:
            validate_edit(e)
        except EditError:
            if not skip_invalid:
                raise
            applied.append(AppliedEdit(kind="invalid", detail=repr(e.get("type"))))
            continue

        etype = e["type"]
        if etype == "replace":
            old = e.get("old_text") or ""
            new = e.get("new_text", "")
            if old in out:
                out = out.replace(old, new, 1)
                applied.append(AppliedEdit(kind="replace", detail=old[:40]))
            else:
                applied.append(AppliedEdit(kind="replace-miss", detail=old[:40]))
        elif etype == "add":
            after = e.get("after")
            block = e.get("new_text", "")
            if after and after in out:
                idx = out.find(after) + len(after)
                out = out[:idx] + "\n" + block + out[idx:]
                applied.append(AppliedEdit(kind="add-after", detail=str(after)[:30]))
            else:
                out = out.rstrip() + "\n\n" + block + "\n"
                applied.append(AppliedEdit(kind="add"))
        elif etype == "delete":
            old = e.get("old_text") or ""
            if old in out:
                out = out.replace(old, "", 1)
                applied.append(AppliedEdit(kind="delete", detail=old[:40]))
            else:
                applied.append(AppliedEdit(kind="delete-miss", detail=old[:40]))

    if stamp:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        trail = ", ".join(e.label() for e in applied) if applied else "none"
        out = out.rstrip() + f"\n\n<!-- skillopt-content-edit {ts}: {trail} -->\n"

    return EditResult(text=out, applied=applied)
