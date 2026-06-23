---
title: API reference for seed_records
doc_type: api_spec
workflow: seed_records
version: "1.4"
---

# seed_records

Inserts initial rows into a table. Rows are validated against the fields of the table and the call is all or nothing.

## Endpoint

`POST /tables/{table_id}/records`

Operation id: `seed_records`. Success status: 201.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| table_id | integer | yes | id of the table |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| records | array of object | yes | 1 to 500 items | Rows to insert, one object per row |

## Errors

- 404: the table does not exist
- 422: the table has no fields, a record is invalid or more than 500 records were sent

## Example

```json
{
  "records": [
    {
      "email": "ada@example.com",
      "tier": "gold"
    },
    {
      "email": "lin@example.com",
      "tier": "basic"
    }
  ]
}
```
