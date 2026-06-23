---
title: Errors and limits
doc_type: reference
workflow: none
version: "1.4"
---

# Errors and limits

All workflows return JSON errors with a single `detail` field holding a readable message.

## Status codes

- 201 Created: the object was created.
- 200 OK: the workflow completed without creating a new object.
- 404 Not Found: an id in the path or body does not exist.
- 409 Conflict: a unique name, slug or auth flow already exists.
- 422 Unprocessable Entity: validation failed or a precondition is not met.

## Retrying

409 and 422 are not transient. Fix the request instead of retrying it. 404 usually means an earlier workflow in the build did not run or returned a different id than expected.

## Quick facts

- Error body field: detail
- Validation errors use status 422
- Missing objects use status 404
