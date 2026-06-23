---
title: API reference for add_component
doc_type: api_spec
workflow: add_component
version: "1.4"
---

# add_component

Places a component on a page at a given position.

## Endpoint

`POST /pages/{page_id}/components`

Operation id: `add_component`. Success status: 201.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| page_id | integer | yes | id of the page |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| position | integer | no | from 0.0 to 200.0; default `0` | Zero based slot on the page |
| props | object | no | none | Component specific properties |
| type | enum | yes | one of `text`, `button`, `image`, `table_view`, `form`, `chart`, `list` | Kind of component to place on the page |

## Errors

- 404: the page does not exist
- 422: the component type is unknown or the page already has 60 components

## Example

```json
{
  "type": "table_view",
  "props": {
    "table_id": 3,
    "page_size": 25
  },
  "position": 1
}
```
