---
title: API reference for publish_site
doc_type: api_spec
workflow: publish_site
version: "1.4"
---

# publish_site

Publishes the app to staging or production and returns the live URL.

## Endpoint

`POST /apps/{app_id}/publish`

Operation id: `publish_site`. Success status: 200.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| app_id | integer | yes | id of the app |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| custom_domain | string | no | none | Custom domain, production only |
| environment | enum | no | one of `staging`, `production`; default `"staging"` | Target environment |

## Errors

- 404: the app does not exist
- 422: the app has no pages, or a custom domain was used outside production

## Example

```json
{
  "environment": "production",
  "custom_domain": "orders.example.com"
}
```
