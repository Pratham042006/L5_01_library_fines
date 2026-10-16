# Lab 5 Static Code Analysis Library Fine and Book Renewal System

This repository contains the completed static analysis lab. The library program
has been corrected, documented, and verified with Pylint, Bandit, Flake8, and
automated tests.

## About the program

A small tracker for a campus library. It records which student has borrowed which book, works out overdue fines, handles renewals, and saves the loan records to `loans.json`.

The program validates loan data and user input, calculates overdue fines,
handles renewals, safely evaluates arithmetic fine rules, and persists loan
records as JSON.

## Run the program

```bash
python library_system.py
```

The program asks for the number of overdue days. Press Enter to use zero.

## Verify the solution

Install the development tools and run all checks:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
pylint library_system.py
bandit -r library_system.py
flake8 library_system.py
```

The final verified results are a Pylint score of 10.00/10, no Bandit findings,
no Flake8 violations, and 15 passing tests.

## Deliverables

1. `library_system.py`: cleaned and corrected implementation.
2. `issues.md`: issue table covering the original findings and fixes.
3. `reflection.md`: answers to all four reflection questions.
4. `pylint_report.txt`, `bandit_report.txt`, and `flake8_report.txt`: final tool output.
5. `tests/test_library_system.py`: regression tests for the corrected behavior.
