# Cocolon / EmlisAI P0-P1 Public Input Feedback Arrival Contract Repair Step 10 既存green回帰確認

作成日: 2026-06-08 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: EmlisAI / `/emotion/submit` / `input_feedback` / `Emlisの観測` / public visibility reliability  
作業範囲: Step 10: 既存greenの回帰確認  
GitHub接続確認: なし（Mash様指定によりローカル作業）

---

## 0. 結論

Step 0〜9の実装内容が受領zipに反映されていることを確認したうえで、Step 10の既存green回帰確認を行った。

Step 10で必要になった修正は、production codeではなく、既存testのsanitizer assertionの更新のみ。

修正対象:

```text
mashos-api/ai/tests/test_emlis_ai_user_label_connection_e2e_contract.py
```

新規記録:

```text
mashos-api/ai/docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_Step10_ExistingGreenRegression_20260608.md
```

---

## 1. Step 0〜9反映確認

受領zip:

```text
/mnt/data/mashos-api_10(29).zip
```

前回までの提出zipから抽出した最新差分10ファイルと、受領zip内の同一パスをsha256で比較した。

結果:

```text
expected latest files: 10
ok: 10
missing: 0
mismatch: 0
```

確認済みファイル:

```text
mashos-api/ai/docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_RedLedger_Step0_20260608.md
mashos-api/ai/docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_Step5_RedA_E2EGreen_20260608.md
mashos-api/ai/docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_RedBClassification_Step6_20260608.md
mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py
mashos-api/ai/services/ai_inference/emotion_submit_service.py
mashos-api/ai/services/ai_inference/emlis_ai_product_surface_validation.py
mashos-api/ai/tests/test_emlis_ai_public_feedback_meta.py
mashos-api/ai/tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py
mashos-api/ai/tests/test_emlis_ai_product_surface_validation_p3.py
mashos-api/ai/tests/test_emlis_ai_display_contract.py
```

---

## 2. Step 10で見つかった回帰

User Label Connection / Product Read Feel subsetで、次のtestがStep 8追加のbody-free boundary markerと衝突していた。

```text
tests/test_emlis_ai_user_label_connection_e2e_contract.py::test_user_label_connection_phase1_public_meta_sanitizer_does_not_expose_raw_text_or_comment_body
```

衝突内容:

```text
旧assert:
  dumped に "candidate_body" という文字列が一切含まれないことを要求していた。

Step 8以降のpublic meta:
  public_feedback_meta_boundary.candidate_body_included = false
  を明示的に持つ。
```

つまり、raw candidate body本文は漏れていないが、body-freeであることを示す安全なboundary flag名に `candidate_body` というsubstringが含まれていた。

これは実装修正対象ではなく、test contractの期待更新対象と判断した。

---

## 3. 修正内容

対象:

```text
mashos-api/ai/tests/test_emlis_ai_user_label_connection_e2e_contract.py
```

修正前:

```python
for fragment in (
    ...,
    "candidate_body",
    "candidate_comment_text",
):
    assert fragment not in dumped
```

修正後:

```python
for fragment in (
    ...,
    "candidate_comment_text",
):
    assert fragment not in dumped

assert '"candidate_body":' not in dumped
boundary = public_meta["public_feedback_meta_boundary"]
assert boundary["raw_input_included"] is False
assert boundary["comment_text_body_included"] is False
assert boundary["candidate_body_included"] is False
assert boundary["internal_meta_returned"] is False
```

意味:

```text
- raw candidate body keyそのものは引き続き禁止する。
- candidate_comment_textも引き続き禁止する。
- raw input / comment text body / candidate body / internal metaがpublic metaへ出ていないことをboolean markerで確認する。
- Step 8で追加した candidate_body_included=false は、body leakではなくbody-free boundary markerとして許可する。
```

---

## 4. 回帰確認結果

### 4.1 RN contract

実行:

```bash
cd /tmp/cocoRN/Cocolon
npm run test:rn-screens --silent
```

結果:

```text
36 passed / 0 failed
```

### 4.2 API contract

実行:

```bash
cd /tmp/cocoA/mashos-api/ai
PYTHONPATH=services/ai_inference pytest -q tests/contract/test_emlis_ai_contracts.py --tb=short
```

結果:

```text
4 passed / 3 warnings
```

### 4.3 TwoStage emotion submit E2E

実行:

```bash
cd /tmp/cocoA/mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q -p pytest_asyncio.plugin \
  tests/test_emotion_submit_two_stage_reception_e2e.py --tb=short
```

結果:

```text
6 passed / 1 warning
```

### 4.4 Public Recovery / D / limited grounding subset

実行:

```bash
cd /tmp/cocoA/mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q -p pytest_asyncio.plugin \
  tests/test_emlis_ai_public_observation_recovery_acceptance_p0.py \
  tests/test_emlis_ai_public_surface_requirement_p1.py \
  tests/test_emlis_ai_product_surface_validation_p3.py \
  tests/test_emlis_ai_public_meta_product_quality_lineage_p8.py \
  tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py \
  tests/test_emotion_submit_phase19_real_device_abcd_public_feedback_e2e.py \
  tests/test_emlis_ai_d_source_unavailable_normal_observation_recovery.py \
  tests/test_emlis_ai_complete_initial_surface_recomposition_p5.py \
  tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py \
  tests/test_emlis_ai_limited_grounding_reception_surface_p4.py \
  --tb=short
```

結果:

```text
53 passed / 1 warning
```

注記:

```text
設計書時点の期待は45 passedだったが、Step 2〜9で追加されたproduct/public周辺testが同subset内に含まれるため、現行zipでは53 passedとなった。
```

### 4.5 User Label Connection / Product Read Feel subset

実行:

```bash
cd /tmp/cocoA/mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q -p pytest_asyncio.plugin \
  tests/test_emlis_ai_user_label_connection_material.py \
  tests/test_emlis_ai_user_label_connection_candidate.py \
  tests/test_emlis_ai_user_label_connection_gate.py \
  tests/test_emlis_ai_user_label_connection_surface.py \
  tests/test_emlis_ai_user_label_connection_public_boundary.py \
  tests/test_emlis_ai_user_label_connection_e2e_contract.py \
  tests/test_emlis_ai_product_readfeel_rubric.py \
  tests/test_emlis_ai_product_readfeel_scorecard.py \
  tests/test_emlis_ai_product_readfeel_phase11_long_run_product_gate.py \
  tests/test_emlis_ai_user_label_connection_product_quality_qa.py \
  tests/test_emlis_ai_user_label_connection_derived_model_cache.py \
  --tb=short
```

結果:

```text
108 passed / 1 warning
```

### 4.6 Focused suite

実行:

```bash
cd /tmp/cocoA/mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q -p pytest_asyncio.plugin \
  tests/test_emlis_ai_public_feedback_meta.py \
  tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py \
  tests/test_emlis_ai_product_surface_validation_p3.py \
  tests/test_emlis_ai_display_contract.py \
  --tb=short
```

結果:

```text
51 passed / 1 warning
```

### 4.7 Step 10修正test単体

実行:

```bash
cd /tmp/cocoA/mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q -p pytest_asyncio.plugin \
  tests/test_emlis_ai_user_label_connection_e2e_contract.py::test_user_label_connection_phase1_public_meta_sanitizer_does_not_expose_raw_text_or_comment_body \
  --tb=short
```

結果:

```text
1 passed / 1 warning
```

---

## 5. 変更していないもの

```text
- services/ai_inference/emlis_ai_public_feedback_meta.py
- services/ai_inference/emotion_submit_service.py
- services/ai_inference/emlis_ai_product_surface_validation.py
- RN production UI
- RN表示条件
- RN表示名 `Emlisの観測`
- /emotion/submit route
- public response top-level key
- DB write path
```

---

## 6. 華恋の判断

Step 10は完了。

今回の修正は、本文漏れを許すものではない。むしろ、Step 8で明示したbody-free境界を、User Label Connection側の既存sanitizer testにも正しく読ませる修正である。

Cocolonとして守るべき線は維持されている。

```text
- 読めたものは public input_feedback として届く。
- 読めていないもの・壊れているもの・安全境界のものはfail-closedする。
- 本文は input_feedback.comment_text にだけ置く。
- public metaはbody-freeのままにする。
- 履歴線・User Label Connectionもraw textを出さない。
```
