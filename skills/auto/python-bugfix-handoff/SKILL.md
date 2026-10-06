---
name: python-bugfix-handoff
description: Use for Python package bug-fix tasks to meet Acme’s public-function typing, regression-test, and changelog conventions.
---
- Inspect the package’s public API and identify every function whose name does not start with `_`.
- Add type annotations for every parameter and the return value of each public function.
- Create `tests/test_regressions.py` with one test function for each bug fixed; include at least 3 test functions.
- Run the test suite and confirm that `tests/test_regressions.py` passes.
- Add a `## Unreleased` heading to `CHANGELOG.md` and record each fix as `- fix(<function name>): <short description>`; include at least 3 bullets.
- Before finishing, check the task for any other Acme convention; say which conventions you could not find.
