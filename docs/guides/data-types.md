---
title: Field data types
doc_type: reference
workflow: add_field
version: "1.4"
---

# Field data types

Every field has one of eight data types. Records are validated against the type, and type checks are strict.

## Types

- `text` accepts any string.
- `email` accepts a string that contains an at sign.
- `integer` accepts whole numbers. Booleans are not integers.
- `float` accepts whole or decimal numbers.
- `boolean` accepts true or false.
- `date` accepts a ten character string such as `2026-03-14`.
- `datetime` accepts an ISO 8601 string with a `T` between date and time.
- `enum` accepts one value from `enum_values`.

## Defaults

A default must satisfy the type of the field. Defaults are applied when the record omits the key, not when it sends null.

## Quick facts

- Number of field types: 8
- Date format: YYYY-MM-DD
- Booleans are accepted by integer fields: no
