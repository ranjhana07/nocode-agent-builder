---
title: Backups and recovery
doc_type: guide
workflow: none
version: "1.4"
---

# Backups and recovery

Nocode takes a snapshot of every database once a day and keeps the snapshots for a limited time. Snapshots cover tables, fields, relations and records but not uploaded files.

## Retention

Free workspaces keep 7 daily snapshots. Team and Business workspaces keep 30. Snapshots older than the retention window are deleted without notice.

## Restoring

Restoring creates a new database next to the original instead of overwriting it. Review the copy, then point forms and table views at it, or rename it to replace the original. A restore of a large database can take several minutes.

## Manual snapshots

A manual snapshot can be taken before risky changes such as bulk seeding. Manual snapshots are kept until they are deleted and count against the storage quota.

## Quick facts

- Snapshots per day: 1
- Retention on Team plans: 30 days
- Restoring overwrites the original database: no
- Uploaded files are included in snapshots: no
