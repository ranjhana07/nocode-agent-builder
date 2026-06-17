---
title: Components reference
doc_type: guide
workflow: add_component
version: "1.4"
---

# Components reference

Components are the building blocks placed on a page. Each component has a type, a props object and a position.

## Component types

- `text` renders rich text. Props: `content` and `size`.
- `button` renders an action button. Props: `label`, `style` and `action`.
- `image` renders an image. Props: `src` and `alt`.
- `table_view` lists records of a table. Props: `table_id`, `columns` and `page_size`.
- `form` embeds a form created with `create_form`. Props: `form_id`.
- `chart` renders bar, line or pie charts. Props: `table_id`, `kind`, `x` and `y`.
- `list` renders a vertical list of records. Props: `table_id` and `title_field`.

## Position

Position is the zero based slot of the component on the page. Two components can share a position, in which case the one created first is shown first.

## Quick facts

- Maximum position value: 200
- Components per page: 60
- Unknown component types return status 422
