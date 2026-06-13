# Cocolon / EmlisAI P7 Product Quality Runner 実装結果メモ 2026-06-12

作業範囲: P7-8 / P7-9
作業対象: `mashos-api/ai`
GitHub接続確認: Mash様指定により未実施

## 実装判断

P7はRelease Readyを作る工程ではなく、P5/P6以降の材料をbody-freeで測定し、赤・HOLD・timeout・未レビューをrelease decision層へ渡す前に分離する工程として固定した。

今回のP7-8では、Long-run Product Gate candidate material、P7 red ledger、runner planからRelease Decision handoff materialを作る。ただし、`release_allowed`は常にfalseであり、Product Pass候補をRelease Readyへ変換しない。

今回のP7-9では、何をgreenと呼べるか、何をRED/HOLD/isolated/unverifiedとして残すかを固定した。P7 core greenはP7 core groupのみ、既存Product Quality reuse subset greenはそのsubsetのみであり、full backend suite greenやrelease readyにはしない。

## 実装ファイル

新規:

- `services/ai_inference/emlis_ai_p7_release_handoff.py`
- `services/ai_inference/emlis_ai_p7_validation_matrix.py`
- `tests/test_emlis_ai_p7_release_handoff_20260612.py`
- `tests/test_emlis_ai_p7_validation_matrix_20260612.py`
- `docs/Cocolon_EmlisAI_P7_ProductQualityRunner_ImplementationResult_20260612.md`

修正:

- `services/ai_inference/emlis_ai_p7_runner_plan.py`
- `tests/test_emlis_ai_p7_runner_plan_20260612.py`

## P7-8 固定内容

- `P7ReleaseDecisionHandoffV1`を追加。
- `release_decision_input_ready`と`release_allowed`を分離。
- P7 red ledgerのopen RED/HOLDをhandoff materialに残す。
- `P7-RED-001`, `P7-RED-002`, `P7-RED-003`をrelease blocker materialとして保持。
- `P7-HOLD-001`, `P7-HOLD-002`, `P7-HOLD-003`, `P7-HOLD-004`を未解消HOLDとして保持。
- timeout / hangはgreen扱いしない。
- Product Pass候補、Long-run candidate、Release Decision input materialのいずれもRelease Readyへ変換しない。
- public contract、RN contract、DB schemaは変更しない。
- body-free境界を維持する。

## P7-9 固定内容

- `P7ValidationRegressionMatrixV1`を追加。
- P7 core contract greenは`p7_core_contract_only`として記録。
- existing reuse subset greenは`existing_subset_only_not_full_backend_suite`として記録。
- Positive Recovery E2EはRED ledgered / classifiedとして残す。
- Product Quality Connection E2E timeoutはisolatedとして残す。
- full backend suiteは未確認HOLDとして残す。
- RN / API response key / DB schemaは変更なしとしてmatrixに残す。
- P7 complete claim、release ready claim、full backend suite green claimは禁止のまま固定。

## 確認結果

P7-0〜P7-9 core:

```text
50 passed
```

既存Product Quality reuse subset:

```text
31 passed, 1 warning
```

P7-8 / P7-9 新規テスト:

```text
10 passed
```

Positive Recovery E2E:

```text
2 failed
```

確認した失敗内容:

- `reader_relation_signal_keys`が`recovery_load_bridge`ではなく`recovery`になる。
- relation surface missingのケースで`rejected`ではなく`passed`になる。

Product Quality Connection E2E:

```text
timeout / hang扱いとしてP7-RED-003へ隔離継続
```

full backend suite:

```text
一括green未確認。P7-9 matrixでは未確認HOLDのまま保持。
```

## 変更していないもの

- RN UI / RN表示契約
- API route
- request key
- public response top-level key
- DB schema / write path
- Emlis本文生成
- fixed commentText / fixed surface
- Product Pass → Release Ready変換
- release_allowed true化

## 華恋の判断

P7-8 / P7-9は、Cocolonをreleaseへ近づけるための抜け道ではなく、Cocolonの商品品質を測るための境界を閉じる作業として実装した。

今残っているRED/HOLDは、Cocolonとして在るべき姿に対して隠してはいけない材料である。そのため、P7はgreenを増やすためではなく、次に直すべき箇所をbody-freeで渡せる構造として固定した。
