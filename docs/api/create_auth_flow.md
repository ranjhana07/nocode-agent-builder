---
title: API reference for create_auth_flow
doc_type: api_spec
workflow: create_auth_flow
version: "1.4"
---

# create_auth_flow

Configures how end users sign in to the app and which roles exist. An app has at most one auth flow.

## Endpoint

`POST /apps/{app_id}/auth`

Operation id: `create_auth_flow`. Success status: 201.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| app_id | integer | yes | id of the app |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| method | enum | yes | one of `email_password`, `magic_link`, `oauth_google`, `oauth_github` | Sign in method offered to end users |
| require_verification | boolean | no | default `true` | Require email verification before first sign in |
| roles | array of string | no | 0 to 10 items | Roles available in the app |

## Errors

- 404: the app does not exist
- 409: the app already has an auth flow

## Example

```json
{
  "method": "email_password",
  "require_verification": true,
  "roles": [
    "admin",
    "member"
  ]
}
```
