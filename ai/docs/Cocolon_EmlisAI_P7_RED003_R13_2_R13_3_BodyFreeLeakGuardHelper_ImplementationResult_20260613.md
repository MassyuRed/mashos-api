# Cocolon / EmlisAI P7-RED-003 R13-2 / R13-3 実装結果

作成日: 2026-06-13 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: P7 Product Quality Runner / P7-RED-003 / Product Quality Connection E2E / body-free leak guard  
実装範囲: R13-2 body-free leak guard helper追加、R13-3 helper単体test追加  
GitHub接続確認: 不要（Mash様指定により未実施）  
コード変更範囲: backend internal-only  
RN変更: なし  
API route / request key / public response top-level key変更: なし  
DB変更: なし  
E2E assertion置換: なし（R13-4以降）  
P7-RED-003 closed化: なし  
release_allowed: false維持  
p7_complete: false維持  
p8_start_allowed: false維持  

---

## 0. 結論

最新zip内に、R13-0 / R13-1で追加した次の3ファイルが存在することを確認した。

```text
mashos-api/ai/services/ai_inference/emlis_ai_p7_body_free_leak_guard.py
mashos-api/ai/tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py
mashos-api/ai/docs/Cocolon_EmlisAI_P7_RED003_R13_0_R13_1_BaselineAndBodyFreeContract_ImplementationResult_20260613.md
```

また、既存R13-1 contract testは次の結果だった。

```text
PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py
=> 6 passed
```

その上で、R13-2 / R13-3として、body-free leak guard helperと単体testを追加した。

今回の実装では、Product Quality Connection E2Eの既存assertionはまだ置き換えていない。  
したがって、P7-RED-003はまだclosedではない。

```text
P7-RED-003: unresolved / helper implemented / helper unit tested / E2E assertion not replaced
P7 complete: false
P8 start allowed: false
release_allowed: false
```

---

## 1. 変更したファイル

### 1.1 変更

```text
mashos-api/ai/services/ai_inference/emlis_ai_p7_body_free_leak_guard.py
```

追加した主なもの:

```text
P7BodyFreeLeakGuardError
collect_p7_body_free_leak_violations
assert_p7_body_free_no_payload_leak
```

### 1.2 新規追加

```text
mashos-api/ai/tests/test_emlis_ai_p7_body_free_leak_guard_20260613.py
mashos-api/ai/docs/Cocolon_EmlisAI_P7_RED003_R13_2_R13_3_BodyFreeLeakGuardHelper_ImplementationResult_20260613.md
```

### 1.3 変更していないもの

```text
tests/test_emlis_ai_complete_product_quality_connection_e2e.py
services/ai_inference/emlis_ai_p7_timeout_isolation.py
services/ai_inference/emlis_ai_p7_red_closure_classification.py
services/ai_inference/emlis_ai_p7_validation_matrix.py
services/ai_inference/emlis_ai_p7_release_handoff.py
Cocolon RN側
API route / request key / public response top-level key
DB schema / write path
```

---

## 2. R13-2: body-free leak guard helper追加

### 2.1 helperの責務

追加したhelperは、body-free境界を次のように構造化して検査する。

```text
1. forbidden key検査
   - dict keyとして current_input / raw_input / memo_action / source_text / comment_text / candidate_body 等が出たらviolation。

2. forbidden raw value検査
   - runtimeから渡された raw value が任意のstring value内に含まれたらviolation。
   - 戻り値・exception messageにはraw valueを含めない。

3. forbidden true flag検査
   - raw_input_included / comment_text_body_included / release_allowed 等が true ならviolation。
   - false markerは許可。

4. safe vocabulary検査
   - current_input tokenは無条件禁止にしない。
   - allowed_string_occurrencesに登録されたpath_suffix + exact_valueに一致する場合のみSAFE。
   - それ以外のcurrent_input token出現は unsafe_unregistered_string_occurrence としてviolation。

5. compact failure policy
   - violationはpath / token_ref / token_kind / violation_kindのみを返す。
   - raw values / serialized payloadは返さない。
   - exception messageもboundedにする。
```

### 2.2 追加関数

```python
collect_p7_body_free_leak_violations(
    value,
    *,
    source,
    contract=None,
    forbidden_keys=None,
    forbidden_raw_values=None,
    forbidden_true_flags=None,
    allowed_string_occurrences=None,
    max_violations=None,
)
```

戻り値はcompact violation list。  
raw runtime valuesは照合にだけ使用し、violation materialへは含めない。

```python
assert_p7_body_free_no_payload_leak(
    value,
    *,
    source,
    contract=None,
    forbidden_keys=None,
    forbidden_raw_values=None,
    forbidden_true_flags=None,
    allowed_string_occurrences=None,
    max_violations=None,
)
```

violationがあれば `P7BodyFreeLeakGuardError` をraiseする。  
error messageにはraw valueやserialized payload dumpを含めない。

---

## 3. R13-3: helper単体test追加

追加test:

```text
tests/test_emlis_ai_p7_body_free_leak_guard_20260613.py
```

固定した境界:

```text
- safe rubric vocabulary allowed
- current_input dict key rejected
- raw current input memo body rejected
- current input id rejected
- memo_action key rejected
- comment_text key rejected
- false body-free markers allowed
- true body-free marker rejected
- current_input token on unregistered path rejected
- current_input token with wrong exact value rejected
- compact error message excludes raw values and payload dump
```

---

## 4. 実行したtest

### 4.1 R13-1確認

```bash
cd mashos-api/ai
PYTHONPATH=services/ai_inference pytest -q tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py
```

結果:

```text
6 passed in 0.40s
```

### 4.2 R13-2 / R13-3 helper + contract

```bash
cd mashos-api/ai
PYTHONPATH=services/ai_inference pytest -q \
  tests/test_emlis_ai_p7_body_free_leak_guard_20260613.py \
  tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py
```

結果:

```text
17 passed in 1.51s
```

### 4.3 R13周辺最小regression

```bash
cd mashos-api/ai
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_p7_body_free_leak_guard_20260613.py \
  tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py \
  tests/test_emlis_ai_p7_connection_e2e_timeout_isolation_20260613.py \
  tests/test_emlis_ai_p7_red_closure_classification_matrix_20260613.py \
  tests/test_emlis_ai_p7_r11_release_validation_final_alignment_20260613.py
```

結果:

```text
27 passed in 2.14s
```

---

## 5. 今回まだ行っていないこと

```text
- Product Quality Connection E2Eのassertion置換
- `assert "current_input" not in serialized` の削除・構造化guard接続
- default pytest timeout解消確認
- P7-RED-003 closed化
- timeout isolation / red closure classification / validation matrix / release handoff更新
- P7 complete true化
- P8 start allowed true化
- release_allowed true化
```

---

## 6. 華恋の判断

今回の実装は、testを通すために `current_input` 検査を弱めたものではない。

Cocolonとして守るべきものは、ユーザーの入力本文・comment_text body・candidate body・raw current_input objectを測定materialへ流さないこと。  
同時に、rubric説明に必要なsafe vocabularyまでraw leak扱いして測定器を壊さないこと。

そのため今回のhelperでは、次を分けた。

```text
current_input dict key: RED
current_input raw memo / raw id: RED
current_input rubric safe vocabulary: path + exact value限定でSAFE
current_input token on unregistered path: RED
false body-free marker: SAFE
true body-free marker: RED
```

R13-2 / R13-3は完了。  
次はR13-4として、Product Quality Connection E2Eのglobal substring assertionをこのhelperへ接続する段階。

ただし、R13-4以降を行うまではP7-RED-003はclosedにしない。
