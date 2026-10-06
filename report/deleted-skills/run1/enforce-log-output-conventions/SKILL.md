---
name: enforce-log-output-conventions
description: Use when parsing logs into structured error reports or other machine-readable outputs.
---
- Read the required output schema before parsing; preserve required top-level metadata and version fields.
- Normalize identifiers such as service names exactly as specified by the output contract.
- Convert timestamps to the required timezone and canonical format before sorting.
- Sort records by the specified keys and direction; do not rely on input order.
- Preserve required error details, attached exceptions, and repetition counts.
- Validate the final structure and ordering against the schema before writing the output.
