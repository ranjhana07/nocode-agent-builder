---
title: Apps and templates
doc_type: guide
workflow: create_app
version: "1.4"
---

# Apps and templates

An app is created once and then extended with pages, data and forms. App names are unique across a workspace, so creating a second app with an existing name fails with a 409 conflict.

## Templates

The template decides what the app contains right after creation.

- `blank` creates an empty app with no pages.
- `crm` adds a contacts table, a deals table and a pipeline page.
- `inventory` adds products and stock movement tables.
- `blog` adds posts and authors tables and a public index page.

Templates only seed structure. You can rename or delete anything they create. The template cannot be changed after the app exists.

## Naming

Names must be between 2 and 120 characters. The name is turned into a slug for the default URL, so `Order Tracker` is served from `order-tracker`.

## Quick facts

- App name length: 2 to 120 characters
- Template cannot be changed after creation
- Duplicate app names return status 409
