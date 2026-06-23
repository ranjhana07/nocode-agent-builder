---
title: API reference for create_page
doc_type: api_spec
workflow: create_page
version: "1.4"
---

# create_page

Adds a page to an app. Pages hold components and are served at the slug you choose.

## Endpoint

`POST /apps/{app_id}/pages`

Operation id: `create_page`. Success status: 201.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| app_id | integer | yes | id of the app |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| layout | enum | no | one of `single`, `two_column`, `dashboard`; default `"single"` | Layout grid used by the page |
| slug | string | yes | length 0 to 80; pattern `^[a-z0-9-]+$` | URL segment, lowercase letters, digits and dashes |
| title | string | yes | length 1 to 120 | Page title shown in the browser tab |

## Errors

- 404: the app does not exist
- 409: the slug is already used by another page of the app
- 422: the slug has invalid characters or the app already has 50 pages

## Example

```json
{
  "title": "Dashboard",
  "slug": "dashboard",
  "layout": "dashboard"
}
```
