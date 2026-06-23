---
title: API reference for create_form
doc_type: api_spec
workflow: create_form
version: "1.4"
---

# create_form

Creates a form that lists the inputs shown to end users.

## Endpoint

`POST /apps/{app_id}/forms`

Operation id: `create_form`. Success status: 201.

## Path parameters

| name | type | required | description |
| --- | --- | --- | --- |
| app_id | integer | yes | id of the app |

## Request body

| name | type | required | constraints | description |
| --- | --- | --- | --- | --- |
| fields | array of string | yes | 1 to 40 items | Input names, in display order |
| name | string | yes | length 2 to 80 | Form name, shown as its heading |
| submit_label | string | no | length 0 to 40; default `"Submit"` | Text on the submit button |

## Errors

- 404: the app does not exist
- 422: input names are not unique or the form has more than 40 inputs

## Example

```json
{
  "name": "Contact us",
  "fields": [
    "name",
    "email",
    "message"
  ],
  "submit_label": "Send"
}
```
