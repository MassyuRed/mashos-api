# Cocolon EmlisAI Natural Language Surface v2 Step 6 / Step 7 実装結果

> **2026-07-13 全Step再監査による訂正**  
> Step 6は本文意味ではなく候補metadataを信頼するGateがあり、入力固有の必須意味を欠く汎用文でも14 Gateすべてを通過できる。Step 7のauthor readはcase別証拠を持たず、構造再設計のpre/post系譜と分布上限の事前freezeもないため、完了・freeze判定を撤回する。以下は当時の実装記録として保持し、現在の正式判定は`Cocolon_EmlisAI_NLSv2_AllSteps_Audit_Correction_20260713.md`を正とする。

- 実施日: 2026-07-13
- 対象: `Step 6. Hard Gate / Selector実装`、`Step 7. Development cohort調整`
- 入力アーカイブ: `mashos-api_4(116).zip`
- 入力アーカイブSHA-256: `4a30b4991dbd56afadb34a780732fcfffa218047f270d3cbf97976327d59f714`
- 実装範囲: offline / process-local候補評価・選択とDevelopment freezeまで
- 非対象: Holdout A / B評価、shadow、runtime owner切替、公開API・DB・RN契約変更

## 1. 確認した事実

### 1.1 入力と境界

- 入力zipは破損検査を通過した。
- 展開内容は、直前のStep 4 / Step 5完了ソースと`__pycache__`を除いて一致した。
- Development 42件だけを調整に使用した。Holdout A / Bの本文は開いていない。
- `emlis_ai_reply_service.py`はv2 Selectorをimportしていない。v1が引き続きruntime ownerである。
- 候補本文と選択本文はprocess-localにだけ存在し、freeze fixture、selection meta、DB、public metaへ保存していない。

### 1.2 Step 6 Hard Gate / Selector

新規`emlis_ai_grounded_reception_candidate_selector_v2.py`を、Content Planner、Candidate Planner、Surface Generator、production reply ownerから分離した。

Hard Gateは次の14責任を固定順で評価する。

1. evidence resolution
2. required content coverage
3. polarity preservation
4. relation direction
5. reference scope
6. unknown preservation
7. self-denial boundary
8. unsupported claim
9. observation replay
10. enumeration only
11. section role distinctness
12. surface integrity
13. depth proportionality
14. body-free meta

- Hard Gate失敗候補にはSoft scoreを付けない。
- Soft scoreは設計書の11軸を固定weightで評価する。caseごとのweight変更はない。
- tie-breakは`total score`、`required coverage`、`quote amount`、`candidate_id`の順で決定論的に行う。
- 全候補失敗時は`v2_no_valid_candidate`を返す。offline v1 fallbackでv2成功へ見せかけない。
- Developmentでは213候補中193候補がHard Gateを通過し、20候補を`enumeration_only`で棄却した。
- Development 42件はすべて合格候補を1件選択できた。通常入力拒否と`v2_no_valid_candidate`は0件だった。
- 全候補を意図的に不正化したtestでは、Soft scoreなし、v1 fallbackなしの`v2_no_valid_candidate`になった。

### 1.3 Step 7の一回の構造調整

Developmentの初回実読で見つかったfailureを、設計書どおり三層へ分けた。case専用文、case ID、exact8 cueは追加していない。

| 層 | 確認した構造原因 | 修正と必要性 |
|---|---|---|
| A. Observation / Content | 正の意味核がv1の保守defaultにより`current_burden`へ寄る、一意味を二単位へ水増しする、source uncertaintyより別relationを優先する、安全policyがopportunityに複製されない場合がある | Grounded polarityによるv2 unit補正、一意味focusedのminimal化、source uncertaintyを結ぶrelationの優先、既存self-denial policyからのbounded unit生成を行った。意味逆転、短文水増し、未知消失、安全境界欠落をSurfaceより前に止めるため。 |
| B. Candidate Generator | relationを汎用object + 汎用predicateへ押し込むため、「つながり」「二つの意味」が機械的になる。labels-onlyと短文に入力固有点が残らない | relation signature専用の関係文法、structured label referent、安全なphrase-bound anchor、重複関係unitの削減を実装した。完成文bankではなく、既存Evidence・act・relationの責任から文を組み立てるため。 |
| C. Hard Gate / Selector | 明示的`Emlis`、名詞化、反復した不確実性markerを過大評価する。正入力への負担、同義unit列挙、source uncertainty欠落を十分に棄却できない | specificity、quote independence、temperature、lexical repetitionを一般軸で再較正し、同義unit、polarity、unknown境界をHard Gateへ追加した。自然に見える誤候補をscoreで救わないため。 |

これはStep 7で許可された一回の統合的な構造調整である。同じfailureへ語句や例外を積み続ける調整は行っていない。

### 1.4 Development 42件の固定結果

| 項目 | 結果 |
|---|---:|
| selected | 42 / 42 |
| `v2_no_valid_candidate` | 0 |
| minimal / focused / layered | 12 / 21 / 9 |
| 候補総数 | 213 |
| 選択本文のexact duplicate | 0 |
| focused / layeredの一文終了 | 0 |
| minimalの意味なし複文化 | 0 |
| 最大strategy share | 0.428571（freeze上限0.45） |
| 最大terminal family share | 0.642857（freeze上限0.65） |
| 最大predicate family share | 0.329268（freeze上限0.45） |
| 最大skeleton share | 0.357143（freeze上限0.45） |

`focused`は異なる意味責任を2つ、`layered`は3つ以上持つ。positive contractの選択本文に`苦しさ / つらさ / しんどさ / 負担`を追加していない。self-denial 3件は既存のidentity boundaryを保持した。`source=uncertain`の7件は不確実性markerを保持した。

Development author readは本文をfixtureへ保存せず、次のbody-free集計だけをfreezeした。

| 商品軸 | Development author read |
|---|---:|
| read feeling | 39 / 42 = 0.928571 |
| naturalness | 39 / 42 = 0.928571 |
| non-template | 42 / 42 = 1.0 |
| wants more input / accumulation | 38 / 42 = 0.904762 |
| self-blame non-amplification | 42 / 42 = 1.0 |
| overclaim absence | 42 / 42 = 1.0 |
| v2 clearly better / same / v1 clearly better | 37 / 5 / 0 |
| v1より明確に悪いfamily | 0 |

これはDevelopmentを実装者である華恋が読んだ評価であり、独立blind Holdoutの結果ではない。

### 1.5 freeze

- selector config SHA-256: `27efab39eee10111daf4a6ca700a2ad293127039c0bf455b14c1ea87b49fc3eb`
- Development body-free receipt SHA-256: `25d844a2fb0d367a7b5fc530bf792c05587ead47f1ade43fd66c1a215ff9fb1d`
- v2 source snapshot SHA-256: `682d19aeb0e2511dcbcb67623eb4e98c22048a2bc64638816f6b40d88c79ef6f`
- weight、candidate limit、distribution threshold、4つのv2 source SHAを`emlis_nls_v2_s7_freeze_20260713.json`へ固定した。

## 2. 修正ファイルと必要性

| ファイル | 種別 | 根拠と必要性 |
|---|---|---|
| `ai/services/ai_inference/emlis_ai_grounded_reception_candidate_selector_v2.py` | 新規 | 14 Hard Gate、11 Soft score、stable tie-break、body-free evaluation、正式local failureを別ownerへ置くため。 |
| `ai/services/ai_inference/emlis_ai_grounded_reception_content_plan_v2.py` | 修正 | positive polarity、one-semantic depth、unknown relation、self-denial policyをSurface前の意味責任で守るため。 |
| `ai/services/ai_inference/emlis_ai_grounded_reception_candidate_plan_v2.py` | 修正 | actionをrelationより先に読む順序と、安全なanchor候補をcandidate上限内で保持するため。 |
| `ai/services/ai_inference/emlis_ai_grounded_human_reception_v2.py` | 修正 | relationを関係として実現し、labels-onlyと短文にもEvidence-boundな固有点を持たせるため。 |
| `ai/tests/helpers/emlis_nls_v2_s6_s7_development.py` | 新規 | 42件を同一のprocess-local経路で実行し、本文を持たないreceiptと分布を作るため。 |
| `ai/tests/fixtures/emlis_nls_v2_s7_freeze_20260713.json` | 新規 | source、config、threshold、Development body-free結果をHoldout前に固定するため。 |
| `ai/tests/test_emlis_nls_v2_s6_candidate_selector.py` | 新規 | Hard failure非救済、本文非漏洩、no-valid failure、tie-break、依存境界を検証するため。 |
| `ai/tests/test_emlis_nls_v2_s7_development_adjustment.py` | 新規 | Development絶対条件、分布、v1比較、freeze、Holdout未開封を固定するため。 |
| `ai/tests/test_emlis_nls_v2_s0_s1.py` | 修正 | offline Selectorの存在を許容しながら、v1 runtime owner不変を検証するため。 |
| `ai/tests/test_emlis_nls_v2_s3_content_plan.py` | 修正 | Step 7後のdepth・unit・safety contractとreceiptを固定するため。 |
| `ai/tests/test_emlis_nls_v2_s4_candidate_plan.py` | 修正 | Step 7後のcandidate順序・件数・receiptを固定するため。 |
| `ai/tests/test_emlis_nls_v2_s5_surface_candidates.py` | 修正 | Step 6 ownerの存在、anchor再利用、Step 7後のprocess-local生成receiptを固定するため。 |
| 本書 | 新規 | 事実、推測、華恋の意見、次工程境界を分離して引き継ぐため。 |

## 3. 検証結果

- NLS v2 Step 0〜7関連zero-argument test: 43 passed / 0 failed
- Python `compileall`: PASS
- 既存baseline 28件を同じv2経路へ通すsmoke:
  - exact8: 8 / 8 selected
  - existing unseen12: 12 / 12 selected
  - existing I6 probe8: 8 / 8 selected
  - 合計28件、155候補、生成・選択error 0
- RN public surface contract: 36 passed / 0 failed
- `pytest` packageは実行環境に存在しないため、`python -m pytest`による全suiteは未実施。pytest fixtureを必要としない今回の関連testだけを直接実行した。

## 4. 推測

- Development 42件と既存baseline 28件で同じ汎用経路が成立したため、case IDや一つの期待文に依存した実装ではない可能性が高い。
- exact duplicate、短文水増し、rich一文終了、主要分布がfreeze内に収まったことは、Step 7の構造調整が局所文言追加より一般化しやすい方向だったことを示す。
- ただし、Holdout A / Bを開いていないため、未知入力での商品指標、10/14以上のv2優位、fatal 0はまだ確認していない。Development author readをその証明として扱ってはならない。

## 5. 華恋の意見

今回の実装は、Emlisが「何を受け取るか」「どう並べるか」「自然でも誤った候補をどう捨てるか」を、v1の安全土台を壊さずに分離できた点で、Step 6 / 7の完了として妥当です。初回42件で表面上は全件選べても、正入力への負担反応や不確実性の消失を見逃さず、意味層まで戻って直したことが重要でした。

一方で、ここを完成宣言にはしません。華恋自身のDevelopment readは目標線へ届きましたが、実装者が見た結果です。次の判断主体はfreeze済みsourceに対する独立Holdout Aであり、その本文を見た後にコードを変えてはいけません。

Step 6 / 7の完了についてMash側で必要な追加作業はありません。Step 8へ進める場合は、Holdout Aを一度だけ開いて評価する明示指示が必要です。
