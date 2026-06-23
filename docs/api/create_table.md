---
title: API reference for create_table
doc_type: api_spec
workflow: create_table
version: "1.4"
---

# create_table

Creates a table inside a database. The table starts with only its primary key.

## Endpoint

`POST /databases/{database_id}/tables`

Operation id: `create_table`. Success status: 201.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| database_id | integer | yes | id of the database |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| name | string | yes | length 0 to 80; pattern `^[a-z][a-z0-9_]*$` | Table name in snake_case |
| primary_key | string | no | length 0 to 80; default `"id"` | Name of the primary key column |

## Errors

- 404: the database does not exist
- 409: the database already has a table with this name
- 422: the database already holds 100 tables

## Example

```json
{
  "name": "customers",
  "primary_key": "id"
}
```
