# N-03 Real-data Vertical Slice

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-03 [P0] 実データVertical Sliceを作る`
- Base: N-02 completed commit `52e145bb142b10cb64a9b82118c9d2c949973c43`
- Branch: `phase-n/n03-real-data-vertical-slice`
- Status: **Complete (2026-10-16)**
- Machine-readable manifest: `benchmark/n03-real-data-vertical-slice-v1.json`

## 1. Decision

N-03はproduction canonical DBへ直接投入せず、**評価専用DB**で実施する。

```text
.local/n03/sgokb-n03.sqlite
```

理由:

- N-03はPhase Nの評価資産であり、運用データへ副作用を与える必要がない。
- N-04〜N-06で同一datasetを再利用できるよう、評価時点のObject / Evidence / Versionを固定しやすい。
- Capture、Package、Result、Embedding / Vector評価を繰り返してもproduction Knowledgeを汚染しない。

production DBからのcopyではなくfresh canonical DBから開始する。

## 2. Vertical Slice構成

最低要件の6 Objectを次で固定する。`object_key`はN-03評価manifest内部の安定キーであり、canonical `object_id`そのものではない。実`object_id`はpublic CLIの`object add`で発行された値をmanifestへ記録する。

| Domain | object_key | Name | Source数 |
|---|---|---|---:|
| Character | `saber` | Saber | 2 |
| Character | `ichigo-kurosaki` | Ichigo Kurosaki | 2 |
| Work | `fate-stay-night` | Fate/stay night | 1 |
| Work | `bleach` | BLEACH | 1 |
| Concept | `tsundere` | Tsundere | 1 |
| Concept | `heros-journey` | Hero's Journey | 1 |

合計8 Source Captureを基準とする。

Character 2件を複数Sourceにすることで、最低条件「複数Sourceを持つObjectを含める」を1件だけでなく2件で満たし、Source統合・Evidence重複・official / secondary source差を後続評価に利用できるようにする。

## 3. Source freeze

### Saber

1. Wikipedia
   - `https://en.wikipedia.org/wiki/Saber_(Fate/Stay_Night)`
2. Fate/stay night [Unlimited Blade Works] official character page
   - `https://www.fate-sn.com/ubw/sp/chara/`

Wikipediaは人物設定・登場経緯等の広いsecondary context、公式ページは作品側が提示する短いofficial character profileとして扱う。

### Ichigo Kurosaki

1. Wikipedia
   - `https://en.wikipedia.org/wiki/Ichigo_Kurosaki`
2. BLEACH: Thousand-Year Blood War official character page
   - `https://bleach-anime.com/en/character/?chara=65-Official`

Wikipediaとofficial profileを組み合わせ、同一Objectに対するSource granularity差を残す。

### Fate/stay night

- `https://en.wikipedia.org/wiki/Fate/Stay_Night`

### BLEACH

- `https://en.wikipedia.org/wiki/Bleach_(manga)`

### Tsundere

- `https://en.wikipedia.org/wiki/Tsundere`

### Hero's Journey

- `https://en.wikipedia.org/wiki/Hero%27s_journey`

N-03ではSource authority ranking自体を合否対象にしない。ただし各Sourceのroleをmanifestへ残し、N-04〜N-06でProvenance説明に使用する。

## 4. Artifact layout

Git管理外の実データは次へ置く。

```text
.local/n03/
├─ sgokb-n03.sqlite
├─ captures/
├─ package-build/
├─ export/
├─ incoming/
└─ logs/
```

Git管理対象にするのは、URL・stable Object ID・評価期待値・最終的なID/checksum/result summary等の再現情報だけとする。

Raw Capture本文やDB本体をrepositoryへcommitしない。

## 5. Object registration policy

public CLIのcanonical contractでは`object add`へ任意`object_id`を渡さない。各Objectは通常の`sgokb object add --name ... --primary-class ...`で登録し、発行されたstable Object IDをmanifestの`object_id`へ記録する。

評価dataset側では次の`object_key`で実Object IDとの対応を固定する。

```text
saber
ichigo-kurosaki
fate-stay-night
bleach
tsundere
heros-journey
```

Class:

```text
Saber / Ichigo Kurosaki -> character
Fate/stay night / BLEACH -> work
Tsundere / Hero's Journey -> concept
```

Aliases:

```text
Saber: Artoria Pendragon
Fate/stay night: Fate/Stay Night
BLEACH: Bleach
Hero's Journey: Monomyth
```

AliasはCapture Evidenceで裏付けが確認できたものだけ登録する。Sourceに裏付けがない場合はmanifest期待値から外すか、登録を保留する。

## 6. Capture / Evidence gate

各URLを通常のWeb Capture方式で`.webcapture.zip`として取得し、`sgokb source import` / `source process`を通す。

各Sourceについて最低限次を記録する。

- URL
- capture file name
- capture SHA-256
- Source ID
- Snapshot ID
- Normalization Run ID
- Evidence count
- included Evidence IDs
- effective Snapshot / Run状態

禁止:

- HTMLを手書きしてreal-data Captureの代替にする。
- N-02のsynthetic `make_bundle` fixtureをN-03成果として数える。
- Source本文をPackage外からResultへ混入する。

Character 2 Objectについては2 Sourceとも`confirmed` associationとし、Package selectionで両SourceからEvidenceが入ることを確認する。自動選択で片方が落ちる場合はEvidence内容を確認したうえで明示includeを使用してよい。

## 7. Package / Result / accepted Version

6 Objectすべてで次を完走する。

```text
real Web Capture
→ Source / Evidence
→ Object association
→ Evidence selection
→ Package build / stage / preflight
→ explicit local evaluation export
→ result.json
→ receive / validate / review
→ explicit import
→ accepted current Version
```

N-03のResultは**実Evidenceにgroundedした評価dataset構築用Result**とする。N-04のAI利用ケース出力品質とは分離する。

Result作成時の最低基準:

- Package外情報をEvidenceとして使用しない。
- summaryはPackage Evidenceで支持可能な内容だけにする。
- Facetは無理に埋めず、Evidence不足なら`not_analyzed` / `insufficient_evidence`相当を使う。
- Relation / AttributeはSourceから明確にgroundできる場合だけ入れる。
- unsupported claimをdatasetのground truthへ混ぜない。

Import後、各Objectについて次を記録する。

- Package ID
- manifest SHA-256
- Receipt ID
- accepted Version ID
- Result SHA-256
- summary / populated Facet一覧
- Evidence grounding数
- validation findings

## 8. Human ground-truth notes

N-03ではLLM scoreをground truthにしない。各Objectに短い人間評価メモを作る。

最低項目:

```text
identity_notes
key_grounded_facts
source_disagreement_or_scope_notes
expected_search_queries
expected_relation_semantics
similarity_rationale
known_unsupported_or_out_of_scope_items
```

このメモをN-04〜N-06の評価時に再利用する。

## 9. Search expectations

Machine-readable manifestの`expected_search_queries`を初期gold候補とする。

最低確認:

- exact name / aliasで対象Objectを取得できる。
- Object固有語でlexical searchした際に対象Objectが上位へ出る。
- historical Versionを作らない限りN-03時点ではcurrent accepted Versionだけが通常scopeとなる。

Semantic / Hybridの正式品質判定はN-06へ送る。N-03ではgold候補と説明可能な期待値を固定するだけでよい。

## 10. Expected relation semantics

N-03ではRelation Registryの拡張を目的にしない。

後続評価用に次の意味関係だけを記録する。

```text
Saber -> Fate/stay night
Ichigo Kurosaki -> BLEACH
```

既存Relation Typeで正確に表現でき、Evidence groundingも成立する場合だけResultへRelationとして格納する。

適切なRelation Typeが存在しない場合、N-03完了のために新規Relation Typeを無理に追加しない。`expected_relation_semantics`としてhuman ground truthへ残し、Registry変更が必要なら別課題として記録する。

## 11. Similarity rationale for N-06

### Character pair

`Saber` ↔ `Ichigo Kurosaki`

- 共通: supernatural / combat-oriented fictional character
- 差分: narrative role、setting、power system、personality
- 期待: ある程度の意味類似はあるが、同一franchise級の近さではない

### Work pair

`Fate/stay night` ↔ `BLEACH`

- 共通: Japanese supernatural fantasy、combat、structured supernatural system
- 差分: visual novel vs manga、物語構造、世界観
- 期待: moderate similarity

### Concept pair

`Tsundere` ↔ `Hero's Journey`

- 共通: character / narrative analysisで利用可能
- 差分: character-development archetype vs broad narrative pattern
- 期待: semantic systemが両者を同一概念のように高く寄せないこと

## 12. N-04 reuse

N-03完了後、次のN-04ケースへそのまま使用する。

1. Character Roleplay: SaberまたはIchigo Kurosaki
2. Similar Work comparison: Fate/stay night ↔ BLEACH
3. Concept combination: Tsundere + Hero's Journey

これによりN-04開始時に別datasetを作らず、N-03で固定したProvenanceとground truthを使用できる。

## 13. Local execution verification

Reference Workstationで、少なくとも次を確認する。

```text
fresh evaluation DB integrity PASS
6 Objects registered and generated stable Object IDs recorded
8 real Web Captures imported
6 Objects all have confirmed Source associations
6 Packages built and validated
6 Results imported
6 accepted current Versions
>= 2 Character
>= 2 Work
>= 2 Concept
>= 1 multi-source Object (target: 2)
all accepted Knowledge statements/relations/attributes retain Evidence grounding
lexical identity/search smoke PASS
full pytest regression: 0 failed
```

N-03 execution logは`.local/n03/logs/`へ保存する。

## 14. Completion update

Reference Workstation実行がPASSしたら、本書へ実値を追記する。

最低限の最終表:

| Object | Object ID | Source IDs | Snapshot IDs | Evidence count | Package ID | Result SHA | Version ID | Status |
|---|---|---|---|---:|---|---|---|---|

さらに以下を更新する。

- `benchmark/n03-real-data-vertical-slice-v1.json`
  - statusを`complete`へ変更
  - 各`object_key`の`object_id`へpublic CLIが発行したstable IDを記録
  - Capture / Source / Evidence / Package / Result / Versionの実IDまたはreproducibility metadataを追記
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - N-03をCompleteへ変更
- `docs/planning/PHASE_N_PREPARATION.md`
  - `N-03 Complete / N-04 Next`へ変更

N-03完了後の次Taskは`N-04 [P0] 3つの代表AI利用ケースを受入試験する`。

## 15. Completion decision

現時点ではdataset、Source freeze、DB分離方針、ground truth形式、後続N-04〜N-06へのreuse条件まで確定済み。

**Complete (2026-10-16)**。8 real Capture、6 valid Result / accepted current Version、全ObjectのProvenance、名前/alias lexical smoke、integrityと回帰検証が完了した。内容語検索とSemantic品質を合格扱いしていない。


## 16. Reference Workstation実行結果

実行日: 2026-10-16 JST。Windows 11 / Python 3.10.6、通常venv。設計基準commitは`45dad489e4c2f159c676c19bd22c1ce8937dab14`。既存評価DBがないことを確認し、`.local/n03/sgokb-n03.sqlite`をfresh作成した。production DBは使用していない。

### Capture方式と保存境界

Playwright CLIの専用Chromium 155.0.8059.40セッションで8 URLを実際に開いた。既存拡張の`captureDocument`と`buildBundle`（WebPageCapture 0.1.0）を変更せず実DOMで実行し、Chrome CDPの`Page.captureSnapshot`による実MHTMLもbundleへ保存した。手書きHTML、単純HTTP取得の偽装、synthetic Captureは使っていない。Native Messaging UIの再受入は今回実施していない。

8件すべて指定URLのまま取得でき、Source差替えなし。全bundleはMHTML成功、closed shadow DOMは既存Capture仕様どおりpartialで、警告をmanifestへ保持した。Capture checksumはimporterで検証し、最終時にもbundle SHA-256不変を確認した。Raw / DB / Package / Result / browser snapshot / logsはすべてGit管理外の`.local/n03/`へ隔離した。実Driveへは送信していない。

### Capture / Source一覧

| Source key | URL | Source ID | Snapshot ID | Run ID | Evidence |
|---|---|---|---|---|---:|
| saber-wikipedia | https://en.wikipedia.org/wiki/Saber_(Fate/Stay_Night) | `657cd6ac-4e53-432b-9077-5fcd96be5b8c` | `36a27057-d025-4f26-ba76-0ac798903326` | `35f658fb-7327-4d16-85f9-8816d272cb75` | 82 |
| saber-fate-official | https://www.fate-sn.com/ubw/sp/chara/ | `74b6c333-82e8-4b47-9306-be0b0cf0fb8f` | `05cf2856-d157-48ab-8e6b-036005009a07` | `446b7a53-67a0-48d7-88d5-e77b1356f13b` | 7 |
| ichigo-wikipedia | https://en.wikipedia.org/wiki/Ichigo_Kurosaki | `30e8eb6c-0402-452f-8c67-dbd2217085e4` | `e8684c3e-72e5-4350-bfd7-72178803cad5` | `da0e1640-266f-4357-8d0c-e4d8a1059140` | 56 |
| ichigo-bleach-official | https://bleach-anime.com/en/character/?chara=65-Official | `6a34805d-2781-44a3-af0c-e1be87a0732b` | `1dc8f032-88a5-48ef-83b1-f4fd5a6c69f3` | `abab9428-45d2-45c0-8cc5-bc3d0be9d4ff` | 41 |
| fate-stay-night-wikipedia | https://en.wikipedia.org/wiki/Fate/Stay_Night | `c653fc93-3ccc-4b22-ac67-f2d8a7cfb131` | `e9c7f4d2-3f7e-4940-b698-a934e78947a5` | `1ba6fa64-e57e-49d7-99cd-bf441b375511` | 102 |
| bleach-wikipedia | https://en.wikipedia.org/wiki/Bleach_(manga) | `8ab4641f-2e2f-4dea-b214-3a1aefbfe68d` | `f750721c-8d7b-4fdd-bb1b-1642adbb4f8e` | `298470a1-418f-4353-8e0d-5821ab8150cb` | 88 |
| tsundere-wikipedia | https://en.wikipedia.org/wiki/Tsundere | `380aec7f-e3aa-4650-a8a5-578b036d680f` | `af3e767c-b043-4d30-ae0c-99c1ac4d8fb7` | `d6e29645-e6a3-4cdc-b174-e2d365647f88` | 24 |
| heros-journey-wikipedia | https://en.wikipedia.org/wiki/Hero%27s_journey | `2b1532a8-c5f0-49ca-9b86-54402d7cb544` | `49b02329-e395-4b85-9c5b-cf9a520852a5` | `64e1b7de-eadb-420b-91d4-64bacb296db4` | 115 |

Capture filename / SHA-256 / timestamp / bytes / warningsおよび全515 Evidence IDはmachine-readable manifestに記録した。8 Sourceすべて指定Objectにconfirmed、effective Snapshotはpublic source snapshots、effective Runはpublic candidatesのeffective_snapshot_and_run scopeと処理Run IDの一致で確認した。

### 完成表

| Object | Object ID | Source IDs | Snapshot IDs | Evidence count (Source / Package) | Package ID | Result SHA | Version ID | Status |
|---|---|---|---|---:|---|---|---|---|
| Saber | `326a97cf-47aa-4760-a7f1-07bfe639fcf0` | `657cd6ac-4e53-432b-9077-5fcd96be5b8c`, `74b6c333-82e8-4b47-9306-be0b0cf0fb8f` | `36a27057-d025-4f26-ba76-0ac798903326`, `05cf2856-d157-48ab-8e6b-036005009a07` | 89 / 11 | `pkg_27c3d92e-65d4-417b-ae3e-a13b2ab2e03d` | `32d218c6024b5269a8a0f689d7cdeafd98e93c613b8b8398714d23e190bc206f` | `fb0ab12a-5e11-4df7-983a-925da458a129` | Complete |
| Ichigo Kurosaki | `3aec055e-e9f3-445d-a7a3-adb2b5864c6f` | `30e8eb6c-0402-452f-8c67-dbd2217085e4`, `6a34805d-2781-44a3-af0c-e1be87a0732b` | `e8684c3e-72e5-4350-bfd7-72178803cad5`, `1dc8f032-88a5-48ef-83b1-f4fd5a6c69f3` | 97 / 14 | `pkg_9cf8b4c7-1e49-4047-a9ca-5cfc23cd8d5a` | `087f73029d3d9f6149ba598c194a44f7e738fd9adbad885509e5fe8ff9daa00c` | `50ca186c-80a5-4447-bf71-216bbad8f1d6` | Complete |
| Fate/stay night | `d5824d33-7008-4121-9cfe-1f95a19667fd` | `c653fc93-3ccc-4b22-ac67-f2d8a7cfb131` | `e9c7f4d2-3f7e-4940-b698-a934e78947a5` | 102 / 13 | `pkg_bbf1d990-0eeb-46f7-b7d0-202c2cd47fee` | `80cfaca3b53dc214bec78d39a581fd91ad935cf272f43a8e4f0f1619ab4c2709` | `47f2b146-20a6-4d06-957f-904cc5ef39a9` | Complete |
| BLEACH | `57db855c-574a-4b38-b474-421c165894f1` | `8ab4641f-2e2f-4dea-b214-3a1aefbfe68d` | `f750721c-8d7b-4fdd-bb1b-1642adbb4f8e` | 88 / 12 | `pkg_3987ff91-d281-42d3-9a1a-a3e8528a6536` | `12001ead73b76c10b7c07459ad1ad49f889b48843d63dc821cdabd4fa1307f26` | `6e75aa45-9c13-42ef-87b4-923beac43bef` | Complete |
| Tsundere | `8c83f986-f491-41a8-8645-9f71dd5874b9` | `380aec7f-e3aa-4650-a8a5-578b036d680f` | `af3e767c-b043-4d30-ae0c-99c1ac4d8fb7` | 24 / 12 | `pkg_d942b1b9-a02c-4342-83ef-174a016b968f` | `77445e5deddaa836f041986979aeaa6c2fa6ffa86e5904bef9f7e29c799a24d2` | `98c16da1-a5a6-4d73-b919-bcadcc3df08f` | Complete |
| Hero's Journey | `fee32007-0f92-449a-ba21-4ec2f78d1cd4` | `2b1532a8-c5f0-49ca-9b86-54402d7cb544` | `49b02329-e395-4b85-9c5b-cf9a520852a5` | 115 / 12 | `pkg_06ccc95c-2a1a-4191-ac9d-cf5734ac2541` | `2c5a32b7f965e01f5877226a88018b66f53c3e0f09bb63bfe274bcb87c9d2485` | `31e52190-fdb2-42da-8860-d4e0bbaa4de6` | Complete |

6 Packageのbase Versionはすべてnull、preflightはすべてallow。8 Sourceの515 EvidenceのうちPackageへの掲載は延べ74 Evidence。Saber / Ichigoは、内容を確認したidentity leadとofficial profileをexplicit includeし、両Sourceの有効Evidenceを保持した。他Object向けSourceから自動選択された関連Evidenceも含まれるため、指定confirmed Source数とPackage included Source数は区別してmanifestへ残した。Resultが使うのは個別に確認したEvidenceだけである。

各ResultはPackageのinstructions / manifest / EvidenceだけからCodexが保守的に作成した。各Objectはsummary 1件 + grounded Facet statement 1件。Characterはrole、Work / Conceptはoverallをpopulatedとし、それ以外はnot_analyzed。Attribute / Relation / Registry proposalは0。適切なRelation TypeがPackageになかったため、Registryを変更せず、Saber→Fate/stay nightとIchigo→BLEACHは意味関係メモだけに残した。

6 Resultすべてvalidation=valid、findingsなし、review=ready_to_importで、明示importによりaccepted current Versionとなった。全12 StatementでPackage内Evidence groundingあり、全74 included EvidenceについてSource / Snapshot / Normalization Run / Raw artifactへのProvenanceをpublic CLIで検証した。Receipt ID、manifest SHA、Result SHA、全Version IDはmanifestを参照する。

### 人間評価向け参照メモ

以下とmanifestのground_truth_notesは、Codexが実Evidenceを確認して作成した人間向け参照メモである。独立した人間の品質採点、LLM confidence、N-04 AI出力品質の合格を意味しない。

**Saber**

- Identity / grounded facts: Saber, also identified as Artoria Pendragon, is a fictional character in Type-Moon's Fate/stay night visual novel. In the Unlimited Blade Works official profile, Saber is a sword-wielding Servant contracted to Shirou.
- Scope / disagreement: Wikipedia covers multiple visual-novel routes; official Fate page is the UBW roster. Only the Saber entry in the roster supports the official statement. Do not merge route-specific behavior or other roster members into Saber.
- Query candidates: `Saber`, `Artoria Pendragon`, `King of Knights`.
- Relation semantics: character appears in / belongs to Fate/stay night
- Similarity rationale: Compare with Ichigo Kurosaki as a supernatural combat-oriented fictional character while preserving clear differences in role, setting, and characterization. This is a later evaluation hypothesis, not a measured similarity result.
- Unsupported / scope: 未分析Facet、独立した人間品質評価、semantic qualityは未検証。

**Ichigo Kurosaki**

- Identity / grounded facts: Ichigo Kurosaki is the protagonist of Tite Kubo's Bleach manga and its adaptations. Ichigo becomes a Substitute Soul Reaper after meeting Rukia Kuchiki; the official profile identifies his Zanpakuto as Zangetsu.
- Scope / disagreement: Wikipedia covers manga and adaptations; official roster is TYBW-specific. Use only Ichigo's profile in the multi-character block. Official English text has a ja normalization language tag; explicit statement language is en. No conflict adjudication was performed.
- Query candidates: `Ichigo Kurosaki`, `Substitute Soul Reaper`, `Zangetsu`.
- Relation semantics: character appears in / belongs to BLEACH
- Similarity rationale: Compare with Saber as another supernatural combat-oriented character; expected similarity should arise from role and conflict themes rather than shared franchise identity. This is a later evaluation hypothesis, not a measured similarity result.
- Unsupported / scope: 未分析Facet、独立した人間品質評価、semantic qualityは未検証。

**Fate/stay night**

- Identity / grounded facts: Fate/stay night is a Japanese visual novel developed by Type-Moon. The story follows Shirou Emiya in the Holy Grail War and branches into Fate, Unlimited Blade Works, and Heaven's Feel routes.
- Scope / disagreement: The Work is the original visual novel; versions and anime/manga adaptations are not separate Objects in this slice. Route details remain scoped to this Work.
- Query candidates: `Fate/stay night`, `Holy Grail War`, `visual novel`.
- Relation semantics: No Relation assertion in this slice.
- Similarity rationale: Compare with BLEACH as a Japanese supernatural fantasy work centered on recurring combat, while format, narrative structure, and franchise history remain distinct. This is a later evaluation hypothesis, not a measured similarity result.
- Unsupported / scope: 未分析Facet、独立した人間品質評価、semantic qualityは未検証。

**BLEACH**

- Identity / grounded facts: BLEACH is a Japanese manga series written and illustrated by Tite Kubo. The story follows Ichigo Kurosaki after he gains Soul Reaper powers from Rukia Kuchiki and confronts Hollows.
- Scope / disagreement: The Work is the manga, not the TYBW anime or unrelated chemical bleaching. Adaptations are out of scope for the two accepted statements.
- Query candidates: `BLEACH`, `Soul Reaper`, `Tite Kubo`.
- Relation semantics: No Relation assertion in this slice.
- Similarity rationale: Compare with Fate/stay night as a supernatural Japanese work with combat and spiritual/fantasy systems, but with different medium and narrative structure. This is a later evaluation hypothesis, not a measured similarity result.
- Unsupported / scope: 未分析Facet、独立した人間品質評価、semantic qualityは未検証。

**Tsundere**

- Identity / grounded facts: Tsundere is a Japanese term for a character-development pattern: a character initially marked by a harsh personality gradually reveals a warmer side. The term combines tsun tsun, associated with aloofness, and dere dere, associated with affection.
- Scope / disagreement: This is a descriptive character-development term. No diagnosis, universal personality claim, or automatic classification of Saber/Ichigo is asserted.
- Query candidates: `Tsundere`, `harsh personality warmer side`, `character archetype`.
- Relation semantics: No Relation assertion in this slice.
- Similarity rationale: A character-development/archetype concept intended to remain distinguishable from the broader narrative-structure concept Hero's Journey. This is a later evaluation hypothesis, not a measured similarity result.
- Unsupported / scope: 未分析Facet、独立した人間品質評価、semantic qualityは未検証。

**Hero's Journey**

- Identity / grounded facts: Hero's Journey, also called Monomyth, is a narrative pattern in narratology and comparative mythology. The pattern follows a hero through adventure, a decisive crisis, and a return in a changed state.
- Scope / disagreement: This is a comparative narrative template. It is not asserted to fit every story; Campbell's interpretations and scholarly criticism were not evaluated.
- Query candidates: `Hero's Journey`, `Monomyth`, `narrative pattern`.
- Relation semantics: No Relation assertion in this slice.
- Similarity rationale: A narrative-structure concept intentionally distinct from Tsundere; N-04 can combine both concepts for controlled character creation. This is a later evaluation hypothesis, not a measured similarity result.
- Unsupported / scope: 未分析Facet、独立した人間品質評価、semantic qualityは未検証。


### Lexical smoke / 残課題

public `sgokb --db .local/n03/sgokb-n03.sqlite search <query> --mode lexical`で全20 probeを実行。6 canonical name + 4 Evidence-backed aliasはすべて対象Objectをrank 1で解決し、N-03の最低必須identity smokeはPASSした。

一方、残る内容語10 probe（King of Knights、Substitute Soul Reaper、Zangetsu、Holy Grail War、visual novel、Soul Reaper、Tite Kubo、harsh personality warmer side、character archetype、narrative pattern）は対象を返さなかった。ImportでSearch Representationがpendingになり、現行public system index rebuildはsemantic runtimeを要求する。optional runtimeをN-03の必須条件に追加せず、内部builderのDB変更も行わなかった。したがって内容語検索は未達として明示し、期待queryはN-06用gold候補のままとする。実モデル・ANN品質・Semantic/Hybrid/Similarityは未評価である。

N-04はaccepted KnowledgeをObject IDでreadできる。内容語検索・similar Work retrievalが必要なケースでは、派生Search Representation生成経路とoptional runtime受入が先に必要であり、この制約を無視してAI use-caseを合格扱いしない。

### Verification / completion

- `sgokb --db <evaluation-db> system integrity`: PASS（integrity_check=ok、foreign_key_violations=[]、migration003〜017）。
- public Object list: Character 2 / Work 2 / Concept 2、全6件がaccepted current Versionを持つ。
- `python -m pytest -q`: **307 passed / 3 skipped / 0 failed**、93.07秒。3 skipは既存optional Qdrant runtime条件。skip / xfail追加なし。
- `git diff --check`: PASS。
- production/test Pythonコード変更なし。実行helperとlogはGit管理外のため、共有Python変更へのRuff対象はない。

実行経路は公開CLIのobject add / alias add / source import / source process / association set / evidence candidates/select / package build/stage/preflight/export / result receive/validate/review/import / object show / search / system integrity。任意IDの強制、内部SQLの変更、validatorやschemaの緩和は行っていない。

実行helperのファイル名/importの準備ミスは修正して途中記録から再開したが、production defectやSource差替えはなかった。Package exportの最初の1件は同一Package IDへのidempotent再実行を含み、distinct Package数は6件を維持した。

**N-03 Complete / N-04 Next。** この完了判定は実データdataset構築、identity smoke、ProvenanceとDB integrityの受入であり、内容語retrievalやAI品質の受入ではない。local証跡は`.local/n03/state.json`、`.local/n03/logs/`、各実artifactに保持する。
