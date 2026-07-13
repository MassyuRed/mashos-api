# Cocolon EmlisAI Natural Language Surface v2 — Step 2 / Step 3 実装結果

作成日: 2026-07-13  
対象設計: `Cocolon_EmlisAI_ModelFreeNaturalLanguageSurfaceV2_DetailedDesign_ImplementationOrder_20260713.md`  
実装範囲: Step 2「70件評価コーパス固定」およびStep 3「Content Planner v2 contract実装」

## 1. 結論

Step 2とStep 3を完了した。

- 14 family × 5件 = 70件を、Development 42／Holdout A 14／Holdout B 14へ分離して固定した。
- 各caseに、family、semantic obligation、forbidden claim、極性、topic分離、反応可能点、depth範囲、safety境界を持たせた。
- 正解文章、正解語尾、正解述語、固定文数、v1文字列一致はfixtureへ置いていない。
- `GroundedObservationPlan`だけを入力とする、frozen dataclassのContent Planner v2 contractを追加した。
- Development 42件すべてで、1〜4個のbody-free Content Unitを決定論的に生成し、全unitを既存Evidence IDへ解決できた。
- Content Planner v2は既存reply runtimeへ接続していない。Step 4以降のCandidate Planner、Surface Generator、Selectorも実装していない。

## 2. 作業前に確認した事実

### 2.1 入力source

- 受領source: `mashos-api_2(148).zip`
- SHA-256: `6edcca5819f1110a26fe2307ac5642e57649d418fa6a9e15a6ee6ba36e9a8845`
- `__pycache__`を除く全体比較で、前回Step 0／1実装済みsourceと差分0件だった。

したがって、Step 0／1で固定したv1 baseline、source owner、public contractを引き継げると確認した。

### 2.2 前後工程

- Step 2は評価材料を実装前に固定する工程であり、正解文章を作る工程ではない。
- Step 3はEmlisが反応する意味材料をSurfaceより前に決める工程である。
- 語順・文構成はStep 4、完成文はStep 5、Hard Gate／SelectorはStep 6、runtime接続はStep 10以降の責任である。
- `/emotion/submit`、`input_feedback.comment_text`、`observation_status`、DB write path、RN二段表示は今回の変更対象外である。

## 3. Step 2 — 70件評価コーパス固定

### 3.1 cohort

| cohort | 1 familyあたり | 件数 | 今回の利用 |
|---|---:|---:|---|
| Development | 3 | 42 | Step 3実装・contract testで使用 |
| Holdout A | 1 | 14 | Step 8まで評価しない |
| Holdout B | 1 | 14 | Step 9まで評価しない |
| 合計 | 5 | 70 | 初期baseline |

Holdout A／Bは別fixtureへ分離し、Development専用loaderおよびStep 3 testから本文fixture名を参照できないようにした。manifest testはHoldout本文をparseせず、ファイルSHAだけを確認する。

### 3.2 family

1. `low_information_short`
2. `limited_grounding`
3. `daily_unpleasant`
4. `daily_positive`
5. `self_denial`
6. `anger_or_boundary`
7. `uncertainty_support`
8. `standard_state_answer`
9. `structure_question`
10. `long_meaning_arc`
11. `relationship_gratitude_recovery`
12. `change_future_intention_transition`
13. `source_unavailable_high_information`
14. `history_line_eligible_input`

### 3.3 app option拘束

感情はRNの `喜び / 悲しみ / 怒り / 不安 / 平穏 / 自己理解`、カテゴリはbackend／RN共通の `生活 / 仕事 / 趣味 / 人間関係 / 恋愛 / 健康 / 学習 / 価値観 / 人生` のみに拘束した。

### 3.4 freeze結果

- 70件すべてで必須fieldが存在する。
- case ID重複: 0
- current input identity重複: 0
- exact8 current input identityとの重複: 0
- 正解Surfaceを持つcase: 0
- 14 familyすべてで、5件のsemantic obligation集合が相互に異なる。
- self-denial 5件すべてが現行Observationの自己否定境界へ到達する。
- `history_line_eligible_input`でも外部history参照は有効化していない。

fixture SHA-256:

| cohort | SHA-256 |
|---|---|
| Development 42 | `9e8e81b553b8f3d5d51e66c434350ebbc2fa134a813250dbb5bc5de251e6aa36` |
| Holdout A 14 | `1e291bc8a57e346b755dcb6de2cb1751a312608eeb823d1988f366ce1d2767bb` |
| Holdout B 14 | `18c05d940da4a1b644afddf140cf74dc04077b0eeb03c1fe48fd3e963161d171` |

body-free corpus identity:

- corpus identity: `852457051bcc9bdc82a74d0d59d833f1f9c32837a85c29812fee8a775d69228e`
- input identity set: `e74fd4408a15a70d824ec1170626728003399d147de3803938cb78d7280fd7cc`
- semantic contract set: `cda423b94f4c6aa19dae1db87a9d45e396c31993800b66abdf4c9bfc2164ef07`

Holdout A／Bはfixtureとして作成・SHA固定済みだが、v2による評価は実行していない。`opened_for_evaluation`は双方falseのままである。

## 4. Step 3 — Content Planner v2 contract

### 4.1 module分離の根拠

新規内部module `emlis_ai_grounded_reception_content_plan_v2.py`へ分離した。

理由:

- 現行Observation ownerへSurface責任を戻さない。
- Step 0／1で固定したv1 ownerの実装とハッシュを変更しない。
- builderの入力を `GroundedObservationPlan` 一つに限定できる。
- case ID、fixture family、raw text cue、expected textを型と関数境界から排除できる。
- Step 4以降の候補生成／runtime接続と独立してtestできる。
- 循環importを作らない。

### 4.2 contract

追加した主なfrozen dataclass:

- `ReceptionContentUnitV2`
- `ReceptionSentenceBudgetV2`
- `ReceptionDiscourseConstraintsV2`
- `ReceptionQuotePolicyV2`
- `ReceptionContentPlanV2`

Content Unitが持つもの:

- `role`
- 汎用構造名である `semantic_signature`
- target／support nucleus ID
- relation ID
- Evidence span ID
- `required`
- `priority`
- allowed stance code
- forbidden claim code

持たないもの:

- case ID
- fixture family
- memo／memo_action
- raw source text
- 完成文
- Surface cue
- expected text
- ユーザー名

### 4.3 unit選択順

実装は次の意味優先を使用する。

1. 入力根拠のある自己否定counterdirection
2. 主たるreception opportunityへのattention
3. 入力全体の方向を変えるrelation／不確実なrelation
4. 別のaction・change・intention opportunityとのconnection
5. depthに余地がある場合のfelt response

単純なnucleus priority降順やraw文字数では選ばない。

### 4.4 depth budget

| depth | Content Unit | sentence budget (min / target / max) |
|---|---:|---:|
| minimal | 1 | 1 / 1 / 2 |
| focused | 2 | 2 / 2 / 3 |
| layered | 3〜4 | 3 / 3 / 4 |

Development 42件の生成結果:

| 項目 | 結果 |
|---|---:|
| 生成成功 | 42 / 42 |
| minimal | 11 |
| focused | 22 |
| layered | 9 |
| 1 unit | 11 |
| 2 units | 22 |
| 3 units | 5 |
| 4 units | 4 |
| 使用role | 5種すべて |
| semantic signature | 18種 |
| unresolved Evidence | 0 |

body-free Development plan receipt hash:

`1137bfa064681ae9093e7540d938a19791378c0e3061494ee3a469b6191474a1`

### 4.5 自己否定境界

自己否定というだけで肯定的counterpositionを捏造しない。

- Observation opportunityに `counterdirection` がある場合だけ `bounded_counterposition` unitを作る。
- counterevidenceがない場合は、Safetyによるidentity claim拒否を保持しつつ、current burdenのattention／felt responseに留める。
- 強い人格肯定、回復保証、負担消去をforbidden claimとする。

### 4.6 決定論

- builderは乱数を使わない。
- 同じObservation Planから同じunit集合・順序・plan IDを得る。
- plan IDはraw textを含まないbody-free semantic fingerprintから作る。
- 外部AI API、ローカルLLM、モデルライブラリをimport／使用しない。

## 5. 公開契約とruntime

確認結果:

- 既存public backend owner 4ファイルのSHAはStep 1 snapshotと一致した。
- `/emotion/submit` 不変。
- `input_feedback.comment_text` 不変。
- `input_feedback.emlis_ai.observation_status` 不変。
- `見えたこと → Emlisから` の順序不変。
- DB write path不変。
- RN表示条件不変。
- `emlis_ai_reply_service.py` はContent Planner v2をimport／callしていない。
- v1 runtime ownerを維持している。

Step 0／1 testのうち、「v2 moduleが一つも存在しない」という時点条件だけは、Step 3の正当なcontract module追加と衝突した。このtestを「Content Planner contractは存在してよいが、runtime未接続かつStep 4以降のmoduleなし」へ更新した。baseline fixture、receipt、可視本文、production ownerは変更していない。

## 6. 検証結果

### 成功

- Step 0／1回帰 + Step 2 freeze + Step 3 contract: 20 test passed（test関数直接実行）
- 既存Observation I6／I7・Human Reception R2の追加回帰: 8 test passed（test関数直接実行）
- RN public contract: 36 test passed / 0 failed
- `compileall`: passed
- 新規JSON 4ファイル: parse passed
- Development 42件の二回生成一致: 42 / 42
- Content Unit Evidence resolution: 全unit passed
- public backend owner snapshot: Step 1と一致

### 未実行

実行環境に`pytest` moduleがないため、既存backend全pytest suiteは実行していない。新規testおよびpytestを必要としない関連回帰は、全test関数を直接実行した。

## 7. 変更ファイル

### 新規

1. `ai/services/ai_inference/emlis_ai_grounded_reception_content_plan_v2.py`
2. `ai/tests/local_only/emlis_nls_v2_s2_development42_20260713.json`
3. `ai/tests/local_only/holdout/emlis_nls_v2_s2_holdout_a14_20260713.json`
4. `ai/tests/local_only/holdout/emlis_nls_v2_s2_holdout_b14_20260713.json`
5. `ai/tests/fixtures/emlis_nls_v2_s2_corpus_manifest_20260713.json`
6. `ai/tests/helpers/emlis_nls_v2_s2_development.py`
7. `ai/tests/test_emlis_nls_v2_s2_corpus_freeze.py`
8. `ai/tests/test_emlis_nls_v2_s3_content_plan.py`
9. `ai/docs/Cocolon_EmlisAI_NLSv2_S2_S3_Result_20260713.md`

### 修正

1. `ai/tests/test_emlis_nls_v2_s0_s1.py`

## 8. 事実・推測・華恋の意見

### 確認した事実

- 70件のfixture契約とSHAは固定済みである。
- Development 42件は現行Observation PlanだけからContent Planを生成できた。
- 必要なEvidenceがObservation PlanにないためSurfaceで補うcaseはなかった。
- Holdout A／BはStep 3 testから参照されていない。
- runtimeとpublic contractは変更していない。

### 推測

- 現時点の18 semantic signatureはStep 4の談話候補を作る材料として十分な広がりがある可能性が高い。ただし、これはStep 4をまだ実装していないため未確認である。
- Content Unitが3〜4あるlayered 9件では、現在のv1より意味密度を上げられる余地がある。ただし、完成文品質はStep 5以降まで判断できない。

### 華恋の意見

Step 3でSurface語や候補文を置かずに止めたことが重要である。70件の意味責任を先に固定し、Observationに存在する材料だけでContent Planが成立することを確認したため、次工程で文言を足して評価caseへ追従する危険を減らせた。Holdoutを評価せずに封印したままStep 4へ渡せる状態が、今回の正しい完了点である。
