# Cocolon / EmlisAI P0-P1 Public Input Feedback Arrival Contract Repair Red Ledger Step0

作成日: 2026-06-08 JST  
作業者: 華恋  
作業範囲: Step 0 baseline固定 / Step 1 focused red test追加  
対象: `/emotion/submit` public `input_feedback` arrival / `should_include_public_input_feedback` / `visible_surface_acceptance_gate`  
コード本体変更: なし  
RN変更: なし  
API route変更: なし  
DB write path変更: なし  
public response key変更: なし  

---

## 0. 結論

Step 0 の baseline は次で固定した。

```text
tests/test_emlis_ai_display_contract.py:
  2 passed / 3 failed
```

Step 1 では、Red A を E2E だけに依存させず、`should_include_public_input_feedback()` の policy 単体で固定する focused red test を追加した。

追加した focused test の現在結果は次である。

```text
tests/test_emlis_ai_public_feedback_meta.py::test_should_include_public_input_feedback_allows_visible_surface_yellow_warn
  FAILED

tests/test_emlis_ai_public_feedback_meta.py::test_should_include_public_input_feedback_blocks_visible_surface_repair_required
  PASSED

tests/test_emlis_ai_public_feedback_meta.py::test_should_include_public_input_feedback_blocks_visible_surface_passed_false_without_warn
  PASSED
```

このため、次Stepで直す対象は `visible_surface_acceptance_gate` の public inclusion policy である。

---

## 1. 実行baseline

### 1.1 display contract baseline

実行意図:

```text
作業前に Display Contract の既知赤を固定する。
```

実行コマンド:

```bash
cd mashos-api/ai
PYTHONPATH=services/ai_inference pytest -q -p no:ddtrace --assert=plain --tb=short tests/test_emlis_ai_display_contract.py -vv
```

ローカル実行注記:

```text
このsandboxでは pytest の ddtrace plugin が大きい失敗payloadの出力後に停止しやすかったため、
contract判定そのものに影響しない範囲で `-p no:ddtrace --assert=plain --tb=short` を付与した。
```

結果:

```text
collected 5 items

PASSED tests/test_emlis_ai_display_contract.py::test_step10_e2e_contract_marks_non_passed_text_exposure_as_blocker
PASSED tests/test_emlis_ai_display_contract.py::test_step10_e2e_passed_candidate_exposes_comment_text_only_after_display_gate
FAILED tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized
FAILED tests/test_emlis_ai_display_contract.py::test_step10_e2e_rejected_candidate_never_exposes_generated_body
FAILED tests/test_emlis_ai_display_contract.py::test_step10_e2e_unavailable_pre_connection_never_exposes_comment_text

3 failed, 2 passed
```

---

## 2. Red Ledger

## Red A

```yaml
red_id: P0P1-ARRIVAL-RED-A-001
test_name: tests/test_emlis_ai_display_contract.py::test_phase5_passed_candidate_keeps_public_meta_sanitized
expected:
  input_feedback_payload_present: true
  public_meta_observation_status: passed
  reply_comment_text_present: true
actual:
  input_feedback_payload_present: false
  should_include_public_input_feedback: false
  public_meta_observation_status: passed
  reply_comment_text_present: true
  reply_comment_text_equals_scoped_fixture: true
gate_summary:
  display_trace:
    passed: true
    comment_text_present: true
  step10:
    observation_status: passed
    comment_text_present: true
    display_gate_passed: true
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
classification_before_fix: implementation_contract_misalignment
implementation_action: Step2で visible_surface yellow/warn の public inclusion policy をDisplay Gate側の意味論へ揃える
test_action: Step1で focused red test を追加済み
```

読み:

```text
comment_text は生成済みで、Display Contract / public_meta 上は passed。
しかし public inclusion 側だけが visible_surface_acceptance_gate.passed=false を terminal blocker として読み、
input_feedback_payload が None になっている。
```

---

## Red B1

```yaml
red_id: P0P1-ARRIVAL-RED-B1-001
test_name: tests/test_emlis_ai_display_contract.py::test_step10_e2e_rejected_candidate_never_exposes_generated_body
expected:
  step10_observation_status: rejected
  reply_comment_text_present: false
actual:
  step10_observation_status: passed
  reply_comment_text_present: true
  unsupported_text_exposed_in_comment_text: false
  public_meta_observation_status: passed
  should_include_public_input_feedback: false
  visible_surface_acceptance_gate:
    evaluated: true
    passed: false
    classification: yellow
    action: warn
classification_before_fix: fixture_ambiguous
implementation_action: Step6以降で stale_contract_expectation / implementation_regression を分類する
test_action: Step0では更新しない
```

読み:

```text
元unsupported bodyは comment_text へは露出していない。
ただし、旧期待の rejected と現在の passed の意味差は、Step1範囲では確定しない。
本件は Step6 以降の Red B分類対象として保持する。
```

---

## Red B2

```yaml
red_id: P0P1-ARRIVAL-RED-B2-001
test_name: tests/test_emlis_ai_display_contract.py::test_step10_e2e_unavailable_pre_connection_never_exposes_comment_text
expected:
  step10_observation_status: unavailable
  reply_comment_text_present: false
actual:
  step10_observation_status: passed
  reply_comment_text_present: true
  public_meta_observation_status: passed
  should_include_public_input_feedback: false
  visible_surface_acceptance_gate:
    evaluated: true
    passed: false
    classification: yellow
    action: warn
classification_before_fix: fixture_ambiguous
implementation_action: Step6以降で stale_contract_expectation / implementation_regression / true_unavailable_fixture_need を分類する
test_action: Step0では更新しない
```

読み:

```text
no composer/default path が現在思想では safe recovery surface として passed になり得るか、
true unavailable まで passed にしているregressionかは Step1範囲では確定しない。
本件は Step6 以降の Red B分類対象として保持する。
```

---

## 3. Step 1 focused red test

追加ファイル:

```text
tests/test_emlis_ai_public_feedback_meta.py
```

追加した契約:

```text
1. visible_surface_acceptance_gate が classification=yellow / action=warn の場合、
   public inclusion の terminal blocker として扱わない。

2. classification=repair_required / action=rerender_surface は引き続き block する。

3. passed=false かつ action が warn ではない場合は、fail-closedで block する。
```

追加test結果:

```text
1 failed / 2 passed
```

失敗しているtest:

```text
test_should_include_public_input_feedback_allows_visible_surface_yellow_warn
```

この失敗は意図通りの Red A focused red である。

---

## 4. 変更していない境界

```text
- RN production UI は変更していない。
- RN表示タイトル `Emlisの観測` は変更していない。
- RN表示条件は変更していない。
- `/emotion/submit` route は変更していない。
- public response top-level key は変更していない。
- DB physical schema / write path は変更していない。
- implementation helper は変更していない。
- fixed fallback commentText は追加していない。
- case専用route / cue / surface は追加していない。
```

---

## 5. 次Stepへの接続

次は Step 2 として、`emlis_ai_public_feedback_meta.py` の `_visible_surface_acceptance_gate_blocks_public_feedback()` を修正する。

ただし修正対象は `yellow / warn` の public inclusion 意味論だけであり、次は引き続き block のまま維持する。

```text
classification=repair_required
classification=red
action=rerender_surface
action=reroute_low_information
action=block
action=fail_closed
passed=false AND action != warn
```

Cocolonとしての意味:

```text
読めていて safe で、Display Gate が passed として扱った本文を、public inclusion側の別解釈で沈黙にしない。
ただし、読めていないもの・危ないもの・壊れているもの・漏れているものを、読めたふりで出さない。
```
