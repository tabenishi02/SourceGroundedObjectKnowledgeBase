# N05D-04R2 Impact Survey / Redesign Freeze

Status: **R2-01 Complete**  
Date: **2026-10-23**  
Audited source of truth: GitHub `main` at `f5f0d2f72b68994cfd61f3fb2eda81f34cc991ae` before this document commit  
Scope: **impact survey and redesign-boundary freeze only**

## 1. Purpose

This document completes **R2-01 [P0] — Impact survey / redesign freeze** for N05D-04R2.

The accepted R2 direction is:

```text
compact object_overview
+ Facet representations
+ Statement representations
+ bounded Object aggregation
+ hierarchical Object Similarity
```

The change is a representation-architecture correction. It is **not** arbitrary token chunking and does not change the canonical Object / Facet / Statement semantic boundaries.

R2-01 does **not** implement the redesign. It inventories the current `object_overall` dependency surface, classifies each impact, freezes the compatibility and migration boundaries, and defines what later R2 tasks must change or preserve.

The following are explicitly outside R2-01:

- no production implementation;
- no schema/data migration execution;
- no embedding/vector rebuild execution;
- no formal N-05 benchmark rerun;
- no Harrier model change;
- no FlashAttention-2 introduction;
- no PyTorch upgrade;
- no CPU fallback;
- no truncation workaround;
- no R2-02 or later contract design.

## 2. Current phase state

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = Historical partial / user-aborted
N05D-04R2 = Active
R2-01 = Complete by this document
R2-02 = Not Started
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

R2-01 completion does not unblock N05D-04 or N-05 by itself.

## 3. Why R2 is required

The old active retrieval design materializes one `object_overall` representation for an Object Version in addition to Facet and Statement representations. In the N05D-04 failure case, a real canonical Object produced an approximately 18,847-token `object_overall`. The same semantic detail already exists under canonical Facet and Statement boundaries, but the old representation duplicates it into one monolithic full-attention embedding input.

N05D-04 diagnostics showed that the dominant failure is not ordinary model residency. The oversized active representation drove approximately 51.1 GiB peak Torch allocation and approximately 628–643 seconds for the problematic embedding path. Consequently, changing model size, attention implementation, runtime, fallback device, or truncation at the same time would obscure whether the representation correction itself fixes the blocker.

Therefore the first R2 baseline keeps **Harrier OSS v1 0.6B** and isolates the effect of the representation redesign.

## 4. Classification vocabulary

Every inventory item below is assigned one primary disposition.

| Classification | Meaning in R2 |
|---|---|
| **KEEP unchanged** | The contract/data/code asset remains valid under R2 and should not be redesigned merely because `object_overall` is retired. |
| **RENAME / compatibility shim** | A name or compatibility boundary must bridge old and new terminology without treating old semantics as new semantics. |
| **CHANGE semantics** | The behavior/meaning must change under the hierarchical multi-vector contract. |
| **MIGRATE data** | Persisted DB values/rows must be transitioned by a forward migration or controlled cleanup/re-materialization. |
| **REBUILD derived artifact** | Rebuildable embedding/vector/derived state must be regenerated from the R2-valid representations rather than migrated as authoritative data. |
| **UPDATE gold/test** | Tests, fixtures, gold expectations, or algorithm-sensitive acceptance assertions encode the old representation contract and need a successor expectation. |
| **HISTORICAL only** | The asset records a completed/aborted earlier contract or diagnostic result and must remain immutable evidence rather than being rewritten as if R2 existed at that time. |

## 5. Redesign boundary freeze

R2-01 freezes the following boundaries for later tasks.

### 5.1 Canonical knowledge boundaries stay unchanged

Object, Version, Facet, Statement, Source, Evidence, Evidence Link, Provenance, temporal scope, class taxonomy, and canonical acceptance semantics are not redesigned by R2.

R2 changes only the **derived search representation and retrieval composition** built from canonical knowledge.

### 5.2 `object_overall` retires from active retrieval

`object_overall` must no longer be an active semantic-search or overall-similarity representation after R2 migration/rebuild.

The replacement is a compact `object_overview` representation plus existing canonical Facet and Statement representations.

### 5.3 `object_overview` is not a rename of `object_overall`

The new overview has intentionally different content and boundedness. Therefore:

- old `object_overall` persisted rows cannot be reinterpreted in place as semantically equivalent overview rows;
- deterministic representation IDs that include representation kind must not be preserved by pretending the kind is unchanged;
- a compatibility parser/shim may recognize legacy `object_overall` only where needed for migration, historical inspection, or controlled cleanup;
- the active contract must emit/use `object_overview`, not the old name.

### 5.4 Facet and Statement representations remain first-class

Existing Facet and Statement representations are the canonical semantic sub-boundaries used by R2. Their basic ownership model remains valid. R2-02 may specify bounded aggregation rules around them, but R2 does not replace them with arbitrary token chunks.

### 5.5 Object aggregation becomes bounded and hierarchical

Hybrid Search may still return one Object-level result, but semantic evidence must be composed from bounded `object_overview` / Facet / Statement contributions rather than relying on one monolithic object vector.

### 5.6 Overall Object Similarity changes internally, public entrypoint stays stable

The public `find_similar_objects` operation remains an Object-level operation. Its non-facet overall comparison must stop using one `object_overall` query/candidate vector and move to hierarchical multi-vector Object scoring.

Facet-specific similarity remains a same-Facet comparison and must not silently fall back to an Object-wide representation.

### 5.7 Derived lifecycle ownership remains valid

The existing lifecycle distinction remains:

```text
canonical DB state
  -> search representations
  -> embeddings
  -> vector index
```

Search representations, embeddings, and vector-index state remain rebuildable derived state. R2 changes the membership/meaning of the first derived layer, not the canonical commit boundary.

### 5.8 First redesign baseline is model/runtime controlled

For the first post-R2 implementation/evaluation baseline:

```text
Harrier OSS v1 0.6B = KEEP
Harrier 270M = do not introduce
FlashAttention-2 = do not introduce
PyTorch upgrade = do not introduce
CPU fallback = do not introduce
truncation = do not introduce
```

This is necessary to attribute any viability/performance change to the representation redesign itself.

## 6. Impact inventory — contracts and design documents

| Asset / contract | Dependency / impact | Classification | Frozen R2 disposition |
|---|---|---|---|
| `docs/requirements/SEARCH_REQUIREMENTS.md` — Object-level search/public behavior | Search remains Object-oriented and source-grounded. | **KEEP unchanged** | Preserve public Object search goals, filtering, grounding, bounded result behavior. |
| `docs/design/SEARCH_REPRESENTATION_SCHEMA.md` — canonical ownership / deterministic representation concept | Object/Facet/Statement-derived representation architecture remains valid. | **KEEP unchanged** | Preserve canonical source ownership and deterministic derivation principles. |
| `docs/design/SEARCH_REPRESENTATION_SCHEMA.md` — `object_overall` kind/content/cardinality | Defines one monolithic `object_overall` per Version. | **CHANGE semantics** | R2 successor contract must define compact `object_overview`; Facet/Statement remain separate. |
| `SearchRepresentationKind.OBJECT = "object_overall"` compatibility alias contract | Old alias can accidentally preserve old meaning. | **RENAME / compatibility shim** | Any legacy alias must be bounded to compatibility/migration; active meaning must resolve to overview semantics only after explicit contract change. |
| `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md` — independent semantic channels | Current channels include `object_overall`, Facet, Statement. | **CHANGE semantics** | Active channels become overview + Facet + Statement with bounded Object aggregation. |
| Hybrid facet-filter rule excluding `object_overall` | Rule prevents Object-wide evidence from leaking into a facet-scoped query. | **CHANGE semantics** | Preserve the safety property; R2-02 must restate whether/how overview is excluded under facet-scoped search. No implicit broadening. |
| Hybrid one-row-per-Object output and bounded evidence model | Independent of old kind name. | **KEEP unchanged** | Preserve external Object-level aggregation/result shape and evidence bounding. |
| `docs/design/OBJECT_SIMILARITY_SEARCH.md` — overall comparison unit | Explicitly uses `object_overall` source/candidate vectors. | **CHANGE semantics** | Overall similarity becomes hierarchical multi-vector scoring. |
| Object Similarity same-space, self-exclusion, latest-target-Version, deterministic sort/filter policy | Independent of monolithic representation. | **KEEP unchanged** | Preserve unless a later task identifies a strictly necessary contract amendment. |
| `docs/decisions/N04P01_DERIVED_SEARCH_LIFECYCLE_CONTRACT.md` — lifecycle ownership/rebuildability | Defines canonical -> representation -> embedding -> vector derived chain. | **KEEP unchanged** | Lifecycle/atomicity/status truthfulness remains authoritative. |
| N04P01 representation membership assumptions tied to old representation set | Expected derived membership changes. | **CHANGE semantics** | R2 successor must update active membership/count semantics without weakening lifecycle correctness. |
| `docs/planning/phases/I/PHASE_I_PREPARATION.md` historical Phase-I execution record | Records the design state that introduced the old contract. | **HISTORICAL only** | Do not rewrite Phase-I history; active design docs receive successor revisions later. |
| N05D-01/N05D-02/N05D-03 diagnostic conclusions under old contract | Explain the blocker and old-contract viability. | **HISTORICAL only** | Preserve as evidence leading to R2; do not restate them as R2 results. |
| N05D-04R1 design/diagnostic records | User-aborted partial remediation path. | **HISTORICAL only** | Preserve; no implicit carry-forward into R2 baseline. |

## 7. Impact inventory — domain, persistence, and migrations

| Asset / code path | Dependency / impact | Classification | Frozen R2 disposition |
|---|---|---|---|
| `src/sgokb/domain/knowledge.py` — Object/Version/Facet/Statement domain types | Canonical semantic boundaries used by R2. | **KEEP unchanged** | R2 must build on these boundaries. |
| `src/sgokb/domain/knowledge.py` — `SearchRepresentationKind.OBJECT_OVERALL` and `OBJECT` alias | Active enum/value encodes old kind. | **RENAME / compatibility shim** | Introduce active overview terminology in a later task; any legacy value recognition is compatibility-only. |
| `src/sgokb/migrations/014_search_representations.sql` — table/ownership columns | Core derived representation storage remains usable. | **KEEP unchanged** | Do not edit historical migration 014 in place. |
| Migration 014 `representation_kind CHECK ('object_overall','facet','statement')` | New active kind cannot be stored under current constraint. | **MIGRATE data** | Add a new forward migration; do not rewrite migration history. |
| Existing `search_representations.representation_kind='object_overall'` rows | Persisted old semantic representation. | **MIGRATE data** | Controlled retirement/cleanup and R2 re-materialization are required; do not relabel text in place. |
| Existing deterministic `object_overall` representation IDs/hashes | Derived from old kind/content. | **MIGRATE data** | New overview must receive R2-valid deterministic identity/hash; old rows are not authoritative overview data. |
| `src/sgokb/migrations/016_hybrid_search.sql` FTS table/triggers | Indexes search representation text generically. | **KEEP unchanged** | No redesign solely for the new representation kind unless later migration mechanics require DDL maintenance. |
| `src/sgokb/storage/semantic_repository.py` generic representation CRUD/list APIs | Storage operations are kind-agnostic except enum/value parsing. | **KEEP unchanged** | Preserve repository shape; active/legacy kind handling changes at contract boundary. |
| Repository enum parsing of persisted `representation_kind` | Must survive controlled migration/legacy inspection. | **RENAME / compatibility shim** | Support only the minimum bounded legacy path needed; active reads after migration use overview. |

## 8. Impact inventory — search representation producer

| Asset / code path | Dependency / impact | Classification | Frozen R2 disposition |
|---|---|---|---|
| `src/sgokb/retrieval/search_representation.py` materialization orchestration | Deletes/rebuilds a Version's derived search representations. | **KEEP unchanged** | Retain deterministic per-Version materialization lifecycle. |
| `_build_object_representation` / mandatory `OBJECT_OVERALL` emission | Concatenates broad Object/Version/Facet/Statement/evidence content into one large input. | **CHANGE semantics** | Replace with compact, bounded overview generation contract in later R2 task. |
| Facet representation generation | Already follows canonical Facet boundary. | **KEEP unchanged** | Keep as R2 first-class semantic vector source. |
| Statement representation generation | Already follows canonical Statement boundary. | **KEEP unchanged** | Keep as R2 first-class semantic vector source. |
| Representation-kind-derived deterministic IDs and text hashes | Overview kind/content changes IDs/hashes. | **CHANGE semantics** | R2 active overview identity must derive from new kind/content; no ID preservation by semantic aliasing. |

## 9. Impact inventory — Derived Search lifecycle / embeddings / vector index

| Asset / code path | Dependency / impact | Classification | Frozen R2 disposition |
|---|---|---|---|
| `src/sgokb/application_derived.py` sync orchestration, idempotence, truthful status model | Generic lifecycle machinery. | **KEEP unchanged** | Preserve synchronization/atomicity/error behavior. |
| Embedding job membership produced from active search representations | Old set includes oversized `object_overall`. | **CHANGE semantics** | Membership follows overview + Facet + Statement after R2 materialization. |
| Existing embedding rows/memberships for `object_overall` | Derived from retired representation IDs/text. | **REBUILD derived artifact** | Regenerate from the R2 representation set; do not migrate vector values as if equivalent. |
| Existing SQLite/Qdrant vector points for `object_overall` memberships | Derived from old embeddings/kind metadata. | **REBUILD derived artifact** | Rebuild/prune index to R2-valid points. |
| Vector point metadata fields such as object/version/facet/statement/currentness | Needed for filtering and hierarchy. | **KEEP unchanged** | Preserve metadata contract; active `kind` value changes through rebuilt points. |
| Derived status/rebuild CLI behavior | Public operational lifecycle remains required. | **KEEP unchanged** | Counts/digests may change, but status must remain truthful and rebuildable. |
| Harrier OSS v1 0.6B embedding provider baseline | Controlled baseline for structural evaluation. | **KEEP unchanged** | First R2 viability run must use this baseline. |

## 10. Impact inventory — Hybrid Search

| Asset / code path | Dependency / impact | Classification | Frozen R2 disposition |
|---|---|---|---|
| `src/sgokb/retrieval/hybrid_search.py` active semantic kind set | Non-facet search currently queries `OBJECT_OVERALL`, Facet, Statement. | **CHANGE semantics** | Query overview + Facet + Statement under bounded hierarchical aggregation. |
| Facet-scoped semantic candidate generation | Currently restricts to Facet/Statement and excludes Object-wide rep. | **KEEP unchanged** | Preserve scope safety; exact overview exclusion wording moves to R2 contract. |
| Lexical channel and exact identity/alias channel | Not dependent on old representation kind. | **KEEP unchanged** | Do not change merely to solve R2. |
| Object-level normalization/fusion and one-row-per-Object contract | Still required, but semantic evidence input composition changes. | **CHANGE semantics** | Bounded hierarchical contribution rules must replace monolithic-object contribution semantics. |
| Public semantic evidence `representation_kind` value | Old results may expose `object_overall`. | **RENAME / compatibility shim** | Active post-R2 evidence uses `object_overview`; old value remains historical/legacy only. |

## 11. Impact inventory — Object Similarity

| Asset / code path | Dependency / impact | Classification | Frozen R2 disposition |
|---|---|---|---|
| `src/sgokb/retrieval/similarity.py` overall source-vector lookup | Hard-requires `OBJECT_OVERALL`. | **CHANGE semantics** | Build bounded hierarchical query representation/score from overview + relevant Facet/Statement vectors. |
| SQLite candidate SQL `representation_kind='object_overall'` | Hard-coded old candidate unit. | **CHANGE semantics** | Replace with hierarchical candidate acquisition/scoring contract. |
| Qdrant candidate filter for `object_overall` | Hard-coded old candidate unit. | **CHANGE semantics** | Replace consistently with the same R2 semantic contract as SQLite path. |
| Facet-specific Similarity | Uses same-Facet representation and no overall fallback. | **KEEP unchanged** | Preserve same-Facet semantics and explicit missing-Facet failure. |
| Same-class default / explicit cross-class option | Independent of representation shape. | **KEEP unchanged** | Preserve public behavior. |
| Self-exclusion, source-Version selection, latest accepted target Version, same embedding-space checks | Independent of monolithic vector. | **KEEP unchanged** | Preserve. |
| Public result shape / deterministic final ordering | Consumer contract remains Object-level. | **KEEP unchanged** | Preserve unless later algorithm design requires an additive explanation field; no breaking change in R2-01. |

## 12. Impact inventory — CLI, MCP, and public API

| Surface | Dependency / impact | Classification | Frozen R2 disposition |
|---|---|---|---|
| CLI `search objects` | User-facing Object search operation; does not require caller to name `object_overall`. | **KEEP unchanged** | Preserve command/options/result surface. |
| CLI `similar objects` | User-facing Object Similarity entrypoint. | **KEEP unchanged** | Preserve command/options; internal scoring changes only. |
| CLI derived `sync` / `status` / `rebuild` operations | Generic derived lifecycle operations. | **KEEP unchanged** | Preserve operational API; expected counts/digests update via tests. |
| MCP `search_objects` tool contract | Public Object search operation; old internal kind is not caller input. | **KEEP unchanged** | Preserve tool name/request/response contract. |
| MCP `find_similar_objects` tool contract | Public Object-level operation; old internal kind is not caller input. | **KEEP unchanged** | Preserve tool name/request/response contract while changing internal overall scoring. |
| MCP `get_object`, `get_facet`, `get_reference`, `get_source_attribution` | Canonical read surfaces. | **KEEP unchanged** | No R2 change. |
| `src/sgokb/application_read.py` canonical read operations | Not dependent on `object_overall`. | **KEEP unchanged** | No R2 change. |
| `src/sgokb/domain/search.py` Object search request/filter/result DTO shape | Public search contract remains Object-oriented. | **KEEP unchanged** | Preserve shape; representation-kind value expectations are test/compatibility concerns. |

## 13. Impact inventory — tests and gold

The following test groups are active regression assets and must not silently continue asserting the old representation contract.

| Asset / test group | Dependency / impact | Classification | Frozen R2 disposition |
|---|---|---|---|
| `tests/test_search_representation.py` | Asserts `object_overall` kind, exact monolithic text, count/order, hash. | **UPDATE gold/test** | Replace Object-wide expectations with compact overview expectations; retain deterministic/idempotence and unaffected Facet/Statement assertions. |
| `tests/test_n04p02_search_representation_sync.py` | Derived representation counts/membership derive from old set. | **UPDATE gold/test** | Update expected active kind/membership after R2 implementation. |
| `tests/test_n04p03_embedding_sync.py` | Embedding membership/count/hash expectations depend on representation set. | **UPDATE gold/test** | Validate R2 representation membership and stale-old-row handling. |
| `tests/test_n04p04_vector_index_sync.py` / vector index tests | Point counts/kind metadata derive from old representation membership. | **UPDATE gold/test** | Assert rebuilt overview/Facet/Statement points and absence of active old-overall points. |
| `tests/test_n04p05_derived_cli.py` | Derived counts/digests/status may encode old membership. | **UPDATE gold/test** | Keep CLI shape, update R2-valid expected state. |
| `tests/test_hybrid_search.py` | Exercises materialized reps and semantic aggregation; facet-scope safety is important. | **UPDATE gold/test** | Add overview channel expectations and bounded aggregation; preserve exact/lexical/filter safety tests. |
| `tests/test_object_similarity.py` | Explicit fixtures map many vectors to `object_overall`; overall tests are single-vector. | **UPDATE gold/test** | Replace overall fixtures/expectations with hierarchical scoring; keep facet-only, class, Version, error, and backend-parity semantics. |
| `tests/test_j01_similarity_application.py`, `tests/test_j01_retrieval_mcp_boundary.py`, `tests/test_j02_mcp_read_tools.py` | Public boundary regression may observe similarity/search results. | **UPDATE gold/test** | Keep public schemas; update algorithm-sensitive expected ranking/evidence only where changed. |
| `tests/test_m01_cli.py` | CLI integration may assert search/similarity/derived output. | **UPDATE gold/test** | Preserve commands; update algorithm-sensitive data only. |
| `tests/test_search_quality_gold.py` and search-gold runners | Frozen gold contains representation counts and similarity/search expectations. | **UPDATE gold/test** | Produce/version an R2-valid successor expectation; do not erase historical provenance. |
| `benchmark/search-quality-gold-v1.json` — relevance intent, target Objects/Facets/query set | Semantic evaluation intent remains valuable. | **KEEP unchanged** | Reuse semantic intent as source material. |
| `benchmark/search-quality-gold-v1.json` — `expected_representations.object_overall`, representation counts and algorithm-sensitive similarity expectations | Encodes old active representation contract. | **UPDATE gold/test** | Create/update a versioned R2-compatible gold asset rather than pretending old executions used R2. |

## 14. Impact inventory — N-03 / N-04 / N-05 / N-06 benchmark assets

### 14.1 N-03

| Asset | Classification | Disposition |
|---|---|---|
| `benchmark/n03-real-data-vertical-slice-v1.json` canonical/evaluation Object + Source + Evidence fixture | **KEEP unchanged** | The real-data fixture is canonical input/evaluation evidence, not an `object_overall` derived artifact. It should be reused for R2 validation rather than rewritten. |
| N-03 historical run conclusions/results | **HISTORICAL only** | Preserve any old derived-search observations as historical evidence if referenced; do not retroactively reinterpret them as R2 results. |

### 14.2 N-04

Committed N-04 benchmark families on `main` include `n04-ai-use-cases-*`, `n04-knowledge-access-*`, `n04-v2-*`, `n04-v3-*`, `n04g20-*`, `n04g23*`, `n04g25a-*`, `n04r05-*`, their benchmark tools, and committed `benchmark/results/n04*` evidence.

| Asset family | Classification | Disposition |
|---|---|---|
| Frozen N-04 benchmark inputs/results and N04G*/N04R* generated evidence | **HISTORICAL only** | N-04 acceptance/remediation history must remain reproducible as history. Do not rewrite past gold/results to R2 terminology. |
| N-04 derived-search lifecycle contracts still used by production (`N04P01` etc.) | **CHANGE semantics** | Active architectural portions that specify representation membership must receive a successor revision in later R2 work; lifecycle ownership remains unchanged as stated above. |
| N-04 public-boundary regression tests still run in the current suite | **UPDATE gold/test** | Tests that exercise current search/similarity behavior must be made R2-valid even though Phase N-04 benchmark records remain historical. |

### 14.3 N-05

| Asset | Classification | Disposition |
|---|---|---|
| `benchmark/n05-performance-contract-v1.json` latency/RSS/quality thresholds and pass/fail policy | **KEEP unchanged** | R2 is not allowed to move the performance target to make the blocker disappear. |
| N05 performance fixture assumptions such as representation density/cardinality where tied to old representation set | **UPDATE gold/test** | Later benchmark preparation must make the workload representative of the R2 active representation topology without changing thresholds. |
| `benchmark/n05-performance-evidence-template-v1.json` generic evidence envelope | **KEEP unchanged** | Preserve unless a later task proves a field is old-contract-specific; do not change in R2-01. |
| `benchmark/tools/n05_evaluate_performance.py` | **KEEP unchanged** | Threshold evaluation remains valid if input evidence schema remains valid. |
| `benchmark/tools/n05_performance_workflow.py` | **KEEP unchanged** | Core orchestration is generic; R2-valid derived state must be prepared before use. |
| `benchmark/tools/n05_resource_preflight.py` | **KEEP unchanged** | It generically inspects the active representation set and remains useful after R2. |
| `benchmark/tools/n05_run_performance.py` | **KEEP unchanged** | Do not run formally until R2 prerequisites are complete. |
| `benchmark/tools/n05d01_*` Qdrant/storage diagnostic tools | **HISTORICAL only** | N05D-01 is complete; retain as diagnostic evidence/tooling, not an R2 design requirement. |
| `benchmark/tools/n05d02_harrier_memory_diagnosis.py` and N05D-02 evidence | **HISTORICAL only** | These establish old-contract memory behavior and motivate R2; do not modify them to claim R2 behavior. |
| N05D-03 formal checkpoint/evidence | **HISTORICAL only** | Preserve as the old-contract checkpoint. |
| N05D-04 preflight/OOM/failure evidence and R1 evidence | **HISTORICAL only** | Preserve the blocker evidence that justified R2. |
| Formal N-05 benchmark rerun | **HISTORICAL only** | Existing aborted/blocked attempts remain historical; a new formal run is prohibited until R2 implementation and validation are complete. |

### 14.4 N-06

No committed `benchmark/n06*` or `benchmark/tools/n06*` asset exists on audited `main` at the R2-01 freeze point.

N-06 is therefore a downstream gate, not a current migration target.

| Asset / dependency | Classification | Disposition |
|---|---|---|
| N-06 phase gate dependence on accepted N-05 search/performance state | **KEEP unchanged** | N-06 remains blocked by N-05. |
| Future N-06 benchmark/search acceptance inputs | **UPDATE gold/test** | When introduced/activated, they must consume R2-valid overview/Facet/Statement derived state, never old active `object_overall` state. |

## 15. Migration and rebuild ordering freeze

R2-01 does not implement migration, but it freezes the dependency order so later tasks cannot mix authoritative and stale derived state.

```text
1. preserve canonical Object / Version / Facet / Statement / Evidence state
2. introduce forward representation-kind/schema compatibility
3. retire/migrate old active object_overall representation rows
4. materialize R2 object_overview + Facet + Statement representation membership
5. regenerate embedding memberships/vectors from R2 representations
6. rebuild/prune SQLite/Qdrant vector-index derived points
7. verify derived status/count/hash consistency and absence of active old-overall points
8. run R2-specific correctness/regression tests and versioned search gold
9. only after correctness/resource preflight: resume formal N-05 performance benchmark
```

No step may treat old embeddings or vector points as transferable authoritative values for the new overview.

## 16. Compatibility freeze

The following compatibility rules are fixed for downstream design:

1. `search_objects`, `find_similar_objects`, CLI Object search, and CLI Object Similarity remain public entrypoints.
2. Callers are not required to know or send `object_overview` in ordinary public search/similarity APIs.
3. `object_overall` may be recognized only in a bounded legacy/migration/history context where necessary.
4. Active search output/evidence after migration must not present old `object_overall` as if it were the new semantic unit.
5. The legacy `OBJECT` alias must not become a loophole that silently maps old persisted `object_overall` data into new overview semantics.
6. Historical benchmark/result documents keep their original terminology.
7. If a compatibility shim is required, its removal condition and allowed call sites must be explicit in a later task.

## 17. Test / acceptance freeze

Later R2 work must prove at minimum:

- exactly the intended compact overview membership exists per accepted Version;
- Facet and Statement representation semantics remain intact;
- no active retrieval path requires `object_overall`;
- no active embedding/vector membership references a retired old-overall representation after rebuild;
- facet-scoped search does not leak Object-wide overview evidence;
- Hybrid Search still returns bounded Object-level results;
- overall Object Similarity uses hierarchical multi-vector scoring;
- facet Object Similarity remains same-Facet and no-fallback;
- SQLite and Qdrant paths remain behaviorally aligned;
- public CLI/MCP/API schemas remain compatible;
- search-quality gold is versioned/updated for R2 where old representation assumptions are encoded;
- N-05 thresholds remain unchanged;
- first R2 resource/performance evaluation uses Harrier OSS v1 0.6B without concurrent runtime/model workarounds.

## 18. R1 local uncommitted assets

R2-01 audited GitHub `main` only. The user explicitly warned that uncommitted local R1 diagnostic tools/tests/docs may still exist on the workstation.

Those local contents were **not touched, reset, checked out over, pulled over, or otherwise destroyed during this R2-01 work**.

Their disposition is provisionally:

```text
HISTORICAL only
```

until a future local session first performs `git status` and diff inspection and determines their exact contents. They must not be silently incorporated into the R2 baseline or discarded.

## 19. R2-01 completion decision

R2-01 is complete because the impact boundary is now frozen across:

- active search contracts;
- representation schema and kind naming;
- DB migration requirements;
- representation materialization;
- Derived Search lifecycle;
- embedding/vector rebuild requirements;
- Hybrid Search;
- Object Similarity;
- CLI/MCP/public API;
- tests and search-quality gold;
- N-03/N-04/N-05/N-06 benchmark assets;
- historical R1/N05D diagnostic evidence.

The next task remains **R2-02** and is **Not Started**. R2-02 or later work may use this survey as the frozen impact inventory, but no production change or formal N-05 rerun is authorized by R2-01 itself.
