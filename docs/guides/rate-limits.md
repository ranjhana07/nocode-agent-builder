---
title: Rate limits
doc_type: reference
workflow: none
version: "1.4"
---

# Rate limits

The workflow API is rate limited per workspace token. Limits protect the shared editor backend and apply to every workflow in the same way.

## Limits

Each token can send 120 requests per minute. Bursts above that return status 429 with a `Retry-After` header that tells you how many seconds to wait. Read only calls such as listing pages do not count against the limit.

## Backing off

Retry a 429 after the delay in `Retry-After`. Do not retry 409 or 422 responses, they will fail the same way again. Build scripts should serialize workflow calls because later calls depend on ids returned by earlier ones anyway.

## Quick facts

- Requests per minute per token: 120
- Status code when the limit is hit: 429
- Header that carries the wait time: Retry-After
