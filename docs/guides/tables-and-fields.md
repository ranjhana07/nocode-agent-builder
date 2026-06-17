---
title: Tables and fields
doc_type: guide
workflow: add_field
version: "1.4"
---

# Tables and fields

Tables store records. Each table has a primary key column, named `id` by default, and any number of fields.

## Table names

Table names use snake_case: a lowercase letter followed by lowercase letters, digits and underscores. Names are unique within a database.

## Field types

- `text`, `email`, `integer`, `float` and `boolean` store single values.
- `date` stores a calendar date as `YYYY-MM-DD`.
- `datetime` stores an ISO 8601 timestamp.
- `enum` stores one value from a fixed list and needs `enum_values`.

## Required fields and defaults

A required field rejects records that leave it empty. A default fills in the value when a record omits the field. A field that is both required and has a default never fails on omission.

## Quick facts

- Default primary key name: id
- Enum fields require at least one entry in enum_values
- enum_values is rejected on any other field type
