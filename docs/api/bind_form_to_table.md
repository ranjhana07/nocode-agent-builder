---
title: API reference for bind_form_to_table
doc_type: api_spec
workflow: bind_form_to_table
version: "1.4"
---

# bind_form_to_table

Connects a form to a table so submissions are stored as records. Calling it again replaces the binding.

## Endpoint

`POST /forms/{form_id}/binding`

Operation id: `bind_form_to_table`. Success status: 200.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| form_id | integer | yes | id of the form |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| field_mapping | object | no | none | Maps form input names to table field names |
| table_id | integer | yes | from 1.0 to unbounded | Table that receives submissions |

## Errors

- 404: the form or the table does not exist
- 422: the table belongs to another app, or the mapping names an unknown input or field

## Example

```json
{
  "table_id": 3,
  "field_mapping": {
    "name": "full_name",
    "email": "email"
  }
}
```
