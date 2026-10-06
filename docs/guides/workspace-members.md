---
title: Workspace members and permissions
doc_type: guide
workflow: none
version: "1.4"
---

# Workspace members and permissions

Members are the people who build apps in a workspace. They are different from the end users who sign in to an app through its auth flow.

## Roles

- Owner can manage billing, members and every app.
- Admin can manage members and every app but not billing.
- Builder can create and edit apps they have been added to.
- Viewer can open apps in the editor but cannot change them.

## Inviting members

Invitations are sent by email and expire after 7 days. An expired invitation has to be sent again. A member can be added to a single app instead of the whole workspace.

## API tokens

Each member can create personal API tokens. A token carries the permissions of its owner, so a Viewer token cannot call workflows that change data.

## Quick facts

- Invitation validity: 7 days
- Role that can manage billing: Owner
- Viewer tokens can create apps: no
