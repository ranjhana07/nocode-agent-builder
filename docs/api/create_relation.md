---
title: API reference for create_relation
doc_type: api_spec
workflow: create_relation
version: "1.4"
---

# create_relation

Links two tables of the same database so records of one can reference records of the other.

## Endpoint

`POST /relations`

Operation id: `create_relation`. Success status: 201.

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| field_name | string | yes | length 0 to 80; pattern `^[a-z][a-z0-9_]*$` | Name of the reference field |
| from_table_id | integer | yes | from 1.0 to unbounded | Table that holds the reference |
| kind | enum | yes | one of `one_to_many`, `many_to_many`, `one_to_one` | Cardinality of the relation |
| to_table_id | integer | yes | from 1.0 to unbounded | Table being referenced |

## Errors

- 404: one of the tables does not exist
- 422: the tables belong to different databases or a one_to_one relation points at its own table

## Example

```json
{
  "from_table_id": 4,
  "to_table_id": 3,
  "kind": "one_to_many",
  "field_name": "customer"
}
```
