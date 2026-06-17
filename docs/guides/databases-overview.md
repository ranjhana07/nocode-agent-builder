---
title: Databases overview
doc_type: guide
workflow: create_database
version: "1.4"
---

# Databases overview

Each app can own several databases. A database is a namespace for tables, which makes it easy to keep operational data apart from reference data.

## Creating a database

Use `create_database` with the id of the owning app and a name. Names are unique per app. The call fails with 404 when the app does not exist and with 409 when the name is taken.

## What comes next

A new database is empty. Add tables with `create_table`, then describe the columns of each table with `add_field`. Records can only be inserted once a table has at least one field.

## Quick facts

- Database name length: 2 to 80 characters
- Database names are unique per app
- Tables per database: 100
