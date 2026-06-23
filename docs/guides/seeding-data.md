---
title: Seeding data
doc_type: guide
workflow: seed_records
version: "1.4"
---

# Seeding data

Seeding inserts sample or initial rows into a table. It is useful for demos, template data and tests.

## Validation

Every record is checked against the fields of the table. Unknown keys are rejected. Required fields must be present or have a default. Enum values must come from the field allowed list. Types are strict, so a string for an integer field fails.

If any record is invalid the whole request fails and nothing is inserted. The error message names the index of the first bad record.

## Batch size

One call accepts between 1 and 500 records. Split larger imports into several calls.

## Quick facts

- Maximum records per seed call: 500
- Seeding fails when the table has no fields
- A failed seed call inserts no rows
