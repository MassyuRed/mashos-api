"""Continuation must expose later checks while retaining every mismatch."""
import pytest
from helpers.retained_assertions import continue_assertions, retained_assertion


def test_later_check_runs_but_original_mismatch_still_fails():
    visited = []
    @continue_assertions
    def original():
        retained_assertion(lambda: False, "old text mismatch")
        visited.append("later operation")
        retained_assertion(lambda: False, "later functional failure")
    with pytest.raises(AssertionError) as failure:
        original()
    assert visited == ["later operation"]
    assert "old text mismatch" in str(failure.value)
    assert "later functional failure" in str(failure.value)


def test_invalid_prerequisite_remains_fatal():
    visited = []
    @continue_assertions
    def original():
        retained_assertion(lambda: {}["missing"], "missing prerequisite")
        visited.append("must not run")
    with pytest.raises(KeyError):
        original()
    assert not visited


def test_clean_checks_pass_and_do_not_inherit_previous_failures():
    @continue_assertions
    def original(value):
        retained_assertion(lambda: value, "value")
        return "finished"
    with pytest.raises(AssertionError):
        original(False)
    assert original(True) == "finished"


def test_reviewed_missing_old_substring_is_retained_without_hiding_later_work():
    visited = []
    @continue_assertions
    def original():
        retained_assertion(lambda: "current".index("old") == 0,
                           '"current".index("old") == 0', evaluation_errors=(ValueError,))
        visited.append("later operation")
    with pytest.raises(AssertionError, match="Evaluation error retained: ValueError"):
        original()
    assert visited == ["later operation"]
