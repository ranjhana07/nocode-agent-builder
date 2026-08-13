---
title: Deployment checklist
doc_type: guide
workflow: publish_site
version: "1.4"
---

# Deployment checklist

Run through this list before the first production publish of an app.

## Before you publish

1. Every page has at least one component and a title that makes sense in a browser tab.
2. Forms are bound to tables and a test submission shows up as a record.
3. An auth flow exists if the app handles private data.
4. A staging publish was reviewed by someone who did not build the app.
5. The CNAME record for the custom domain points at the production host.

## After you publish

Publishing again replaces the live version without downtime. Roll back by publishing the previous state of the app, since each publish creates a new deployment record.

## Quick facts

- Publishing again causes downtime: no
- Each publish creates: a deployment record
- Rollback method: publish the previous state
