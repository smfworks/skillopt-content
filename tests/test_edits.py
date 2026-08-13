"""Oppositional tests for bounded edits."""

from __future__ import annotations

import pytest

from loop.edits import (
    EditError,
    apply_bounded_edits,
    apply_bounded_edits_detailed,
    validate_edit,
)


def test_replace_first_occurrence_only():
    skill = "alpha beta alpha"
    out = apply_bounded_edits(
        skill,
        [{"type": "replace", "old_text": "alpha", "new_text": "ALPHA", "utility": 1}],
        1,
        stamp=False,
    )
    assert out == "ALPHA beta alpha"


def test_delete_missing_is_recorded_not_raised():
    result = apply_bounded_edits_detailed(
        "hello",
        [{"type": "delete", "old_text": "missing", "utility": 1}],
        1,
        stamp=False,
    )
    assert result.text == "hello"
    assert result.hit_count == 0
    assert any("delete-miss" in m for m in result.missed)


def test_add_after_marker_and_append_fallback():
    skill = "line one\nline two"
    after = apply_bounded_edits_detailed(
        skill,
        [{"type": "add", "after": "line one", "new_text": "INSERTED", "utility": 1}],
        1,
        stamp=False,
    )
    assert after.text == "line one\nINSERTED\nline two"

    append = apply_bounded_edits_detailed(
        skill,
        [{"type": "add", "new_text": "TAIL", "utility": 1}],
        1,
        stamp=False,
    )
    assert append.text.endswith("TAIL\n")


def test_lr_zero_is_noop_without_stamp():
    skill = "unchanged"
    result = apply_bounded_edits_detailed(
        skill,
        [{"type": "delete", "old_text": "un", "utility": 9}],
        0,
        stamp=False,
    )
    assert result.text == skill
    assert result.applied == []
    assert result.missed == []


def test_utility_ranking():
    skill = "ab"
    result = apply_bounded_edits_detailed(
        skill,
        [
            {"type": "delete", "old_text": "a", "utility": 0.1},
            {"type": "delete", "old_text": "b", "utility": 0.9},
        ],
        1,
        stamp=False,
    )
    assert result.text == "a"
    assert result.hit_count == 1


def test_validate_edit_rejects_unknown_and_empty():
    with pytest.raises(EditError):
        validate_edit({"type": "mutate"})
    with pytest.raises(EditError):
        validate_edit({"type": "replace", "old_text": "", "new_text": "x"})
    with pytest.raises(EditError):
        validate_edit({"type": "add", "new_text": ""})


def test_skip_invalid_by_default():
    result = apply_bounded_edits_detailed(
        "abc",
        [
            {"type": "nope", "utility": 1},
            {"type": "replace", "old_text": "a", "new_text": "A", "utility": 0.5},
        ],
        2,
        stamp=False,
    )
    assert result.text.startswith("Abc")
    assert any("invalid" in m for m in result.missed)


def test_strict_invalid_raises():
    with pytest.raises(EditError):
        apply_bounded_edits_detailed(
            "abc",
            [{"type": "nope", "utility": 1}],
            1,
            stamp=False,
            strict=True,
        )


def test_stamp_appended():
    out = apply_bounded_edits(
        "hello",
        [{"type": "add", "new_text": "x", "utility": 1}],
        1,
    )
    assert "<!-- skillopt-content-edit" in out
