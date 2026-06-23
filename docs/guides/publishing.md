---
title: Publishing and environments
doc_type: guide
workflow: publish_site
version: "1.4"
---

# Publishing and environments

Publishing makes the current state of an app available at a URL. Nocode has two environments.

## Staging and production

Staging URLs look like `https://order-tracker.staging.nocode.example` and are meant for review. Production is the live site. Publishing to production does not change staging, and vice versa.

## Custom domains

A custom domain can be attached when publishing to production. Using one with staging returns 422. Point a CNAME record of your domain at the production host before you publish.

## Preconditions

An app must contain at least one page before it can be published.

## Quick facts

- Default publish environment: staging
- Custom domains: production only
- An app without pages cannot be published
