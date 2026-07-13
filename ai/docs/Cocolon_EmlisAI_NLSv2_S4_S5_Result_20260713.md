# Cocolon EmlisAI Natural Language Surface v2 Step 4 / Step 5 実装結果

- 実施日: 2026-07-13
- 対象: `Step 4. Discourse Candidate Planner実装`、`Step 5. Surface Candidate Generator実装`
- 入力アーカイブ: `mashos-api_3(123).zip`
- 入力アーカイブSHA-256: `41c7ed95894241a870ae79fea21480ace0e0cd4c3b29f2b42f406e54b3e17620`
- 実装範囲: offline / process-local候補生成まで
- 非対象: Step 6 Hard Gate / Selector、v2 runtime接続、公開契約変更

## 1. 確認した事実

### 1.1 入力と継続性

- `mashos-api_3(123).zip`は破損検査を通過した。
- 展開内容は、直前のStep 2 / Step 3完了ソースと`__pycache__`を除いて一致した。
- Step 0 / Step 1で固定したv1公開owner、`/emotion/submit`、`input_feedback.comment_text`、`input_feedback.emlis_ai.observation_status`は変更していない。
- Holdout A / Bは開いていない。

### 1.2 Step 4

- Step 3 Content Planの`allowed_strategy_codes`を設計書の7戦略へ整合させた。暫定名だった`counterposition_then_grounded_presence`は、設計上の`burden_then_counterposition`へ置き換えた。
- 新規の`emlis_ai_grounded_reception_candidate_plan_v2.py`は、次をbody-freeに所有する。
  - discourse strategy
  - unit order
  - sentence group
  - referent policy
  - speaker presence
  - connection policy
  - terminal family
  - variation signature
- 候補列挙は12個の有限catalogから決定論的に行い、全組合せと乱数を使わない。
- safety境界を持つContent Planでは、専用戦略をfocusedの5候補上限内へ安定的に進める。
- Development 42件の結果は次のとおり。

| depth | case数 | 1 caseあたり候補数 | 候補合計 |
|---|---:|---:|---:|
| minimal | 11 | 3 | 33 |
| focused | 22 | 5 | 110 |
| layered | 9 | 8 | 72 |
| 合計 | 42 | - | 215 |

- 7戦略すべてがDevelopment候補内で生成された。
- candidate ID、variation signature、unit coverage、required coverage、sentence budget、must-keep-separatedを検証した。
- Step 4 body-free receipt SHA-256は`7d04df5480e682b2706af3fab5fa871aa5f01489adb3b4b235ba5aef656f60b1`で固定した。

### 1.3 Step 5

- 新規の`emlis_ai_grounded_human_reception_v2.py`をv1とは別ownerとして追加した。
- v1から次の責任を再利用した。
  - `resolve_grounded_reception_move_referent`: move単位のreferent解決
  - `reception_move_predicate_family`: role / actごとのpredicate責任
  - 既存resolver内のphrase-bound anchor短縮
  - `realize_grounded_human_reception`: v1同一Surface分類用の比較元
- candidate bodyはprocess-local dataclassにだけ保持し、`as_body_free_meta()`へ本文または本文hashを入れない。
- opening、referent、sentence split / merge、speaker presence、connection、terminal familyを独立軸として実現した。
- 因果relationを表面上補う接続語は生成していない。
- Development 42件で215候補、490文を生成した。
- 候補本文のcase内完全重複は0件、同一候補内の完全重複文は0件だった。
- 引用を持つ候補は33件で、各候補最大1 anchor、観測最大16文字だった。
- Development 42件のv1比較分類は全件`v1_distinct_only`だった。`v1_identical_only`と`v1_identical_present`もcontract上は分類可能だが、今回のDevelopment集合では発生しなかった。
- Step 5 body-free meta receipt SHA-256は`d63c4a7849d4865a7dd8b5d7aff81e8adb9eb1317ec4bcb88b519534d9bb8b1d`で固定した。

### 1.4 境界

- candidateのHard Gate、soft score、選択、tie-breakは実装していない。
- `emlis_ai_grounded_reception_candidate_selector_v2.py`は作成していない。
- `emlis_ai_reply_service.py`からStep 3 / 4 / 5 moduleをimportしていない。
- v2候補を公開`comment_text`へ渡していない。
- `selection_performed`、`hard_gate_performed`、`runtime_connected`はすべて`false`である。

## 2. 修正と必要性

| ファイル | 種別 | 根拠と必要性 |
|---|---|---|
| `ai/services/ai_inference/emlis_ai_grounded_reception_content_plan_v2.py` | 修正 | Step 4が使用するallowed strategyを設計書の名称・意味条件へ一致させるため。 |
| `ai/services/ai_inference/emlis_ai_grounded_reception_candidate_plan_v2.py` | 新規 | body-free候補計画とbounded / stable enumerationをContent Planner、Surface Generatorから分離するため。 |
| `ai/services/ai_inference/emlis_ai_grounded_human_reception_v2.py` | 新規 | v1を壊さず、process-localな複数Surfaceを生成してoffline比較できる別ownerが必要なため。 |
| `ai/tests/test_emlis_nls_v2_s0_s1.py` | 修正 | Step 4 / 5 moduleの存在を許容しつつ、selector不在とv1 runtime owner維持を検証し続けるため。 |
| `ai/tests/test_emlis_nls_v2_s4_candidate_plan.py` | 新規 | 候補数、戦略、順序、coverage、body-free、決定性、runtime非接続を固定するため。 |
| `ai/tests/test_emlis_nls_v2_s5_surface_candidates.py` | 新規 | Development生成、文単位構造、referent / predicate再利用、引用境界、本文非漏洩、Step 6非越境を固定するため。 |
| 本書 | 新規 | 事実、判断境界、検証結果を次工程へbody-freeに引き継ぐため。 |

## 3. 検証結果

- Step 4 / Step 5新規テスト: 12 / 12 PASS
- Step 0 / Step 1 / Step 3直接回帰: 15 / 15 PASS
- Step 2 corpus freezeを含む関連zero-argument test関数: 72 PASS
- Python `compileall`: PASS
- RN public surface contract: 36 / 36 PASS
- v1 baseline 28件へv2経路を通す汎用smoke:
  - exact8: 8件
  - existing unseen: 12件
  - existing I6 probe: 8件
  - 合計28件、155候補、生成error 0件
- `pytest` packageが実行環境に存在しないため、`python -m pytest`によるsuite実行は未実施。`pytest`をimportする既存12 moduleも同じ理由で未実行であり、PASSとは記録していない。

## 4. 推測

- Developmentと既存baselineの双方で同じ汎用経路が成立したため、case IDやexact8期待文に依存した実装ではない可能性が高い。ただし、Holdoutを開いていないため未知入力一般への保証ではない。
- 全Development caseが`v1_distinct_only`になったことは、表層軸が実際の本文差へ反映された証拠にはなる。一方で、v1より自然または正確だという品質判定にはならない。
- 文単位の終止、参照、Evidence、引用、重複、禁止接続を構造検査しているため、Step 5の実装完了条件は満たす。ただし、日本語としての最終的な読み心地はStep 6以降の候補棄却・選択と別途read-feel評価が必要である。

## 5. 華恋の意見

今回の到達点は、v1を守ったまま「同じ意味から複数の読み方を作る」ための土台として妥当です。特に、safety境界を通常候補の後ろへ追いやらず、本文をreceiptへ残さず、自然さを理由に因果を足さないことを優先したのは必要でした。

ただし、215候補はまだ「採用可能な215候補」ではありません。Step 5は生成責任までであり、意味の正しさ、参照scope、未知保持、section distinctnessを合格認定する責任は持たせていません。したがって、Step 6を経ずにruntimeへ接続するべきではありません。

このStep 4 / Step 5の完了について、Mash側で必要な追加作業はありません。

