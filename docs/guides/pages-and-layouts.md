---
title: Pages and layouts
doc_type: guide
workflow: create_page
version: "1.4"
---

# Pages and layouts

Pages are the screens of an app. Each page has a title, a slug and a layout. The slug is the URL segment and must be unique within the app.

## Layouts

- `single` is one full width column and suits landing pages and forms.
- `two_column` places a narrow sidebar next to the main content.
- `dashboard` uses a twelve column grid intended for charts and table views.

## Slugs

Slugs may contain lowercase letters, digits and dashes. Uppercase letters, spaces and underscores are rejected with a 422 validation error. A slug that is already used by another page of the same app returns 409.

## Limits

An app holds at most 50 pages. Deleting a page frees its slug immediately.

## Quick facts

- Page slug pattern: lowercase letters, digits and dashes
- Default page layout: single
- Maximum slug length: 80 characters
