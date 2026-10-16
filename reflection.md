# Static Analysis Reflection

## 1 Which issues were easiest and hardest to fix and why

The easiest issues were the style and resource-management findings. Removing
the unused import, adding docstrings and blank lines, renaming `renewBook` to
`renew_book`, and opening files with UTF-8 context managers were direct changes
with clear messages from Pylint and Flake8.

The hardest issue was replacing `eval`. Removing it was easy, but preserving
useful arithmetic rules without allowing function calls, attribute access, or
arbitrary names required a restricted parser and evaluator. The renewal logic
also needed careful attention because changing the global fine rate was a
functional defect rather than a simple style warning.

## 2 Did the tools report any false positives

There were no clear false positives in the final review. The low-severity
Bandit B110 finding about `try` and `except` with `pass` could look harmless
because the program intentionally ignored a missing loan. However, the warning
was useful: the catch-all also hid unexpected programming and data errors.
Replacing it with explicit checks preserved the intended behavior while making
failures visible.

## 3 How would I integrate static analysis into a development workflow

I would run Flake8 and Pylint while developing and run Bandit whenever code
changes affect input, files, commands, serialization, or other security-sensitive
behavior. All three tools and the test suite should run automatically in a
pre-commit check or continuous-integration workflow on every pull request. A
change should only be merged when the checks pass, with any suppression kept
specific and documented.

## 4 What tangible improvements did I observe

The corrected program is more secure because it no longer executes fine rules
with `eval`. It is more robust because it validates identifiers, overdue days,
renewal limits, JSON data, and interactive input. It is more predictable because
renewals cannot change the global fine rate and missing loans are handled
explicitly. Readability improved through snake-case naming, focused helper
functions, docstrings, type hints, deterministic JSON output, and structured
logging. The 15 regression tests provide evidence that these behaviors remain
correct while all three static analysis tools now pass cleanly.
