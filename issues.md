# Static Analysis Issue Report

The original program was checked with Pylint, Bandit, and Flake8, then reviewed
for functional defects that static tools did not report. The table lists the
original line numbers before the fixes were applied.

| Issue | Type | Original line(s) | Description | Fix approach |
|---|---|---:|---|---|
| Unsafe `eval` | Security - medium | 44-45 | Bandit B307 reported that a fine rule could execute arbitrary Python code. | Replaced `eval` with a restricted AST evaluator that accepts only the `days` variable, numeric constants, and basic arithmetic operators. |
| Negative fines accepted | Logic and validation - high | 24-25, 57 | A negative overdue-day value produced a negative fine. | Added centralized non-negative integer validation for fine calculations and interactive input. |
| Renewal changes global fine rate | Logic - high | 27-31 | Renewing for more than 14 days permanently increased the fine rate for every student. | Made the fine rate constant, limited renewals to 1-14 days, and verified that the requested loan exists. |
| Mutable default argument | Reliability - medium | 9-14 | Pylint W0102 reported that `dates=[]` was shared across calls, so unrelated loans reused date history. | Changed the default to `None` and created a new list for each call. |
| Bare exception silently ignored errors | Reliability - medium | 16-22 | Pylint W0702, Flake8 E722, and Bandit B110 reported a catch-all `except` followed by `pass`. | Replaced exception suppression with explicit existence checks, a Boolean result, and a warning for missing loans. |
| Invalid identifiers accepted | Validation - medium | 9-14, 56 | Empty student IDs and non-string book IDs could enter the loan data. | Added reusable validation requiring non-empty strings for student and book IDs. |
| Invalid interactive input crashed program | Reliability - medium | 60-61 | Non-numeric overdue input raised `ValueError` and ended the program. | Added a prompt loop that reports the validation error and asks again. |
| Unsafe file handling | Reliability - medium | 33-42 | Pylint W1514 and R1732 reported unspecified encoding and files opened without context managers. | Used `Path.open` with UTF-8 and `with` blocks, plus JSON structure validation before changing application state. |
| Importing module ran the whole program | Design - medium | 68 | `main()` ran during import, preventing safe reuse and testing. | Added the standard `if __name__ == "__main__"` guard and configured logging only for direct execution. |
| Naming, documentation, and formatting violations | Style - low | Throughout | Pylint and Flake8 reported a non-snake-case function, missing docstrings, an unused import, spacing errors, long lines, and old string formatting. | Renamed `renewBook`, added docstrings, removed the unused import, applied PEP 8 spacing and line lengths, and used clear formatted output or lazy logging. |

## Verification

- Pylint: 10.00/10
- Bandit: no issues identified
- Flake8: no output and exit status 0
- Pytest: 15 tests passed
