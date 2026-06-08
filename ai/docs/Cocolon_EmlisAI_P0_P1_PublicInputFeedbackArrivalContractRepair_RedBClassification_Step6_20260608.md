# Cocolon / EmlisAI P0-P1 Public Input Feedback Arrival Contract Repair Step6 Red B分類

作成日: 2026-06-08 JST  
作業者: 華恋  
作業範囲: Step 6: Red B1/B2をred ledger分類する  
対象: `tests/test_emlis_ai_display_contract.py` の残赤2件  
GitHub接続: なし。ローカルzipのみ確認。  
コード本体変更: なし  
test source変更: なし  
RN変更: なし  
API route変更: なし  
DB write path変更: なし  
public response key変更: なし  

---

## 0. 結論

Step 6では、Red B1 / Red B2を次のように分類した。

```text
Red B1:
  classification: stale_contract_expectation
  secondary_action: update_test_expectation_in_later_step

Red B2:
  classification: stale_contract_expectation
  secondary_action: split_true_unavailable_fixture_in_later_step
```

どちらも、このStep 6時点では実装修正対象にはしない。

理由は次である。

```text
- actualはどちらも passed になっている。
- しかし、元unsupported body / raw input / candidate body / comment_text body は public comment_text / public meta へ露出していない。
- public_surface_lineage 上の candidate_source_kind は許可されたpublic observation candidate系である。
- gate_recovery_material_surface_used_as_public_body は false。
- diagnostic_recovery_surface_used_as_public_body は false。
- public_candidate_source_allowed は true。
- public_candidate_source_forbidden は false。
- should_include_public_input_feedback は true。
- public meta boundary は sanitized / body-free を維持している。
```

したがって、現時点の赤は「現在思想では safe recovery / recomposition 後に displayable になり得るfixtureに対して、旧testが rejected / unavailable 固定を期待している」ことによる **stale contract expectation** として扱う。

ただし、これは `rejected / unavailable` 境界を消してよいという意味ではない。  
Step 7以降で、true infrastructure / true unavailable / safety fail-closed の別fixtureを追加または確認し、非表示境界を別契約で守る必要がある。

---

## 1. 受領zip内の既存反映確認

受領した `mashos-api_6(50).zip` 内で、Step 0〜5の成果物が入っていることを確認した。

```text
Step 0 / 1:
- docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_RedLedger_Step0_20260608.md
- tests/test_emlis_ai_public_feedback_meta.py

Step 2:
- services/ai_inference/emlis_ai_public_feedback_meta.py

Step 3:
- services/ai_inference/emotion_submit_service.py
- tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py

Step 4:
- services/ai_inference/emlis_ai_product_surface_validation.py
- tests/test_emlis_ai_product_surface_validation_p3.py

Step 5:
- docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_Step5_RedA_E2EGreen_20260608.md
```

前回Step 0〜5の提出zipと、受領zip内の該当ファイルを比較し、すべて一致した。

```text
OK identical:
- mashos-api/ai/docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_RedLedger_Step0_20260608.md
- mashos-api/ai/tests/test_emlis_ai_public_feedback_meta.py
- mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py
- mashos-api/ai/services/ai_inference/emotion_submit_service.py
- mashos-api/ai/tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py
- mashos-api/ai/services/ai_inference/emlis_ai_product_surface_validation.py
- mashos-api/ai/tests/test_emlis_ai_product_surface_validation_p3.py
- mashos-api/ai/docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_Step5_RedA_E2EGreen_20260608.md
```

---

## 2. Step 6 baseline確認

実行コマンド:

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q \
  tests/test_emlis_ai_display_contract.py \
  -vv -p pytest_asyncio.plugin --tb=short --assert=plain
```

結果:

```text
3 passed / 2 failed
```

green:

```text
- test_step10_e2e_contract_marks_non_passed_text_exposure_as_blocker
- test_step10_e2e_passed_candidate_exposes_comment_text_only_after_display_gate
- test_phase5_passed_candidate_keeps_public_meta_sanitized
```

remaining red:

```text
Red B1:
- test_step10_e2e_rejected_candidate_never_exposes_generated_body
- expected: rejected
- actual: passed

Red B2:
- test_step10_e2e_unavailable_pre_connection_never_exposes_comment_text
- expected: unavailable
- actual: passed
```

この時点で、Red Aは引き続きgreenである。

---

## 3. Red B1分類

### 3.1 対象

```text
red_id: P0P1-ARRIVAL-RED-B1-001
test_name: tests/test_emlis_ai_display_contract.py::test_step10_e2e_rejected_candidate_never_exposes_generated_body
old_expected:
  step10_observation_status: rejected
  reply_comment_text_present: false
actual:
  step10_observation_status: passed
  reply_comment_text_present: true
```

### 3.2 確認した事実

```yaml
reply_comment_text_present: true
step10_observation_status: passed
diagnostic_observation_status: passed
public_meta_observation_status: passed
should_include_public_input_feedback: true
unsupported_text_exposed_in_comment_text: false
unsupported_text_exposed_in_public_meta: false
raw_input_snippet_exposed_in_public_meta: false
public_meta_forbidden_keys_present: []
public_feedback_meta_boundary:
  sanitized: true
  internal_meta_returned: false
  raw_input_included: false
  comment_text_included: false
visible_surface_acceptance_gate:
  evaluated: true
  passed: false
  classification: yellow
  action: warn
state_answer_gate_boundary:
  passed: true
  blocked: false
  terminal_surface_block: false
two_stage_reception_gate:
  passed: true
  blocked: false
  terminal_surface_block: false
  labels_present: true
  label_order_valid: true
  observation_section_non_empty: true
  reception_section_non_empty: true
public_surface_lineage:
  candidate_source_kind: labelled_two_stage_surface_recomposition_candidate
  public_candidate_source_allowed: true
  public_candidate_source_forbidden: false
  public_display_allowed_by_boundary: true
  public_surface_role: public_observation_candidate
  surface_requirement_family: labelled_two_stage
  two_stage_required: true
  labelled_two_stage_surface_recomposition_used: true
  complete_initial_surface_recomposition_used: false
  normal_observation_rebuild_used: false
  gate_recovery_material_surface_used_as_public_body: false
  diagnostic_recovery_surface_used_as_public_body: false
  raw_input_included: false
  candidate_body_included: false
  comment_text_body_included: false
  display_gate_relaxed: false
  runtime_surface_gate_relaxed: false
  visible_surface_gate_relaxed: false
  grounding_gate_relaxed: false
  template_gate_relaxed: false
  safety_gate_relaxed: false
connection_visibility:
  connection_status: provided_client
  explicit_client_used: true
  resolved_client_class: _UnsupportedComposer
  composer_connection_attempted: true
  composer_generation_attempted: true
  composer_candidate_status: generated
  actual_composer_rejection: false
  pre_connection_stop: false
```

### 3.3 判断

```text
classification: stale_contract_expectation
implementation_action: none_in_step6
test_action: later_update_expected_contract
```

判断理由:

```text
旧testは「unsupported composerが作った本文は必ず rejected / comment_text empty」と見ている。
しかし現在の実装では、元unsupported bodyをpublic本文へ露出せず、labelled_two_stage_surface_recomposition_candidate として safeなpublic observation candidateへ戻している。

このため、旧testの守るべき契約は「必ずrejected」ではなく、
「元unsupported generated bodyをpublic comment_text / public metaへ露出しない」に更新するのが現在思想に合う。
```

B1は実装修正対象ではなく、後続Stepでtest期待値を更新する対象である。  
ただし、non-passed本文露出を検知する低レベルcontractは維持する。

---

## 4. Red B2分類

### 4.1 対象

```text
red_id: P0P1-ARRIVAL-RED-B2-001
test_name: tests/test_emlis_ai_display_contract.py::test_step10_e2e_unavailable_pre_connection_never_exposes_comment_text
old_expected:
  step10_observation_status: unavailable
  reply_comment_text_present: false
actual:
  step10_observation_status: passed
  reply_comment_text_present: true
```

### 4.2 確認した事実

```yaml
reply_comment_text_present: true
step10_observation_status: passed
diagnostic_observation_status: passed
public_meta_observation_status: passed
should_include_public_input_feedback: true
unsupported_text_exposed_in_comment_text: false
unsupported_text_exposed_in_public_meta: false
raw_input_snippet_exposed_in_public_meta: false
public_meta_forbidden_keys_present: []
public_feedback_meta_boundary:
  sanitized: true
  internal_meta_returned: false
  raw_input_included: false
  comment_text_included: false
visible_surface_acceptance_gate:
  evaluated: true
  passed: false
  classification: yellow
  action: warn
state_answer_gate_boundary:
  passed: true
  blocked: false
  terminal_surface_block: false
two_stage_reception_gate:
  passed: true
  blocked: false
  terminal_surface_block: false
  labels_present: true
  label_order_valid: true
  observation_section_non_empty: true
  reception_section_non_empty: true
public_surface_lineage:
  candidate_source_kind: complete_initial_surface_recomposition_candidate
  public_candidate_source_allowed: true
  public_candidate_source_forbidden: false
  public_display_allowed_by_boundary: true
  public_surface_role: public_observation_candidate
  surface_requirement_family: labelled_two_stage
  two_stage_required: true
  complete_initial_surface_recomposition_used: true
  labelled_two_stage_surface_recomposition_used: false
  normal_observation_rebuild_used: false
  gate_recovery_material_surface_used_as_public_body: false
  diagnostic_recovery_surface_used_as_public_body: false
  raw_input_included: false
  candidate_body_included: false
  comment_text_body_included: false
  display_gate_relaxed: false
  runtime_surface_gate_relaxed: false
  visible_surface_gate_relaxed: false
  grounding_gate_relaxed: false
  template_gate_relaxed: false
  safety_gate_relaxed: false
complete_initial_surface_recomposition_summary:
  candidate_source_kind: complete_initial_surface_recomposition_candidate
  source_unavailable_recovered: true
  case_specific_route_used: false
  gate_recovery_material_surface_used: false
  plain_surface_allowed: false
  raw_input_included: false
  comment_text_body_included: false
connection_visibility:
  connection_status: blocked_feature_flag
  pre_connection_stop: true
  pre_connection_stop_stage: flag
  pre_connection_reasons:
    - default_limited_composer_feature_disabled
    - feature_flag_disabled
  blocked_before_composer: true
  composer_connection_attempted: false
  composer_generation_attempted: false
  composer_candidate_status: generated
  composer_model: complete_initial_surface_recomposition_v1
  actual_composer_rejection: false
  composer_client_not_connected_present: false
```

### 4.3 判断

```text
classification: stale_contract_expectation
secondary_classification: requires_true_unavailable_fixture
implementation_action: none_in_step6
test_action: later_split_current_default_recovery_and_true_unavailable_contract
```

判断理由:

```text
旧testは「composerなし / feature flag disabled は必ず unavailable / comment_text empty」と見ている。
しかし現在の実装では、このfixtureは true infrastructure error ではなく、source-unavailable recovery laneとして complete_initial_surface_recomposition_candidate へ復旧している。

public metaはbody-freeで、Gate Recovery material surfaceやdiagnostic recovery surfaceをpublic本文へ昇格していない。
また、case_specific_route_used も false である。
```

このため、B2も現時点では実装修正対象ではない。  
ただし、B2は `pre_connection_stop: true` を含むため、後続Stepで次の2契約へ分割する必要がある。

```text
1. current default / feature-flag-disabled path が safe recovery surface として passed になり得ることを確認する契約。
2. true infrastructure / true unavailable は unavailable かつ input_feedback absent になることを確認する契約。
```

---

## 5. Red B分類後のledger

```yaml
red_b_classification:
  B1:
    red_id: P0P1-ARRIVAL-RED-B1-001
    final_classification_step6: stale_contract_expectation
    implementation_regression: false
    fixture_ambiguous_after_step6: false
    reason:
      - unsupported generated body is not exposed in public comment_text
      - unsupported generated body is not exposed in public meta
      - public candidate source is allowed
      - labelled_two_stage_surface_recomposition_candidate is used
      - body-free public boundary is preserved
    later_action:
      - update display contract expectation from always rejected to no unsupported body exposure
      - keep non-passed text exposure low-level blocker contract

  B2:
    red_id: P0P1-ARRIVAL-RED-B2-001
    final_classification_step6: stale_contract_expectation
    secondary_classification: requires_true_unavailable_fixture
    implementation_regression: false
    fixture_ambiguous_after_step6: false
    reason:
      - current fixture is recovered as complete_initial_surface_recomposition_candidate
      - public candidate source is allowed
      - source_unavailable_recovered is true
      - case_specific_route_used is false
      - body-free public boundary is preserved
      - no gate recovery material surface is used as public body
      - no diagnostic recovery surface is used as public body
    later_action:
      - split current default recovery expectation from true unavailable fail-closed expectation
      - add or identify true infrastructure / true unavailable fixture
```

---

## 6. 今回変更したもの

```text
新規:
- docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_RedBClassification_Step6_20260608.md
```

コード本体、test source、RN、API route、DB write path、public response keyは変更していない。

---

## 7. 未変更境界

```text
- services/ai_inference/emlis_ai_public_feedback_meta.py
- services/ai_inference/emotion_submit_service.py
- services/ai_inference/emlis_ai_product_surface_validation.py
- tests/test_emlis_ai_public_feedback_meta.py
- tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py
- tests/test_emlis_ai_product_surface_validation_p3.py
- tests/test_emlis_ai_display_contract.py
- RN production UI
- RN表示条件
- RN表示名 `Emlisの観測`
- /emotion/submit route
- public response top-level key
- DB write path
- fixed fallback commentText
- case専用route / cue / surface
```

---

## 8. 確認済み / 未確認 / 書かれていない / 推測禁止

### 確認済み

```text
- GitHub接続はしていない。
- 受領zip内にStep 0〜5の成果物が入っている。
- Step 0〜5の該当ファイルは、前回提出zip内の同名ファイルと一致した。
- Display contractは 3 passed / 2 failed。
- Red Aはgreenのまま。
- Red B1は stale_contract_expectation と分類した。
- Red B2は stale_contract_expectation + requires_true_unavailable_fixture と分類した。
- B1/B2とも、public metaのbody-free boundaryは維持されている。
- B1/B2とも、Gate Recovery material surface / diagnostic recovery surfaceはpublic本文に使われていない。
- B1/B2とも、public candidate sourceはallowedである。
- 今回、コード本体・test source・RN・API route・DB write path・public response keyは変更していない。
```

### 未確認

```text
- 全backend suite完全green。
- RN contractの今回zip基準での再実行。
- TwoStage E2Eの今回zip基準での再実行。
- true infrastructure / true unavailable fixtureの追加後green。
- Red B1/B2 test期待値更新後の display contract 5 passed。
```

### 書かれていない

```text
- B1/B2の旧期待値を、このStep 6で即更新するとは書かれていない。
- true unavailable / infrastructure fail-closed testを、このStep 6で追加するとは書かれていない。
- RN表示条件を変更するとは書かれていない。
- public response keyを増やすとは書かれていない。
```

### 推測禁止

```text
- B1/B2がgreenではない状態を、完了扱いしない。
- stale_contract_expectation分類を、fail-closed境界の撤回として読まない。
- source-unavailable recoveryを、true infrastructure errorの正常化として読まない。
- public candidate allowedを、商品品質合格やrelease可として読まない。
- fixture greenをCocolon商品価値合格として扱わない。
```

---

## 9. 次Stepへの接続

次に進むなら、設計書どおりStep 7へ進む。

```text
Step 7:
  true unavailable / true safety の fail-closed regression を追加または確認する。
```

ただし、Step 7へ進む前提は、今回の分類を崩さないこと。

```text
B1:
  旧rejected固定ではなく、unsupported body non-exposure契約へ更新する対象。

B2:
  current default recovery契約と true unavailable fail-closed契約へ分割する対象。
```

華恋の判断として、Step 6はここで止める。  
Red B1/B2は「赤を放置」ではなく、「旧期待値の意味が現在思想に合っていない赤」として分類できた。  
次に必要なのは、表示を増やすことではなく、true unavailable / safety / infrastructure のfail-closed境界を別testで守った上で、古いDisplay contractを現在のCocolon思想へ更新することである。
