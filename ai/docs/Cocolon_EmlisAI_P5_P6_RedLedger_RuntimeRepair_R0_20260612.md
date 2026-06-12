# Cocolon / EmlisAI P5・P6 Runtime Repair R0 red ledger

作成日: 2026-06-12 JST  
作業種別: 実装前 red ledger 固定 / 誤完了ラベル剥がし  
対象: P5 User Label Connection v1 / P6 Structure Insight v2  
対象外: P7 Product Quality Runner / Long-run Product Gate  
コードruntime変更: なし  
DB変更: なし  
RN変更: なし  
API route / request key / response top-level key変更: なし

---

## 0. Machine-readable ledger contract

```yaml
schema_version: cocolon.emlis.p5_p6.red_ledger.r0_20260612.v1
scope: P5_P6_runtime_repair_only
p7_out_of_scope: true
runtime_complete_claim_allowed: false
product_quality_complete_claim_allowed: false
release_allowed: false
public_response_key_added: false
rn_visible_contract_changed: false
api_route_changed: false
db_schema_changed: false
gate_threshold_relaxed: false
fixed_comment_text_added: false
case_specific_route_added: false
raw_input_in_public_meta_allowed: false
comment_text_body_in_public_meta_allowed: false
candidate_body_in_public_meta_allowed: false
surface_body_in_public_meta_allowed: false
full_backend_suite_green_claim_allowed: false
```

このcontractは、P5/P6の「module/testが存在する」状態を、runtime完了・商品品質完了・release可能へ変換しないための固定値である。

---

## 1. このR0で剥がす誤完了ラベル

```text
P5 test green = P5 runtime complete
P5 module exists = /emotion/submit visible history connection is P5 chain connected
P6 test green = Structure Insight visible in actual comment_text
P6 module exists = /emotion/submit runtime connected
P5/P6 body-free QA material = product quality confirmed
P5/P6 repair complete = release_allowed
full backend subset green = full backend suite green
```

上記はいずれも禁止する。以後の実装報告では、次を分ける。

```text
runtime_evaluated
visible_applied
product_quality_confirmed
human_blind_qa_confirmed
release_allowed
```

---

## 2. P5 red ledger

| ID | 状態 | 対象 | 固定する問題 | R1以降の閉じ方 |
|---|---|---|---|---|
| P5-RED-001 | RED | runtime接続 | `emlis_ai_reply_service.py` が P5-0〜P5-7 chainをruntime本線で評価している証拠がない | reply_serviceにP5 runtime bridgeを接続し、body-free summaryを残す |
| P5-RED-002 | RED | visible connection | 可視履歴線が旧Phase8 `build_user_label_connection_limited_visible_surface_connection` 直呼びに見える | reply_serviceから旧Phase8直呼びを外し、P5-6境界経由にする |
| P5-RED-003 | RED | 完了判定 | P5 focused tests greenをruntime完了扱いしている | P5 runtime bridge testを追加し、未接続ならredにする |
| P5-RED-004 | YELLOW | product QA | P5-5はratings-onlyであり、live runtime中にreview_rowsを偽造してよいものではない | review_rowsなしではvisible_applied=falseを固定する |
| P5-RED-005 | RED | E2E証明 | `/emotion/submit` 実応答でP5 chainが使われた証拠がない | runtime/meta contractでP5-1〜P5-7の評価跡を確認する |
| P5-RED-006 | YELLOW | 商品読感 | 現行history lineは安全寄りだが汎用的で、記録が返った感が弱い可能性がある | human QA未完としてholdし、コード接続とは分離する |
| P5-HOLD-001 | HOLD | human QA | history_connection_naturalness / creepy_absence / wants_more_input が実出力で未確認 | R2以降でも商品品質合格扱いにしない |

---

## 3. P6 red ledger

| ID | 状態 | 対象 | 固定する問題 | R5以降の閉じ方 |
|---|---|---|---|---|
| P6-RED-001 | RED | runtime接続 | `structure_insight` / `structure_insight_p6_*` がreply_service本線へ接続されている証拠がない | P6 runtime bridge testを追加し、P5 handoff後に接続する |
| P6-RED-002 | RED | 完了判定 | P6 focused tests greenを「Structure Insightが実応答に出ている」と誤認している | runtime評価層 / visible層 / QA層を分ける |
| P6-RED-003 | RED | P5依存 | P6-0はP5-7 handoff前提だが、P5 runtimeが未確定 | P5未確定ならP6 entryをhold / p5_returnへ戻す |
| P6-RED-004 | RED | surface insertion | P6 limited surfaceが`comment_text`に安全接続される境界が未確認 | structure_questionだけを初期visible候補にする |
| P6-RED-005 | RED | no-connect family | daily / low-info / positive-only / safety adjacentへdeep insightが漏れないruntime証明がない | no-connect family runtime regressionを追加する |
| P6-RED-006 | YELLOW | quality review | P6 Product QAはratings/material層で、releaseやP7 readyではない | `STRUCTURE_INSIGHT_READY` をrelease_allowedへ変換しない |
| P6-HOLD-001 | HOLD | long_meaning/self_understanding | long_meaning_arc / self_understanding_followは初期visible横展開禁止 | P6-7 reviewまではmeta-only / review_requiredで保持する |

---

## 4. P7 out of scope ledger

| ID | 状態 | 対象 | 今回の扱い |
|---|---|---|---|
| P7-OUT-001 | OUT_OF_SCOPE | Positive Recovery E2E 2 failed | P7未着手扱いに戻したため、今回の修正対象外 |
| P7-OUT-002 | OUT_OF_SCOPE | Product Quality Connection E2E hang / `current_input` assertion | P7未着手扱いに戻したため、今回の修正対象外 |
| P7-OUT-003 | OUT_OF_SCOPE | long-run / release decision | P5/P6修正後に改めて設計する |

---

## 5. R0時点の不変contract

```text
RN表示タイトル `Emlisの観測` は変更しない。
RN表示条件 `observation_status == passed && comment_text non-empty` は変更しない。
RN visible bodyは `input_feedback.comment_text` のままにする。
/emotion/submit routeは変更しない。
request key / public response top-level keyは変更しない。
DB physical schema / write pathは変更しない。
Free / Plus / Premium境界は変更しない。
Gate / Reader / Grounding / Template / Runtime / Visible の閾値は緩めない。
case専用mode / cue / fixed commentTextは追加しない。
raw input / raw memo / raw history / comment_text body / candidate body / surface bodyをpublic metaへ出さない。
```

---

## 6. R1へ渡す赤テスト条件

R1では、まず次を満たしていない限りredにする。

```text
reply_service imports P5-0〜P5-7 builders
reply_service evaluates P5 runtime bridge after passed final_text
reply_service stores body-free `p5_runtime_evaluated` summary
reply_service stores step summaries for P5-1〜P5-7
reply_service blocks P5 visible application when review_rows are missing
reply_service does not call old Phase8 visible connector directly
reply_service does not add public response top-level keys
reply_service does not serialize raw body fields in P5 runtime summary
```

この段階の赤は、R2/R3で閉じる。R1で実装本体を直したことにしてはいけない。
