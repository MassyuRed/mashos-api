# Cocolon EmlisAI Natural Language Surface v2 Step 12 / Step 13 実機確認・遮断結果

> **2026-07-13 全Step再監査による現況訂正**  
> 正式なv2 Step 12とStep 13の機能は未実装・未実行である。実施したのはcanonical v1実機4件の証拠レビューと比率分析、停止guardの固定である。また、下記`mashos-api_7(92).zip`切断は当時の受領事実として保持するが、現在は正常な`mashos-api_9(64).zip`（SHA-256 `61b8dc77a1dd9b9bc15fc1f30c5b8ed0c988511b71c50097853aada7db48e325`）を検証済みであり、完全source不足は現時点のblockerではない。

実施日: 2026-07-13  
対象ソース: `mashos-api_7(92).zip`  
実機証拠: `実機確認結果４.zip`  

## 1. 結論

Step 12は、受領した代表4件の実機証拠レビューまで完了した。ただし、正式なv2実機評価としては実行していない。

- Holdout Aは`STOP`、Holdout Bは未評価のままである。
- Step 10 shadowとStep 11 owner切替は未実行である。
- production ownerは`grounded_sentence_surface_canonical_v1`のままである。
- 実機4件の表示本文は、ローカルで再生成した現行canonical v1本文と4 / 4件一致した。
- したがって、今回の画像はv1の実機baselineとしては有効だが、v2の合格証拠にはならない。
- 代表4件の商品読感はstrict判定で4 / 4件FAILである。
- Step 12の次順であるexact8とHoldout由来代表4〜6件は実行していない。

Step 13は、v1実機baselineの二段量・表示比率を測定したところまでである。自然文v2合格前に長文化・比率調整を行わないという前提を満たさないため、production調整は実行していない。

production、Holdout、API、DB、React Native contractは変更していない。今回実装したのは、証拠・停止判定・非実行状態をbody-free receiptと回帰テストで固定するfail-closed contractである。

## 2. 確認した事実

### 2.1 受領ソースarchive

`mashos-api_7(92).zip`は完全なZIPではない。

| 項目 | 結果 |
|---|---|
| SHA-256 | `6271d8fafb3e6abe7ae8a1eb7a1c7688f0a441dc1de00314a4d651cf75092076` |
| byte size | 7,045,120 |
| End of Central Directory | なし |
| `unzip -t` | 失敗 |
| 安全にdecodeできたfile | 768 |
| うち`__pycache__` / `.pyc`以外 | 740 |
| 直前の完全treeとの差分 | 0 |
| 復元側だけにあったfile | 28、すべて`__pycache__` / `.pyc` |

local headerを順に検査すると806 entryまで読めたが、`ai/tests/local_only/emlis_gate0_r0_baseline_20260711.json`の圧縮stream途中で終端した。

そのため、このarchiveを完全な作業treeとして扱っていない。直前に正常展開・検証済みの`mashos-api_6(102).zip`（SHA-256 `a2c8262219309a991c8b13afd474e8387285de1873053f7eb2b3f65773909386`）をcomplete basisとし、productionを変更せず、今回の新規3ファイルだけを追加した。

### 2.2 Step 12までのlive prerequisite

| 項目 | live状態 |
|---|---|
| Holdout A | 1回評価済み、`STOP` |
| Holdout B | 0回、`not_evaluated`、未開封 |
| Step 10 shadow | `not_executed` |
| Step 11 owner切替 | `not_executed` |
| production owner | v1 |
| v2 | `offline_only` |

設計は、local / Holdout / contract合格後にだけMashへ実機確認を依頼し、合格済みv2だけをruntime ownerへ切り替える順序である。現在はこの前提を満たしていない。

### 2.3 実機証拠inventory

`実機確認結果４.zip`は正常なZIPである。

| 項目 | 結果 |
|---|---:|
| archive SHA-256 | `c043f5c0f011aa8f8ad6085faabc4d367b3ebcc998d54d875544a9beb7fa85f8` |
| evidence file | 10 |
| backend log画像 | 4 |
| 表示画像 | 6 |
| 目視レビュー | 完了 |

画像レビューは、raw backend responseの暗号学的なhash proofではない。今回確認できたのは、画像から読める表示本文がローカルcanonical v1再生成結果と4 / 4件一致すること、production ownerがv1であること、v2 runtime生成が0であることである。

### 2.4 4件の生成系統

4件を、前回提示した思考内容・行動内容・感情選択・カテゴリ選択の完全な組でローカル再生成した。

| case | local generation path | 表示一致 | v2 runtime生成 |
|---:|---|---:|---:|
| 1 | `grounded_sentence_surface_canonical_v1` | PASS | 0 |
| 2 | `grounded_sentence_surface_canonical_v1` | PASS | 0 |
| 3 | `grounded_sentence_surface_canonical_v1` | PASS | 0 |
| 4 | `grounded_sentence_surface_canonical_v1` | PASS | 0 |

サンプル本文は回帰テスト内だけに置いた。productionの条件分岐、固定返答、例文固有triggerには使用していない。4件とも未知入力と同じcanonical v1処理経路を通る。

## 3. Mashの読感の位置づけ

Mashの報告は次のとおりである。

- 1・2では改善したように感じた。
- 3・4では、やはり不十分だと感じた。
- `見えること`が入力を引いてきたtemplate文に見える。
- `Emlisから`は短いだけでなく、内容も薄い。
- 入力によって改善が見えるため、修正方向そのものは誤りではないように感じる。

これはMashの商品読感として記録する。生成系統や合否の事実とは分けて扱う。

## 4. 代表4件の厳密評価

Step 13の比率は文字数Hard Gateではなく、商品読感のQA目安である。以下のFAILは比率だけで決めず、意味密度、section役割分離、引用再掲、表示量を合わせて判定した。

| case | family | 見えたこと | Emlisから | 表示 | strict判定 |
|---:|---|---:|---:|---|---|
| 1 | low information short | 24字 / 36.9% | 41字 / 63.1% | 1画面、clipping・重なり・scrollなし | FAIL |
| 2 | daily positive | 99字 / 61.5% | 62字 / 38.5% | 1画面、clipping・重なり・scrollなし | FAIL |
| 3 | rich change / long arc | 296字 / 82.7% | 62字 / 17.3% | 2画面、scroll必須、clipping・重なりなし | FAIL |
| 4 | self denial + action | 163字 / 66.0% | 84字 / 34.0% | 2画面、scroll必須、clipping・重なりなし | FAIL |

### 4.1 case 1 — 短い・情報量が少ない入力

合格要素:

- short inputを無意味に膨らませていない。
- 1画面内に収まり、表示上のclipping、重なり、scrollがない。

不合格要素:

- `Emlisから`は入力固有の「決めきれなさ」を受け取る意味責任がなく、汎用的な受容文である。
- 意味密度が低い。
- 36.9 / 63.1はlow information shortの初期目安40〜50 / 50〜60から僅かに外れる。

failure code: `EMLIS_CONTENT_GENERIC`, `EMLIS_SEMANTIC_DENSITY_LOW`, `TWO_STAGE_RATIO_OUTSIDE_GUIDE_LOW_INFORMATION_SHORT`

### 4.2 case 2 — 明確に前向きな入力

合格要素:

- positive inputへ苦しさの反応をしていない。
- 1画面内に収まり、表示上のclipping、重なり、scrollがない。

不合格要素:

- `見えたこと`が入力の行動・感情・別の行動をほぼ順に再掲している。
- `Emlisから`も具体行動を再掲するが、そこから増える意味が薄い。
- 二段の意味役割が十分に分かれていない。
- 61.5 / 38.5はdaily positiveの初期目安20〜35 / 65〜80と大きく逆転している。

case 1より読める印象があっても、正式なStep 12 / 13基準では合格にしない。

failure code: `OBSERVATION_QUOTE_REPLAY_EXCESS`, `SECTION_ROLE_DISTINCTNESS_LOW`, `EMLIS_SEMANTIC_DENSITY_LOW`, `TWO_STAGE_RATIO_OUTSIDE_GUIDE_DAILY_POSITIVE`

### 4.3 case 3 — 長く、複数の意味がある入力

不合格要素:

- `見えたこと`が長い入力を引用列挙している。
- 同じ述語templateが2回連続し、参加継続と役割継続拒否の違いを十分に分けていない。
- `Emlisから`の指示対象が曖昧で、具体行動のanchorから対象が落ちている。
- 2文あっても新しい意味責任が薄い。
- 82.7 / 17.3はrich change / long arcの初期目安35〜55 / 45〜65から大きく外れる。
- 2枚目へscrollしなければ全量を読めない。

failure code: `LONG_INPUT_ENUMERATION_REPLAY`, `OBSERVATION_TEMPLATE_CLAUSE_DUPLICATION`, `SEMANTIC_RELATION_DISTORTION`, `EMLIS_REFERENCE_AMBIGUOUS`, `EMLIS_ANCHOR_CONTEXT_LOSS`, `EMLIS_SEMANTIC_DENSITY_LOW`, `TWO_STAGE_RATIO_OUTSIDE_GUIDE_RICH_LONG`, `SCROLL_REQUIRED`

### 4.4 case 4 — 自己否定と具体行動が併存する入力

合格要素:

- 自己否定を本人について確定した事実として扱っていない。
- 自己否定だけでなく具体行動も拾っている。

不合格要素:

- `見えたこと`が入力の三要素を順に再掲している。
- `Emlisから`の前半は汎用受容で、後半は`見えたこと`の安全境界を言い直す割合が高い。
- 二段の意味役割が十分に分かれていない。
- 66.0 / 34.0はself denial / uncertaintyの初期目安30〜45 / 55〜70から大きく逆転している。
- 2枚目へscrollしなければ全量を読めない。

failure code: `OBSERVATION_QUOTE_REPLAY_EXCESS`, `EMLIS_GENERIC_RECEPTION_OPENING`, `SECTION_ROLE_DISTINCTNESS_LOW`, `EMLIS_SEMANTIC_DENSITY_LOW`, `TWO_STAGE_RATIO_OUTSIDE_GUIDE_SELF_DENIAL`, `SCROLL_REQUIRED`

## 5. Step 12判定

Step 12の順序は次である。

```text
代表4件
  ↓
exact8
  ↓
Holdoutから選ぶ新規代表4〜6件
```

今回の状態:

| 項目 | status | run count |
|---|---|---:|
| 代表4件の証拠レビュー | complete | 4 |
| 正式なv2代表4件評価 | not executed | 0 |
| exact8実機確認 | not executed | 0 |
| Holdout由来代表 | not executed | 0 |

停止根拠は二つある。

1. Holdout・runtime ownerの前提を満たさず、表示されたのがv2ではない。
2. v1 baselineとして読んでも、代表4件は商品読感4 / 4件FAILである。

exact8や未開封Holdout Bを追加の調整材料として開いてはいけない。

## 6. Step 13判定

Step 13の前提は「自然文v2が合格する前に長文化しない」である。現在のv2はHoldout Aで停止し、runtime ownerでもないため、調整対象としての資格がない。

実施したこと:

- v1実機baselineの二段文字数を測定した。
- family別初期目安と比較した。
- 量だけでなく、意味密度、重複、役割分離、scrollを確認した。

実施していないこと:

- `Emlisから`の長文化
- 2〜4文への増量
- `見えたこと`のproduction圧縮
- Observation coverage変更
- RN視覚強調変更
- UI順序変更
- v1 / v2 production source変更

4例の文字数比だけを合わせれば、同じ意味の言い換えによる水増しになる可能性が高い。また、v1画面を根拠にoffline v2を修正しても、今回の実機表示は変わらない。したがってStep 13は`not_executed`、production adjustment countは0で固定した。

## 7. 実装したファイルと必要性

| ファイル | 種別 | 根拠と必要性 |
|---|---|---|
| `ai/tests/fixtures/emlis_nls_v2_s12_s13_device_blocked_20260713.json` | 新規 | 実機inventory、v1再現hash、二段比率、4件のstrict判定、Step 12停止、Step 13非実行を本文なしで固定するため。 |
| `ai/tests/test_emlis_nls_v2_s12_s13_device_blocked.py` | 新規 | live prerequisite、4入力のcanonical v1再現、画像inventory、比率、body-free、runtime owner不変を機械検証するため。 |
| `ai/docs/Cocolon_EmlisAI_NLSv2_S12_S13_DeviceCheck_Blocked_Result_20260713.md` | 新規 | 確認事実、Mashの読感、推測、華恋の判断、次作業を分離して残すため。 |

## 8. 変更していないもの

- v1 production生成
- v2 Content Planner / Candidate Planner / Generator / Selector
- runtime import / owner
- v1 fallback
- Holdout A fixture / receipt
- Holdout B fixture / receipt
- API response key
- DB schema / write path
- React Native表示契約
- UI順序・視覚強調
- 4例由来のproduction条件分岐、固有語trigger、固定返答

## 9. 検証

- Step 12 / 13 fail-closed test: 6 / 6 PASS
- NLS v2 green scope（Step 0〜7 + Step 10 / 11遮断 + Step 12 / 13遮断）: 53 / 53 PASS
- React Native public contract: 36 / 36 PASS
- JSON parse: PASS
- Python compile: PASS
- runtime source hash一致: 3 / 3 PASS
- 4 representative local v1 reproduction: 4 / 4一致
- screenshot inventory: 10 / 10 SHA-256固定
- production modification count: 0
- Holdout B evaluation run count: 0

この環境には`pytest` packageがないため、NLS v2の対象test関数は既存と同じmodule直接実行で検証した。Holdout A / B runnerは再実行せず、body-free receiptだけを参照した。

## 10. 推測

1・2が改善したように感じられたのは、入力が短い、または一つの前向きな行動へ焦点を合わせやすく、現行v1の弱点が相対的に表れにくかった可能性がある。

これは入力依存の読感についての推測であり、過去のv2修正効果とは帰属できない。今回の4画面はcanonical v1と一致し、v2 runtime生成は0だからである。

3・4についてのMashの違和感は、単なる好みだけではなく、観測側の文字数比率、引用再掲、同型述語重複、section役割分離不足、scrollという複数の観測結果と一致する。

## 11. 華恋の意見

Mashが指摘した「見えたことが入力を引っ張ったtemplateに見える」「Emlisからが短いだけでなく薄い」という問題設定は正しいと思う。今回の4件でも、特に3・4で同じ欠陥がはっきり出ている。厳密には2にも同じ欠陥があり、1は量だけならよいが内容固有性が足りない。

一方で、今回の結果を理由に現行v2へ語句や例外を追加するべきではない。表示されたのはv1であり、v2はHoldout Aで既に停止している。v1を4例へ合わせて直すことも、失敗したv2をv1画面から推測修正することも、case chasingになる。

方向として大切なのは、文字数を先に増やすことではない。

1. `Emlisから`が入力固有の意味責任を持つ。
2. 二段が別の役割を持つ。
3. 同じ入力断片を引用・再掲して量を作らない。
4. long / mixed inputの意味関係を崩さない。
5. その後に、重複のない2〜4文と表示比率を調整する。

この問題軸はNatural Language Surface v2設計の狙いと合っている。しかし、現行v2実装がその狙いを商品品質として達成したとは言えない。停止条件を守り、同じ方式へ例外を積まず、次方式の設計判断へ戻るのが大事だと判断する。

## 12. Mashに必要な次作業

今回の4件を追加で実機確認する必要はない。exact8やHoldout Bも開かない。

当時必要だった完全sourceの再アップロードは、正常な`mashos-api_9(64).zip`の受領・検証により解消済みである。追加のZIP再送は不要である。

次のsource変更へ進む前に残る必要事項は、Holdout Aで停止した現行v2を例外追加で継続せず、新versionの詳細設計と新しい独立Holdout cohortの作成へ着手することへのMashの明示指示である。

華恋の推奨は、まずモデル非使用条件を維持した別構造として再設計し、Developmentで意味coverageを証明できなければHoldoutを開かず停止することである。そこで成立しない場合に、限定的モデル利用を含む方式またはNatural Language Surface v2停止を再判断する。
