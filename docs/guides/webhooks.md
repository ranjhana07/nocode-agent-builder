---
title: Webhooks and integrations
doc_type: guide
workflow: none
version: "1.4"
---

# Webhooks and integrations

Webhooks notify other systems when something happens in an app. They are configured per app in the editor.

## Events

- `form.submitted` fires after a bound form writes a record.
- `record.created` fires for every new record, including seeded ones.
- `site.published` fires when a publish finishes.

## Delivery

Each delivery is an HTTPS POST with a JSON body and an `X-Nocode-Signature` header that holds an HMAC of the body. Deliveries that fail are retried 5 times with growing delays. After the last retry the webhook is paused.

## Integrations

Native integrations exist for Slack, Google Sheets and Stripe. They use the same event stream as webhooks, so an event can feed both.

## Quick facts

- Delivery retries: 5
- Signature header: X-Nocode-Signature
- Event fired after a publish finishes: site.published
- Native integrations: Slack, Google Sheets and Stripe
