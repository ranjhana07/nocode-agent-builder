---
title: How to set up sign in for a customer portal
doc_type: guide
workflow: create_auth_flow
version: "1.4"
---

# How to set up sign in for a customer portal

This walkthrough adds email sign in to a portal with two roles.

## Steps

1. Create the app with `create_app` and note its id.
2. Add the login page with `create_page` using the slug `login`.
3. Call `create_auth_flow` with `method` set to `email_password` and `roles` set to customer and support.
4. Leave `require_verification` at its default so new accounts confirm their email.
5. Publish to staging and test the sign in before going to production.

## Troubleshooting

If the call returns 409 the app already has an auth flow. Each app has exactly one, so decide on a single method for the app.

## Quick facts

- The sign in page slug is a convention, not a requirement
- Auth flows are created per app, not per page
