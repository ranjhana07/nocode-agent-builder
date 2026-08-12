---
title: Platform changelog
doc_type: reference
workflow: none
version: "1.4"
---

# Platform changelog

## 1.4

Custom domains can be attached when publishing to production. The `publish_site` workflow gained the `custom_domain` field. Auth flows now skip email verification for OAuth methods.

## 1.3

Added the `magic_link` sign in method. Seeding now validates enum values and rejects unknown keys, where earlier versions ignored them. The per call limit of `seed_records` was raised from 100 to 500 records.

## 1.2

Introduced `bind_form_to_table` with optional field mapping. Forms created before 1.2 stay unbound until you call the workflow.

## 1.1

Added relations between tables and the `many_to_many` kind.

## Quick facts

- Current API version: 1.4
- Version that raised the seed limit to 500: 1.3
- Version that introduced form binding: 1.2
- Version that added custom domains: 1.4
