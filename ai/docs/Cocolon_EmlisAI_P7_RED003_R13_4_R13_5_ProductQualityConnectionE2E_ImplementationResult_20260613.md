# Cocolon / EmlisAI P7-RED-003 R13-4 / R13-5 実装結果メモ

作成日: 2026-06-13 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: Cocolon / EmlisAI / P7 Product Quality Runner / P7-RED-003 / Product Quality Connection E2E  
実施範囲: R13-4 Product Quality Connection E2E更新 / R13-5 default pytest timeout解消確認  
GitHub接続確認: 不要（Mash様指定により未実施）  
DB変更: なし  
RN変更: なし  
API route / request key / public response top-level key変更: なし  
release_allowed: false維持  
p7_complete: false維持  
p8_start_allowed: false維持  

---

## 0. 結論

今回の実装では、設計書のR13-4 / R13-5に限定して、Product Quality Connection E2Eのbody-free検査を旧式の巨大JSON substring assertionから、R13-2/R13-3で追加済みの構造化body-free leak guardへ接続した。

変更後、次を確認した。

```text
timeout 30s pytest -q --tb=short tests/test_emlis_ai_complete_product_quality_connection_e2e.py
=> 1 passed

pytest -q --tb=short tests/test_emlis_ai_complete_product_quality_connection_e2e.py
=> 1 passed
```

これにより、R13-5の範囲では、default pytest timeoutは解消した。

ただし、本作業ではP7-RED-003をまだclosedにしていない。  
RED-003のtimeout isolation / red closure classification / validation matrix / release handoff更新はR13-6以降に残す。  
P7-HOLD-001〜004も未解消のままであるため、p7_complete / p8_start_allowed / release_allowed はすべてfalse維持とする。

---

## 1. R13-0〜R13-3 実装確認

最新ローカルzip内で、R13-0〜R13-3までの成果物が入っていることを確認した。

```text
services/ai_inference/emlis_ai_p7_body_free_leak_guard.py
tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py
tests/test_emlis_ai_p7_body_free_leak_guard_20260613.py
docs/Cocolon_EmlisAI_P7_RED003_R13_0_R13_1_BaselineAndBodyFreeContract_ImplementationResult_20260613.md
docs/Cocolon_EmlisAI_P7_RED003_R13_2_R13_3_BodyFreeLeakGuardHelper_ImplementationResult_20260613.md
```

確認実行:

```text
PYTHONPATH=services/ai_inference pytest -q \
  tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py \
  tests/test_emlis_ai_p7_body_free_leak_guard_20260613.py

=> 17 passed
```

---

## 2. R13-4 実装内容

変更ファイル:

```text
tests/test_emlis_ai_complete_product_quality_connection_e2e.py
```

変更前は、scorecard全体を `json.dumps(..., sort_keys=True)` で巨大文字列化し、次のsubstring assertionでraw leakを検査していた。

```text
_SAMPLE_MEMO not in serialized
memo_action not in serialized
current_input not in serialized
source_text not in serialized
```

このうち `current_input` は、raw current_input key/bodyではなく、rubric説明文のsafe vocabularyに含まれるため、global substring禁止では過広だった。

変更後は、次のR13 body-free helperへ置き換えた。

```text
build_p7_product_quality_connection_scorecard_body_free_contract()
assert_p7_body_free_no_payload_leak(...)
```

runtime検査で渡すraw valueは、helperのmatching用途に限定し、violation / exception / result mdへraw value本文を出さない契約を維持した。

検査対象は次である。

```text
- current_input dict key: RED
- raw current input body: RED
- current input id: RED
- memo_action key: RED
- source_text key: RED
- comment_text / candidate_body / surface_body key: RED
- forbidden true flag: RED
- rubric safe current_input vocabulary: path + exact value限定でSAFE
```

---

## 3. R13-5 default pytest timeout解消確認

実行結果:

```text
PYTHONPATH=services/ai_inference timeout 30s pytest -q --tb=short \
  tests/test_emlis_ai_complete_product_quality_connection_e2e.py

=> 1 passed
```

```text
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_complete_product_quality_connection_e2e.py

=> 1 passed
```

読み:

```text
- Product Quality Connection E2Eは、通常pytestでtimeoutせず結果を返す状態になった。
- R13-5の範囲では、旧 `current_input` substring assertion failureに伴うdefault pytest timeoutは解消した。
- ただし、P7-RED-003 closedの台帳反映はまだ実施していない。
```

---

## 4. 追加確認

R13-4/R13-5後に、関連subsetを確認した。

```text
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py \
  tests/test_emlis_ai_p7_body_free_leak_guard_20260613.py \
  tests/test_emlis_ai_complete_product_quality_connection_e2e.py \
  tests/test_emlis_ai_p7_connection_e2e_timeout_isolation_20260613.py \
  tests/test_emlis_ai_p7_red_closure_classification_matrix_20260613.py \
  tests/test_emlis_ai_p7_r11_release_validation_final_alignment_20260613.py

=> 28 passed
```

補足:

```text
- 実行環境のPython startupでartifact_toolのspreadsheet warmup warningがstderrに出ることがあった。
- ただしpytestのexit statusは0で、対象test自体はgreen。
- full backend suiteは未実行。
```

---

## 5. 変更していないもの

```text
- RN
- API route
- request key
- public response top-level key
- DB schema / DB write path
- EmlisAI visible surface generation
- release handoff
- validation matrix
- red closure classification
- timeout isolation material
```

今回、P7-RED-003をclosedへ更新する処理は入れていない。  
R13-6以降で、timeout isolation / red closure classification / validation matrix / release handoffを、今回の実測結果に合わせて更新する。

---

## 6. 確認済み / 未確認 / 書かれていない / 推測禁止 / 次に実行すべきこと

### 確認済み

```text
- R13-0〜R13-3の実装ファイルは最新zip内に入っている。
- R13 body-free contract/helper/unit testはgreen。
- Product Quality Connection E2Eは、構造化body-free leak guardへ置換済み。
- Product Quality Connection E2Eは、timeout 30s wrapperありでもなしでも1 passed。
- 関連subsetは28 passed。
- RN / API / DB / public response shapeは変更していない。
```

### 未確認

```text
- full backend suite green。
- 実機submit / modal読感。
- P5 human QA。
- R13-6以降のRED-003 closed台帳整合。
- P7 validation matrix / release handoffへのRED-003結果反映。
```

### 書かれていない

```text
- R13-4/R13-5だけでP7 completeにしてよい根拠はない。
- R13-4/R13-5だけでP8へ進んでよい根拠はない。
- R13-4/R13-5だけでrelease_allowedをtrueにしてよい根拠はない。
```

### 推測禁止

```text
- E2Eがgreenになったことを、P7 complete / 商品品質合格 / release readyへ変換しない。
- body-free marker falseだけでraw body検査完了と扱わない。
- RED-003 closed台帳更新前にclosed扱いしない。
- P7-HOLD-001〜004を今回の作業で閉じない。
```

### 次に実行すべきこと

```text
R13-6:
  P7-RED-003 timeout isolation / observationを、今回のE2E pass結果に合わせて更新する。

R13-7以降:
  red closure classification / validation matrix / release handoffへ反映する。
  ただしP7-HOLD-001〜004が残るため、p7_complete=false / p8_start_allowed=false / release_allowed=falseを維持する。
```
