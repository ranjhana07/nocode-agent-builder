---
title: API reference for create_database
doc_type: api_spec
workflow: create_database
version: "1.4"
---

# create_database

Creates an empty database inside an app. Databases group tables.

## Endpoint

`POST /databases`

Operation id: `create_database`. Success status: 201.

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| app_id | integer | yes | from 1.0 to unbounded | App that owns the database |
| name | string | yes | length 2 to 80 | Database name, unique within the app |

## Errors

- 404: the app does not exist
- 409: the app already has a database with this name

## Example

```json
{
  "app_id": 1,
  "name": "main"
}
```
