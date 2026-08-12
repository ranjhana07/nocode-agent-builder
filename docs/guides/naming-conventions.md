---
title: Naming conventions
doc_type: guide
workflow: none
version: "1.4"
---

# Naming conventions

Names are validated by each workflow, and the rules differ by object. Following one convention across an app keeps data models readable.

## Rules by object

- App names are free text and must be unique per workspace.
- Page slugs use lowercase letters, digits and dashes, for example `order-history`.
- Table names and field names use snake_case, for example `customer_orders`.
- Form names are free text of 2 to 80 characters. Form inputs are matched to table fields by name.

## Reserved names

The names `id`, `created_at` and `updated_at` are managed by the platform. A field called `id` conflicts with the default primary key and returns 409.

## Quick facts

- Table and field names: snake_case
- Reserved field names: id, created_at and updated_at
- Page slugs may not contain uppercase letters
