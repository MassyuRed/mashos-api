# Cocolon / EmlisAI P0-P1 Public Input Feedback Arrival Contract Repair Step5 Red A E2E Green確認

作成日: 2026-06-08 JST  
作業者: 華恋  
作業範囲: Step 5: Red A E2E display contractをgreen化する  
対象: `tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized`  
GitHub接続: なし。ローカルzipのみ確認。  
コード本体変更: なし  
test source変更: なし  
RN変更: なし  
API route変更: なし  
DB write path変更: なし  
public response key変更: なし  

---

## 0. 結論

Step 5対象の Red A E2E display contract は、受領zip内のStep 0〜4実装が反映された状態でgreenになった。

```text
tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized
  PASSED
```

今回、Red A green化のための追加コード修正は不要だった。  
理由は、Step 2〜4で揃えた `visible_surface_acceptance_gate = yellow / warn` のpublic arrival policyが、すでにRed A E2E到達条件を満たしていたためである。

---

## 1. 受領zip内の既存反映確認

受領した `mashos-api_5(57).zip` 内で、Step 0〜4の成果物が存在することを確認した。

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
```

確認したpolicy要点:

```text
- visible_surface_acceptance_gate の yellow / warn は public inclusion blocker にしない。
- repair_required / red は引き続きblock。
- rerender_surface / reroute_low_information / block / fail_closed は引き続きblock。
- passed=false かつ action != warn は引き続きblock。
- runtime / state_answer / two_stage はstrictを維持。
```

---

## 2. Step 5で確認した契約

対象testが確認している契約は次。

```text
- reply.comment_text == SCOPED_PASSING_TEXT
- input_feedback_payload is not None
- input_feedback_payload.comment_text == SCOPED_PASSING_TEXT
- input_feedback_payload.emlis_ai.observation_status == passed
- public_feedback_meta_boundary.sanitized == true
- internal_meta_returned == false
- raw_input_included == false
- comment_text_included == false
- public metaへ comment_text / composer_candidate / current_input / raw_input / text を含めない
- public meta文字列内へ SCOPED_PASSING_TEXT / PASSING_TEXT / raw input相当本文を含めない
```

このため、Step 5は単に `input_feedback` を出すだけではなく、public metaのbody-free境界を維持したままRed Aをgreenにできている。

---

## 3. 実行コマンドと結果

### 3.1 Red A exact

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference timeout 90s pytest -q -p pytest_asyncio.plugin \
  tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized \
  -vv
```

結果:

```text
collected 1 item

tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized PASSED [100%]

1 passed
```

### 3.2 Step 2〜5 focused suite

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference timeout 180s pytest -q -p pytest_asyncio.plugin \
  tests/test_emlis_ai_public_feedback_meta.py \
  tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py \
  tests/test_emlis_ai_product_surface_validation_p3.py \
  tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized \
  -vv
```

結果:

```text
41 passed / 1 warning
```

内訳:

```text
tests/test_emlis_ai_public_feedback_meta.py:
  22 passed

tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py:
  7 passed

tests/test_emlis_ai_product_surface_validation_p3.py:
  11 passed

tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized:
  1 passed
```

warning:

```text
PydanticDeprecatedSince20: Pydantic V1 style @root_validator is deprecated.
```

このwarningは今回のStep 5対象外であり、Red Aのpublic arrival契約には影響していない。

---

## 4. Full display contractの現状

Step 5対象のRed Aはgreenになった。  
一方、Display contract全体では、設計どおりRed B1/B2が残っている。

実行コマンド:

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference timeout 180s pytest -q -p pytest_asyncio.plugin \
  tests/test_emlis_ai_display_contract.py \
  -vv
```

結果:

```text
3 passed / 2 failed
```

残り:

```text
Red B1:
- tests/test_emlis_ai_display_contract.py::test_step10_e2e_rejected_candidate_never_exposes_generated_body
- expected: rejected
- actual: passed

Red B2:
- tests/test_emlis_ai_display_contract.py::test_step10_e2e_unavailable_pre_connection_never_exposes_comment_text
- expected: unavailable
- actual: passed
```

この2件はStep 5の修正対象ではなく、設計書上のStep 6で `stale_contract_expectation / implementation_regression / fixture_ambiguous` へ分類する対象として残す。

---

## 5. 今回変更したもの

```text
新規:
- docs/Cocolon_EmlisAI_P0_P1_PublicInputFeedbackArrivalContractRepair_Step5_RedA_E2EGreen_20260608.md
```

コード本体、test source、RN、API route、DB write path、public response keyは変更していない。

---

## 6. 未変更境界

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
```

---

## 7. 確認済み / 未確認 / 書かれていない / 推測禁止

### 確認済み

```text
- GitHub接続はしていない。
- 受領zip内にStep 0〜4の実装内容が入っている。
- Step 5対象Red A E2Eはgreen。
- Step 2〜5 focused suiteは 41 passed / 1 warning。
- Full display contractは 3 passed / 2 failed。
- 残り2件はRed B1/B2で、Step 6分類対象。
- 今回、コード本体・test source・RN・API route・DB write path・public response keyは変更していない。
```

### 未確認

```text
- 全backend suite完全green。
- RN contractの今回zip基準での再実行。
- TwoStage E2Eの今回zip基準での再実行。
- Red B1/B2の最終分類。
```

### 書かれていない

```text
- Step 5時点でRed B1/B2を修正する、とは書かれていない。
- Step 5でRN表示条件を変更する、とは書かれていない。
- Step 5でpublic response keyを増やす、とは書かれていない。
```

### 推測禁止

```text
- Red B1/B2を古いtest期待値と断定しない。
- Red B1/B2を実装regressionと断定しない。
- Red A greenをP1全体完了と断定しない。
```

---

## 8. 華恋の判断

Step 5は、コードを増やして直す段階ではなく、Step 2〜4で整えた到達線がRed A E2Eに届いていることを確認する段階だった。

今回の確認で、`yellow / warn` を沈黙理由にしないpolicyが、public feedback meta、submit inclusion summary、product surface validationを通って、Red Aのpublic `input_feedback` 到達までつながった。

Cocolonとして大事なのは、内部で読めたものが、入力直後のユーザーに届くこと。  
Red Aはこの出口が閉じた。  
次はRed Bの意味を誤魔化さず、旧期待が古いのか、実装が本当に危ないのかを分類する。
