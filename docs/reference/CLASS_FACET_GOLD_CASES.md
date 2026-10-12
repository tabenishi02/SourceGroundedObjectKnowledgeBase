# Source Grounded Object Knowledge Base — Class / Facet Gold Cases

更新日: 2026-10-12

- Task: `E-02C [P0] Class / Facet境界gold casesを作成する`
- Status: Complete / Facet taxonomy freeze
- Inputs:
  - `docs/design/FACET_TAXONOMY_SURVEY.md`
  - `docs/design/FACET_VOCABULARY_REVIEW.md`
- Machine-readable fixture: `tests/fixtures/class_facet_gold_cases.json`

## 1. 目的

E-02Aで整理した全62 Classの意味境界と、E-02Bで統合した55 Facet vocabularyを具体例へ適用し、Class / Facet / Relation / Attribute / Statement境界が崩れないことを回帰試験可能にする。

本Taskのgold caseを通過したため、**Facet taxonomyは既存18 + 新規37 = 55 Facetでfreezeする。** 物理Registryは`005_facet_taxonomy_freeze.sql`でadditiveに反映し、既存Migration 004は書き換えない。

---

## 2. Gold case判定規則

1. 各初期Classにpositive / negative例を最低1件ずつ持つ。
2. Structural ClassをPrimary Object Classとして使わない。
3. `FictionalEntity`はAdditional-onlyとする。
4. Facet配置はfreeze済み55語彙だけを使う。
5. 独立Objectとの接続はRelation、scalar/identifier/dateはAttributeを優先する。
6. 適切な専用Facetがある情報を`overall`へ逃がさない。
7. ProfileにFacetがない場合、意味の近いFacetや`overall`へsilent fallbackしない。
8. 同一Facet IDのcross-class similarityは意味契約が成立する場合だけ行い、narrow FacetはClass scopeを併用する。

---

## 3. 62 Class gold cases

| Class | Policy | Positive | Negative / boundary | Representative placement |
|---|---|---|---|---|
| `object_class` | structural | Class hierarchyのrootとしてCharacter等のancestorを束ねる | 未知ObjectをPrimary=ObjectClassへ割り当てる | classification → `structural_only` |
| `fictional_entity` | additional_only | 架空OrganizationへAdditional Classとしてfictionalityを付与する | FictionalEntityをPrimary Classとして使う | classification → `additional_only` |
| `agent` | structural | Character / Person / Organization等のstructural ancestorとして使う | 実在人物をPrimary=Agentへ割り当てる | classification → `structural_only` |
| `character` | primary_eligible | 物語上の人格主体である架空主人公 | 実在俳優そのものはPerson | facet → `personality` |
| `person` | primary_eligible | 実在の作者・研究者・歴史人物 | 作品内の架空人物はCharacter | facet → `background` |
| `organization` | primary_eligible | 出版社・学校・法人・架空機関 | 制度性のない一時的な集まりはGroupまたは非Object | facet → `structure` |
| `group` | primary_eligible | 名称と継続Identityを持つバンド・ユニット | 偶然居合わせた人々はGroup Objectにしない | facet → `purpose` |
| `team` | primary_eligible | 共同目標を持つスポーツ/制作チーム | 企業全体はOrganization | facet → `activities` |
| `faction` | primary_eligible | 政治・軍事・思想的な陣営や派閥 | 短期作業班はTeam | facet → `values` |
| `creature` | primary_eligible | 固有名を持つ実在または架空の非人間個体 | 猫という種全体はSpecies | facet → `behavior` |
| `creative_work` | structural | Work / Series等を束ねるstructural ancestor | 小説をPrimary=CreativeWorkへ割り当てる | classification → `structural_only` |
| `work` | primary_eligible | 個別の小説・映画・ゲーム作品 | 複数作品を束ねるまとまりはSeries | facet → `themes` |
| `adaptation` | primary_eligible | 小説を原作とする映画版など独立した翻案作品 | 同一媒体の改訂版はWorkEdition | facet → `changes` |
| `work_edition` | primary_eligible | 改訂版・remake・revised edition | SGOKB Knowledge VersionはWorkEditionではない | facet → `changes` |
| `series` | primary_eligible | 複数Workを継続的まとまりとして束ねるSeries | 単一作品はWork | facet → `scope` |
| `franchise` | primary_eligible | 複数mediaやSeriesを跨ぐIP的まとまり | 一つのTV SeriesだけならSeries | facet → `history` |
| `work_component` | structural | Episode / Chapter / Arc等のstructural ancestor | 実際の第1話をPrimary=WorkComponentへ割り当てる | classification → `structural_only` |
| `episode` | primary_eligible | 固有Identityを持つTV第1話 | 目次上の番号だけで独立Knowledge不要ならObject化しない | facet → `narrative` |
| `chapter` | primary_eligible | 独立して参照する価値のある章 | 単なるページ範囲はChapter Objectにしない | facet → `themes` |
| `volume` | primary_eligible | 漫画第5巻など独立Identityを持つ巻 | 単巻完結書籍を機械的にVolume扱いしない | facet → `scope` |
| `season` | primary_eligible | 公式Season 2など複数Episodeを束ねる単位 | 歴史上の季節や時期はPeriod | facet → `chronology` |
| `arc` | primary_eligible | 安定名称を持つ物語編 | 恣意的に選んだ数話集合はArc Objectにしない | facet → `significance` |
| `place` | primary_eligible | 都市・学校・施設など地理/施設的対象 | Workが学校を舞台にするという説明はsetting Facet | facet → `geography` |
| `world` | primary_eligible | 複数Place/Eventを包含する架空世界・宇宙 | 単一都市はPlace | facet → `rules` |
| `event` | primary_eligible | 特定時点・期間に起きた戦争・大会・事件 | 地震という反復可能な現象typeはPhenomenon | facet → `causes` |
| `artifact` | primary_eligible | 固有Identityを持つ人工物・道具・遺物 | 剣という一般型はArtifactTypeConcept | facet → `design` |
| `product` | primary_eligible | 市場上の製品model | その一個体を個別追跡するならArtifact寄り | facet → `usage` |
| `taxon` | primary_eligible | 属・科などtaxonomy上の分類群 | 固有個体はCreature | facet → `properties` |
| `species` | primary_eligible | Felis catus等の実在species | 作品世界のrace-like集団はFictionalRace | facet → `distribution` |
| `fictional_race` | primary_eligible | 公式設定された架空種族 | 思想で集まった陣営はFaction | facet → `culture` |
| `concept` | primary_eligible | 独立定義・比較価値を持つ抽象概念 | 固有特殊能力はAbility | facet → `definition` |
| `theme` | primary_eligible | 作品横断で扱う成長・自己犠牲等の主題概念 | あるWork内でのテーマ説明はWork.themes | facet → `manifestations` |
| `ideology` | primary_eligible | 体系化された思想・doctrine | Personの単発意見はStatement | facet → `values` |
| `trait` | primary_eligible | 外向性など独立概念として扱う持続的性質 | 今怒っている状態はEmotion/Stateの具体例 | facet → `measurement` |
| `emotion` | primary_eligible | 恐怖・喜び等の感情概念 | Character Aが今恐れていることはCharacter Knowledge | facet → `conditions` |
| `motivation` | primary_eligible | 承認欲求等の動機概念 | Character固有の復讐動機はCharacter.motivation | facet → `effects` |
| `state_concept` | primary_eligible | 孤立・飢餓等を独立Knowledge化する状態概念 | objects.status=active等のRegistry状態 | facet → `conditions` |
| `role_concept` | primary_eligible | 教師・指揮官等の役割概念 | Aが教師である事実そのものはRelation/value | facet → `requirements` |
| `artifact_type_concept` | primary_eligible | 剣・容器等の人工物type概念 | エクスカリバー等の固有物はArtifact | facet → `function` |
| `capability` | structural | Ability / Skillのstructural ancestor | 固有能力をPrimary=Capabilityへ割り当てる | classification → `structural_only` |
| `ability` | primary_eligible | 名称・ルール・制約を持つ特殊能力 | 訓練可能な技能中心ならSkill | facet → `mechanism` |
| `skill` | primary_eligible | 習得・訓練可能な技能・technique | 一回の斬撃実行はAction/Event | facet → `procedure` |
| `process` | primary_eligible | stage/input/outputを持つ過程type | 特定日時の事故はEvent | facet → `mechanism` |
| `action` | primary_eligible | 離散的な行為type | Relation predicate usesを何でもAction Object化しない | facet → `purpose` |
| `activity` | primary_eligible | 継続・反復される活動type | 特定日の公演はEvent | facet → `usage` |
| `temporal_entity` | structural | Period / Timeline等のstructural temporal ancestor | 任意date rangeをPrimary=TemporalEntityにしない | classification → `structural_only` |
| `period` | primary_eligible | 名称・Identityを持つ期間 | 無名の2020-01-01〜02-01区間はtyped temporal scopeで足りる | facet → `scope` |
| `era` | primary_eligible | 歴史的・作品世界上の意味を持つ時代 | 単なる10年間はEraにしない | facet → `culture` |
| `timeline` | primary_eligible | 公式な時間系列・world-line context | UIで生成した表示年表はderived view | facet → `rules` |
| `continuity` | primary_eligible | canon/reboot/world-lineを区別するcontinuity context | 単なるSeries分類はContinuityではない | facet → `changes` |
| `system` | primary_eligible | 独自ルール・構成要素を持つ体系 | 単純な抽象概念はConcept | facet → `structure` |
| `software` | primary_eligible | 独立名称・機能・Versionを持つsoftware | software提供会社はOrganization | facet → `properties` |
| `service` | primary_eligible | 継続的に提供されるWeb/配信等のservice | 提供会社そのものはOrganization | facet → `usage` |
| `rule_system` | primary_eligible | 複数Objectの挙動を規定するrule-governed system | 単一ルール文はStatement | facet → `rules` |
| `material` | primary_eligible | 材料として独立性質・用途を持つ対象 | その材料から作られた製品はProduct/Artifact | facet → `composition` |
| `substance` | primary_eligible | 化学的・物理的identityを強く持つ物質 | 用途中心の複合材料はMaterial | facet → `properties` |
| `phenomenon` | primary_eligible | 反復して生じる現象type | 特定日時の発生はEvent | facet → `mechanism` |
| `natural_phenomenon` | primary_eligible | 自然界のphenomenon type | 2026年の特定台風はEvent | facet → `safety` |
| `social_phenomenon` | primary_eligible | 社会に反復・広域的に現れるphenomenon type | 政党はOrganization、単発選挙はEvent | facet → `manifestations` |
| `symbolic_system` | structural | Language / WritingSystem等のstructural ancestor | 実言語をPrimary=SymbolicSystemにしない | classification → `structural_only` |
| `language` | primary_eligible | 日本語・人工言語・架空言語 | Latin alphabetはWritingSystem | facet → `vocabulary` |
| `writing_system` | primary_eligible | Latin alphabet・漢字体系等の表記体系 | 日本語という言語全体はLanguage | facet → `symbols` |

---

## 4. Cross-cutting boundary gold cases

| ID | 検証境界 | Rejectする誤り |
|---|---|---|
| `purpose_function_usage` | 製品は映像を表示するために設計され、信号を画素へ変換し、PC接続で利用される | single facet collapse |
| `history_chronology_changes` | シリーズは1990年開始。作中ではA→B→Cの順。新版でBが削除された | history/chronology/changes equivalence |
| `structure_relation_components` | Systemは3 subsystemで構成され、個々のsubsystemは独立Objectである | component list duplicated as facet truth |
| `properties_vs_attribute` | GPUは24 GB VRAMを持ち、高帯域メモリ構成を特徴とする | numeric value only in properties |
| `rules_constraints_conditions` | 能力は夜間のみ使用可能、1回10秒まで、対象接触時に発動する | rules/constraints/conditions collapse |
| `mechanism_procedure_behavior` | 発酵は代謝でCO2を生じ、工程は混合→発酵→焼成、酵母は糖濃度で活動が変化する | mechanism/procedure/behavior collapse |
| `causes_effects_implications` | 資源不足が暴動を引き起こし物流停止を生んだ。この事例は制度脆弱性を示唆する | causal result treated as implication |
| `relation_not_collection_facet` | Organizationのmembers A/B/C | members facet |
| `overall_not_catchall` | Organizationの設立目的がEvidenceで明示される | overall |
| `work_component_inheritance` | Episodeの物語上の重要性 | overall |
| `capability_inheritance` | Abilityの発動原理 | new ability_mechanism facet |
| `temporal_inheritance` | Eraの対象範囲 | date range attribute only |
| `symbolic_inheritance` | Languageの文法規則 | grammar facet |
| `concept_subclass_direct` | Emotionが具体的に表情や行動へ現れる形 | examples only |
| `provenance_reserved` | Artifactが誰から誰へ受け継がれたか | provenance facet |
| `cross_class_shared` | OrganizationとTeamの存在目的を比較する | separate organization_purpose/team_purpose ids |
| `narrow_similarity_scope` | WorkとEpisodeのnarrative similarity | unscoped all-class comparison |
| `missing_profile_no_fallback` | Class profileにfacet Xがない | overall fallback |
| `structural_not_primary` | named Person object | agent, object_class |
| `fictional_additional_only` | 架空Organization | primary fictional_entity |
| `adaptation_edition_version` | 映画翻案・改訂版・Knowledge更新 | three-way conflation |
| `event_phenomenon_process` | 2026年の台風 / 台風という現象 / 台風形成過程 | single event class |
| `artifact_product_type` | 固有の剣 / 市販製品model / 剣という一般型 | single artifact class |
| `taxon_species_race_creature` | 科 / 実在species / 架空race / 固有個体 | species for all |
| `language_writing_system` | 日本語とLatin alphabet | same class |

### 4.1 重点判定

- `purpose / function / usage`は統合しない。存在目的、作用、利用方法を分離する。
- `history / chronology / changes`は過去の変遷、内部順序、差分を分離する。
- `rules / constraints / conditions`、`mechanism / procedure / behavior`、`causes / effects / implications`もそれぞれ別意味として維持する。
- `members / participants / users / components`等のcollectionはRelationを正本とし、Facetを新設しない。
- 数値仕様・日付・identifier等はtyped Attributeへ出す。
- `provenance`はE-03のSource / Evidence Provenance用語として予約し、semantic Facetにはしない。

---

## 5. Taxonomy freeze結果

- Initial Class coverage: **62/62**
- Structural: **7**
- Additional-only: **1**
- Primary-eligible: **54**
- Facet vocabulary: **18 existing + 37 new = 55**
- Class profile rows: **19 existing + 169 new = 188**
- E-02B vocabularyへの修正要求: **0**
- silent fallback許可: **0**

E-02CでE-02Bの55語彙を覆す矛盾は見つからなかった。したがって、この55 FacetをPhase EのFacet taxonomy logical freezeとする。

---

## 6. 後続Taskへの利用契約

- **E-05 / H-01**: ResultのClass / Facet referential validationとprofile適合性に利用する。
- **I-07**: cross-class / facet similarity queryのgold corpusへ再利用する。
- **N-01 / N-02**: taxonomy regressionとmigration/profile整合試験へ利用する。
- Facet追加・rename・profile変更時はfixtureを更新し、既存gold caseのregressionを確認する。

---

## 7. 完了条件

- [x] 初期62 Classすべてにpositive / negative例を作成した。
- [x] 全Classで代表Knowledgeの期待配置を記録した。
- [x] Structural / Additional-only assignment境界をgold化した。
- [x] ancestor inheritance・shared Facet・意味的fallback禁止をcross-cutting case化した。
- [x] 55 Facet vocabulary外のFacet配置がないことを機械確認可能にした。
- [x] E-02B vocabularyを具体例で検証し、変更不要と判断した。
- [x] 後続テストで再利用できるJSON fixtureを作成した。

## 8. 結論

E-02A〜E-02Cにより、Class Registryの広さとFacet vocabularyの統制を分離しつつ、`overall`への過剰集約とClassごとの局所Facet乱立の両方を防ぐ基準が成立した。**Facet taxonomy hardening、E-03 Source / Evidence / Evidence Link / Provenance、E-04 Versioning、E-05 Object Result JSON Schemaまで完了し、Phase Eは完了している。現在の次TaskはF-01で既存Capture / Import / Normalize / Evidenceを新設計へ接続することである。**
