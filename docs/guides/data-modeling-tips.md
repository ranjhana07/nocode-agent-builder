---
title: Data modeling tips
doc_type: guide
workflow: create_table
version: "1.4"
---

# Data modeling tips

A few habits keep the data model of an app easy to extend.

## One table per thing

Create one table for each kind of object, such as customers and orders, and link them with a relation instead of repeating customer details on every order.

## Prefer enums for fixed choices

Use an `enum` field for statuses and tiers. Records that use a value outside the list are rejected, which keeps filters and charts clean.

## Keep names stable

Form bindings, table views and charts refer to fields by name. Renaming a field later means updating each of them, so choose names that will still make sense in a year.

## Seed early

Seed a handful of records right after the fields exist. Table views and charts are much easier to design with real rows on screen.

## Quick facts

- Recommended table naming: plural snake_case nouns
- Field type for fixed choices: enum
- Fields are referenced by: name
