---
title: Getting started with Nocode
doc_type: guide
workflow: none
version: "1.4"
---

# Getting started with Nocode

Nocode is a visual platform for building internal tools, customer portals and public websites without writing code. Everything you can do in the editor is also available as an API workflow, so scripts and agents can build the same apps.

## Core concepts

An app is the top level container. It owns pages, databases, forms, an optional auth flow and its deployments. A page is a screen of the app and holds components such as text, buttons, charts and table views. A database holds tables, tables hold fields and records, and forms collect input from end users and write it into tables.

## Your first app

1. Create an app with the `create_app` workflow. Pick the `blank` template unless you want a starter data model.
2. Add a page with `create_page`. The first page is served at the root of the site.
3. Place components on the page with `add_component`.
4. Create a database and tables if the app stores data.
5. Publish to staging with `publish_site` and check the preview URL.

## Quick facts

- Maximum pages per app: 50
- Maximum components per page: 60
- Default environment when publishing: staging
- Starter templates available: blank, crm, inventory and blog
