---
title: Ordering workflow calls
doc_type: guide
workflow: none
version: "1.4"
---

# Ordering workflow calls

Workflows depend on ids returned by earlier calls. Running them in the wrong order is the most common reason a build fails.

## Dependency chain

1. `create_app` first, since pages, databases, forms, auth and publishing all need an app id.
2. `create_page` before `add_component`.
3. `create_database` before `create_table`, and `create_table` before `add_field`.
4. `add_field` before `seed_records`, because records are validated against the fields.
5. `create_relation` once both tables exist.
6. `create_form` before `bind_form_to_table`, and the table must exist first.
7. `publish_site` last, once the app has a page.

## Independent steps

Auth flows, pages and databases do not depend on each other and can be created in any order after the app exists.

## Quick facts

- The first workflow of every build is create_app
- publish_site is always the last workflow of a build
- seed_records needs fields to exist first
