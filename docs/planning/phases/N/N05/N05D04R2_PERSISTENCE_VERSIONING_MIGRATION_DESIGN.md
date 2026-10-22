# N05D-04R2 — Persistence / Versioning / Migration Design

Status: **R2-03 Complete / Design Freeze**  
Date: **2026-10-23**  
Parent: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`  
Prerequisites:

- `docs/planning/phases/N/N05/N05D04R2_IMPACT_SURVEY.md` — R2-01 Complete
- `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md` — R2-02 Complete / Design Freeze

## 1. Purpose

This document completes **R2-03 [P0] — Persistence / versioning / migration design**.

R2-02 fixed the active semantic contract as:

```text
object_overview
+ facet
+ statement
+ bounded Object aggregation
+ hierarchical Object Similarity
```

R2-03 defines how that contract is persisted and introduced without reinterpreting v1 `object_overall`, mixing v1/v2 active retrieval, or destructively replacing the currently usable Derived Search state before the candidate generation is accepted.

This document is a design freeze only. It does **not**:

- write or execute migration SQL;
- modify production Python code;
- materialize `object_overview` rows;
- generate Embeddings;
- rebuild Qdrant;
- cut over active retrieval;
- delete v1 artifacts;
- run search-quality acceptance;
- run the formal N-05 benchmark.

## 2. Current state after this decision

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = Historical partial / user-aborted
N05D-04R2 = Active
R2-01 = Complete
R2-02 = Complete
R2-03 = Complete
R2-04 = Next / Not Started
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

R2-03 completion authorizes migration/schema implementation work in later R2 tasks. It does not authorize production cutover or formal N-05 timing.

## 3. Design goals

The persistence design must satisfy all of the following at the same time:

1. preserve canonical Object / Version / Facet / Statement / Evidence state;
2. retain v1 `object_overall` rows as identifiable legacy derived artifacts;
3. introduce `object_overview` as a distinct active kind;
4. permit v1 and v2 Derived Search state to coexist during rebuild;
5. make active retrieval select exactly one Knowledge Search generation;
6. permit unchanged Facet/Statement representation and Embedding reuse;
7. isolate Qdrant state per Derived Search generation;
8. allow candidate rebuild failure without damaging the previous active generation;
9. make cutover a small atomic routing change rather than a destructive rebuild;
10. keep current/historical Knowledge semantics membership-based and canonical-pointer-based;
11. make rollback possible without canonical Knowledge rollback;
12. prevent legacy `object_overall` from becoming active merely through an enum/name compatibility alias.

## 4. Identity model — five identities must remain separate

R2 freezes the following identity layers.

### 4.1 Representation content identity

Identifies deterministic semantic text:

```text
kind
+ builder_key
+ builder_version
+ content_hash
```

Stored by `search_representations`.

### 4.2 Knowledge membership identity

Identifies which canonical Object Version / Facet / Statement owns a Search Representation:

```text
membership_id
object_id
version_id
target_kind
facet_id?
statement_id?
```

Stored by `knowledge_search_representation_memberships`.

### 4.3 Embedding Space identity

Identifies the vector space:

```text
provider
model
revision
dimension
normalization/configuration
```

Stored by the existing Embedding Space contract.

### 4.4 Knowledge Search generation identity

**New in R2.**

Identifies one coherent active/candidate Derived Search representation contract and membership set.

A generation is not a Search Representation and is not an Embedding Space.

Example:

```text
Phase-I v1 generation
  object_overall + facet + statement

R2 v2 generation
  object_overview + facet + statement
```

### 4.5 Vector namespace identity

Identifies one backend-specific Vector Index namespace for:

```text
Knowledge Search generation
+ Embedding Space
+ Vector backend
```

For Qdrant this maps to a separate collection/namespace.

These five identities must not be collapsed into one version number.

## 5. `SearchRepresentationKind` contract

R2 implementation must change the domain enum to make semantics explicit.

Active and legacy values:

```text
OBJECT_OVERVIEW = "object_overview"   # active R2 Object-level kind
OBJECT_OVERALL  = "object_overall"    # legacy v1 readable kind
FACET           = "facet"
STATEMENT       = "statement"
EVIDENCE        = "evidence"
```

### 5.1 Generic `OBJECT` alias

The existing generic alias:

```text
OBJECT = "object_overall"
```

must be retired from the active domain contract.

R2 must **not** remap the generic symbol `OBJECT` to `object_overview`, because doing so would make old source code appear semantically compatible while changing its meaning.

Call sites must use explicit names:

```text
OBJECT_OVERVIEW
OBJECT_OVERALL
```

`OBJECT_OVERALL` remains parseable only because persisted legacy rows and historical evidence must remain readable.

### 5.2 Active-path rule

Normal post-cutover materialization/retrieval must reject or exclude `OBJECT_OVERALL` unless the operation is explicitly marked as:

- legacy migration;
- rollback/recovery;
- historical inspection;
- historical benchmark interpretation;
- controlled cleanup.

## 6. Builder key and builder-version persistence

R2-02 already fixed:

```text
builder_key = sgokb-canonical-search
```

Per-kind content-contract versions are:

```text
object_overall  -> 1  # legacy only
object_overview -> 2
facet           -> 1  # unchanged byte contract
statement       -> 1  # unchanged byte contract
evidence        -> 1  # unaffected
```

### 6.1 Global builder-version constant is no longer sufficient

The current implementation has one global `BUILDER_VERSION = "1"`.

R2 must move to per-kind version selection. Conceptually:

```text
builder_version_for(object_overview) = "2"
builder_version_for(facet)           = "1"
builder_version_for(statement)       = "1"
builder_version_for(evidence)        = "1"
```

The generation contract version does not replace these values.

### 6.2 No false version bump

Facet/Statement/Evidence must not be changed to builder version `2` merely because the active generation is v2.

Builder version means semantic/byte content contract, not deployment generation.

## 7. Forward migration number

The current highest committed migration is:

```text
017_cli_registry_proposal_reviews.sql
```

R2 therefore reserves the next forward migration as:

```text
018_search_generation_contract.sql
```

The exact filename is frozen for implementation.

Historical migrations `014`, `015`, `016`, and `017` must not be edited in place.

## 8. Migration 018 — Search Representation kind constraints

Migration 014 currently constrains `search_representations.kind` to the v1 values.

Migration 018 must replace the relevant SQLite table constraint so persisted values allow:

```text
object_overall
object_overview
facet
statement
evidence
```

The old `object_overall` value remains legal for historical/coexistence data.

### 8.1 No row relabeling

Migration 018 must not execute semantic reinterpretation such as:

```sql
UPDATE search_representations
SET kind = 'object_overview'
WHERE kind = 'object_overall';
```

That operation is prohibited.

Existing rows are copied/preserved byte-for-byte when the SQLite CHECK constraint is rebuilt.

### 8.2 Content uniqueness remains unchanged

The uniqueness contract stays:

```text
(kind, builder_key, builder_version, content_hash)
```

Therefore old overall and new overview rows cannot accidentally deduplicate into one content record.

## 9. Migration 018 — Knowledge membership constraints

`knowledge_search_representation_memberships.target_kind` must allow:

```text
object_overall
object_overview
facet
statement
```

Evidence continues to use its separate membership family.

### 9.1 Existing uniqueness remains

Preserve legacy uniqueness for:

```text
one object_overall membership per Object + Version
one facet membership per Object + Version + Facet
one statement membership per Object + Version + Statement
```

### 9.2 New overview uniqueness

Add the equivalent partial uniqueness rule:

```text
one object_overview membership per Object + Version
```

Conceptually:

```text
UNIQUE(object_id, version_id, target_kind)
WHERE target_kind = 'object_overview'
```

### 9.3 Generation ID must not be added to membership identity

Do **not** solve side-by-side generation support by duplicating every Facet/Statement membership row with a `generation_id` column.

Reason:

- unchanged Facet/Statement memberships are semantically identical across v1 and v2;
- duplicated membership rows would create unnecessary point/identity churn;
- current/historical identity belongs to canonical Version membership, not deployment generation.

Generation membership is represented by a separate link table defined below.

## 10. New persistence — `knowledge_search_generations`

Migration 018 must introduce a Knowledge-only generation table.

Logical schema:

```text
knowledge_search_generations
----------------------------
id                    TEXT PRIMARY KEY
contract_key          TEXT NOT NULL
contract_version      INTEGER NOT NULL
state                 TEXT NOT NULL
source_catalog_digest TEXT
membership_digest     TEXT
created_at            TEXT NOT NULL
ready_at              TEXT
retired_at            TEXT
last_error            TEXT
```

Allowed generation state:

```text
building
ready
failed
retired
```

### 10.1 Meaning

`contract_key` identifies the search architecture contract.

Frozen keys:

```text
phase-i-search-v1
n05d04r2-hierarchical-v2
```

`contract_version` is:

```text
1 for Phase-I v1
2 for N05D-04R2 v2
```

It is not a representation builder version.

### 10.2 Generation scope

This generation mechanism applies to **Object Knowledge Derived Search only**.

Evidence Search remains independent and is not migrated into this generation contract by R2.

### 10.3 `ready` meaning

A generation may become `ready` only when its expected Search Representation membership set is complete for the recorded canonical catalog snapshot/digest.

Vector readiness is tracked separately because one representation generation may theoretically be indexed in more than one Embedding Space/backend.

## 11. New persistence — generation membership link

Introduce:

```text
knowledge_search_generation_memberships
---------------------------------------
generation_id  TEXT NOT NULL
membership_id  TEXT NOT NULL
created_at     TEXT NOT NULL
PRIMARY KEY(generation_id, membership_id)
```

Foreign keys:

```text
generation_id -> knowledge_search_generations.id
membership_id -> knowledge_search_representation_memberships.id
```

### 11.1 Why this link exists

This table defines the exact membership set eligible for one generation.

Example:

```text
Facet membership F1 ─┬─ Phase-I v1 generation
                     └─ R2 v2 generation

Statement S1 ────────┬─ Phase-I v1 generation
                     └─ R2 v2 generation

object_overall O1 ──── Phase-I v1 generation only
object_overview V2 ─── R2 v2 generation only
```

This is the core mechanism that allows content/Embedding reuse without active-contract mixing.

## 12. Generation membership invariants

### Phase-I v1 generation

May contain only:

```text
object_overall
facet
statement
```

### R2 v2 generation

May contain only:

```text
object_overview
facet
statement
```

It must contain **no `object_overall` membership**.

### Evidence

`evidence` memberships are never linked to Knowledge generations.

### Verification

A generation cannot become `ready` if:

- an unexpected representation kind is linked;
- an accepted Version expected by the build scope is missing required membership;
- a v2 generation contains `object_overall`;
- an R2 Object Version lacks its required `object_overview`;
- required content Facet/Statement membership is incomplete.

## 13. Generation digests

R2 requires deterministic integrity digests so a candidate cannot be cut over after the canonical catalog changed underneath it.

### 13.1 `source_catalog_digest`

A deterministic digest over the canonical search-routing source snapshot used to build/validate the generation.

At minimum the digest projection must include stable representations of:

```text
accepted Object Version IDs in scope
Object -> current_version_id pointers
Object active/archive status relevant to normal retrieval
Version classification identity required for filters
```

The implementation may include additional canonical identifiers if required for stronger invalidation.

### 13.2 `membership_digest`

A deterministic digest over the generation membership projection.

At minimum sort and hash:

```text
object_id
version_id
target_kind
facet_id?
statement_id?
representation kind
builder_key
builder_version
content_hash
```

Do not depend on database row order.

### 13.3 Cutover guard

Immediately before cutover:

```text
candidate.source_catalog_digest
== freshly computed canonical source catalog digest
```

must hold.

If not, the candidate is stale and must be synchronized/revalidated before it can become active.

## 14. New persistence — active generation pointer

Introduce one Knowledge Search routing pointer:

```text
knowledge_search_active_generation
----------------------------------
scope               TEXT PRIMARY KEY
active_generation_id TEXT NOT NULL
activation_revision  INTEGER NOT NULL
activated_at         TEXT NOT NULL
```

For R2 the only allowed scope is:

```text
knowledge
```

`active_generation_id` references a `ready` Knowledge Search generation.

### 14.1 Single source of active-routing truth

Do not duplicate active state as an independent Boolean on every generation row.

The singleton pointer is the routing truth.

A generation row may be `ready` while not active. This is required for:

- candidate validation before cutover;
- retaining the previous generation as a rollback target.

### 14.2 Query snapshot rule

Every Object Knowledge search/similarity operation must resolve the active generation once at operation start and use the same generation for all channels of that operation.

A single request must not begin on v1 and finish on v2.

## 15. New persistence — generation switch audit

Introduce append-only operational history:

```text
knowledge_search_generation_switches
------------------------------------
id                 TEXT PRIMARY KEY
from_generation_id TEXT
 to_generation_id   TEXT NOT NULL
switch_kind         TEXT NOT NULL
reason              TEXT NOT NULL DEFAULT ''
source_catalog_digest TEXT
switched_at         TEXT NOT NULL
```

Allowed `switch_kind`:

```text
bootstrap
cutover
rollback
recovery
```

This is Derived Search operational audit, not canonical Knowledge.

The active pointer update and switch-log insert must occur in the same SQLite transaction.

## 16. Vector namespace persistence

Current Qdrant collection identity is derived only from Embedding Space. That is insufficient for side-by-side v1/v2 rebuild because rebuilding one space currently replaces the same collection.

Introduce generation-aware vector binding persistence:

```text
knowledge_search_generation_vector_indexes
------------------------------------------
generation_id       TEXT NOT NULL
embedding_space_id  TEXT NOT NULL
backend_key         TEXT NOT NULL
namespace_key       TEXT NOT NULL
status              TEXT NOT NULL
membership_digest   TEXT
point_count          INTEGER
created_at           TEXT NOT NULL
updated_at           TEXT NOT NULL
last_error           TEXT
PRIMARY KEY(generation_id, embedding_space_id, backend_key)
UNIQUE(backend_key, namespace_key)
```

Allowed status:

```text
building
ready
failed
retired
```

### 16.1 Namespace meaning

`namespace_key` is backend-neutral persisted routing metadata.

For Qdrant it identifies one collection dedicated to:

```text
generation_id + embedding_space_id
```

A candidate R2 collection must not reuse or destructively rebuild the active v1 collection.

### 16.2 Existing v1 Qdrant collection

The current Phase-I Qdrant namespace is derived from the Embedding Space and has no persisted generation identity.

Migration SQL cannot safely infer the operator's runtime/backend state.

Therefore:

- migration 018 creates the generation schema and bootstraps v1 membership identity;
- an Application-level legacy bootstrap/registration step later inspects the explicitly configured local Harrier/Qdrant runtime;
- if the existing v1 collection is present and validates, it is registered as the v1 generation's vector namespace;
- if it is absent or invalid, v1 semantic state is explicitly unavailable/rebuild-required rather than fabricated as ready.

No cloud/backend fallback is allowed.

## 17. Vector point identity and payload

### 17.1 Point identity remains membership-scoped

Inside one generation-specific Vector namespace:

```text
point_id = Knowledge membership ID
```

remains valid.

The same Facet/Statement membership ID may exist as a point in both the v1 and v2 collections because the collections are different namespaces.

### 17.2 Payload

Existing payload semantics remain, including:

```text
membership_id
representation_id
kind
object_id
version_id
primary_class
additional_classes
ancestor_classes
object_status
is_current
facet_id
facet
statement_id
derivation_kind
temporal metadata
```

R2 adds:

```text
generation_id
```

as defensive/audit metadata.

For R2 points:

```text
kind = object_overview | facet | statement
```

`kind = object_overall` must not appear in the R2 generation namespace.

### 17.3 Defensive verification

Vector retrieval must verify that returned payload generation identity equals the generation resolved at query start.

A mismatch is an integrity error, not a candidate to silently ignore and replace from another generation.

## 18. FTS / Knowledge lexical generation scoping

The existing FTS table indexes `search_representations` globally.

That table may contain both:

```text
legacy object_overall
new object_overview
shared facet/statement
```

This is allowed because FTS is a derived content index.

Normal Knowledge lexical retrieval must scope FTS candidates through:

```text
active generation
  -> generation membership link
  -> Knowledge membership
  -> Search Representation / FTS
```

Therefore old `object_overall` text can remain physically indexed without becoming active retrieval evidence.

### 18.1 Migration 018 FTS handling

Because migration 018 must rebuild the `search_representations` CHECK constraint, the migration must explicitly preserve/recreate Migration-016 FTS triggers and rebuild/repopulate `search_representation_fts` deterministically after the parent-table swap.

FTS is derived and may be rebuilt; canonical Knowledge is not touched.

## 19. Embedding persistence and reuse

The existing Embedding cache key remains correct:

```text
representation_id + embedding_space_id
```

No generation ID is added to Embedding identity.

### 19.1 `object_overview`

Must receive a new representation identity and therefore a new Harrier embedding.

It cannot reuse an `object_overall` vector.

### 19.2 Facet / Statement

May reuse the existing embedding when all are true:

```text
same representation_id
same kind
same builder_key
same builder_version
same content_hash
same Embedding Space
```

Because R2-02 leaves their content contract unchanged, this is the expected normal case.

### 19.3 Legacy overall embedding

Existing `object_overall` embeddings are retained for:

- v1 rollback while eligible;
- historical diagnostics;
- old benchmark interpretation.

They are not copied into the R2 generation.

## 20. Migration 018 data strategy

Migration 018 is a **schema/coexistence migration**, not the R2 data cutover.

It must:

1. expand Search Representation kind persistence to allow `object_overview` while preserving v1 rows;
2. expand Knowledge membership kind persistence while preserving v1 memberships;
3. add overview uniqueness;
4. add generation tables and routing metadata;
5. seed a legacy Phase-I v1 generation representing the existing Knowledge membership set;
6. link all existing Knowledge memberships to that legacy v1 generation;
7. preserve all existing Search Representation IDs, membership IDs, Embedding rows, and canonical data;
8. recreate/repopulate FTS safely after table-constraint rebuild;
9. run SQLite integrity / foreign-key verification after copy/swap;
10. leave creation of R2 `object_overview` rows to R2-04;
11. leave Qdrant candidate generation/cutover to R2-07.

### 20.1 Legacy bootstrap generation

Use one explicit legacy contract identity:

```text
contract_key     = phase-i-search-v1
contract_version = 1
```

Its generation ID may be a stable migration-defined ID so the migration is deterministic/idempotent.

It contains all pre-existing Knowledge Search memberships and no Evidence memberships.

### 20.2 No destructive cleanup in migration 018

Do not delete:

- `object_overall` representations;
- `object_overall` memberships;
- old Embeddings;
- existing Qdrant collection;
- historical accepted Version memberships.

## 21. Candidate R2 generation construction

R2-04/R2-07 will construct a candidate generation with:

```text
contract_key     = n05d04r2-hierarchical-v2
contract_version = 2
state            = building
```

For each accepted Version in rebuild scope:

```text
object_overview v2 membership  -> create/link
facet v1 membership            -> reuse/link when unchanged
statement v1 membership        -> reuse/link when unchanged
```

After complete membership verification and digest calculation:

```text
state = ready
```

No active pointer change occurs merely because the candidate becomes ready.

## 22. Candidate embedding/vector build

For the first R2 baseline:

```text
Embedding Space = frozen Harrier OSS v1 0.6B / 1024-dim space
```

Build order:

```text
candidate generation membership set
  ↓
reuse existing Facet/Statement embeddings
  ↓
generate missing object_overview embeddings
  ↓
build fresh generation-specific Qdrant namespace
  ↓
verify point count / membership digest / payload generation_id
  ↓
vector binding status = ready
```

A candidate generation is not cutover-eligible until its frozen Harrier vector binding is `ready`.

## 23. Active/candidate cutover contract

Cutover is routing, not data rewriting.

### 23.1 Preconditions

Before changing the active pointer, all must pass:

1. candidate generation `state = ready`;
2. candidate contract is `n05d04r2-hierarchical-v2`;
3. no candidate membership has `target_kind = object_overall`;
4. every required accepted Version has expected R2 memberships;
5. candidate `source_catalog_digest` matches a freshly computed canonical digest;
6. candidate `membership_digest` matches the persisted link set;
7. frozen Harrier Embedding completeness passes;
8. candidate Qdrant binding is `ready`;
9. Vector point count/digest agrees with generation membership requirements;
10. Vector payload generation identity is correct;
11. required smoke/filter checks pass;
12. R2-required quality authorization for the cutover stage has been obtained according to the later R2 task order.

### 23.2 Atomic switch

The actual switch is one SQLite transaction:

```text
read current active generation
update knowledge_search_active_generation -> candidate
increment activation_revision
insert knowledge_search_generation_switches(cutover)
commit
```

No Qdrant mutation occurs inside this switch transaction.

The candidate Qdrant namespace already exists and is ready before the pointer changes.

### 23.3 Retrieval after commit

All new Knowledge retrieval resolves the new generation and its vector namespace.

The previous generation remains physically intact and `ready` as a bounded rollback target.

## 24. Preventing v1/v2 query mixing

After generation-aware retrieval is enabled, the following are prohibited:

- scanning all `knowledge_search_representation_memberships` without active-generation scope for normal Object search;
- querying the v1 and v2 Qdrant namespaces in the same normal request;
- unioning `object_overall` and `object_overview` candidate sets;
- resolving active generation separately per channel within one request;
- using the active v2 SQLite membership set with the v1 Vector collection;
- accepting a Qdrant point whose payload generation differs from the request generation.

A request resolves one generation and uses it for:

```text
Knowledge lexical
Object semantic
Facet semantic
Statement semantic
Object Similarity
```

Evidence Search is outside this generation scope.

## 25. Current / historical semantics remain membership-based

Generation does not redefine Knowledge time/version semantics.

Normal current retrieval remains:

```text
active Object
+ accepted Version
+ Object.current_version_id == membership.version_id
+ membership belongs to resolved active generation
```

Historical retrieval remains:

```text
explicit accepted Version scope
+ membership belongs to resolved active generation
```

A generation may contain memberships for multiple accepted historical Versions.

`is_current` remains derived from canonical Object current pointers, not generation age.

## 26. Incremental maintenance after cutover

The existing N04P01 per-Object revision guard remains authoritative for normal accepted-Version promotion/rollback maintenance.

R2 generation identity adds contract routing; it does not replace:

```text
object_id
kind
target_version_id
revision
```

revision guards.

Post-cutover incremental sync must write/link newly materialized active R2 memberships only into the active R2 generation.

It must not silently continue maintaining the retired v1 `object_overall` path.

During an explicit rollback-validation window, keeping v1 synchronized would require an explicit dual-generation maintenance mode; R2 does not assume such dual-write behavior.

## 27. Full rebuild contract after R2

### 27.1 Search-contract/full-pipeline rebuild

When a full Derived Search contract rebuild is required, use a **new candidate generation**.

Do not clear the active generation first.

Flow:

```text
active generation remains serving
        ↓
new candidate generation
        ↓
representation membership build
        ↓
embedding reuse/generation
        ↓
new Vector namespace
        ↓
validation
        ↓
atomic pointer switch
```

### 27.2 Vector-only recovery

The existing `system index rebuild` meaning remains Vector-only.

For an active generation whose Vector namespace is lost/corrupt, recovery must not claim readiness until a complete namespace is rebuilt from the generation's memberships + persisted Embeddings.

When an intact previous namespace exists, rebuild should prefer a fresh namespace and routing update over destructive in-place replacement.

A lost active Vector namespace may make semantic retrieval explicitly unavailable while Lexical/Identity paths remain available according to existing failure semantics.

## 28. Interrupted candidate rebuild

If R2 candidate construction stops at any point:

```text
active generation pointer = unchanged
candidate state            = building or failed
candidate Vector binding   = building or failed
canonical Knowledge         = unchanged
```

Normal retrieval continues through the previous active generation if that generation is healthy.

A partially built candidate must never be selected automatically.

No process may infer active status from "newest generation" or highest contract version.

Only the explicit active pointer authorizes serving.

## 29. Rollback contract

Rollback changes Derived Search routing only.

It never rolls back:

- canonical Object Version;
- current Object pointer;
- accepted Knowledge;
- Evidence;
- Source/Provenance.

### 29.1 Rollback eligibility

A previous generation may be selected only when:

1. generation state is `ready`;
2. its required Vector binding for the selected Embedding Space/backend is `ready`;
3. its recorded source/catalog compatibility still matches the current canonical state required for correct retrieval;
4. its membership/vector integrity checks pass.

### 29.2 Canonical changes after cutover

R2 does not require indefinite dual-write of v1 and v2.

Therefore, after canonical accepted/current state changes under v2, the old v1 generation may no longer be rollback-eligible.

If its catalog digest is stale:

```text
rollback = prohibited
```

until an explicit compatible legacy rebuild/backfill is performed.

Never serve a stale v1 generation merely because its Qdrant collection still exists.

### 29.3 Atomic rollback

Eligible rollback uses the same active-pointer transaction as cutover and records:

```text
switch_kind = rollback
```

## 30. Physical retirement / cleanup

Logical cutover and physical deletion are separate operations.

After v2 cutover:

- v1 is removed from **normal active routing immediately** by the pointer switch;
- v1 Search Representations/memberships/Embeddings/Qdrant namespace may remain for rollback/evidence;
- physical cleanup is not part of R2-03 or migration 018.

Physical cleanup may occur only after the later acceptance/rollback-retention decision.

Historical benchmark/evaluation files remain untouched regardless of derived database cleanup.

## 31. Migration 018 implementation order

The forward migration implementation must follow this logical order.

```text
1. establish migration preconditions / existing schema checks
2. rebuild search_representations constraint with object_overview allowed
3. rebuild knowledge membership constraint with object_overview allowed
4. recreate all preserved indexes / foreign keys
5. create object_overview partial uniqueness index
6. create knowledge_search_generations
7. create knowledge_search_generation_memberships
8. create knowledge_search_active_generation
9. create knowledge_search_generation_switches
10. create knowledge_search_generation_vector_indexes
11. bootstrap Phase-I v1 generation
12. link all existing Knowledge memberships to v1 generation
13. create bootstrap active-generation routing record where applicable
14. recreate/repopulate search_representation_fts and triggers
15. verify row counts / IDs / content hashes unchanged for copied v1 data
16. run foreign-key/integrity checks
17. commit migration
```

Exact SQLite DDL mechanics may use temporary replacement tables as required, but they must preserve the semantics above.

## 32. Migration verification requirements

Migration-focused tests must prove at least:

### Schema

- `object_overview` representation insert is accepted;
- `object_overview` Knowledge membership insert is accepted;
- invalid representation kind is rejected;
- Evidence cannot enter Knowledge membership family;
- overview uniqueness is enforced;
- legacy overall uniqueness still works;
- existing Facet/Statement uniqueness still works.

### Preservation

Given a pre-018 database with v1 rows:

- every `search_representations.id` is preserved;
- every v1 content hash/content is preserved;
- every Knowledge membership ID is preserved;
- every Embedding row is preserved;
- canonical Object/Version/Facet/Statement row counts and values are unchanged.

### Generation bootstrap

- existing Knowledge memberships are linked to the legacy v1 generation;
- Evidence memberships are not linked;
- the v1 generation contains no `object_overview`;
- generation/member digests are deterministic.

### FTS

- pre-existing v1 text remains searchable at the raw FTS layer after migration;
- new `object_overview` rows are indexed by the recreated trigger;
- active-generation-scoped retrieval can exclude legacy `object_overall` after v2 cutover.

### Integrity

- `PRAGMA foreign_key_check` equivalent passes;
- migration is deterministic from the same pre-migration state;
- no automatic Qdrant deletion/rebuild occurs as an SQL migration side effect.

## 33. R2 implementation boundaries created by this design

### R2-04

May implement:

- enum change;
- per-kind builder version selection;
- deterministic `object_overview` builder;
- migration 018 schema support required for persistence;
- overview membership materialization;
- generation membership linking needed by the builder path.

R2-04 must not perform production cutover merely because schema/building works.

### R2-05

Must make Hybrid/Knowledge lexical retrieval generation-aware and active-family-aware.

### R2-06

Must make hierarchical Similarity generation-aware and must use only vector points from the resolved generation.

### R2-07

Owns:

- legacy v1 Vector namespace registration/verification;
- candidate R2 generation assembly/backfill;
- side-by-side Harrier Embedding completion;
- generation-specific Qdrant namespace build;
- cutover preflight;
- atomic active pointer switch;
- rollback rehearsal;
- post-cutover no-mixing verification.

## 34. Explicitly rejected alternatives

### A. Rename `object_overall` in place

Rejected because the semantic content contract changes.

### B. Put generation ID directly into representation content identity

Rejected because identical Facet/Statement content must remain reusable.

### C. Duplicate all Facet/Statement membership rows for v2

Rejected because membership identity is canonical Version ownership, not generation ownership.

### D. Reuse one Qdrant collection and tag points with generation only

Rejected for the R2 cutover path because destructive rebuild or partially mixed point sets could affect the serving generation.

Generation-specific namespace isolation is safer.

### E. Treat Embedding Space as the generation identity

Rejected because v1 and v2 deliberately use the same Harrier Embedding Space for causal comparison.

### F. Delete v1 before building v2

Rejected because candidate failure would destroy the last known serving state and violate R2 safety requirements.

### G. Let newest generation automatically become active

Rejected. Only the explicit active pointer may authorize serving.

## 35. R2-03 exit checklist

The following decisions are frozen:

- [x] active enum adds `object_overview`;
- [x] `object_overall` remains legacy-readable only;
- [x] ambiguous generic `OBJECT` alias is retired rather than remapped;
- [x] migration number is `018_search_generation_contract.sql`;
- [x] historical migrations are not edited;
- [x] SQLite kind constraints permit old/new coexistence;
- [x] old rows are preserved, not relabeled;
- [x] builder versioning is per representation kind;
- [x] overview membership uniqueness is defined;
- [x] generation ownership uses a separate generation→membership link;
- [x] Facet/Statement memberships may be shared across generations;
- [x] Embedding reuse remains representation × Embedding Space scoped;
- [x] old overall embedding is not reusable as overview;
- [x] Knowledge lexical retrieval becomes generation-scoped;
- [x] vector point identity remains membership-scoped inside a generation namespace;
- [x] Qdrant namespace becomes generation-aware;
- [x] vector payload includes generation identity;
- [x] active generation uses one explicit SQLite pointer;
- [x] cutover/rollback pointer changes are transactional and audited;
- [x] interrupted candidate rebuild leaves active generation unchanged;
- [x] rollback requires catalog/integrity compatibility;
- [x] current/historical semantics remain membership + canonical pointer based;
- [x] Evidence Search remains outside Knowledge generation migration;
- [x] no destructive v1 cleanup occurs before later acceptance.

No unresolved persistence/versioning/migration design question blocks implementation.

## 36. Next task

```text
R2-04 [P0] — Implement compact object_overview
```

R2-04 may implement the schema/domain/builder pieces needed to persist the frozen contract, but must not skip ahead to production cutover, R2-08 quality acceptance, or R2-09 formal N-05 rerun.
