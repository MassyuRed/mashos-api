# Cocolon EmlisAI P7-PQR I3-Q P5 Roadmap-Delta Sidecar Form

date: 2026-07-10  
phase: P7  
stage: P7-PQR  
form_version_ref: `p7_pqr_i3q_p5_roadmap_delta_sidecar_form.bodyfree.v1`  
form_kind: body-free blank local-review form definition  
form_status: `FORM_FIXED_ACTUAL_ROWS_NOT_STARTED`  
completed_sidecar_schema_version_ref: `cocolon.emlis.p7.cross_lane_question_need_observation.bodyfree.v1`  

## 0. このformの役割

このformは、P5 Human Blind QA 24件で、2026-07-06 roadmap差分を本文purge前に人間が残すためのblank form正本である。

R49 question-need observation rowを置換しない。R48 rating row、R49 exact row、P7-PQR sidecarを1件ずつ1:1で接続する。sidecarは追加review unitではない。

```text
R48 human rating row:
  Pass Aの正本

R49 exact question-need observation row:
  Pass Bのprimary observation正本

P7-PQR sidecar:
  Pass A / Bへのlinkとhuman provenance
  roadmap追加観察
  Pass C plan candidate overlay

replacement_of_r49:
  false

additional_review_unit_count:
  0

required_form_slot_count:
  24

actual_sidecar_row_count_at_form_fix:
  0
```

このrepo内のMarkdownにはform定義だけを置く。将来のreview中working copyは、有効な `COCOLON_EMLIS_LOCAL_REVIEW_ROOT` 配下のbody-free保存領域にだけ置き、body-full packetへ混ぜない。

purge / disposalとno-body / no-question guardの成立後に作られるsanitized body-free evidenceについては、I5のcurrent ownerがhandoff / export可否を判断する。このformは、その将来判断を事前許可せず、永久禁止もしない。

## 1. ownerと接続mode

| 項目 | 固定値 |
|---|---|
| review lane | `P5_HUMAN_BLIND_QA` |
| review kind | `p5_history_line_readfeel` |
| source contract mode | `R49_EXACT_REFERENCE` |
| observation source | `HUMAN_REVIEWER` |
| Pass A owner | `cocolon.emlis.p7_r48.p5_rating_row.bodyfree.v1` |
| Pass B owner | `cocolon.emlis.p7_r49.question_need_observation_row.bodyfree.v1` |
| Pass C owner | this P7-PQR body-free sidecar form |
| completed sidecar schema | `cocolon.emlis.p7.cross_lane_question_need_observation.bodyfree.v1` |
| R49 replacement | false |
| question text / answer body | forbidden |
| automatic / machine observation | forbidden |

R51 question rowはR49 exact schemaではないため、`R49_EXACT_REFERENCE` として扱わない。現行R51のratingとsemantic selectionを同時取得する形だけでは、以下の三pass freeze順を証明できない。I4 actual operationでは、Pass A、Pass B、Pass Cを別のlocal formまたは同等のread-only境界に分けてからR51 lifecycleへ接続する。

## 2. 必須順序とvisibility

### Pass A — blind readfeel

目的は、問いやplan候補でP5 surfaceの弱さを隠さず、現在のproduct readfeelを先に人間が判定すること。

```text
visible:
  current_input_review_surface
  returned_emlis_surface
  bounded_owned_history_review_surface
  blind case id
  R48 rating form

hidden:
  controller case ref
  family
  subscription tier
  expected result
  gate result
  primary question reason
  question kind
  plan candidate

completion:
  R48 rating row refを確定
  human reviewer refを確定
  rating reviewed_atを確定
  Pass Aをread-onlyへfreeze
```

sidecarはrating値を複製しない。`linked_human_rating_row_ref` とfreeze状態だけを接続する。

### Pass B — blind semantic question-need

Pass Aがfreeze済みでなければ開かない。Pass Bでも上記3つのbody-full surfaceはlocal-onlyで閲覧できるが、family、tier、expected result、gate result、plan candidateは引き続き見せない。

```text
R49 exact row fields:
  question_need_primary_class
  ambiguity_kind_refs
  one_question_fit_ref
  plan_candidate_flags
  repair_required_refs
  sanitized_reason_ids

P7-PQR sidecar semantic fields:
  source_question_observation_ref
  source_primary_class_ref
  reason_family_ref
  ambiguity_kind_refs
  one_question_fit_ref
  repair_target_refs
  preliminary_observation_possible_ref
  question_kind_candidate_ref
  answer_affordance_candidate_refs
  interrogation_risk_ref
  self_blame_amplification_risk_ref
  immediate_observation_delay_risk_ref
  question_system_eligibility_ref
  refined_observation_eligibility_ref
  legacy_plan_class_primary_present
  manual_reason_family_mapping_status_ref
  sanitized_reason_ids

completion:
  semantic human reviewer refを確定
  reviewed_atを確定
  Pass Bをread-onlyへfreeze
```

R49の `plan_candidate_flags` はR49 exact normalizerが持つdictであり、P7-PQRのscalar `plan_candidate_ref` とは別物である。R49 flagsをreviewerへplan候補として提示せず、Free / Plus / Premium normal / Premium deep overlayはPass Cで分離して記録する。

### Pass C — body-free plan overlay

Pass AとPass Bがfreeze済みでなければ開かない。body-full surfaceは再表示しない。safeなfamily / tier metadataとfreeze済みPass Bだけを使う。

```text
capture:
  family_ref
  plan_candidate_ref
  plan_overlay_resolver_ref
  plan_overlay_resolved_at
  plan_overlay_source_ref
  blind_rating_frozen_before_plan_overlay
  semantic_observation_frozen_before_plan_overlay

must remain:
  plan_overlay_source_ref = SAFE_METADATA_POST_BLIND_FREEZE
  blind_rating_frozen_before_plan_overlay = true
  semantic_observation_frozen_before_plan_overlay = true

forbidden:
  body-full surface再表示
  Pass Aのrating変更
  Pass Bのsemantic selection変更
```

`subscription_tier_ref` はPass Cのsafe display metadataとして参照できるが、§14.4 exact completed sidecar rowには保存しない。

## 3. completed sidecarの識別・provenance field

blank slotにはactual linkageやhuman selectionを入れない。I4で実際にreviewする際、completed sidecarは詳細設計§14.4のexact schemaに従い、次をすべて必須とする。

```text
schema_version
review_session_id
review_unit_ref
human_reviewer_ref
reviewed_at
observation_source_ref
linked_human_rating_row_ref
review_lane_ref
family_ref
source_contract_mode_ref
source_question_observation_ref
source_primary_class_ref
reason_family_ref
ambiguity_kind_refs
one_question_fit_ref
plan_candidate_ref
preliminary_observation_possible_ref
question_kind_candidate_ref
answer_affordance_candidate_refs
interrogation_risk_ref
self_blame_amplification_risk_ref
immediate_observation_delay_risk_ref
repair_target_refs
question_system_eligibility_ref
refined_observation_eligibility_ref
legacy_plan_class_primary_present
manual_reason_family_mapping_status_ref
plan_overlay_resolver_ref
plan_overlay_resolved_at
plan_overlay_source_ref
blind_rating_frozen_before_plan_overlay
semantic_observation_frozen_before_plan_overlay
sanitized_reason_ids
question_text_included
draft_question_text_included
raw_answer_included
reviewer_free_text_included
body_removed
body_free
```

fixed values:

```text
schema_version = cocolon.emlis.p7.cross_lane_question_need_observation.bodyfree.v1
review_lane_ref = P5_HUMAN_BLIND_QA
source_contract_mode_ref = R49_EXACT_REFERENCE
observation_source_ref = HUMAN_REVIEWER
plan_overlay_source_ref = SAFE_METADATA_POST_BLIND_FREEZE
blind_rating_frozen_before_plan_overlay = true
semantic_observation_frozen_before_plan_overlay = true
question_text_included = false
draft_question_text_included = false
raw_answer_included = false
reviewer_free_text_included = false
body_removed = true
body_free = true
```

### 3.1 local controller linkage

§14.4 schemaは `additionalProperties = false` であるため、次はcompleted sidecar rowへ追加しない。local-only controller bindingで照合する。

```text
packet_ref_id
blind_case_id
case_ref_id
review_kind
subscription_tier_ref
optional local sidecar row id
```

R48 rating rowとR49 exact rowの次のidentity quartetをlocal controllerで一致させ、そのbindingをbody-freeの `review_session_id`、`review_unit_ref`、`linked_human_rating_row_ref`、`source_question_observation_ref` へ接続する。

```text
review_session_id
packet_ref_id
blind_case_id
case_ref_id
```

`source_question_observation_ref` と `linked_human_rating_row_ref` は、既存R49 / R48 row fieldではない。local controllerが各body-free rowへ付けるbody-free refであり、上記identity quartetへbindする。本文、本文由来hash、record hash、absolute pathから生成しない。

24個の `I3Q-P5-SIDECAR-*` はform-local slot refである。I4でexplicit current sourceとR48 / R49 bindingが解決した後にだけ `review_unit_ref` へbindでき、slot ref自体をactual source refにしない。

### 3.2 human provenanceと時刻

`human_reviewer_ref` はPass B semantic observationを行ったpseudonymous human refである。linked R48 rating rowの `reviewer_ref` もhuman provenanceを持つ。同一reviewerであることを暗黙推定せず、異なる場合もlocal controller bindingで両方のprovenanceを保持する。

`plan_overlay_resolver_ref` もpseudonymous human refを必須とする。machine、automatic process、modelをresolverとして許可しない。

R49 exact rowにはhuman provenanceとrow idがないため、sidecarの `human_reviewer_ref`、`reviewed_at`、controller-owned `source_question_observation_ref` で補う。

時刻順は次を満たす。

```text
R48 rating reviewed_at
  <= sidecar reviewed_at
  <= sidecar plan_overlay_resolved_at
```

`reviewed_at` と `plan_overlay_resolved_at` はtimezone付きISO-8601等、同じ規則で比較可能なactual timestampに固定する。empty、default、`reviewed_at_unset`、時刻でないrefを拒否し、単なる任意文字列比較で順序を判定しない。

### 3.3 body-free markerとdisposal

`body_removed = true` はcompleted sidecar row自体へbodyを持たないprojection markerであり、body-full packetのpurgeやdisposal receipt検証を意味しない。

Pass C完了だけでdisposal verifiedを主張しない。packet / notesのpurgeとdisposal receiptはI5の別ownerで確認する。

## 4. field enum

### 4.0 R49 exact sourceとsidecar normalized fieldの分離

R49 exact rowの `question_need_primary_class` は、sidecarの `source_primary_class_ref` へexact refする。許可値は現行R49の次の9つだけである。

```text
no_question_needed_emlis_can_observe
question_may_reduce_overread_risk
question_would_make_immediate_observation_heavy
not_question_emlis_readfeel_repair_required
not_question_p5_surface_repair_required
not_question_gate_boundary_required
plus_single_question_candidate_later
premium_deep_dive_candidate_later
insufficient_material_execution_blocker
```

R49 exact row側:

```text
question_need_primary_class
ambiguity_kind_refs
one_question_fit_ref
plan_candidate_flags
repair_required_refs
sanitized_reason_ids
```

completed sidecar側:

```text
source_primary_class_ref
reason_family_ref
ambiguity_kind_refs
one_question_fit_ref
plan_candidate_ref
repair_target_refs
sanitized_reason_ids
```

同名fieldがあってもrow ownerは別である。R49 source rowを書き換えず、sidecarは§14.5.1のnormative mappingを保持する。特にR49 `plan_candidate_flags` はdict、sidecar `plan_candidate_ref` はscalarであり、相互置換しない。

R49 `repair_required_refs` の許可値:

```text
emlis_readfeel_repair_required
p5_surface_repair_required
gate_boundary_repair_required
no_repair_required
```

sidecar `repair_target_refs` のP5許可値:

```text
emlis_core_readfeel
p5_history_line_surface
gate_boundary
```

normalization:

| R49 repair required ref | sidecar repair target |
|---|---|
| `emlis_readfeel_repair_required` | `emlis_core_readfeel` |
| `p5_surface_repair_required` | `p5_history_line_surface` |
| `gate_boundary_repair_required` | `gate_boundary` |
| `no_repair_required` | empty array |

`no_repair_required` をsidecar repair targetへ混ぜない。

R49 `ambiguity_kind_refs` と `one_question_fit_ref` は現行R49 frozen enumだけをsourceとして受ける。sidecarのnormalized `one_question_fit_ref` は下記normative mappingに従い、legacy 2 class以外を人間の自由mappingにしない。

### 4.1 reason family

```text
EMLIS_OBSERVABLE_WITHOUT_QUESTION
ONE_QUESTION_MAY_REDUCE_OVERREAD
QUESTION_WOULD_BURDEN_IMMEDIATE_OBSERVATION
NOT_QUESTION_REPAIR_OR_BOUNDARY
INSUFFICIENT_MATERIAL
```

### 4.2 plan candidate

primary reasonとは別fieldにする。

```text
NONE
FREE_LIGHT_SINGLE_QUESTION_CANDIDATE_LATER
PLUS_SINGLE_QUESTION_CANDIDATE_LATER
PREMIUM_SINGLE_QUESTION_CANDIDATE_LATER
PREMIUM_DEEP_DIVE_CANDIDATE_LATER
UNRESOLVED
```

Free / Premium normal candidateをR49 primary classや既存flagとして捏造しない。販売仕様、質問回数、plan guard、API / DB / RN仕様へ昇格しない。

### 4.3 preliminary observation

```text
AVAILABLE
NOT_AVAILABLE
UNRESOLVED
```

仮観測本文は含めない。

### 4.4 question kind candidate

```text
NONE
EVENT_CONFIRMATION
CORE_CONFIRMATION
REASON_OR_TRIGGER_CONFIRMATION
DISTANCE_OR_CHANGE_CONFIRMATION
UNRESOLVED
```

質問文は含めない。

### 4.5 answer affordance candidate

複数選択を許す。

```text
CHOICES
DONT_KNOW
CONTINUE_OBSERVATION
FREE_TEXT
NOT_APPLICABLE
```

`NOT_APPLICABLE` は単独でだけ許可する。question candidateがある場合は、少なくとも1つのnon-`NOT_APPLICABLE` affordanceを必要とする。これはP8 UI仕様の確定ではない。

### 4.6 risk

次の3 fieldへそれぞれ使用する。

```text
interrogation_risk_ref
self_blame_amplification_risk_ref
immediate_observation_delay_risk_ref
```

許可値:

```text
ABSENT
PRESENT
UNRESOLVED
```

1つでも `PRESENT` なら `question_system_eligibility_ref = ELIGIBLE` を拒否する。

### 4.7 eligibility

```text
ELIGIBLE
NOT_ELIGIBLE
UNRESOLVED
```

`question_system_eligibility_ref` と `refined_observation_eligibility_ref` へ別々に記録する。`ELIGIBLE` をplan candidateやreview unit数から推定しない。

### 4.8 legacy primary mapping

R49 legacy primary class:

```text
plus_single_question_candidate_later
premium_deep_dive_candidate_later
```

source R49 rowは書き換えない。人間がreason family、one-question fit、repair、eligibilityを明示してから `manual_reason_family_mapping_status_ref = COMPLETED` にする。

```text
NOT_REQUIRED
REQUIRED
COMPLETED
```

legacy classがなく `false` なら `NOT_REQUIRED` のみ。legacy classがあり `true` なら `REQUIRED` または `COMPLETED` のみ。`REQUIRED` が1件でも残る間はsummary / closureを作らない。

`legacy_plan_class_primary_present` は `source_primary_class_ref` からderiveし、caller入力を信頼しない。

新規I4 Pass Bのreviewer-facing optionとして、legacy 2 classのPlus / Premium名称を表示しない。これらは既存R49 exact rowをadoptする場合の互換入力としてだけ受け、発生時はmanual mappingを必須にする。新規semantic判断ではplan-neutral primary classを使い、plan candidateはPass Cだけで扱う。

### 4.9 primary class normative mapping

非legacy primary classは次へ固定する。

| source primary class | reason family | sidecar one-question fit | repair target | question eligibility | refined eligibility |
|---|---|---|---|---|---|
| `no_question_needed_emlis_can_observe` | `EMLIS_OBSERVABLE_WITHOUT_QUESTION` | `not_needed` | empty | `NOT_ELIGIBLE` | `NOT_ELIGIBLE` |
| `question_may_reduce_overread_risk` | `ONE_QUESTION_MAY_REDUCE_OVERREAD` | `fits_one_question` | empty | `ELIGIBLE` | `ELIGIBLE` or `UNRESOLVED` |
| `question_would_make_immediate_observation_heavy` | `QUESTION_WOULD_BURDEN_IMMEDIATE_OBSERVATION` | `would_delay_immediate_observation` | empty | `NOT_ELIGIBLE` | `NOT_ELIGIBLE` |
| `not_question_emlis_readfeel_repair_required` | `NOT_QUESTION_REPAIR_OR_BOUNDARY` | `repair_required_not_question` | `emlis_core_readfeel` | `NOT_ELIGIBLE` | `NOT_ELIGIBLE` |
| `not_question_p5_surface_repair_required` | `NOT_QUESTION_REPAIR_OR_BOUNDARY` | `repair_required_not_question` | `p5_history_line_surface` | `NOT_ELIGIBLE` | `NOT_ELIGIBLE` |
| `not_question_gate_boundary_required` | `NOT_QUESTION_REPAIR_OR_BOUNDARY` | `unsafe_or_boundary_not_question` | `gate_boundary` | `NOT_ELIGIBLE` | `NOT_ELIGIBLE` |
| `insufficient_material_execution_blocker` | `INSUFFICIENT_MATERIAL` | `insufficient_material` | empty | `UNRESOLVED` | `UNRESOLVED` |

gate-boundary rowのR49 exact source `one_question_fit_ref` は現行ownerの値を変更しない。completed sidecarのnormalized `one_question_fit_ref` は、詳細設計§14.5.1に従い `unsafe_or_boundary_not_question` とする。

`question_may_reduce_overread_risk` を実際に `ELIGIBLE` とするには、preliminary observationが `AVAILABLE`、3 riskがすべて `ABSENT`、question kindが `NONE` / `UNRESOLVED` 以外、non-`NOT_APPLICABLE` affordanceが1件以上であることも必要とする。いずれかが不成立ならeligibilityだけを `NOT_ELIGIBLE` / `UNRESOLVED` へdowngradeせず、semantic inconsistencyとしてcompleted sidecarをrejectし、source classificationの人間再確認へ戻す。

legacy 2 classだけはhuman explicit mappingとし、`manual_reason_family_mapping_status_ref = COMPLETED` までsummary / closureをblockする。source primaryは変更しない。

## 5. 24 blank form slots

以下はform slotであり、actual source case、actual R49 row、human observation、review evidenceではない。R48 default case distributionの `p7r48-p5-case-001..024` をactual sourceへ昇格させない。

| ordinal | form slot ref | source linkage | Pass A | Pass B | Pass C |
|---:|---|---|---|---|---|
| 1 | `I3Q-P5-SIDECAR-001` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 2 | `I3Q-P5-SIDECAR-002` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 3 | `I3Q-P5-SIDECAR-003` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 4 | `I3Q-P5-SIDECAR-004` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 5 | `I3Q-P5-SIDECAR-005` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 6 | `I3Q-P5-SIDECAR-006` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 7 | `I3Q-P5-SIDECAR-007` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 8 | `I3Q-P5-SIDECAR-008` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 9 | `I3Q-P5-SIDECAR-009` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 10 | `I3Q-P5-SIDECAR-010` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 11 | `I3Q-P5-SIDECAR-011` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 12 | `I3Q-P5-SIDECAR-012` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 13 | `I3Q-P5-SIDECAR-013` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 14 | `I3Q-P5-SIDECAR-014` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 15 | `I3Q-P5-SIDECAR-015` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 16 | `I3Q-P5-SIDECAR-016` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 17 | `I3Q-P5-SIDECAR-017` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 18 | `I3Q-P5-SIDECAR-018` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 19 | `I3Q-P5-SIDECAR-019` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 20 | `I3Q-P5-SIDECAR-020` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 21 | `I3Q-P5-SIDECAR-021` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 22 | `I3Q-P5-SIDECAR-022` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 23 | `I3Q-P5-SIDECAR-023` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |
| 24 | `I3Q-P5-SIDECAR-024` | `CURRENT_SOURCE_UNRESOLVED` | `PASS_A_UNFILLED` | `PASS_B_UNFILLED` | `PASS_C_UNFILLED` |

全slot共通state:

```text
FORM_SLOT_ONLY
CURRENT_SOURCE_UNRESOLVED
PASS_A_UNFILLED
PASS_B_UNFILLED
PASS_C_UNFILLED
ACTUAL_REVIEW_NOT_STARTED
ACTUAL_SIDECAR_ROW_NOT_MATERIALIZED
```

これらはproduction contract enumではなく、このMarkdown formだけのstatus refである。runtimeやR48〜R51のenumへ追加しない。

## 6. semantic guard

completed sidecarでは次を必須とする。

1. R49 exact referenceはP5だけで使う。
2. `source_question_observation_ref` を必須とし、参照先R49 primary classと一致させる。
3. P5 `R49_EXACT_REFERENCE` modeでは、sidecar `ambiguity_kind_refs` を参照先R49 rowとexact一致させ、Pass Cで変更しない。
4. plan candidateはprimary reasonを決定しない。
5. Free / Plus / Premium candidateを販売仕様、P8開始、plan guardへ昇格しない。
6. repair targetがあるrowをquestion eligibleだけでPASSにしない。
7. insufficient materialを `ELIGIBLE` にしない。
8. question eligibleにはpreliminary observation `AVAILABLE` と3 riskすべて `ABSENT` を必要とする。
9. `ONE_QUESTION_MAY_REDUCE_OVERREAD` ではquestion kindを `NONE` / `UNRESOLVED` にせず、non-`NOT_APPLICABLE` affordanceを必要とする。
10. `EMLIS_OBSERVABLE_WITHOUT_QUESTION` / `NOT_QUESTION_REPAIR_OR_BOUNDARY` ではquestion kindを `NONE`、affordanceを `[NOT_APPLICABLE]` にする。
11. R48 ratingとR49 exact rowのsession / packet / blind case / case identityをlocal controllerで一致させ、sidecarのreview session / review unit / linked refsへbindする。
12. `source_question_observation_ref` をcontroller-owned body-free refとし、body / record hash由来を拒否する。
13. human reviewerとhuman plan resolverのprovenanceを必須とし、machine / automatic / model rowを拒否する。
14. actual timezone付きtimestampがないrowや、時刻順が逆のrowを拒否する。
15. Pass A / B freeze前のPass Cを拒否する。
16. Pass CからPass A / Bへのmutationを拒否する。
17. `body_removed = true` をdisposal verifiedへ昇格しない。
18. 24件未満・超過、duplicate、missing link、legacy mapping `REQUIRED` をclosure blockerにする。

## 7. 禁止field

form、completed sidecar、body-free summaryに次を含めない。

```text
raw_input
raw_answer
comment_text
comment_text_body
returned_emlis_surface
current_input_review_surface
bounded_owned_history_review_surface
preliminary_observation_text
question_text
draft_question_text
question_body
reviewer_free_text
reviewer_note
reviewer_notes
local_absolute_path
body_content_hash
packet_content_hash
raw_text_hash
terminal_output
stdout
stderr
traceback
```

sanitized reason IDは許可するが、本文由来hashをreason IDに使わない。

## 8. form受入条件

```text
[x] 24 blank slot ref固定
[x] slotをactual source / actual observationとして数えない
[x] R48 rating → R49 exact → P7-PQR overlay順を固定
[x] Pass A / B / C visibilityとfreezeを固定
[x] human provenanceと1:1 identity linkを固定
[x] Free / Plus / Premium normal / Premium deep candidateをprimary reasonから分離
[x] preliminary observation / question kind / affordance / 3 risk / eligibilityを固定
[x] body / question / answer / free text / path / hash禁止
[x] review中working copyはexternal local rootだけに保存
[x] sanitized body-free evidenceの将来handoff / exportを本formで事前許可しない
[x] actual sidecar rows 0
[x] actual review未開始
```

## 9. JSON / schema実ファイル判断

今回は作らない。

理由は、actual current 24 source link、valid local root、filled-row storage、I4のlocal form分離方式が未確定であり、いまJSON/schemaを作ると仮のactual row validatorや保存責務を先行実装するためである。

I4開始前に、別local formでPass A / B / C順を機械検証する必要が確定した場合だけ、このformを正本としてtest-only validatorまたはJSON Schemaの実ファイル化を再判断する。

## 10. stopped closure

```text
I3-Q blank body-free form:
  FIXED

current source linkage:
  UNRESOLVED

actual sidecar rows:
  0

actual human review:
  NOT_STARTED

P5 preflight:
  P5_ACTUAL_LOCAL_REVIEW_PREFLIGHT_BLOCKED_STOPPED

I4 start allowed:
  false

question system implemented:
  false

P7 complete:
  false

P8 start allowed:
  false

P9 pilot started:
  false

API / DB / RN / runtime changed:
  false

release allowed:
  false
```
