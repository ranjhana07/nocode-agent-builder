---
title: Authentication and roles
doc_type: guide
workflow: create_auth_flow
version: "1.4"
---

# Authentication and roles

Apps are public until you add an auth flow. An auth flow decides how end users sign in and which roles exist.

## Methods

- `email_password` uses an email address and a password.
- `magic_link` emails a one time sign in link.
- `oauth_google` and `oauth_github` delegate sign in to the provider.

## Verification

When `require_verification` is true, new users must confirm their email address before they can sign in. OAuth methods always trust the provider, so verification is turned off for them automatically.

## Roles

Roles are free text labels such as `admin` and `editor`. The default role list is `member`. Up to 10 roles can be defined.

## Quick facts

- One auth flow per app
- A second auth flow returns status 409
- Maximum roles per app: 10
