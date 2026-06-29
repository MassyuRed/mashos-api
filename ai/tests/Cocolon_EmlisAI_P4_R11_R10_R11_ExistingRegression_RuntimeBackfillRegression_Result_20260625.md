# Cocolon / EmlisAI P4-R11 R10/R11 Regression Result

作成日: 2026-06-25 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: Cocolon / EmlisAI / Product Read Feel / P4-R11 Residual Family Current-only Surface Audit  
対象step: R11-10 P4 Existing Regression / R11-11 H/I/J Runtime Backfill Regression  
基準snapshot: `mashos-api_6(77).zip`  
GitHub接続確認: Mash指定により不要。未実施。  

---

## 0. 結論

今回、現snapshot内にP4-R11 R11-0〜R11-9の実装・test群が入っていることを確認したうえで、次を実行した。

```text
R11-10: P4 Existing Regression
R11-11: H/I/J Runtime Backfill Regression
```

結果:

```text
R11-0〜R11-9 target split:
  83 passed

R11-10 P4 Existing Regression split:
  60 passed

R11-11 H/I/J Runtime Backfill Regression split:
  8 passed / warnings only

compileall:
  pass
```

今回の差分は、実装本体・runtime・API・DB・RNを変更しない。  
R11-10/R11-11は、既存測定器とH/I/J backfill regressionの確認段階であり、修正実装段階ではない。

---

## 1. 事前確認: R11-0〜R11-9の現snapshot内存在

### 1.1 確認したR11 service module

```text
services/ai_inference/emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit.py
services/ai_inference/emlis_ai_product_readfeel_p4_r11_surface_specificity_role_verdict_audit.py
services/ai_inference/emlis_ai_product_readfeel_p4_r11_summary_decision_handoff.py
```

### 1.2 確認したR11 test群

```text
tests/test_emlis_ai_product_readfeel_p4_r11_scope_matrix_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_body_free_schema_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_case_ref_selection_coverage_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_material_route_audit_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_surface_path_audit_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_surface_specificity_role_audit_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_summary_decision_handoff_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_decision_handoff_20260624.py
tests/test_emlis_ai_product_readfeel_p4_r11_targeted_tests_20260624.py
```

### 1.3 R11-0〜R11-9 target確認

Command 1:

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q \
 tests/test_emlis_ai_product_readfeel_p4_r11_scope_matrix_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_body_free_schema_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_case_ref_selection_coverage_20260624.py \
 --tb=short
```

Result:

```text
63 passed in 3.56s
```

Command 2:

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q \
 tests/test_emlis_ai_product_readfeel_p4_r11_material_route_audit_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_surface_path_audit_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_surface_specificity_role_audit_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_summary_decision_handoff_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_decision_handoff_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_targeted_tests_20260624.py \
 --tb=short
```

Result:

```text
20 passed in 20.48s
```

Collect-only:

```text
83 tests collected in 3.73s
```

---

## 2. R11-10: P4 Existing Regression

### 2.1 目的

P4-R11追加で、既存P4測定器を壊していないことを確認する。

### 2.2 実行方針

R11-10設計上の対象60件を、環境の一括timeoutを避けるため4分割で実行した。  
一括実行はこの環境では途中timeoutしたため、一括greenとは扱わない。  
ただし、設計書上の対象test fileは全て実行し、対象60件は全件greenを確認した。

### 2.3 実行結果

#### Chunk 1

Command:

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q \
 tests/test_emlis_ai_product_readfeel_p4_connection_freeze_20260610.py \
 tests/test_emlis_ai_product_readfeel_p4_target_case_selection_20260610.py \
 tests/test_emlis_ai_product_readfeel_p4_material_audit_20260610.py \
 --tb=short
```

Result:

```text
16 passed in 6.09s
```

#### Chunk 2

Command:

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q \
 tests/test_emlis_ai_product_readfeel_p4_surface_requirement_boundary_20260610.py \
 tests/test_emlis_ai_product_readfeel_p4_family_tuning_policy_20260610.py \
 tests/test_emlis_ai_product_readfeel_p4_surface_signature_audit_20260610.py \
 --tb=short
```

Result:

```text
19 passed in 9.53s
```

#### Chunk 3

Command:

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q \
 tests/test_emlis_ai_product_readfeel_p4_daily_unpleasant_family_tuning_20260610.py \
 tests/test_emlis_ai_product_readfeel_p4_structure_question_family_tuning_20260610.py \
 tests/test_emlis_ai_product_readfeel_p4_self_denial_yellow_review_20260610.py \
 --tb=short
```

Result:

```text
11 passed in 17.27s
```

#### Chunk 4

Command:

```bash
cd mashos-api/ai
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q \
 tests/test_emlis_ai_product_readfeel_p4_ratings_review_20260610.py \
 tests/test_emlis_ai_product_readfeel_p4_regression_handoff_20260610.py \
 --tb=short
```

Result:

```text
14 passed in 9.41s
```

### 2.4 R11-10判定

```text
R11-10 target total:
  60 passed

判定:
  P4-0〜P4-10の既存測定器は、P4-R11追加後も保持されている。
```

---

## 3. R11-11: H/I/J Runtime Backfill Regression

### 3.1 目的

R10で閉じたH future-direction surface redを再発させていないことを確認する。

### 3.2 実行方針

H/I/J runtime backfill regressionにはasync testが含まれる。  
そのため、R10 result memoと同じく、plugin autoloadを抑えたうえで `pytest_asyncio.plugin` を明示loadした。  
また、この環境では `asyncio-mode=strict` のまま複数async testを実行するとprocess終了時にtimeoutする場合があったため、`--asyncio-mode=auto` を明示した。

これはruntime / test code / API contractを変更するものではない。  
実行環境側のpytest/asyncio runner指定である。

### 3.3 実行結果

#### R0/R1 surface audit

Command:

```bash
cd mashos-api/ai
env PYTHONPATH=services/ai_inference PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  pytest -q -p pytest_asyncio.plugin --asyncio-mode=auto \
  tests/test_emlis_ai_p4_runtime_backfill_hij_future_direction_surface_audit_20260624.py \
  --tb=short
```

Result:

```text
2 passed / 1 warning in 17.27s
```

#### R2/R3 repair + R4 generic surface guard

Command:

```bash
cd mashos-api/ai
env PYTHONPATH=services/ai_inference PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  pytest -q -p pytest_asyncio.plugin --asyncio-mode=auto \
  tests/test_emlis_ai_p4_runtime_backfill_hij_future_direction_surface_repair_20260624.py \
  tests/test_emlis_ai_p4_runtime_backfill_hij_future_direction_generic_surface_guard_20260624.py \
  --tb=short
```

Result:

```text
3 passed / 1 warning in 18.93s
```

#### H/I/J submit E2E

Command:

```bash
cd mashos-api/ai
env PYTHONPATH=services/ai_inference PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  pytest -q -p pytest_asyncio.plugin --asyncio-mode=auto \
  tests/test_emlis_ai_hij_reception_required_regression_p8.py \
  --tb=short
```

Result:

```text
3 passed / 1 warning in 18.63s
```

Collect-only:

```text
8 tests collected in 7.85s
```

### 3.4 R11-11判定

```text
R11-11 target total:
  8 passed / warnings only

確認できたこと:
  - R0/R1 body-free red ledger / lineage auditが維持されている。
  - R2/R3 future-direction surface repairが維持されている。
  - R4 generic surface guardが維持されている。
  - H/I/J submit E2Eが維持されている。
  - H future-direction surface redを再openしていない。
```

---

## 4. compile / collect-only

### 4.1 compileall

Command:

```bash
cd mashos-api/ai
python -m compileall -q services/ai_inference \
 tests/test_emlis_ai_product_readfeel_p4_r11_scope_matrix_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_body_free_schema_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_case_ref_selection_coverage_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_material_route_audit_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_surface_path_audit_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_surface_specificity_role_audit_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_summary_decision_handoff_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_decision_handoff_20260624.py \
 tests/test_emlis_ai_product_readfeel_p4_r11_targeted_tests_20260624.py
```

Result:

```text
compileall_pass
```

---

## 5. 守った境界

今回も、次は変更していない。

```text
- runtime path
- Emlis visible output generation
- API route
- DB
- RN
- public response key
- public meta key
- Gate threshold
- json/schema実ファイル
- R54 actual review rows
- P5 human Blind QA evidence
- rating rows
- question observation rows
- P6 / P8 / release flags
```

P4-R11は、残familyのcurrent-only surface specificityをbody-freeにaudit / triageする工程であり、R11-10/R11-11はその追加が既存P4とR10 H/I/J closureを壊していないことを確認する工程として扱う。

---

## 6. 華恋の判断

今回、code修正を追加しなかった。  
理由は、R11-10/R11-11は修正実装段階ではなく、既存P4測定器とR10 H/I/J runtime backfill regressionを確認する段階だからである。

ここで無理にruntimeやhelperを触ると、P4-R11の目的である「残family auditをP5/P8/releaseへ進めず、current-only surface blocker確認に留める」という境界が濁る。  
必要だった差分は、今回の回帰結果をbody-freeに残す結果メモだけと判断した。

また、H/I/J regressionはasync testを含むため、runner指定を雑にすると、test codeやruntimeが壊れていなくても失敗またはtimeoutに見える。  
そのため、R10 result memoの実行思想に合わせ、plugin autoloadを抑えつつ、`pytest_asyncio.plugin` と `--asyncio-mode=auto` を明示した。

これはCocolon本体の仕様変更ではなく、確認を正確に行うためのtest実行境界である。

---

## 7. 未確認

```text
- full backend suite green
- full collect-only green
- RN実機modal読感
- 実機submit
- R11-12 P3 Product Read Feel Regression
- R11-13 RN Contract Regression
- R11-14 Compile / Collect-only full
- R11-15 Result Memo / Handoff finalization
- R54 actual local-only human review
- P5 actual human Blind QA evidence
- P8観測補助問い詳細設計
- release readiness
```

R11-12以降には進めていない。
