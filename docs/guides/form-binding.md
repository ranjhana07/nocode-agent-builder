---
title: Binding forms to tables
doc_type: guide
workflow: bind_form_to_table
version: "1.4"
---

# Binding forms to tables

Binding connects a form to a table so every submission becomes a record.

## Field mapping

The mapping translates form input names to table field names. When you omit it, Nocode maps every input whose name matches a field of the table. Use an explicit mapping when the names differ, for example mapping the input `full_name` to the field `name`.

## Checks

The table must belong to the same app as the form. Every mapped input must exist on the form and every mapped field must exist on the table. Violations return 422.

## Rebinding

Calling the workflow again replaces the previous binding. Existing records are kept.

## Quick facts

- A form is bound to one table at a time
- Rebinding does not delete records
- Omitting field_mapping maps inputs with matching names
