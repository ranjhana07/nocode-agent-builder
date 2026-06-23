---
title: Relations between tables
doc_type: guide
workflow: create_relation
version: "1.4"
---

# Relations between tables

Relations link two tables of the same database. They are what lets a table view show, for example, the orders of a customer.

## Kinds

- `one_to_many` stores a reference field on the table at the many side. A customer has many orders.
- `many_to_many` creates a hidden join table. A student has many courses and a course has many students.
- `one_to_one` stores a unique reference. A user has one profile.

## Rules

Both tables must belong to the same database, otherwise the call returns 422. A table can relate to itself with `one_to_many` or `many_to_many`, for example a category tree. A `one_to_one` relation cannot point a table at itself.

## Quick facts

- Relations across databases are not supported
- Self relations are allowed for one_to_many and many_to_many
- field_name is the name of the reference field
