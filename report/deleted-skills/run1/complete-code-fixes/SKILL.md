---
name: complete-code-fixes
description: Use when modifying a code package to fix bugs or add behavior.
---
- Inspect the repository’s contribution rules and existing conventions before editing.
- Add type annotations for every parameter and return value of each public function you add or change.
- Add a persistent regression test for each bug fixed; meet any minimum test-count requirement.
- Record each fix in the changelog under `## Unreleased` using the required bullet format.
- Run the regression tests and the full test suite after editing.
- Review the final diff to confirm the tests and changelog entries are included.
