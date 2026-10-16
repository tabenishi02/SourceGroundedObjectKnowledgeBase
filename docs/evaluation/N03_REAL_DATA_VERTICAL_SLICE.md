# N-03 Real-data Vertical Slice

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-03 [P0] 実データVertical Sliceを作る`
- Base: N-02 completed commit `52e145bb142b10cb64a9b82118c9d2c949973c43`
- Branch: `phase-n/n03-real-data-vertical-slice`
- Status: **Dataset / execution plan prepared — Reference Workstation execution pending**
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

**N-03はReference Workstation上でのreal Capture / Result / accepted Version作成が完了するまでCompleteとはしない。**
