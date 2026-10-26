# K-03 Relation Traversal Remediation

Date: 2026-10-26

## Status

Implemented for happy-path acceptance remediation. Final acceptance remains pending until K-03 is rerun against the existing acceptance database after merge.

## Problem

`object relations --object <id>` previously resolved the queried Object's own current Knowledge Version first and then returned only Relations stored in that Version.

This failed for a valid Registry Object that was only the target endpoint of another Object's current accepted Relation and had no Knowledge Version of its own. The happy-path case was:

- OBJ-A current V2 owns `OBJ-A --relation:protagonist_of_work--> OBJ-B`.
- OBJ-B exists in the Object Registry.
- OBJ-B has no current Knowledge Version.
- Reading Relations from OBJ-B failed with `Object has no current Knowledge Version` before Relation traversal occurred.

## Decision

Canonical Relation storage is unchanged. `object_relations.version_id` continues to identify the immutable Knowledge Version that owns the Relation, and canonical subject/object direction is never inverted or duplicated.

`get_object_relations` now has two explicit scopes:

1. `current_relation_graph` when `version_id` is omitted.
   - The queried Object only needs to exist in the Object Registry.
   - Search both `subject_object_id` and `object_object_id` endpoints.
   - Include a Relation only when its owner Version is `accepted` and is the owner Object's current Version.
   - The queried Object may have `current_version_id = NULL`.
   - Return `perspective = outgoing | incoming | self` without changing canonical direction.
   - Return `owner_object_id` and `owner_version_id` so the immutable Version source remains explicit.
   - Resolve Relation Evidence from each Relation's owner Version.

2. `pinned_object_version` when `version_id` is provided.
   - Preserve the previous Version-local historical read semantics.
   - The pinned Version must belong to the queried Object and be accepted.

`get_object()` remains an immutable Object-Version snapshot read and is not broadened to include incoming Relations owned by other Objects.

## Data model impact

No SQLite migration and no canonical data rewrite are required.

Existing indexes already cover:

- `object_relations(subject_object_id, relation_type_id)`
- `object_relations(object_object_id, relation_type_id)`
- `object_relations(version_id)`

No inverse Relation is synthesized and no Relation is duplicated into the target Object's Knowledge Version.

## Public read contract

Current graph responses include:

- `scope = current_relation_graph`
- `requested_version_id = null`
- `object_current_version_id` nullable
- `resolved_version_id` nullable for compatibility with the queried Object's own Version state
- `is_current = true`
- canonical Relation rows with `perspective`, `owner_object_id`, and `owner_version_id`

Pinned responses use `scope = pinned_object_version` and retain Version-local semantics.

The MCP output schema permits nullable `resolved_version_id` for this Tool because an endpoint Object can legitimately have no Knowledge Version.

## Regression coverage

Focused tests cover:

- outgoing traversal from the owning subject Object;
- incoming traversal from a target Object with no Knowledge Version;
- preservation of canonical subject/object direction;
- owner Object / owner Version visibility;
- exclusion of Relations from historical non-current owner Versions;
- pinned historical Version reads;
- MCP output validation for an unversioned endpoint Object.

## Acceptance continuation

After merge, rerun K-03 against the existing happy-path acceptance DB. Expected OBJ-B read:

- command succeeds;
- `scope = current_relation_graph`;
- `object_current_version_id = null` is allowed;
- exactly the current `relation:protagonist_of_work` edge is visible;
- `perspective = incoming`;
- canonical `subject_object_id = OBJ-A` and `object_object_id = OBJ-B` remain unchanged;
- Relation Evidence remains resolvable from the owner Version.
