---
title: Forms
doc_type: guide
workflow: create_form
version: "1.4"
---

# Forms

Forms collect input from end users. A form belongs to an app and lists the names of its inputs in display order.

## Creating a form

Call `create_form` with a name, the input names and an optional submit label. Input names must be unique inside the form. The submit label defaults to `Submit`.

## Showing a form

Place the form on a page with an `add_component` call of type `form` and `form_id` in its props. The same form can appear on several pages.

## Saving submissions

A form does nothing with its submissions until it is bound to a table. See the binding guide.

## Quick facts

- Inputs per form: 1 to 40
- Default submit label: Submit
- Form input names must be unique
