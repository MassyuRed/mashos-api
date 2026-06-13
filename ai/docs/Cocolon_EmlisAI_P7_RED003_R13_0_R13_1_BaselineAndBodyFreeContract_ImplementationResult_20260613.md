# Cocolon / EmlisAI P7-RED-003 R13-0 / R13-1 実装結果

作成日: 2026-06-13 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: P7 Product Quality Runner / P7-RED-003 / Product Quality Connection E2E / body-free leak guard  
実装範囲: R13-0 Baseline freeze / no-code再現固定、R13-1 Body-free leak guard contract定義  
GitHub接続確認: 不要（Mash様指定により未実施）  
コード変更範囲: backend internal-only  
RN変更: なし  
API route / request key / public response top-level key変更: なし  
DB変更: なし  
E2E assertion置換: なし（R13-4以降）  
recursive scanner実装: なし（R13-2以降）  
release_allowed: false維持  
p7_complete: false維持  
p8_start_allowed: false維持  

---

## 0. 結論

R13-0 / R13-1として、次だけを実ファイル化した。

```text
R13-0:
  P7-RED-003の実装前baselineを再現・記録した。

R13-1:
  body-free leak guard contractを、raw key / raw value ref / forbidden true flag / safe rubric vocabulary / compact failure policyに分けて定義した。
```

今回の範囲では、Product Quality Connection E2Eの既存assertionはまだ置き換えていない。  
したがって、P7-RED-003はまだclosedではない。

```text
P7-RED-003: unresolved / baseline fixed / contract defined
P7 complete: false
P8 start allowed: false
release_allowed: false
```

---

## 1. 変更したファイル

### 1.1 新規追加

```text
mashos-api/ai/services/ai_inference/emlis_ai_p7_body_free_leak_guard.py
mashos-api/ai/tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py
mashos-api/ai/docs/Cocolon_EmlisAI_P7_RED003_R13_0_R13_1_BaselineAndBodyFreeContract_ImplementationResult_20260613.md
```

### 1.2 既存ファイル変更

```text
なし
```

---

## 2. R13-0: Baseline freeze / no-code再現固定

### 2.1 通常pytest timeout再現

実行:

```bash
cd mashos-api/ai
export PYTHONPATH=services/ai_inference
/usr/bin/timeout 10s pytest -q --tb=short tests/test_emlis_ai_complete_product_quality_connection_e2e.py
```

結果:

```text
EXIT_STATUS:124
captured output bytes: 0
```

読み:

```text
Product Quality Connection E2Eは、現行assertionのまま通常pytestでは10秒timeoutとして再現する。
この段階ではclosed扱いしない。
```

### 2.2 assertion failureとしての再現

巨大なassertion failure出力を避けるため、failure location確認は `--tb=line` で固定した。

実行:

```bash
cd mashos-api/ai
export PYTHONPATH=services/ai_inference
/usr/bin/timeout 30s pytest --assert=plain -q --tb=line tests/test_emlis_ai_complete_product_quality_connection_e2e.py
```

結果:

```text
EXIT_STATUS:1
1 failed in 13.55s
failure location:
  tests/test_emlis_ai_complete_product_quality_connection_e2e.py:99
failure kind:
  AssertionError
source line:
  assert "current_input" not in serialized
```

読み:

```text
P7-RED-003は、少なくともassertion rewriteを抑制した観測では、timeoutだけではなくline 99のcurrent_input substring assertion failureとして固定できる。
ただし、この時点ではE2E修復は行っていない。
```

### 2.3 scorecard直接走査

実行内容:

```text
render_emlis_ai_replyをE2E testと同じ環境変数・同じinput idで呼び出し、
scorecardだけをjson化してkey path / string value pathを走査した。
```

結果:

```json
{
  "serialized_len": 505347,
  "current_input.memo_sample_body_included": false,
  "memo_action_token_included": false,
  "source_text_token_included": false,
  "input_id_included": false,
  "current_input_token_included": true,
  "current_input_key_paths": [],
  "current_input_value_paths": [
    [
      "scorecard.phase2_product_readfeel_rubric.dimensions.evidence_boundary.green",
      "claims_stay_within_current_input_or_safe_known_user_fact"
    ]
  ]
}
```

読み:

```text
- dict keyとしての current_input は見つからない。
- current_input.memo sample bodyは見つからない。
- current input idは見つからない。
- memo_action / source_text tokenも見つからない。
- current_input tokenはrubric説明文のsafe vocabulary候補として1箇所だけ見つかる。
```

---

## 3. R13-1: Body-free leak guard contract定義

### 3.1 追加module

追加:

```text
services/ai_inference/emlis_ai_p7_body_free_leak_guard.py
```

定義した主なもの:

```text
P7_BODY_FREE_LEAK_GUARD_CONTRACT_SCHEMA_VERSION
P7_BODY_FREE_LEAK_GUARD_CONTRACT_STEP
P7_BODY_FREE_SCOPE_PRODUCT_QUALITY_CONNECTION_SCORECARD
P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_PATH_SUFFIX
P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE
P7BodyFreeLeakGuardContractError
build_p7_product_quality_connection_scorecard_body_free_contract
assert_p7_body_free_leak_guard_contract
```

このmoduleは、R13-1時点ではcontract definition-onlyである。

```text
scanner_implemented=false
e2e_assertion_replaced=false
```

### 3.2 contractで禁止するもの

```text
forbidden_key_names:
  current_input
  raw_input
  source_text
  memo
  memo_action
  comment_text
  candidate_body
  surface_body
  既存P7_FORBIDDEN_BODY_KEYSのbody payload key群

forbidden_raw_value_refs:
  current_input.memo
  current_input.id
  input_feedback.comment_text
  product_quality.candidate_body

forbidden_true_flags:
  raw_input_included
  comment_text_body_included
  candidate_body_included
  surface_body_included
  release_allowed
  既存P7_FORBIDDEN_TRUE_FLAGSのpublic contract mutation / release mutation flag群
```

raw value refsは、実値をcontractへ入れない。

```text
value_materialized_in_contract=false
```

### 3.3 contractで許可するsafe vocabulary

許可は1箇所に限定した。

```json
{
  "token": "current_input",
  "path_suffix": "phase2_product_readfeel_rubric.dimensions.evidence_boundary.green",
  "exact_value": "claims_stay_within_current_input_or_safe_known_user_fact",
  "reason_code": "safe_rubric_vocabulary_not_raw_payload"
}
```

読み:

```text
current_input dict key / raw object / raw body / input idはRED。
rubric説明文のpath限定safe vocabularyだけSAFE。
```

### 3.4 failure output policy

```json
{
  "include_raw_values": false,
  "include_serialized_payload": false,
  "max_reported_violations": 6,
  "max_path_length": 220
}
```

読み:

```text
R13-2以降のscanner / assertion helperで違反を返す場合も、raw bodyや巨大serialized payloadを出さない契約を先に固定した。
```

---

## 4. 実行したtest

### 4.1 R13-1 contract単体test

実行:

```bash
cd mashos-api/ai
export PYTHONPATH=services/ai_inference
pytest -q tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py
```

結果:

```text
6 passed in 0.56s
```

### 4.2 既存P7周辺regression subset

実行:

```bash
cd mashos-api/ai
export PYTHONPATH=services/ai_inference
pytest -q --tb=short \
  tests/test_emlis_ai_p7_body_free_leak_guard_contract_20260613.py \
  tests/test_emlis_ai_p7_connection_e2e_timeout_isolation_20260613.py \
  tests/test_emlis_ai_p7_red_closure_classification_matrix_20260613.py \
  tests/test_emlis_ai_p7_r11_release_validation_final_alignment_20260613.py
```

結果:

```text
16 passed in 2.16s
```

---

## 5. 変更していないcontract

```text
RN visible contract:
  変更なし。

API route / request key / public response top-level key:
  変更なし。

DB schema / DB write path:
  変更なし。

Product Quality Connection E2E assertion:
  未変更。R13-4以降で置換対象。

recursive leak scanner / assertion helper:
  未実装。R13-2以降で対象。

P7 red classification / validation matrix / release handoff:
  未変更。R13-6以降で対象。
```

---

## 6. 確認済み

```text
- 通常pytestではProduct Quality Connection E2EがEXIT_STATUS:124になる。
- assertion plain + compact tracebackではline 99 AssertionErrorとして返る。
- 現行line 99は `assert "current_input" not in serialized`。
- scorecard内で、current_input dict keyは見つからない。
- scorecard内で、current_input.memo sample body / input id / memo_action / source_text tokenは見つからない。
- current_input tokenはrubric説明文のsafe vocabulary候補として1箇所だけ見つかる。
- body-free leak guard contractは、raw key / raw value ref / forbidden true flag / safe vocabulary / failure output policyを分けて定義した。
- R13-1 contract testはgreen。
- 既存P7周辺regression subsetはgreen。
```

---

## 7. 未確認

```text
- R13-2のrecursive scanner実装。
- R13-3のscanner単体test。
- R13-4のProduct Quality Connection E2E assertion置換。
- R13-5のdefault pytest timeout解消確認。
- R13-6以降のtimeout isolation / red classification / validation matrix / release handoff整合。
- full backend suite green。
- 実機submit / modal読感。
- P5 human QA。
```

---

## 8. 書かれていない

```text
- R13-1完了だけでP7-RED-003をclosedにしてよい根拠はない。
- R13-1完了だけでP7 complete / P8 start / release_allowedをtrueにしてよい根拠はない。
- current_input safe vocabularyを全pathで許可してよい根拠はない。
- raw body検査を省略してよい根拠はない。
```

---

## 9. 推測禁止

```text
- current_input tokenがあるからraw input leakだ、と断定しない。
- raw bodyが直接見つからないからbody-free境界が完全、と断定しない。
- contract定義ができたからE2Eが修復済み、と扱わない。
- timeoutがassertion diff由来の可能性が高いからP7-RED-003をclosed、と扱わない。
- R13-1 greenを商品品質合格へ変換しない。
```

---

## 10. 次に実行すべきこと

```text
R13-2:
  body-free leak guard helperを実装する。
  recursive walkでforbidden key / forbidden raw value / forbidden true flag / allowed safe vocabularyを判定する。
  failure messageはraw body-free / compactにする。

R13-3:
  helper単体testを追加する。

R13-4:
  Product Quality Connection E2Eのglobal substring assertionを構造化assertionへ置き換える。
```

---

## 11. 華恋の判断

今回のR13-0/R13-1では、testを通すための修正にはまだ入っていない。  
先に、何をbody leakとして止め、何をrubric vocabularyとして許すのかをcontractとして固定した。

Cocolonとして守るべきものは、ユーザーの本文・raw object・comment_text body・candidate bodyを測定materialへ流さないこと。  
同時に、読まれたかを測るための評価語彙までraw leak扱いして測定器を壊さないこと。

この2つを混ぜないために、R13-1では `current_input` を一括禁止ではなく、次の境界へ分けた。

```text
current_input dict key / raw object / raw body / input id:
  RED

rubric説明文のpath限定safe vocabulary:
  SAFE
```

次は、ここで固定したcontractを使って、実際のscannerとE2E assertion修復へ進む。
