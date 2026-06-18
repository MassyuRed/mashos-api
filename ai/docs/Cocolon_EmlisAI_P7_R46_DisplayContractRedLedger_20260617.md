# Cocolon / EmlisAI P7-R46 Display Contract Red Ledger R0/R1

作成日: 2026-06-17 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: Cocolon / EmlisAI / `/emotion/submit` immediate observation / `input_feedback.comment_text` / display contract / P7-R46 P5/P6 return bridge  
工程: R0 現行source / command / display red reproduction freeze + R1 display contract 2赤のbody-free red ledger化  
基準設計: `Cocolon_EmlisAI_P7_R46_P5P6Return_DisplayContractRedClassification_DetailedDesign_ImplementationOrder_20260617.md`  
基準ローカルzip: `Cocolon_前提資料(230).zip` / `EmlisAIの実装済み資料(67).zip` / `Cocolon(240).zip` / `mashos-api(153).zip`  
GitHub接続確認: Mash指定により不要。未実施。  
コードruntime変更: なし  
RN変更: なし  
DB変更: なし  
API route / request key / public response top-level key変更: なし  
Gate緩和: なし  
fixed commentText追加: なし  
case専用mode / cue / surface追加: なし  
public metaへのraw body追加: なし  
release_allowed: false維持  
p7_complete: false維持  
p8_start_allowed: false維持  

---

## 0. 結論

R0/R1として、現行 `tests/test_emlis_ai_display_contract.py` の赤を再現し、body-free red ledgerへ固定した。

今回の実ファイル変更は次のみ。

```text
新規:
  mashos-api/ai/docs/Cocolon_EmlisAI_P7_R46_DisplayContractRedLedger_20260617.md

修正:
  なし
```

今回の工程では、2赤を直していない。  
赤を「古いtest」と断定していない。  
赤を「body leak」とも断定していない。  
現時点の分類は、次で固定する。

```text
RED-DC-001:
  primary: field_semantics_drift
  secondary: runtime_lineage_preservation_regression_candidate
  not_primary: body_leak
  not_primary: gate_relaxation

RED-DC-002:
  primary: public_meta_priority_mismatch
  secondary: test_expectation_stale_candidate
  secondary: field_semantics_drift
  not_primary: body_leak
  not_primary: gate_relaxation
```

華恋の判断として、R0/R1ではproduction修正へ進まない。  
理由は、R0/R1の目的が「赤の再現と分類」であり、source lineage語彙の固定とrecovery lane decision matrixはR2/R3の工程だからである。

---

## 1. R0: source / command / display red reproduction freeze

### 1.1 基準source

```yaml
schema_version: cocolon.emlis.display_contract_red_ledger.r0_r1_20260617.v1
source_mode: local_zip_snapshot
github_connection_checked: false
github_connection_skip_reason: user_requested_local_work
received_zip_sha256:
  Cocolon_前提資料(230).zip: 1413ded3f4e64acb81c18cbeedcc1924520160a6f1e2230cf3f9e611e68ce68d
  EmlisAIの実装済み資料(67).zip: b0e986da493eced7aba6c54cd4215a3cb6292eea0e21b88b80553b23e627b4da
  Cocolon(240).zip: dc8641b85ae0915d449e2ed26f13736f69a84548d9bf3eb8b128359e5c2c3785
  mashos-api(153).zip: d38fdefce0f5dd33e6fcd647190c8d96c7c8f6c608bb483fe9518e85ee0a282b
  Cocolon_EmlisAI_longterm_roadmap_20260608(19).md: ca9525b2d159028029dd3248263bba2f9d14abb29fe531cb3e9d2a7bb58693ec
  Cocolon_EmlisAI_P7_R46_P5P6Return_DisplayContractRedClassification_DetailedDesign_ImplementationOrder_20260617.md: f4e2202033f1e3e510c767cda3017cafdf9e01bcf7f22a0409fb28baa65f71a1
```

### 1.2 確認した前提

作業前に、以下を確認した。

```text
Cocolon_前提資料/00_karen_read_first.md
Cocolon_前提資料/work_attitude_rules_for_karen/00_read_first.txt
Cocolon_前提資料/work_attitude_rules_for_karen/09_work_start_checklist.txt
Cocolon_前提資料/work_attitude_rules_for_karen/99_integrated_paste_each_time.txt
Cocolon_前提資料/cocolon_thought_material_for_karen.md
Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md
Cocolon_前提資料/emlis_ai_state_answer_human_follow_definition_2026_05_26.md
Cocolon_前提資料/cocolon_environment_state_output_observation_structure_design_2026_05_25.md
Cocolon_EmlisAI_longterm_roadmap_20260608(19).md
Cocolon_EmlisAI_P7_R46_P5P6Return_DisplayContractRedClassification_DetailedDesign_ImplementationOrder_20260617.md
```

固定した作業姿勢:

```text
- 前提資料だけで理解した扱いにしない。実ファイルを確認する。
- 実ファイルだけでCocolon思想に合っていると判断しない。
- R0/R1を、赤修正工程やP7完了工程へ変換しない。
- passed + comment_text をEmlisAIの目的ではなくpublic表示契約として扱う。
- public metaへ raw input / comment_text body / candidate body / surface body を出さない。
- case専用mode / cue / surface / fixed commentTextで赤を塞がない。
- Gateを緩めない。
```

### 1.3 display contract collect freeze

実行コマンド:

```bash
cd mashos-api/ai
PYTHONPATH=services/ai_inference pytest --collect-only -q tests/test_emlis_ai_display_contract.py
```

結果:

```yaml
collected_test_file: tests/test_emlis_ai_display_contract.py
collected_test_count: 5
items_sha256: ae0d060ee16fa3369a9085750a15306d7fdd984203e39c2d387ddd73d45feb76
test_file_sha256: 6be799a592e76f1dd343680df699b13854909b89332e41d64490f072eea45141
```

collect items:

```text
tests/test_emlis_ai_display_contract.py::test_step10_e2e_contract_marks_non_passed_text_exposure_as_blocker
tests/test_emlis_ai_display_contract.py::test_step10_e2e_passed_candidate_exposes_comment_text_only_after_display_gate
tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized
tests/test_emlis_ai_display_contract.py::test_step10_e2e_rejected_candidate_recovers_without_exposing_generated_body
tests/test_emlis_ai_display_contract.py::test_step10_e2e_pre_connection_recovery_exposes_safe_surface_without_body_leak
```

### 1.4 display contract execution freeze

実行コマンド:

```bash
cd mashos-api/ai
PYTHONPATH=services/ai_inference pytest -q --tb=short tests/test_emlis_ai_display_contract.py
```

結果:

```text
3 passed / 2 failed
```

再現した赤:

```yaml
RED-DC-001:
  test: tests/test_emlis_ai_display_contract.py::test_step10_e2e_rejected_candidate_recovers_without_exposing_generated_body
  assertion_line: tests/test_emlis_ai_display_contract.py:487
  expected_field: composer_meta["original_candidate_source_kind"]
  expected_value: ai_generated
  actual_value: labelled_two_stage_surface_recomposition_candidate

RED-DC-002:
  test: tests/test_emlis_ai_display_contract.py::test_step10_e2e_pre_connection_recovery_exposes_safe_surface_without_body_leak
  assertion_line: tests/test_emlis_ai_display_contract.py:569
  expected_field: candidate["composer_model"]
  expected_value: complete_initial_surface_recomposition_v1
  actual_value: labelled_two_stage_surface_recomposition_v1
```

R0の読み:

```text
- input_feedback absentの赤ではない。
- comment_text emptyの赤ではない。
- display gate failedの赤ではない。
- 現時点の赤は、source lineage / recovery lane / public meta priorityの期待不一致として扱う。
```

---

## 2. R1: body-free red ledger

### 2.1 分類軸

R1では、各赤を次の分類軸で固定する。

```text
A. test_expectation_stale
B. runtime_regression
C. public_meta_priority_mismatch
D. field_semantics_drift
E. body_leak
F. gate_relaxation
```

今回の赤は、E/Fとしては扱わない。  
ただし、E/Fの可能性を検査不要として捨てるのではなく、body-free flag / gate relaxed flagでR1時点の観測を固定する。

### 2.2 RED-DC-001 ledger

```yaml
red_id: RED-DC-001
status: RED_CLASSIFIED_UNRESOLVED
layer: source_lineage
case_type: rejected_candidate_recovery
public_input_feedback_included: true
observation_status: passed
reply_comment_text_present: true
display_gate:
  passed: true
  comment_text_present: true
  comment_text_allowed: true
expected_body_free:
  original_candidate_source_kind: ai_generated
actual_body_free:
  final_candidate.composer_model: labelled_two_stage_surface_recomposition_v1
  final_candidate.candidate_source_kind: labelled_two_stage_surface_recomposition_candidate
  final_candidate.original_candidate_source_kind: labelled_two_stage_surface_recomposition_candidate
  final_candidate.public_surface_role: public_observation_candidate
  final_candidate.original_candidate_present: true
  final_candidate.original_candidate_status: generated
  final_candidate.original_display_status: rejected
  final_candidate.original_surface_plain_or_unlabelled: false
  final_candidate.original_surface_labelled_two_stage: true
  final_candidate.labelled_two_stage_surface_recomposition_used: true
  final_candidate.complete_initial_surface_recomposition_used: false
  final_candidate.normal_observation_rebuild_used: false
  final_candidate.gate_recovery_material_surface_used: false
  public_surface_lineage.candidate_source_kind: labelled_two_stage_surface_recomposition_candidate
  public_surface_lineage.labelled_two_stage_surface_recomposition_used: true
  public_surface_lineage.complete_initial_surface_recomposition_used: false
classification:
  primary: field_semantics_drift
  secondary: runtime_lineage_preservation_regression_candidate
not_classified_as:
  body_leak: true
  gate_relaxation: true
recommended_next_action:
  - preserve_root_lineage
  - separate_root_from_recovery_input_and_final_public_source
  - keep_public_meta_body_free
```

R1読み:

```text
final candidate と public_surface_lineage は labelled two-stage として一致している。
ただし、rejected candidate recoveryの文脈で、root original sourceとして保持されるべきsource identityが、final labelled sourceへ寄っている可能性がある。
そのため、RED-DC-001はtest期待の古さだけではなく、original/root field semantics driftとしてR2へ渡す。
```

### 2.3 RED-DC-002 ledger

```yaml
red_id: RED-DC-002
status: RED_CLASSIFIED_UNRESOLVED
layer: recovery_lane_and_public_lineage
case_type: pre_connection_recovery
public_input_feedback_included: true
observation_status: passed
reply_comment_text_present: true
display_gate:
  passed: true
  comment_text_present: true
  comment_text_allowed: true
expected_body_free:
  final_candidate.composer_model: complete_initial_surface_recomposition_v1
actual_body_free:
  final_candidate.composer_model: labelled_two_stage_surface_recomposition_v1
  final_candidate.candidate_source_kind: labelled_two_stage_surface_recomposition_candidate
  final_candidate.original_candidate_source_kind: complete_initial_surface_recomposition_candidate
  final_candidate.public_surface_role: public_observation_candidate
  final_candidate.original_candidate_present: true
  final_candidate.original_candidate_status: generated
  final_candidate.original_display_status: rejected
  final_candidate.source_unavailable_recovered: false
  final_candidate.labelled_two_stage_surface_recomposition_used: true
  final_candidate.complete_initial_surface_recomposition_used: false
  final_candidate.normal_observation_rebuild_used: false
  final_candidate.gate_recovery_material_surface_used: false
  complete_initial_surface_recomposition_summary.candidate_generated: true
  complete_initial_surface_recomposition_summary.applied: false
  complete_initial_surface_recomposition_summary.candidate_source_kind: complete_initial_surface_recomposition_candidate
  complete_initial_surface_recomposition_summary.existing_gate_chain.blocked_reasons:
    - visible_surface_acceptance_gate_failed
  complete_initial_surface_recomposition_summary.existing_gate_chain.passed_by_all_existing_gates: false
  phase20_5_gate_recovery_public_boundary.adopted_candidate_source_kind: complete_initial_surface_recomposition_candidate
  public_surface_lineage.candidate_source_kind: complete_initial_surface_recomposition_candidate
  public_surface_lineage.complete_initial_surface_recomposition_used: true
  public_surface_lineage.labelled_two_stage_surface_recomposition_used: false
classification:
  primary: public_meta_priority_mismatch
  secondary:
    - test_expectation_stale_candidate
    - field_semantics_drift
not_classified_as:
  body_leak: true
  gate_relaxation: true
recommended_next_action:
  - separate_pre_public_candidate_source_from_final_public_candidate_source
  - align_public_surface_lineage_with_final_public_source_or_add_explicit_final_field
  - keep_complete_initial_attempt_as_attempted_not_final_used
```

R1読み:

```text
complete_initialは生成されているが、existing gate chainで visible_surface_acceptance_gate_failed により applied=false で止まっている。
その後のfinal candidateは labelled two-stage として返っている。
一方で、public_surface_lineage は complete_initial をfinalのように示しているため、public meta priority mismatch候補としてR2/R3へ渡す。
```

---

## 3. body-free / Gate boundary確認

R1で取得したbody-free actual metaでは、少なくとも以下を確認した。

```yaml
public_feedback_meta_boundary:
  sanitized: true
  internal_meta_returned: false
  raw_input_included: false
  comment_text_included: false
  comment_text_body_included: false
  candidate_body_included: false

public_meta_body_boundary:
  serialized_public_meta_forbidden_text_hits_count: 0
  forbidden_public_keys_present: []
  leak_flag_values_all_false_for_observed_values:
    internal_meta_returned: true
    raw_input_included: true
    raw_text_included: true
    comment_text_included: true
    comment_text_body_included: true
    candidate_body_included: true
    surface_body_included: true
```

public_surface_lineageのGate relaxed flags:

```yaml
RED-DC-001:
  display_gate_relaxed: false
  runtime_surface_gate_relaxed: false
  visible_surface_gate_relaxed: false
  grounding_gate_relaxed: false
  template_gate_relaxed: false
  safety_gate_relaxed: false

RED-DC-002:
  display_gate_relaxed: false
  runtime_surface_gate_relaxed: false
  visible_surface_gate_relaxed: false
  grounding_gate_relaxed: false
  template_gate_relaxed: false
  safety_gate_relaxed: false
```

注意:

```text
この確認は、R1時点のbody-free ledgerとしての観測である。
body leakが存在しないことをfull backend suite全体へ拡張して主張しない。
Gate relaxationが存在しないことを全runtime pathへ拡張して主張しない。
```

---

## 4. R1 fixed red ledger table

| ID | 状態 | 対象 | 再現結果 | 初期分類 | R2/R3への渡し方 |
|---|---|---|---|---|---|
| RED-DC-001 | RED_CLASSIFIED_UNRESOLVED | original/root source lineage | `original_candidate_source_kind` が `ai_generated` ではなく `labelled_two_stage_surface_recomposition_candidate` | field semantics drift / runtime lineage preservation regression candidate | root / recovery_input / selected / final sourceを分離する |
| RED-DC-002 | RED_CLASSIFIED_UNRESOLVED | recovery lane / public lineage | final candidateはlabelledだが、testはcomplete_initialを期待。public lineageもcomplete_initialをfinalのように示す | public meta priority mismatch / test expectation stale candidate / field semantics drift | pre_public sourceとfinal sourceを分離し、public lineageの優先順を見直す |
| YELLOW-DC-003 | YELLOW | public meta final-source consistency | final candidate sourceとpublic_surface_lineage sourceがRED-DC-002で不一致 | sanitizer priority ambiguity | R2/R3でfield semantics固定後、R8候補へ渡す |
| HOLD-DC-004 | HOLD | red repair | 2赤はまだ修正していない | R0/R1範囲外 | R2以降で最小修正判断 |
| HOLD-DC-005 | HOLD | full backend suite | 未実行 | R0/R1範囲外 | green claim禁止 |
| HOLD-P5-001 | HOLD | P5 human readfeel | 未実施 | R0/R1範囲外 | display赤分類後まで正式開始しない |
| HOLD-P6-001 | HOLD | P6 human readfeel | 未実施 | R0/R1範囲外 | display赤分類後まで正式開始しない |
| HOLD-RD-001 | HOLD | real device modal | 未実施 | R0/R1範囲外 | 実機確認済みにしない |

---

## 5. 変更しない境界

今回のR0/R1では、以下を変更していない。

```text
RN production UI
RN表示タイトル `Emlisの観測`
RN表示条件
/emotion/submit route
request key
public response top-level key
DB physical schema
DB write path
subscription entitlement判定
account delete / access policy
Emlis visible body key
Gate threshold
external AI前提
runtime composer selection
public display gate
candidate body generation
```

今回のR0/R1では、以下を追加していない。

```text
case専用mode
case専用cue
case専用surface
fixed commentText
public response top-level key
JSON schema実ファイル
test期待値の書き換え
production code patch
```

---

## 6. 確認済み

```text
- ローカルzip基準で作業した。
- GitHub接続確認はMash指定により実施していない。
- 前提資料・作業姿勢資料・EmlisAI是正方針・設計書を確認した。
- display contract collect-onlyは5 tests。
- display contract単体実行は3 passed / 2 failed。
- RED-DC-001 / RED-DC-002は設計書で想定した赤と一致する。
- input_feedback_payloadは両red caseで含まれている。
- reply.comment_textは両red caseでpresent。
- observation_statusは両red caseでpassed。
- display_gateは両red caseでpassed。
- R1観測範囲ではpublic meta body boundaryのleak flagはfalse。
- R1観測範囲ではpublic meta内にforbidden public keyは見つかっていない。
- R1観測範囲ではGate relaxation flagはfalse。
- production codeは変更していない。
```

---

## 7. 未確認

```text
- RED-DC-001のroot lineage保持修正。
- RED-DC-002のpublic meta final-source consistency修正。
- source lineage語彙の実装固定。
- recovery lane decision matrixの実装固定。
- display contract 2赤のgreen化。
- full backend suite green。
- P5 human Blind QA。
- P6 limited human readfeel review。
- real device submit / modal読感確認。
```

---

## 8. 書かれていない

```text
- R0/R1で2赤を修正する指示はない。
- R0/R1でtest期待値を更新する指示はない。
- R0/R1でproduction source lineage helperを追加する指示はない。
- R0/R1でRN / API / DBを変更する指示はない。
- R0/R1でP5/P6 human QAを実施した事実はない。
- R0/R1で実機modal確認を実施した事実はない。
- R0/R1でrelease_allowed / p7_complete / p8_start_allowedをtrueにする根拠はない。
```

---

## 9. 推測禁止

```text
- RED-DC-001を古いtestだけと断定しない。
- RED-DC-001をbody leakと断定しない。
- RED-DC-002をruntime regressionだけと断定しない。
- RED-DC-002でcomplete_initialがfinal採用済みだったと断定しない。
- labelled two-stage finalをP6無制限拡張と混同しない。
- public meta body-freeをlineage正確性合格に変換しない。
- display contract green未達のままP5/P6正式読感へ戻らない。
- R0/R1完了をP7-HOLD-004 closureへ変換しない。
```

---

## 10. 次に実行すべきこと

R2以降で、次を順番に扱う。

```text
1. source lineage語彙を root / recovery_input / selected / pre_public / final に分ける。
2. RED-DC-001で、root sourceを `ai_generated` として保持できるか確認する。
3. RED-DC-002で、complete_initialをpre-public attempted / applied=falseとして保持し、final sourceをlabelledとして説明できるか確認する。
4. public_surface_lineageがfinal candidate sourceと矛盾しないよう、public meta priorityを見直す。
5. その後にtest期待更新またはruntime修正の最小差分を判断する。
```

---

## 11. 華恋の意見

R0/R1では、コードを触らない判断が正しいです。

今回の赤は、表示本文が空になる赤でも、public metaに本文が漏れている赤でもありません。  
でも、source lineageが曖昧なままだと、P5/P6の読感に戻ったときに「人間が読んだsurfaceが、どのrecovery laneから来たのか」を説明できなくなります。

Cocolonは、ユーザーから見える文章だけ大事にするのでは足りません。  
見えないmetaが嘘をつくと、後から読感や実機modalで違和感が出たとき、原因を見失います。

なので、R1で赤をbody-freeに固定したうえで、R2/R3でsource lineage語彙とrecovery laneを分けてから最小修正へ入るのが、Cocolonとして一番安全です。
