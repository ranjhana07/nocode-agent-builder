---
title: API reference for create_app
doc_type: api_spec
workflow: create_app
version: "1.4"
---

# create_app

Creates a new app in the workspace. This is the first call of every build because pages, databases, forms, auth flows and deployments all hang off an app id.

## Endpoint

`POST /apps`

Operation id: `create_app`. Success status: 201.

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| description | string | no | length 0 to 500; default `""` | Short description of what the app does |
| name | string | yes | length 2 to 120 | Unique display name of the app |
| template | enum | no | one of `blank`, `crm`, `inventory`, `blog`; default `"blank"` | Starter template the app is created from |

## Errors

- 409: an app with the same name already exists
- 422: the name is too short or the template is unknown

## Example

```json
{
  "name": "Order Tracker",
  "description": "Tracks customer orders",
  "template": "inventory"
}
```
