# Source Grounded Object Knowledge Base (SGOKB)

Web上のSource / Evidenceを根拠に、Character・Work・ConceptなどのObject Knowledgeを構造化・版管理し、検索・比較・AI利用できるローカルKnowledge Base。

## Status

Phase A〜Lは完了しました。L-05で旧PrototypeのFragment / Final / benchmark / Generative LLM・互換API/CLIを撤去し、canonical Source / Evidence / Object / Version / Search / MCPを維持しています。fresh DBはmigration003〜016のみから構築し、Prototype DBは自動upgradeせず拒否します。

次Taskは`M-01 [P0] 新しいObject中心CLIを設計する`です。Phase Mの実装は未着手です。検証結果と既知のPackage Transfer failure・任意依存制約は[Phase L Closure Audit](docs/planning/PHASE_L_CLOSURE_AUDIT.md)を参照してください。

現在の設計判断・要件・作業状況は **[Documentation Index](docs/README.md)** を入口として確認してください。

## Current documentation

- [SGOKBの目的要件](docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md)
- [World / Object Knowledge Layer要件](docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md)
- [UPDS Personal Inference Layer要件](docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md)
- [Concept Ownership Boundary要件](docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md)
- [SGOKB → UPDS Integration Contract要件](docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md)
- [Object要件](docs/requirements/OBJECT_REQUIREMENTS.md)
- [Object分類モデル](docs/requirements/OBJECT_TYPE_MODEL.md)
- [Object / Class / Facet / Relation境界](docs/requirements/OBJECT_TYPE_BOUNDARIES.md)
- [Source / Evidence要件](docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md)
- [Object Result要件](docs/requirements/OBJECT_RESULT_REQUIREMENTS.md)
- [Search / Retrieval要件](docs/requirements/SEARCH_REQUIREMENTS.md)
- [人間工程 / 自動工程要件](docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md)
- [非機能要件](docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md)
- [Embedding / Vector Search技術調査](docs/reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md)
- [Knowledge Base再設計Decision](docs/decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md)
- [再設計タスク / 現在の進捗](docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md)
- [再設計引継ぎ資料](docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md)
- [Phase D Preparation](docs/planning/PHASE_D_PREPARATION.md)
- [Phase I Closure Audit](docs/planning/PHASE_I_CLOSURE_AUDIT.md)
- [Phase J Preparation](docs/planning/PHASE_J_PREPARATION.md)
- [Standard Pipeline / Legacy Fragment Boundary](docs/design/STANDARD_PIPELINE_BOUNDARY.md)
- [Operator Association / Evidence Selection Controls](docs/design/OPERATOR_ASSOCIATION_CONTROLS.md)
- [既存資産分類](docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md)
- [既存依存関係調査](docs/reference/KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md)

旧Prototypeの要件・設計・評価・モデル比較等は [`docs/archive/prototype-0.2/`](docs/archive/prototype-0.2/) へ分離しました。名称変更の作業履歴は [`docs/archive/rename-2026-10/`](docs/archive/rename-2026-10/) にあります。

## Repository layout

```text
docs/                       # 現行文書の入口 + Archive
src/sgokb/                  # 現在のPython実装（再設計移行中）
extensions/web-page-capture/ # Web Page Capture / Native Host
scripts/                    # 評価・移行・補助script
benchmark/                  # 現行Search quality gold / Vector / Reranker評価資産
sample/                     # Capture sample
```

## Web Page Capture

Web取得部分はKnowledge Base再設計から独立して再利用する資産です。詳細は[Web Page Capture README](extensions/web-page-capture/README.md)を参照してください。

## Development commands

現行コードベースの基本検証:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m sgokb --help
ruff check src tests scripts
ruff format --check src tests scripts
git diff --check
```

旧Prototype固有のFragment / Final Document / モデル評価手順が必要な場合は、現行設計と混同せず[Prototype 0.2 Archive](docs/archive/prototype-0.2/)を参照してください。
