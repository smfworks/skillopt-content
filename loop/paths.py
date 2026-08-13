"""Safe path helpers for CLI inputs and outputs."""

from __future__ import annotations

from pathlib import Path


class PathSafetyError(ValueError):
    """Raised when a user-supplied path would escape the working tree."""


def resolve_existing(path: Path, *, must_be_file: bool = False, must_be_dir: bool = False) -> Path:
    resolved = path.expanduser().resolve()
    if must_be_file and not resolved.is_file():
        raise FileNotFoundError(f"file not found: {resolved}")
    if must_be_dir and not resolved.is_dir():
        raise FileNotFoundError(f"directory not found: {resolved}")
    return resolved


def resolve_output(path: Path, *, cwd: Path | None = None, allow_absolute: bool = False) -> Path:
    """
    Resolve an output path.

    Relative paths resolve under cwd. Absolute paths are refused unless
    allow_absolute is True, to stop accidental writes outside the tree.
    """
    cwd = (cwd or Path.cwd()).resolve()
    raw = Path(path).expanduser()
    if raw.is_absolute() and not allow_absolute:
        raise PathSafetyError(
            f"refusing absolute output path {raw}; pass --allow-absolute if intentional"
        )
    resolved = (cwd / raw).resolve() if not raw.is_absolute() else raw.resolve()
    try:
        resolved.relative_to(cwd)
    except ValueError as exc:
        if not allow_absolute:
            raise PathSafetyError(f"output path escapes working directory: {resolved}") from exc
    return resolved
