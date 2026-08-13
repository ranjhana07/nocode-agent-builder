---
title: Frequently asked questions
doc_type: guide
workflow: none
version: "1.4"
---

# Frequently asked questions

## Can I rename an app after creating it?

Yes. Renaming changes the display name and the default URL slug, but custom domains stay as they are.

## Why does publishing fail with 422?

Either the app has no pages yet, or a custom domain was used with the staging environment. Add a page with `create_page` or publish to production.

## Can one form write to two tables?

No. A form is bound to one table at a time. Use two forms or a relation between the tables instead.

## How do I make a field optional?

Fields are optional unless `required` is true. Set a default value if records should always carry the field.

## What happens to records when I delete a table?

Records are deleted with the table. Forms bound to the table keep working but lose their binding.

## Quick facts

- Forms bound to one table at a time: yes
- Records survive table deletion: no
- Fields are optional unless: required is true
