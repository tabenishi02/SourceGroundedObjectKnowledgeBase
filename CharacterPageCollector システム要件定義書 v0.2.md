# CharacterPageCollector システム要件定義書 v0.2

> **プロトタイプ実装方針**
>
> 本書は、CharacterPageCollectorの最終仕様を完全に固定するものではなく、まず一連の処理を実行可能なプロトタイプを構築するための**最低限の実装要件**を定義する。
>
> 本書に明示されていない詳細仕様、補助機能、内部Schema、例外処理、開発用機能等について、プロトタイプを成立させるために必要であれば実装担当者（Codex）が合理的な判断で追加してよい。
>
> ただし、追加要件は本書の基本原則・責務境界・Raw原本性・出典追跡性と矛盾してはならない。追加した要件や重要な設計判断は、後から見直せるようドキュメントへ記録する。
>
> プロトタイプで採用したSchema、アルゴリズム、モデル、Prompt、検索方式、出力形式等は暫定実装であり、実データによる評価後に変更可能とする。

## 1. システムの目的

### 1.1 大目標

Web上などに存在する作品・キャラクター等に関する情報を収集・整理し、LLMなどのAIが利用しやすい専用ドキュメントを生成する。

本システムの目的は、単純なWebページ保存ではない。

複数の情報源から取得した情報を、

**Source → Raw → 正規化 → Evidence → Fragment → 検索・選択 → AI向けDocument**

という論理的処理によって整理し、AIが作品やキャラクターについて理解・推論するための情報基盤を構築する。

---

# 2. 基本原則

| ID | 要件 |
|---|---|
| BP-01 | 調査対象となるWebページ等の採用判断はユーザーが行う。 |
| BP-02 | 情報源を自動発見して無条件に収集することを主要機能とはしない。 |
| BP-03 | ユーザーが内容を確認した情報源を明示的にシステムへ登録する。 |
| BP-04 | 情報源選定後の取得・解析・整理・検索・生成は可能な限り自動化する。 |
| BP-05 | 原資料と加工後情報を明確に区別する。 |
| BP-06 | Rawから最終成果物まで出典を追跡可能にする。 |
| BP-07 | AIによる処理と、決定的アルゴリズムによる処理を分離する。 |
| BP-08 | HTMLの不要部分除去には原則としてAIを使用しない。 |
| BP-09 | 一般的な処理には既存ライブラリを優先し、独自実装を必要最小限とする。 |
| BP-10 | 論理的情報構造を物理的ファイル・フォルダ構造へ依存させない。 |
| BP-11 | 中間成果物が必ず独立したファイルである必要はない。 |
| BP-12 | 最終成果物や検索Index等は再生成可能な派生成果物として扱える構造を目指す。 |
| BP-13 | 特定のLLM、Embeddingモデル、Vector DB、GUI実装等へCoreを強く依存させない。 |
| BP-14 | 将来、HTML以外の画像・動画・PDF等をSourceとして追加できる構造を目指す。 |

---

# 3. 情報源の選定

## 3.1 ユーザー主導

情報源を採用するかどうかの判断はユーザーが行う。

例えばWebページの場合、

1. ユーザーが通常のWebブラウザでページを閲覧する。
2. 内容を確認する。
3. 必要であれば折りたたみ部分、返信、追加表示等をユーザー自身が操作する。
4. 「資料として採用する」と判断した時点のページ状態をCPCへ登録する。

ことを基本フローとする。

これにより、

- 情報の品質判断をユーザー自身が行える
- JavaScript依存ページへ対応できる
- ログイン済みページの表示結果を利用できる
- Bot対策による自動取得失敗を回避しやすい
- ユーザーが実際に確認した範囲を資料化できる

という利点を得る。

---

# 4. Webページ取得方式

## 4.1 Browser Capture

Webページ取得の標準方式は、サーバー側からURLへ再アクセスする方式ではなく、

**ユーザーがWebブラウザ上で表示している現在のDOMを取得する方式**

とする。

取得対象は、HTTPレスポンスとして最初に返されたHTMLそのものではなく、

**ユーザー操作およびJavaScript実行後にブラウザ上へ構築されたDOM Snapshot**

を基本とする。

---

## 4.2 Captureフロントエンド

Webページ取得には、リポジトリ内の `extensions/web-page-capture/` で管理する自作Chrome Extensionを使用する。

Capture側の詳細仕様は同ディレクトリ内の設計書を正本とする。

現在の基本フロー：

```text
Chromeでページ閲覧
        ↓
ユーザーが内容確認
        ↓
右クリックからWeb Page Captureを実行
        ↓
現在DOM・URL・タイトル・metadata等を取得
        ↓
Web Capture Bundle
*.webcapture.zip
        ↓
extensions/web-page-capture/local-captures/
        ↓
CharacterPageCollectorが後からImport
```

Capture ExtensionとCharacterPageCollector本体は分離する。

Chrome ExtensionはWebページ情報の取得とRaw Capture保存を担当し、本文抽出、Source分類、Entity判定、Evidence / Fragment生成等は行わない。

CharacterPageCollector本体は、保存済みWeb Capture Bundleを入力として後段処理を行う。

Chrome Extensionは、ユーザーが明示的に操作したページを対象として取得することを基本とする。

---

## 4.3 Userscript

簡易導入または補助取得手段として、Userscriptも使用可能とする。

候補：

- Violentmonkey
- Tampermonkey
- Greasemonkey

CPC自体は特定のUserscript Managerへの依存を必須としない。

OSSとしての正式取得フロントエンドは自作Chrome Extensionを第一候補とする。

---

## 4.4 Browser Captureの制約

DOM Snapshotは「画面上で実際に見えている文字列のみ」を意味しない。

例えば以下もDOM内に存在すれば取得され得る。

- `display:none` の要素
- 非表示の補助要素
- ページ内部metadata
- JSON-LD
- 未表示だがDOMへロード済みの情報

一方で以下は通常のDOM serializationだけでは完全保存できない場合がある。

- Canvas描画内容
- closed Shadow DOM
- JavaScriptランタイム内部にのみ存在する状態
- ブラウザ内部情報

これらはBrowser Captureの既知制約として扱う。

---

# 5. 対象情報源

## 5.1 百科事典系

- Wikipedia
- Pixiv百科事典
- ニコニコ大百科
- アニヲタWiki

---

## 5.2 掲示板系

- 5ch
- ふたば☆ちゃんねる
- あにまん掲示板
- その他類似BBS

---

## 5.3 Wiki系

- wikiwiki.jp
- atwiki.jp
- Seesaa Wiki
- PukiWiki
- Miraheze
- その他Wiki

---

## 5.4 ブログ系

- はてなブログ
- Amebaブログ
- FC2ブログ
- 楽天ブログ
- note
- Tumblr
- ライブドアブログ
- 忍者ブログ
- Blogger
- WordPressサイト
- その他個人ブログ

---

## 5.5 版権元・公式情報

作品、キャラクター、企業等の公式Webページを対象とする。

例：

- 作品公式サイト
- アニメ公式サイト
- ゲーム公式サイト
- 出版社公式サイト
- 制作会社公式サイト
- 原作者・版権元による公式ページ

公式情報であることはSource metadataとして表現可能であることが望ましい。

---

## 5.6 Web記事・ニュースメディア

少なくとも以下を想定する。

- GIGAZINE
- 4Gamer.net
- ファミ通.com
- Game*Spark
- IGN Japan
- ORICON NEWS
- WebNewtype
- その他ゲーム・アニメ・漫画・エンターテインメント系Webメディア

記事形式サイトでは本文だけでなく、可能であれば以下も取得する。

- タイトル
- 著者
- 公開日時
- 更新日時
- サイト名

JSON-LD等の構造化metadataが存在する場合は利用可能とする。

---

## 5.7 Twitter / X

Twitter / Xの投稿をSourceとして利用可能とする。

対象単位として、

- 単一投稿
- 投稿とその返信
- 引用投稿
- ユーザーが表示・展開した範囲のConversation

を想定する。

CPCが自動的にConversation全体を最後まで収集することは基本要件としない。

ユーザーがブラウザ上で資料として必要な範囲を表示した後、その時点でDOMへロードされている情報を取得する。

可能であれば以下の構造を保持する。

- 投稿本文
- 投稿者
- handle
- 投稿日時
- Reply関係
- Quote関係
- 投稿URL
- Mediaとの関連

画像そのものをRawとして保存するかどうかは今後決定する。

ただし可能であれば、

- Media URL
- alt text
- 投稿との関連

等は保持できる構造とする。

---

## 5.8 その他一般Webページ

既知サイト以外の一般的なWebページも処理可能とする。

未知サイトについてはGeneric Extractorを利用する。

---

# 6. Source分類

Sourceの論理的な種類と、具体的なWebサイトを分離する。

例：

```text
source_type = news_article
site = famitsu

source_type = encyclopedia
site = wikipedia

source_type = social_post
site = x
```

想定するSource Type：

- encyclopedia
- wiki
- bbs
- blog
- official
- news_article
- social_post
- generic_web
- 将来追加されるSource Type

新しいサイト追加のたびにデータモデル変更を必要としない構造を目指す。

---

# 7. Source / Snapshot / Raw

## 7.1 Source

ユーザーが資料として採用した情報源をSourceとして扱う。

Sourceは「情報源の論理的存在」を表す。

例：

```text
https://example.com/article/123
```

---

## 7.2 Snapshot

同じSourceでも時間経過によって内容が変化する可能性がある。

そのため、

**Source**

と

**特定時点で取得された内容**

を区別する。

後者をSnapshotと呼ぶ。

---

## 7.3 Raw Snapshot

Browser Captureによって取得されたWeb Capture Bundleを、WebページSourceに対するRaw原資料として扱う。

Bundle内のRendered DOMはRaw Snapshotの中心情報であるが、将来の再解析に利用できるmetadata、MHTML、Frame情報、Structured Data等もRaw Captureの一部として保持する。

Rawには少なくとも以下を関連付ける。

- Source
- Snapshot
- capture_id
- URL
- page title
- captured_at
- capture method
- site
- Source Type
- Raw DOM
- 元Web Capture Bundleまたはその保存位置

Web Capture Bundle自体はImport後も原則として直接書き換えない。

可能であれば追加metadataも保持する。

---

## 7.4 Rawの原本性

Raw Snapshotは取得後に直接書き換えない。

加工処理はRawとは別の成果物として生成する。

目的：

- 将来の再解析
- Extractor変更への対応
- AI処理変更への対応
- バグ修正後の再処理
- 出典検証

---

## 7.5 WebCaptureImporter

CharacterPageCollectorは、`extensions/web-page-capture/local-captures/` 等に保存された `*.webcapture.zip` を取り込むImporterを持つ。

プロトタイプでは最低限、以下を実現する。

```text
*.webcapture.zip
        ↓
WebCaptureImporter
        ↓
Bundle / manifest検証
        ↓
capture_idによる重複Import確認
        ↓
URLを基準にSourceを特定または作成
        ↓
Snapshot登録
        ↓
Raw Bundleとの参照を保持
        ↓
後段処理対象として登録
```

最低要件：

- `manifest.json` および必要なArtifactを読み取れる。
- `capture_id` を一意なCapture識別子として扱い、同じBundleの二重Importを防止する。
- 同一URLに複数Captureが存在する場合、1つのSourceに対する複数Snapshotとして保持可能とする。
- 元のWeb Capture BundleをImport処理によって変更しない。
- Import成功・失敗を識別できる。
- 失敗したImportによって既存正常データを破壊しない。
- Import後もSnapshotから元Bundleへ追跡可能とする。

具体的なDB SchemaやArtifact参照方式はプロトタイプ実装で決定してよい。

---

# 8. HTML解析

## 8.1 Extractor方式

HTML処理には既存システムで採用しているExtractor方式を引き継ぐ。

概念：

```text
Raw Snapshot
      ↓
Site / Source Type判定
      ↓
Extractor選択
      ↓
正規化された本文・構造
```

---

## 8.2 Site-specific Extractor

既知サイトについては専用Extractorを利用可能とする。

例：

- WikipediaExtractor
- PixivExtractor
- NiconicoExtractor
- AniotaExtractor
- XExtractor
- BBSExtractor
- その他

---

## 8.3 Generic Extractor

専用Extractorが存在しないWebページについてはGeneric Extractorを利用する。

Generic抽出には既存の本文抽出ライブラリを優先する。

技術候補：

- Trafilatura
- Mozilla Readability
- Beautiful Soup
- lxml

独自本文抽出アルゴリズムの実装は必要最小限とする。

---

# 9. 不要情報除去

Raw DOMからAI処理に不要な情報を除去する。

原則としてAIは使用しない。

代表的な削除対象：

- 広告
- サイト共通ナビゲーション
- サイドバー
- フッター
- SNS共有UI
- 関係のない関連記事
- JavaScript
- CSS
- Tracking要素
- 操作用UI
- 本文と無関係なリンク一覧

---

# 10. 保持すべき文書構造

単純なプレーンテキスト化は避ける。

可能な限り以下を保持する。

- 見出し
- 段落
- 箇条書き
- 番号付きリスト
- 表
- 引用
- セクション構造
- 投稿境界
- Reply関係
- 必要なリンク
- 記事metadata

BBSやSNSでは特に、投稿境界や投稿間関係を失わないようにする。

---

# 11. 正規化データ

Rawから不要部分を除去し、意味構造を整理した結果を正規化データとする。

従来の「整形ファイル」に相当する。

ただし、正規化データを必ず独立ファイルとして永続化することは要求しない。

保存方法は、

- DB
- Artifact
- Cache
- File

等から設計段階で決定する。

---

# 12. Evidence

正規化されたSource内の情報を、検索・AI処理へ利用可能な単位に分割する。

これをEvidenceまたはEvidence Chunkと呼ぶ。

Evidenceは元Sourceとの対応関係を失わない。

少なくとも、

- Source
- Snapshot
- 元文書内位置またはSection
- Content

を追跡可能とする。

---

# 13. Fragment

EvidenceからAIを使用して抽出・整理された意味的な断片情報をFragmentとする。

Fragmentは単なるMarkdown文書ではなく、

**検索・分類・統合・再生成可能な情報単位**

として扱う。

詳細なFragment Schemaは今後の要件議論で決定する。

最低限検討する項目：

- Subject
- Category
- Content
- Evidence
- Source
- Extraction metadata
- 関連Entity
- 時系列情報
- 情報間関係

---

# 14. 出典追跡

Fragmentから元資料まで追跡可能とする。

理想的な追跡経路：

```text
Fragment
   ↓
Evidence
   ↓
Normalized Data
   ↓
Raw Snapshot
   ↓
Source
```

これにより、

- AI抽出内容の確認
- 誤情報の検証
- Source更新時の再処理
- AI hallucination検出
- Source間比較

を可能にする。

---

# 15. 重複・矛盾

異なるSourceが同じ情報を記述する場合がある。

また、Source間で内容が矛盾する場合がある。

抽出段階で一方を不可逆に破棄しない。

原則として出典付き情報を保持し、

- 重複
- 一致
- 相違
- 矛盾

を後段処理で判断可能とする。

---

# 16. Entity

少なくとも以下のEntityを扱う。

## 16.1 Work

作品。

例：

- 漫画
- アニメ
- ゲーム
- 小説
- 映画

シリーズ、派生作品等の関係を持ち得る。

---

## 16.2 Character

キャラクター。

1つまたは複数のWorkと関連可能とする。

---

# 17. 属性

WorkおよびCharacterについて、分類・検索・出力に利用できる属性を扱う。

## Work例

- ジャンル
- 作者
- 掲載誌
- 出版社
- 発表年代
- 放送年代
- メディア種別

## Character例

- 性格
- 出自
- 所属
- 社会的立場
- 人間関係
- 能力
- 外見
- 作中での活躍
- 経歴

これらをすべて固定DB columnにすることは要件としない。

属性モデル自体は今後設計する。

---

# 18. 検索の目的

本システムでは、情報を保存するだけでなく、

**人間による単純なKeyword検索では発見しにくい情報をAIへ提供すること**

を重要目的とする。

そのためSemantic Searchは補助機能ではなく中核要件とする。

---

# 19. Keyword / Full-text Search

固有名詞や正確な表現の検索には全文検索を使用する。

例：

- 「斬月」
- 「尸魂界」
- Character名
- 固有能力名

第一候補としてSQLite FTS5等を想定する。

---

# 20. Semantic Search

意味的に近い情報を検索可能とする。

例：

```text
「社会的立場と個人的信念の間で苦悩しているキャラクター」
```

というQueryから、

```text
王族という立場を嫌っている
家業を継ぐことに葛藤している
組織への忠誠と個人的信念の間で悩んでいる
```

など、Queryと同じ単語を含まない情報も検索可能とする。

Semantic SearchにはEmbeddingを利用する。

---

# 21. Hybrid Search

Semantic Searchのみへ依存しない。

基本検索方式として、

```text
Query
 │
 ├─ Full-text / lexical search
 │
 ├─ Vector Semantic Search
 │
 └─ Metadata filtering
        ↓
Candidate Merge
        ↓
Reranking
        ↓
Relevant Evidence / Fragment
```

というHybrid Searchを目標とする。

---

# 22. Reranking

初期検索で得られた候補を、より高精度なモデルによって再評価可能とする。

概念：

```text
検索結果 Top 50
       ↓
Reranker
       ↓
Top 10
```

Rerankingの具体的技術・モデルは交換可能とする。

---

# 23. Embedding対象

少なくとも以下の2種類をEmbedding対象候補とする。

## 23.1 Evidence Chunk

元Sourceから得られた情報。

利点：

AIによるFragment抽出時に見逃された情報でも検索可能。

---

## 23.2 Fragment

AIによって意味的に整理された情報。

利点：

より抽象的・意味的な検索に向く。

---

原則候補：

```text
Raw
 ↓
Normalized Data
 ↓
Evidence Chunk ───→ Embedding
 ↓
AI Extraction
 ↓
Fragment ─────────→ Embedding
```

EvidenceとFragment双方をSemantic Search対象とすることを有力方針とする。

---

# 24. Embedding管理

Embeddingは生成したモデルに依存する。

そのためEmbeddingには少なくとも以下を関連付ける。

- model name
- model revision/version
- vector dimension
- created_at
- source data version
- 対象データ種別

モデル変更時にはEmbeddingを再生成可能とする。

異なるモデルで生成したEmbeddingを無条件に同一Vector空間として扱わない。

---

# 25. Vector Search Backend

Vector Search実装を特定ライブラリへ強く依存させない。

概念的な抽象層を設けることを推奨する。

例：

```text
VectorIndex
 ├─ SQLite Vector Backend
 └─ External Vector DB Backend
```

初期実装ではSQLiteと共存可能な方式を優先する。

将来的な大規模化に伴い外部Vector DBへ交換可能な構造を目指す。

---

# 26. RAG

検索されたEvidence / FragmentをLLMへ提供し、最終成果物を生成する。

概念：

```text
User Request
      ↓
Hybrid Search
      ↓
Reranking
      ↓
Evidence / Fragment Selection
      ↓
LLM
      ↓
AI専用Document
```

これを本システムにおけるRAGの基本構成とする。

---

# 27. 最終成果物

EvidenceおよびFragmentを利用して、AI向けの最終ドキュメントを生成する。

出力内容はユーザーが指定可能とする。

---

# 28. 出力対象

## Entity単位

例：

- BLEACHについて
- 黒崎一護について

---

## 属性単位

例：

- 黒崎一護の性格
- 黒崎一護の能力
- 黒崎一護の人間関係
- BLEACHの世界観

---

## 複数Entity

例：

- Character AとCharacter B
- Work AとWork B

---

## 条件集合

将来的には、

- 特定ジャンル
- 特定作者
- 特定年代
- 特定属性
- 特定の意味条件

等によって複数Entityを選択して出力可能とする。

Semantic Search結果をEntity選択へ利用することも想定する。

---

# 29. AI処理の追跡

AIによって生成されたデータは、生成条件を追跡可能にする。

少なくとも以下を検討する。

- model
- model version
- Prompt
- Prompt version
- executed_at
- input
- output
- task type

Promptまたはモデル変更後に再生成可能とする。

---

# 30. AI Provider依存回避

特定のクラウドLLMまたはローカルLLMだけに固定しない。

例えば、

```text
LLM Abstraction
 ├─ Cloud LLM
 ├─ Local LLM
 └─ OpenAI-compatible API
```

のような交換可能な構造を目標とする。

---

# 31. Database

構造化データの永続化にはRDBを利用する方向を第一候補とする。

初期実装ではSQLiteを有力候補とする。

想定されるデータ：

- Source
- Snapshot
- Entity
- Evidence
- Fragment
- Attribute
- Generation
- Embedding
- Artifact
- Processing metadata

---

# 32. DBアクセス

PythonコードからDBを直接SQL文字列だけで操作するのではなく、DBアクセス層を設ける。

SQLAlchemy等のORM / SQL Toolkitを有力候補とする。

ただしDomain LogicをSQLAlchemyへ直接依存させすぎないことを推奨する。

---

# 33. DB Migration

システム更新時に既存DBを削除せずSchemaを更新できることを要求する。

DB Schema Versionを管理し、

```text
Schema v1
   ↓
Migration
Schema v2
```

という更新を可能にする。

Alembic等を有力候補とする。

---

# 34. GUIとCoreの分離

GUI実装がCore Logicを支配しない構造とする。

概念：

```text
GUI / CLI / API
       ↓
Application Layer
       ↓
Domain / Processing
       ↓
Persistence
```

これにより、

- Desktop GUI
- Web UI
- CLI
- 外部自動化

等から同じCoreを利用可能とする。

---

# 35. CLI

保守・再処理用途としてCLIを提供できる構造を推奨する。

想定用途：

- Source再処理
- Extraction再実行
- Embedding再生成
- Document再生成
- DB診断
- Migration
- Batch処理

---

# 36. 再生成

以下の変更時に必要範囲だけ再生成可能とすることを目標とする。

- Raw Snapshot追加
- Snapshot更新
- Source削除
- Extractor変更
- Normalization処理変更
- Fragment extraction Prompt変更
- LLM変更
- Embedding model変更
- Reranker変更
- Final generation Prompt変更
- Entity情報変更

成果物間の依存関係を追跡可能にする。

---

# 37. エラー時の保護

途中処理失敗によって、既存正常データを破壊しない。

少なくとも、

- Raw
- Evidence
- Fragment
- Embedding
- 最終成果物

について、失敗した新処理と既存正常成果物を区別可能とする。

具体的なTransaction方式は設計段階で決定する。

---

# 38. Regression Test

Extractor変更による情報欠落を検出するため、実際のRaw HTML / DOM Snapshotを利用したFixture Testを重視する。

例えば：

```text
tests/fixtures/
 ├─ wikipedia/
 ├─ pixiv/
 ├─ nicopedia/
 ├─ aniota/
 ├─ bbs/
 ├─ x/
 ├─ news/
 └─ generic/
```

などを想定する。

検出対象：

- 本文欠落
- Section欠落
- Table破壊
- 投稿境界破壊
- Reply関係破壊
- metadata欠落

---

# 39. 開発品質

Pythonコードについて、自動的なLint / Format / Testを導入することを推奨する。

候補：

- Ruff
- pytest
- Type checker

Ruffはシステム実行機能ではなく開発品質管理ツールとして扱う。

---

# 40. OSS方針

将来的に本システムをMIT Licenseで公開可能な構成を優先する。

依存技術については、

- MIT
- BSD
- Apache-2.0
- Public Domain

等のPermissive Licenseを優先する。

GPL / AGPL等、CPC本体のライセンスや配布方法へ強い制約を与える依存は可能な限り避ける。

LGPL依存については採用可能だが、配布条件を確認して利用する。

---

# 41. 現段階で有力な技術候補

この項目は「要件」ではなく、現在の要件を実現するための設計候補である。

| 領域 | 有力候補 |
|---|---|
| Browser Capture | 自作Chrome Extension |
| Userscript | Violentmonkey / Tampermonkey互換 |
| DOM解析 | Beautiful Soup / lxml |
| Generic本文抽出 | Trafilatura |
| Article抽出補助 | Mozilla Readability |
| Data validation | Pydantic |
| Database | SQLite |
| DB access | SQLAlchemy |
| Migration | Alembic |
| Full-text search | SQLite FTS5 |
| Embedding framework | SentenceTransformers |
| Embedding model | multilingual modelを比較選定 |
| Vector index | sqlite-vec等 |
| Large-scale Vector DB | Qdrant等 |
| Reranker | multilingual rerankerを比較選定 |
| LLM abstraction | Pydantic AI等 |
| CLI | Typer等 |
| Test | pytest |
| Lint / Format | Ruff |

特定ライブラリの採用そのものを、この段階ですべて確定とはしない。

---

# 42. 将来：画像

画像をSourceとして扱えるよう拡張可能とする。

想定：

```text
Image
 ↓
Vision AI
 ↓
Evidence
 ↓
Fragment
```

対象例：

- Character画像
- 設定資料
- 相関図
- 漫画ページ
- Screenshot

画像ファイルそのものを恒久保存するかは今後決定する。

---

# 43. 将来：動画

動画についてもSource化を検討する。

利用可能な情報：

- 映像
- 音声
- 字幕
- 説明文
- コメント

想定：

```text
Video
 ├─ Frame
 ├─ Subtitle
 ├─ Audio transcription
 └─ Metadata
       ↓
    Evidence
       ↓
    Fragment
```

動画ファイルそのものを恒久保存するかは未確定。

---

# 44. 将来的なSource統一モデル

将来的には入力形式が異なっても、

```text
HTML ─────┐
Social ───┤
Image ────┤
Video ────┼→ Evidence → Fragment → Search → Document
PDF ──────┤
Text ─────┘
```

という共通処理モデルへ収束できる構造を目指す。

---

# 45. 現段階では確定しない事項

以下は後続設計または要件議論で決定する。

ただし、これらが未確定であることを理由にプロトタイプ実装を停止する必要はない。

プロトタイプを成立させるために具体値や暫定Schemaが必要な場合、実装担当者は本書の基本原則に反しない範囲で暫定仕様を決定してよい。暫定仕様は最終仕様として固定せず、実装理由と変更可能性をドキュメントへ記録する。

- Fragmentの詳細Schema
- Evidence Chunkの分割単位
- Chunk size
- Chunk overlap
- Work / Character以外のEntity
- Attributeモデル
- 重複Fragmentの統合方法
- 矛盾情報の表現
- 信頼度・Source優先度
- Embedding model
- Reranker
- Vector backend
- Final Document形式
- Final DocumentへのCitation形式
- X画像の保存有無
- 画像・動画Raw保存方式
- Artifactの物理保存方式
- GUI Framework

---

# 46. 次に要件定義すべき領域

優先順位は以下とする。

以下は最終設計へ向けて引き続き検討すべき領域であり、プロトタイプ実装の開始条件ではない。プロトタイプでは必要な範囲だけ暫定仕様を採用し、実際の出力・検索品質・運用性を確認した後に正式設計を見直す。

## 1. Fragment

最優先。

検討事項：

- Fragmentとは何か
- 最小単位
- Subject
- Predicate / Category
- Content
- Evidence
- 複数Entityを含む情報
- 時系列
- 重複
- 矛盾
- Fragment間関係

---

## 2. Evidence / Chunk

Semantic Searchの品質へ直接影響する。

検討事項：

- Chunk単位
- Sectionとの関係
- Paragraphとの関係
- Table
- BBS投稿
- X投稿
- Chunk overlap
- Chunk metadata
- EvidenceとFragmentの対応関係

---

## 3. Entity / Attribute

検討事項：

- Work
- Character
- Series
- Person
- Organization
- Author
- Publisher
- 自由Attribute
- 固定Attribute

---

## 4. Search / RAG

検討事項：

- Metadata filtering
- FTSとVector結果統合
- Reranking
- Evidence検索
- Fragment検索
- Query expansion
- 検索結果のLLM投入方法

---

## 5. Final Output

検討事項：

- Entity指定
- Attribute指定
- Semantic条件指定
- 複数Entity
- 出力構造
- Citation
- 情報量
- 再生成条件

---

## 6. 更新・再生成

検討事項：

- Source追加
- Snapshot更新
- Extractor更新
- Fragment Prompt更新
- Embedding model更新
- 旧成果物保持
- Dependency tracking

---

# 47. プロトタイプ実装要件

## 47.1 位置づけ

最初の実装は、各機能を個別に完成させることよりも、

**実際のWeb Captureを入力し、最終Documentを生成するまでの処理を一通り実行できること**

を優先する。

本節に記載する内容はプロトタイプとしての最低限の実装範囲である。

本書に明示されていない追加要件についても、Vertical Sliceを成立させるために必要であればCodexが追加してよい。

追加時は以下を守る。

1. 既存の基本原則と矛盾しない。
2. Raw情報を不可逆に失わない。
3. Sourceから最終成果物までの追跡性を損なわない。
4. 特定のLLM、Vector Backend、GUI等へCoreを不必要に固定しない。
5. 大きな設計変更ではなく実装上の補完であることを優先する。
6. 追加した要件・Schema・重要な判断をドキュメントへ記録する。
7. 暫定実装であるものは、その旨を明記する。

既存要件そのものを変更する必要が生じた場合は、実装内で暗黙に変更せず、変更点を明示する。

---

## 47.2 Prototype Vertical Slice

最低限、以下の処理を1本の流れとして実行可能にする。

```text
Web Capture Bundle
*.webcapture.zip
        ↓
WebCaptureImporter
        ↓
Source / Snapshot / Raw
        ↓
Site / Source Type判定
        ↓
Extractor
        ↓
Normalized Data
        ↓
Evidence
        ↓
Fragment
        ↓
Database
        ↓
Full-text Search
        +
Semantic Search
        +
Metadata filtering
        ↓
Candidate Merge
        ↓
簡易Reranking
        ↓
Evidence / Fragment Selection
        ↓
LLM
        ↓
Final Document
```

最初のプロトタイプでは大量データ・多数サイト・多数Entityへの対応を完成条件としない。

少数の実Captureと少数のEntityを用いて、この一連の処理が成立することを優先する。

---

## 47.3 Evidenceの暫定実装

Evidenceの最終Chunk設計は未確定である。

プロトタイプでは、文書構造を失わないことを優先し、以下を基本単位候補として実装してよい。

- Section
- Paragraph
- List
- Table
- BBS / SNS等の投稿単位

長すぎる単位は必要に応じて分割する。

プロトタイプEvidenceには最低限、以下を追跡可能とする。

- Evidence ID
- Source
- Snapshot
- 元文書内位置またはSection
- Content
- Evidence生成に必要なmetadata

Chunk size、overlap、Table分割等は暫定仕様として実装してよい。

---

## 47.4 Fragmentの暫定実装

Fragmentの最終Schemaは未確定である。

プロトタイプでは少なくとも以下を保持可能な暫定Schemaを採用する。

- Fragment ID
- Subjectまたは関連Entity
- Category / Facet等の分類
- Content
- 根拠となるEvidence参照
- Extraction metadata
- created_at等の生成管理情報

必要であれば、関連Entity、時系列、関係情報等を追加してよい。

Fragment Schemaはプロトタイプ出力を評価した後に変更可能とする。

---

## 47.5 Entity / Attributeの暫定実装

プロトタイプでは少なくともWorkとCharacterを扱う。

内部的に拡張可能なEntityモデルを採用し、実装上必要であれば、

- Concept
- Person
- Organization
- Place
- Series
- その他

等のEntity Typeを暫定追加してよい。

ただし、これらの追加を最終Entity分類の確定とはみなさない。

性格、能力、外見、人間関係等のAttribute / Facetについても、初期段階では固定DB columnへ過度に展開せず、変更可能な形式を優先する。

---

## 47.6 Search / Embedding / Rerankingの暫定実装

プロトタイプでは以下を一通り動作させる。

- Full-text / lexical search
- Semantic Search
- Metadata filtering
- Candidate Merge
- Reranking

具体的なEmbedding model、Vector Backend、Rerankerは暫定選定でよい。

ただし後から交換可能な境界を設け、使用モデル・version等を記録する。

Rerankingは初期段階では簡易方式でもよく、高精度化はプロトタイプ評価後に行う。

---

## 47.7 AI処理とPrompt

EvidenceからFragmentを生成する処理、および検索結果からFinal Documentを生成する処理について、プロトタイプ用Promptを作成してよい。

Promptはコードへ固定せず、可能な限り外部ファイルまたは交換可能な設定として管理する。

少なくとも以下を追跡可能とする。

- task type
- model
- model version
- Prompt
- Prompt version
- executed_at
- input
- output

Prompt内容はプロトタイプ結果を評価して変更する前提とする。

---

## 47.8 Final Documentの暫定実装

Final Documentの最終形式は未確定である。

プロトタイプではMarkdownを有力な暫定形式とし、少なくとも、

- 指定EntityについてDocumentを生成できる。
- Evidence / Fragmentを検索して材料として使用できる。
- 元Source / Evidenceへ追跡できる情報を保持できる。

ことを満たす。

Citationの厳密な表示形式、Section構成、文章量等はプロトタイプ評価後に見直してよい。

---

## 47.9 プロトタイプで優先しない事項

初回プロトタイプでは、以下の完成度を優先しない。

- 大量データでの性能最適化
- Fragment重複統合の最終アルゴリズム
- 矛盾情報の最終表現
- Source信頼度の最終モデル
- Embedding modelの最適選定
- Rerankerの最適選定
- Vector Backendの最終選定
- 高度なQuery Expansion
- GUI Frameworkの最終選定
- 画像・動画Sourceの本実装
- Final Documentの最終書式
- Work / Character以外のEntity分類の完全確定

これらはVertical Sliceによる実データ評価後に設計する。

---

## 47.10 プロトタイプ完成条件

最低限、以下を満たした時点で初回プロトタイプが成立したとみなす。

1. 実際の `*.webcapture.zip` をImportできる。
2. Source / Snapshot / Rawとして登録できる。
3. Extractorによって本文・構造を正規化できる。
4. Evidenceを生成できる。
5. LLM等を利用してFragmentを生成できる。
6. EntityとFragment / Evidenceを関連付けられる。
7. Full-text Searchを実行できる。
8. Semantic Searchを実行できる。
9. Metadata filteringを実行できる。
10. 検索候補を統合し、簡易Rerankingできる。
11. 検索結果をLLMへ渡し、指定EntityについてFinal Documentを生成できる。
12. Final Documentまたはその生成記録から、使用したFragment / Evidence / Snapshot / Sourceへ追跡できる。
13. 同じRaw Captureから、Extractor・Prompt・Model等の変更後に再処理可能な構造を保つ。
14. プロトタイプ実装で追加した要件・暫定仕様・未解決事項がドキュメント化されている。

初回プロトタイプ完成後、実際のCaptureを利用して出力品質・検索品質・運用性を評価し、Fragment、Evidence、Entity、Search、Final Output等の正式設計を改めて行う。
