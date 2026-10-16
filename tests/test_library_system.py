"""Tests for the library loan system."""

import json

import pytest

import library_system


@pytest.fixture(autouse=True)
def clear_loans():
    """Keep global loan state isolated between tests."""
    library_system.loans.clear()
    yield
    library_system.loans.clear()


def test_add_book_loan_does_not_share_default_dates():
    """Separate calls must not share a mutable default list."""
    library_system.add_book_loan("S101", "B-ONE")
    library_system.add_book_loan("S102", "B-TWO")
    assert library_system.loans == {"S101": ["B-ONE"], "S102": ["B-TWO"]}


@pytest.mark.parametrize("student_id, book_id", [("", "B-ONE"), ("S101", 42)])
def test_add_book_loan_rejects_invalid_identifiers(student_id, book_id):
    """Student and book IDs must be non-empty strings."""
    with pytest.raises(ValueError):
        library_system.add_book_loan(student_id, book_id)


def test_return_book_handles_a_missing_loan():
    """A missing loan returns False instead of hiding an exception."""
    assert library_system.return_book("S999", "B-NONE") is False


def test_return_book_removes_empty_student_entry():
    """Returning the final book removes the student's empty record."""
    library_system.loans["S101"] = ["B-ONE"]
    assert library_system.return_book("S101", "B-ONE") is True
    assert "S101" not in library_system.loans


def test_calculate_fine_rejects_negative_days():
    """Negative overdue days must not produce a negative fine."""
    with pytest.raises(ValueError):
        library_system.calculate_fine(-1)


def test_renewal_does_not_change_the_fine_rate():
    """Renewing a loan must not mutate the global fine rate."""
    library_system.loans["S101"] = ["B-ONE"]
    assert library_system.renew_book("S101", "B-ONE", 14) == 14
    assert library_system.calculate_fine(5) == 10


@pytest.mark.parametrize("extra_days", [0, 15])
def test_renewal_rejects_days_outside_the_allowed_range(extra_days):
    """Renewals must remain within the documented 1-14 day range."""
    library_system.loans["S101"] = ["B-ONE"]
    with pytest.raises(ValueError):
        library_system.renew_book("S101", "B-ONE", extra_days)


def test_records_round_trip(tmp_path):
    """Saved records should load without changing their structure."""
    record_path = tmp_path / "loans.json"
    library_system.loans["S101"] = ["B-ONE"]
    library_system.save_records(record_path)
    library_system.loans.clear()
    library_system.load_records(record_path)
    assert library_system.loans == {"S101": ["B-ONE"]}
    assert json.loads(record_path.read_text(encoding="utf-8")) == library_system.loans


def test_load_records_rejects_invalid_data(tmp_path):
    """Malformed record shapes must not enter the application state."""
    record_path = tmp_path / "loans.json"
    record_path.write_text('{"S101": [42]}', encoding="utf-8")
    with pytest.raises(ValueError):
        library_system.load_records(record_path)


def test_fine_rule_supports_safe_arithmetic():
    """Allowed arithmetic rules should retain the original behavior."""
    assert library_system.fine_from_rule("days * 2 + 10", 4) == 18


@pytest.mark.parametrize(
    "rule",
    ["__import__('os').system('echo unsafe')", "days ** 100", "unknown + 1"],
)
def test_fine_rule_rejects_unsafe_or_unsupported_expressions(rule):
    """Rules cannot call functions, use exponentiation, or access names."""
    with pytest.raises(ValueError):
        library_system.fine_from_rule(rule, 4)
