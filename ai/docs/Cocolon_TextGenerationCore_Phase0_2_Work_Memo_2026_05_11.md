# Cocolon Text Generation Core Phase 0-2 Work Memo

作成日: 2026-05-11
対象: 共通文章生成基盤 Phase 0 / Phase 1 / Phase 2

## Phase 0: 作業境界固定

今回の変更はローカル snapshot のみで確認した。GitHub 接続確認は行わない。

変更しない境界:

- DB physical name / DB write path / DB rename / drop
- 既存 public API route
- 既存 request / response key
- `input_feedback.comment_text`
- `observation_status=passed` のみ表示する境界
- 画面表示名 `Emlisの観測`
- Piece / Analysis の runtime 接続
- 外部 AI / 固定観測文 fallback / role 別完成文テンプレ

旧名称は互換・DB境界・payload境界として残る可能性があるため、この作業では rename しない。

## Phase 1: EmlisAI Phase8 安定面固定

EmlisAI Phase8 は新規作成対象ではなく、共通化前の実装母体として扱う。

安定面として確認する対象:

- `services/ai_inference/emlis_ai_limited_composer_client.py`
- `services/ai_inference/emlis_ai_limited_sentence_quality_guard.py`
- `services/ai_inference/emlis_ai_limited_observation_scope_service.py`
- `services/ai_inference/emlis_ai_template_echo_guard.py`
- `services/ai_inference/emlis_ai_grounding_judge.py`
- `services/ai_inference/emlis_ai_reply_service.py`
- `tests/test_emlis_ai_phase8_real_input_quality.py`
- `tests/fixtures/emlis_ai_phase8_cases.py`

Phase 1 では既存 EmlisAI ファイルを変更しない。共通化候補は次の通り。

| 候補 | 共通化方針 | Phase 2 での扱い |
|---|---|---|
| SourceAnchor / EvidenceSpanLike | 根拠の共通入力 | 新規型として追加 |
| PhraseUnit | 本文化可能な最小単位 | 中核非依存の型だけ追加 |
| SentencePlan | 完成文ではなく文構成計画 | 中核非依存の型だけ追加 |
| TextGenerationResult | status / text / evidence / quality meta | fail-closed 結果型として追加 |
| ObservationProfile | Emlis固有の構造型 | Phase 2 では移さない |
| Emlis の距離感 / 表示名 / passed-only | Emlis固有境界 | 共通基盤へ移さない |

## Phase 2: 共通基盤の最小パッケージ作成

追加した範囲:

- `services/ai_inference/cocolon_text_generation_core/__init__.py`
- `services/ai_inference/cocolon_text_generation_core/policies.py`
- `services/ai_inference/cocolon_text_generation_core/types.py`
- `tests/test_cocolon_text_generation_core_types.py`

この Phase では、既存 EmlisAI runtime へ接続しない。共通型だけを置き、payload 不足・根拠不足・本文不足は `unavailable` / 空本文へ fail-closed する。

最小出力契約:

- `status`
- `text`
- `used_evidence_span_ids`
- `coverage_scope`
- `quality_flags`
- `rejection_reasons`
- `composer_model`

## 実行確認

実行コマンド:

```bash
PYTHONPATH=services/ai_inference:tests:tests/fixtures python -m pytest \
  tests/test_cocolon_text_generation_core_types.py \
  tests/test_emlis_ai_phase8_real_input_quality.py \
  tests/test_emlis_ai_limited_composer_client.py \
  tests/test_emlis_ai_scoped_grounding.py -q
```

追加の境界確認:

```bash
PYTHONPATH=services/ai_inference:services/analysis_engine:tests:tests/fixtures python -m pytest \
  tests/contract/test_new_national_core_emlis_contracts.py \
  tests/contract/test_new_national_core_piece_contracts.py \
  tests/contract/test_new_national_core_analysis_contracts.py -q
```
