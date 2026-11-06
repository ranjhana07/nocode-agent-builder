---
title: Troubleshooting builds
doc_type: guide
workflow: none
version: "1.4"
---

# Troubleshooting builds

Most failed builds come from a small set of causes. Check the status code first, then the `detail` message.

## A call returns 404

The id in the path or body does not exist. Either the earlier workflow that should have produced it failed, or the id was typed by hand. Use the id from the response of the earlier call.

## A call returns 409

A name or slug is already taken. Pick another name, or reuse the existing object. App names are unique per workspace and page slugs are unique per app.

## A call returns 422

The request was understood but rejected. The usual causes are a value outside the allowed list, a missing required field, a slug with uppercase letters, or a precondition that is not met, such as seeding a table without fields.

## A published site shows a blank page

The page exists but has no components. Place at least one component with `add_component` and publish again.

## Form submissions do not appear in the table

The form is probably not bound. Call `bind_form_to_table` and check that every mapped input and field name exists.

## Quick facts

- Status code for an unknown id: 404
- Status code for a taken name: 409
- Fix for a blank published page: add a component and publish again
