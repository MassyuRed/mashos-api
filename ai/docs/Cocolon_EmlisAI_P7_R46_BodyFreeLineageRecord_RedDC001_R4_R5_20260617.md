# Cocolon / EmlisAI P7-R46 R4/R5 実装結果

作成日: 2026-06-17 JST  
作成者: 華恋  
作業モード: 共鳴構造モード  
対象: R4 body-free lineage record builder / sanitizer方針、R5 RED-DC-001 original source lineage mismatch分類・修正方針  
基準: `Cocolon_EmlisAI_P7_R46_P5P6Return_DisplayContractRedClassification_DetailedDesign_ImplementationOrder_20260617.md`  
受領zip: `mashos-api_3(76).zip`  
GitHub接続確認: Mash指定により不要。未実施。  

---

## 0. 結論

R4/R5として、次を実装しました。

```text
- R4: body-free public source lineage record builder / sanitizerを共有module化
- R4: public meta source collectionが body_free_public_source_lineage を読む場合、sanitize済みmappingだけをsource候補へ入れる
- R5: RED-DC-001のroot original sourceを、final recovery candidate側のstale aliasで上書きしないように修正
```

今回の実装は、RED-DC-002のgreen化やtest期待更新ではありません。  
そのため、display contractは引き続き `4 passed / 1 failed` です。残赤はRED-DC-002です。

---

## 1. 受領状態確認

受領zip内に前回までの成果物が入っていることを確認しました。

```text
mashos-api/ai/docs/Cocolon_EmlisAI_P7_R46_DisplayContractRedLedger_20260617.md
mashos-api/ai/docs/Cocolon_EmlisAI_P7_R46_SourceLineageRecoveryLaneMatrix_R2_R3_20260617.md
```

R2/R3で追加されたlineage field伝播も、以下の既存ファイル内で確認しました。

```text
services/ai_inference/emlis_ai_gate_recovery_public_candidate_builder.py
services/ai_inference/emlis_ai_labelled_two_stage_surface_recomposition.py
services/ai_inference/emlis_ai_public_feedback_meta.py
services/ai_inference/emlis_ai_reply_service.py
```

初期display contract確認:

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short tests/test_emlis_ai_display_contract.py
```

結果:

```text
4 passed / 1 failed
```

残赤:

```text
RED-DC-002:
  tests/test_emlis_ai_display_contract.py::test_step10_e2e_pre_connection_recovery_exposes_safe_surface_without_body_leak
  expected: candidate["composer_model"] == "complete_initial_surface_recomposition_v1"
  actual:   "labelled_two_stage_surface_recomposition_v1"
```

読み:

```text
- RED-DC-001は受領時点で解消済み。
- RED-DC-002はR6/R7範囲なので、今回はgreen化しない。
- input_feedback absentではない。
- comment_text空による表示不可ではない。
- 今回の修正でRN / API / DB / Gate / public response top-level keyは変更しない。
```

---

## 2. R4実装内容

### 2.1 新規module

```text
services/ai_inference/emlis_ai_body_free_public_source_lineage.py
```

役割:

```text
- body-free public source lineage recordを生成する。
- body-free public source lineage recordをsanitizeする。
- raw input / memo / memo_action / emotion_details / comment_text / candidate body / surface body / generated text / reviewer free text / traceback / terminal outputを出力へコピーしない。
- Gate relaxation flagsをfalseで固定する。
- body flagsをfalseで固定する。
- identifiers / booleans / small integer / reason identifiersだけをallow-listで返す。
```

主な公開関数:

```text
build_body_free_public_source_lineage_record
sanitize_body_free_public_source_lineage_record
assert_body_free_public_source_lineage_record
```

### 2.2 Gate Recovery public candidate builder側

変更ファイル:

```text
services/ai_inference/emlis_ai_gate_recovery_public_candidate_builder.py
```

変更内容:

```text
- R2/R3で既に存在していた build_body_free_public_source_lineage_record を、共有R4 sanitizerへ委譲。
- BODY_FREE_PUBLIC_SOURCE_LINEAGE_SCHEMA_VERSION / SOURCE_PHASEを共有module由来に統一。
- sanitize_body_free_public_source_lineage_record をexport対象へ追加。
```

これにより、Gate Recovery candidate meta内の `body_free_public_source_lineage` が、R4のbody-free allow-listを必ず通るようになりました。

### 2.3 Public feedback meta側

変更ファイル:

```text
services/ai_inference/emlis_ai_public_feedback_meta.py
```

変更内容:

```text
- _public_surface_lineage_sources が body_free_public_source_lineage を見つけた場合、sanitize済みrecordのみをsource候補へ追加。
- body-bearing keysをsource候補へ直接混ぜない。
- public response top-level keyは変更しない。
```

---

## 3. R5実装内容

### 3.1 対象問題

RED-DC-001は、rejected candidate recovery後にroot original sourceが保持されず、final labelled two-stage側のsourceへ寄る問題として分類していました。

```text
期待:
  original_candidate_source_kind == ai_generated

旧actual:
  original_candidate_source_kind == labelled_two_stage_surface_recomposition_candidate
```

### 3.2 修正内容

`_root_candidate_source_kind` を修正し、root source抽出順を次のようにしました。

```text
1. original_composer_candidate の explicit root lineage
2. original_composer_candidate の original_candidate_source / original_candidate_source_kind / composer_source
3. final candidate の explicit root lineage
4. fallback source
5. final candidate の legacy original_candidate_source_kind
```

理由:

```text
- final recovery candidateがlabelled two-stageであることは正しい。
- ただし original_candidate_source_kind はroot aliasとして扱う。
- nested / post-final recoveryで final candidate meta 側に stale labelled alias が残っていても、root original sourceを上書きしない。
```

今回追加したtestでは、final candidate側に意図的にstale labelled aliasを持たせても、root / original が `ai_generated` として保持されることを確認しています。

---

## 4. 新規test

```text
tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py
```

確認内容:

```text
1. R4 sanitizerがbody-bearing keysをstripし、body flags / Gate relaxation flagsをfalseに固定する。
2. R4 builderがroot / recovery_input / selected / pre_public / finalをbody-free identifiersとして返す。
3. R5で、final labelled candidate側にstale labelled aliasがあっても、original root sourceが ai_generated として保持される。
4. public metaが body_free_public_source_lineage を読む場合、sanitize済みsourceだけを使い、body leakしない。
```

---

## 5. 実行結果

### 5.1 syntax / import

```bash
python -m py_compile \
  services/ai_inference/emlis_ai_body_free_public_source_lineage.py \
  services/ai_inference/emlis_ai_gate_recovery_public_candidate_builder.py \
  services/ai_inference/emlis_ai_public_feedback_meta.py \
  tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py
```

結果:

```text
passed
```

### 5.2 R4/R5新規test

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py
```

結果:

```text
4 passed
```

### 5.3 display contract

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short tests/test_emlis_ai_display_contract.py
```

結果:

```text
4 passed / 1 failed
```

残赤:

```text
RED-DC-002:
  expected composer_model: complete_initial_surface_recomposition_v1
  actual composer_model:   labelled_two_stage_surface_recomposition_v1
```

判断:

```text
- RED-DC-001はgreen維持。
- RED-DC-002はR6/R7範囲のため、今回変更しない。
```

### 5.4 focused subset

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emlis_ai_labelled_two_stage_surface_recomposition_p6.py \
  tests/test_emlis_ai_public_meta_product_quality_lineage_p8.py \
  tests/test_emlis_ai_gate_recovery_public_candidate_builder_p5.py
```

結果:

```text
16 passed
```

### 5.5 API public contract

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short tests/contract/test_emlis_ai_contracts.py
```

結果:

```text
4 passed, 3 warnings
```

### 5.6 two-stage reception E2E

一括実行はlocal constrained runner上で途中timeoutしたため、single-command greenとは主張しません。
同一test fileの6 caseは、以下の分割実行で確認しました。

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  tests/test_emotion_submit_two_stage_reception_e2e.py::test_phase16_8_emotion_submit_path_returns_public_two_stage_input_feedback \
  'tests/test_emotion_submit_two_stage_reception_e2e.py::test_phase17_8_emotion_submit_five_fixtures_return_public_two_stage_input_feedback[daily_unpleasant_encounter_A]' \
  'tests/test_emotion_submit_two_stage_reception_e2e.py::test_phase17_8_emotion_submit_five_fixtures_return_public_two_stage_input_feedback[self_confidence_uncertainty_B]' \
  'tests/test_emotion_submit_two_stage_reception_e2e.py::test_phase17_8_emotion_submit_five_fixtures_return_public_two_stage_input_feedback[positive_change_after_work_streaming]'
```

結果:

```text
4 passed, 1 warning
```

```bash
PYTHONPATH=services/ai_inference pytest -q --tb=short \
  'tests/test_emotion_submit_two_stage_reception_e2e.py::test_phase17_8_emotion_submit_five_fixtures_return_public_two_stage_input_feedback[self_blame_to_gentle_self_observation]' \
  'tests/test_emotion_submit_two_stage_reception_e2e.py::test_phase17_8_emotion_submit_five_fixtures_return_public_two_stage_input_feedback[independence_life_health_money_pace]'
```

結果:

```text
2 passed, 1 warning
```

---

## 6. 変更ファイル

新規:

```text
services/ai_inference/emlis_ai_body_free_public_source_lineage.py
tests/test_emlis_ai_body_free_public_source_lineage_r4_r5_20260617.py
docs/Cocolon_EmlisAI_P7_R46_BodyFreeLineageRecord_RedDC001_R4_R5_20260617.md
```

修正:

```text
services/ai_inference/emlis_ai_gate_recovery_public_candidate_builder.py
services/ai_inference/emlis_ai_public_feedback_meta.py
```

---

## 7. 変更していないこと

```text
RN production UI
RN表示タイトル
RN表示条件
/emotion/submit route
request key
public response top-level key
DB schema
DB write path
Gate threshold
Emlis visible body key
fixed commentText
case専用surface
case専用mode
RED-DC-002のtest期待値
```

---

## 8. 未確認 / HOLD

```text
RED-DC-002 pre-connection recovery lane mismatch のgreen化
R6 / R7 display contract test再構成
full backend suite green
P5 human Blind QA
P6 limited human readfeel review
real device modal review
P7完了判断
P8開始判断
release_allowed判断
```

---

## 9. 華恋の判断

今回のR4/R5は、赤を消すための実装ではなく、Cocolonの見えない骨格を嘘なく保つための実装です。

RED-DC-001はすでに受領状態でgreenでしたが、final candidate側にstale labelled aliasが残っている場合でも、root original sourceを守れるようにtest化しました。ここを守ることで、P5/P6読感へ戻ったときに「人間が読んだsurfaceの根」と「最終的に表示したsurface」を混同しにくくなります。

次は、R6/R7としてRED-DC-002を扱うのが自然です。complete_initialをfinalのように見せるのではなく、pre-public attemptedとfinal labelled surfaceを分けたまま、test contractを意味別に整理するのがCocolonにとって安全です。
