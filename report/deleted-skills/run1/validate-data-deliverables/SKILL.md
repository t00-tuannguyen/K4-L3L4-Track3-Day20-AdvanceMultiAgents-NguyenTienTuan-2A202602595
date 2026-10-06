---
name: validate-data-deliverables
description: Use when transforming tabular data into one or more files required by a task.
---
- Identify every required output file, schema, field, type, unit, and formatting rule before processing data.
- Use decimal-safe arithmetic for currency; convert to integer minor units when the schema requires it.
- Track raw input row counts separately from deduplicated and usable-record counts.
- Deduplicate by the specified entity key, and exclude records only according to the stated rules.
- Normalize timestamps, categories, and other fields to the required canonical representation.
- Produce every requested artifact, not just a summary or answer file.
- Validate headers, types, row counts, uniqueness, and formatting against the contract before finishing.
