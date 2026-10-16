"""Manage library loans, renewals, persistence, and overdue fines."""

import ast
import json
import logging
import operator
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Union

FINE_PER_DAY = 2
MAX_RENEWAL_DAYS = 14
DEFAULT_RECORDS_FILE = Path("loans.json")

LoanRecords = dict[str, list[str]]
Number = Union[int, float]

loans: LoanRecords = {}

LOGGER = logging.getLogger(__name__)

BinaryOperation = Callable[[Number, Number], Number]
_BINARY_OPERATORS: dict[type[ast.operator], BinaryOperation] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[Number], Number]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _require_non_empty_string(value: object, field_name: str) -> str:
    """Return a stripped string or raise a clear validation error."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_non_negative_integer(value: object, field_name: str) -> int:
    """Return an integer that is zero or greater."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def add_book_loan(
    student_id: str,
    book_id: str,
    dates: Optional[list[str]] = None,
) -> None:
    """Record a book loan and its timestamp."""
    validated_student_id = _require_non_empty_string(student_id, "student_id")
    validated_book_id = _require_non_empty_string(book_id, "book_id")
    loan_dates = [] if dates is None else dates
    loan_dates.append(datetime.now(timezone.utc).isoformat())
    loans.setdefault(validated_student_id, []).append(validated_book_id)
    LOGGER.info(
        "%s borrowed %s (loan dates on record: %d)",
        validated_student_id,
        validated_book_id,
        len(loan_dates),
    )


def return_book(student_id: str, book_id: str) -> bool:
    """Remove a matching loan and report whether it was found."""
    validated_student_id = _require_non_empty_string(student_id, "student_id")
    validated_book_id = _require_non_empty_string(book_id, "book_id")
    student_loans = loans.get(validated_student_id)
    if not student_loans or validated_book_id not in student_loans:
        LOGGER.warning(
            "No loan found for student %s and book %s",
            validated_student_id,
            validated_book_id,
        )
        return False

    student_loans.remove(validated_book_id)
    if not student_loans:
        del loans[validated_student_id]
    return True


def calculate_fine(days_overdue: int) -> int:
    """Calculate a fine for a validated number of overdue days."""
    validated_days = _require_non_negative_integer(
        days_overdue,
        "days_overdue",
    )
    return validated_days * FINE_PER_DAY


def renew_book(student_id: str, book_id: str, extra_days: int) -> int:
    """Validate and record a renewal of at most 14 days."""
    validated_student_id = _require_non_empty_string(student_id, "student_id")
    validated_book_id = _require_non_empty_string(book_id, "book_id")
    validated_days = _require_non_negative_integer(extra_days, "extra_days")
    if validated_days == 0 or validated_days > MAX_RENEWAL_DAYS:
        raise ValueError(
            f"extra_days must be between 1 and {MAX_RENEWAL_DAYS}"
        )
    if validated_book_id not in loans.get(validated_student_id, []):
        raise ValueError("the requested loan does not exist")

    LOGGER.info(
        "Renewed %s for %s by %d days",
        validated_book_id,
        validated_student_id,
        validated_days,
    )
    return validated_days


def _validate_loaded_records(records: object) -> LoanRecords:
    """Validate the shape and values of records loaded from JSON."""
    if not isinstance(records, dict):
        raise ValueError("loan records must be a JSON object")

    validated_records: LoanRecords = {}
    for student_id, book_ids in records.items():
        validated_student_id = _require_non_empty_string(
            student_id,
            "student_id",
        )
        if not isinstance(book_ids, list):
            raise ValueError("each student's loans must be a list")
        validated_records[validated_student_id] = [
            _require_non_empty_string(book_id, "book_id")
            for book_id in book_ids
        ]
    return validated_records


def load_records(file: Union[str, Path] = DEFAULT_RECORDS_FILE) -> None:
    """Replace in-memory loans with validated records from a JSON file."""
    record_path = Path(file)
    with record_path.open("r", encoding="utf-8") as record_file:
        records = json.load(record_file)
    validated_records = _validate_loaded_records(records)
    loans.clear()
    loans.update(validated_records)


def save_records(file: Union[str, Path] = DEFAULT_RECORDS_FILE) -> None:
    """Save the current loans to a UTF-8 JSON file."""
    record_path = Path(file)
    with record_path.open("w", encoding="utf-8") as record_file:
        json.dump(loans, record_file, indent=2, sort_keys=True)
        record_file.write("\n")


def _evaluate_expression(node: ast.AST, days: int) -> Number:
    """Evaluate a restricted arithmetic expression tree."""
    if isinstance(node, ast.Expression):
        return _evaluate_expression(node.body, days)
    if isinstance(node, ast.Name) and node.id == "days":
        return days
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        operation = _BINARY_OPERATORS[type(node.op)]
        return operation(
            _evaluate_expression(node.left, days),
            _evaluate_expression(node.right, days),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        operation = _UNARY_OPERATORS[type(node.op)]
        return operation(_evaluate_expression(node.operand, days))
    raise ValueError("rule may only use 'days' and basic arithmetic")


def fine_from_rule(rule: str, days: int) -> Number:
    """Calculate a fine from a safely parsed arithmetic rule."""
    validated_rule = _require_non_empty_string(rule, "rule")
    validated_days = _require_non_negative_integer(days, "days")
    try:
        expression = ast.parse(validated_rule, mode="eval")
        return _evaluate_expression(expression, validated_days)
    except (SyntaxError, TypeError, ZeroDivisionError) as error:
        raise ValueError("invalid fine rule") from error


def print_report() -> None:
    """Print the current loans in a stable, human-readable order."""
    print("Loan Report")
    for student_id, book_ids in sorted(loans.items()):
        print(f"{student_id} -> {book_ids}")


def _read_overdue_days() -> int:
    """Prompt until the user provides a valid overdue-day count."""
    while True:
        response = input("Days overdue for S102 (press Enter for 0): ").strip()
        try:
            days = int(response or "0")
            return _require_non_negative_integer(days, "days_overdue")
        except ValueError as error:
            print(f"Invalid input: {error}")


def main() -> None:
    """Run a short demonstration of the library loan workflow."""
    loans.clear()
    add_book_loan("S101", "B-ALGO")
    add_book_loan("S102", "B-NETW")
    return_book("S999", "B-NONE")
    renew_book("S101", "B-ALGO", 14)
    print("Fine for 5 days:", calculate_fine(5))
    print("Fine via rule:", fine_from_rule("days * 2 + 10", 4))
    print("S102 owes:", calculate_fine(_read_overdue_days()))
    save_records()
    load_records()
    print_report()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    main()
