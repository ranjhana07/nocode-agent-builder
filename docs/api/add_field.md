---
title: API reference for add_field
doc_type: api_spec
workflow: add_field
version: "1.4"
---

# add_field

Adds a typed field to a table. Enum fields need their allowed values listed.

## Endpoint

`POST /tables/{table_id}/fields`

Operation id: `add_field`. Success status: 201.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| table_id | integer | yes | id of the table |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| default | any | no | none | Value used when a record omits the field |
| enum_values | array of string | no | none | Allowed values when type is enum |
| name | string | yes | length 0 to 80; pattern `^[a-z][a-z0-9_]*$` | Field name in snake_case |
| required | boolean | no | default `false` | Reject records that leave the field empty |
| type | enum | yes | one of `text`, `integer`, `float`, `boolean`, `date`, `datetime`, `email`, `enum` | Data type of the field |

## Errors

- 404: the table does not exist
- 409: the table already has a field with this name
- 422: enum_values is missing for an enum field or present for another type

## Example

```json
{
  "name": "status",
  "type": "enum",
  "required": true,
  "enum_values": [
    "open",
    "paid",
    "refunded"
  ]
}
```
