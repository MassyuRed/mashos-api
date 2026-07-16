# Cocolon EmlisAI Natural Language Surface v2 — 全Step監査・完了判定訂正

作成日: 2026-07-13  
対象設計: `Cocolon_EmlisAI_ModelFreeNaturalLanguageSurfaceV2_DetailedDesign_ImplementationOrder_20260713.md`  
対象source: `mashos-api_9(64).zip`  

## 1. 結論

「ちゃんと実装していなかった」のは **Step 3から** である。

- Step 0〜2は、設計の完了条件とlive artifactを再照合し、実体として適合している。
- Step 3は、正常系42件を生成できるだけで完了扱いにした。しかしcontract validatorが不正planを拒否できず、Content Plannerの意味選択も設計目的を満たしていない。ここが最初の確定未達である。
- Step 4は形式上の複数候補を作るが、Development 42件で文統合・文数variationが0件であり、「複数の読み順・文構成」の実質が不足している。
- Step 5は、入力引用と汎用的なreferent／predicate／terminalへ収束する。ここが最初の明確な商品・Surface生成品質上の破綻である。
- Step 6は、本文が意味を実現したかではなく、候補自身が持つmetadataを信頼している。必須意味を欠く汎用文でも14 Gateすべてを通過できる。
- Step 7の完了・freeze判定は成立しない。商品評価はcase別証拠を持たない手入力集計で、分布上限は事前freezeされていない。
- Step 8は未実装ではない。凍結済み手順で一度実行され、少なくとも`STOP`条件が有効に成立した最初の非合格Stepである。
- Step 9は最初の完全な未実施Stepである。ただしStep 8の`STOP`後なので、実施しなかった判断自体は設計どおりである。
- Step 10〜13の機能は未実装・未実行である。実装したのは停止状態を壊さないguardと証拠固定だけであり、「各Stepを実装した」と呼ぶのは不正確だった。

現行v2 production sourceをこの監査で直接直していない。Holdout Aを既に開き、その結果が`STOP`だからである。ここで同じv2へ後付け修正すると、Step 8／9の「結果を見てコードを変えない」と一回評価の系譜を破壊する。

## 2. 確認済みの事実

### 2.1 sourceと参照資料

- `mashos-api_9(64).zip`は正常なZIPである。
- SHA-256: `61b8dc77a1dd9b9bc15fc1f30c5b8ed0c988511b71c50097853aada7db48e325`
- byte size: 10,249,291
- entry: 1,837、file: 1,789、`__pycache__`等を除くfile: 1,761
- unsafe path、symlink、duplicate entryはいずれも0件である。
- non-cache 1,761 / 1,761件は直前の完全treeとbyte一致した。
- したがって、以前の`mashos-api_7(92).zip`切断は歴史上の受領事実だが、現在のsource blockerではない。
- 指定設計書SHA-256は`b2441917ee80b22c84973c4205bc1cb1a9c471037fe270391438cbd7d7694752`である。
- `Karen-Diary`は指定順に`00_READ_FIRST.md`、`memory/karen_operating_principles.md`、`memory/mash_and_karen.md`を確認した。これはCocolon仕様の正本には使わず、事実・推測・華恋の意見を分けること、目的へ接続しない代替作業を増やさないこと、停止条件を守ることの判断基準として使った。
- Cocolon側の`work_attitude_rules_for_karen`、EmlisAI関連資料、今回の設計、実source、全Step receipt／testを照合した。

### 2.2 全Step判定

| Step | 監査判定 | 実行の実態 | 主な根拠 |
|---:|---|---|---|
| 0 | 適合 | 完了 | 設計hash、owner、変更禁止contract、Holdout境界がlive artifactと一致 |
| 1 | 適合 | 完了 | v1 28件を現行sourceから再生成可能。本文とbody-free receiptを分離 |
| 2 | 適合 | 完了 | 14 family × 5件、計70件。3 cohort分離、必須field・app option・identityを再検査 |
| 3 | **不適合・最初の未達** | 実装はあるが未完成 | validatorが不正role、非bool、誤policy、上限外quote、未知strategyを受理。`felt_response` 0 / 42 |
| 4 | 部分適合 | 実装はあるが目的未証明 | 213 candidateはbounded／stable。ただしmerged group 0 / 42、文数variation 0 / 42 |
| 5 | 不適合 | 実装はあるが商品目的未達 | 汎用骨格と引用へ収束。Holdout Aの`non_template` 1 / 14 |
| 6 | 不適合 | 実装はあるが意味Gate未完成 | 汎用3文へ本文だけ置換してもmetadata維持で14 Gate全部PASS |
| 7 | **完了・freeze撤回** | 調整は行ったが完了未証明 | case別review証拠なし、pre/post再設計系譜なし、閾値事前freezeなし |
| 8 | 評価済み`STOP` | 一回実行済み | machine failure 1、分布FAIL、自然さ5 / 14、非template 1 / 14、v1優位6 / 14 |
| 9 | 未実施・正しく遮断 | 0回 | A不合格時はBへ進まない設計条件を遵守 |
| 10 | 機能未実装・未実行 | guardのみ | shadow 0回、runtime import／接続なし |
| 11 | 機能未実装・未実行 | guardのみ | owner切替0回。production ownerはcanonical v1 |
| 12 | 正式v2未実施 | v1画像4件のレビューのみ | 画像4 / 4件はcanonical v1。exact8 0、Holdout由来0 |
| 13 | 機能未実装・未実行 | v1比率分析のみ | production調整0件。自然文v2合格の前提なし |

## 3. Step 3から未達だった根拠

### 3.1 validatorがcontract違反を拒否しない

対象は`emlis_ai_grounded_reception_content_plan_v2.py`の`validate_reception_content_plan_v2()`である。

正常なDevelopment planへ次のmutationを一つずつ行っても、validatorはすべてissueなしの`()`を返す。

- 存在しないContent role
- `required="yes"`という非bool
- 現行safety policyと一致しない`safety_policy_ref`
- `max_anchor_count=99`
- 存在しないdiscourse strategy

既存Step 3 testはbuilder自身が作った正常planを同じvalidatorへ戻す検査が中心であり、不正contractのnegative testを持たない。したがって、7 / 7 PASSはcontractの拒否能力を証明していない。

### 3.2 Emlis自身の受け取りがContent層から消えている

現行Development 42件のContent Unit roleは次である。

| role | unit数 |
|---|---:|
| attention | 42 |
| connection | 30 |
| significance | 7 |
| bounded_counterposition | 3 |
| felt_response | **0** |

それにもかかわらず、42 / 42件で`attention_then_felt`を許可している。Contentに`felt_response`がないため、Generatorが汎用の「Emlisの受け取り」を表面だけで補う構造になっている。

またprimary attentionの24 / 42件が`concrete_action_recorded`である。v2が離れるべきだったv1 required moveをprimary選択に再利用しており、意味の固有性をSurfaceより前に落としている。

## 4. Step 4〜7の連鎖

### 4.1 Step 4

候補数、上限、stable ordering、body-free contractは成立している。一方で、Development 42件のどのcaseにも複数unitを一文へまとめるcandidateがなく、candidate間の文数variationもない。variationの多くはreferent、speaker presence、terminal familyであり、談話構成そのものの違いを十分に検査していない。

### 4.2 Step 5

Surface Generatorは固定的なreferent／predicate catalogへ意味を押し込み、長い入力でも「その二つのつながり」「その変化」「その願い」などへ畳む。Development選択結果では32 / 42件がsource anchorを使い、anchor候補を持つ全32件で非anchor候補より高く選ばれた。

これはMashの「見えることが入力を引っ張ったtemplateに見える」「Emlisからが短いだけでなく薄い」という実機読感と整合する。ただし、その4件はv1なので、4件だけをv2失敗の直接証拠にはしていない。v2側の直接証拠はHoldout Aの`non_template=1 / 14`と生成結果の構造分布である。

### 4.3 Step 6

Hard Gateの`required_content_coverage`等は、実際の本文意味より`realized_unit_ids`などの自己申告metadataを信頼する。

`NLS2-F10-D01`の選択本文だけを、入力固有の5 obligationを一つも表さない汎用3文へ置換し、metadataを保持したmutationでは次になった。

- 14 Gate: 全PASS
- failed code: 0
- covered unit: `cu_01 / cu_02 / cu_03`
- missing unit: 0

つまり「誤りをSoft scoreで救わない」以前に、Hard Gateが意味の欠落を検出できていない。

### 4.4 Step 7

`naturalness 39 / 42`、`non_template 42 / 42`、`v2 clearly better 37 / 42`等は、case別の判定行、本文hash、理由codeを持たない集計値である。testはその値が基準以上かを読み返すだけで、読感評価の実施や再現性を証明しない。

さらに次が欠けている。

- 一回の構造再設計について、変更前source hash、failure case、変更層、変更後結果を結ぶpre/post receipt
- semantic obligationをContent Plan／選択Surfaceまで追跡するcoverage
- 14 Gateそれぞれの独立negative path。現行では9 / 14 Gateに専用negative testがない
- predicate／terminal／skeleton集中上限の実装前baseline receipt

現行上限はDevelopment結果を見た後にStep 6／7で現れ、観測値の直上に置かれている。独立した合格基準として扱えない。

## 5. Step 8〜13の正確な位置づけ

### 5.1 Step 8は「未実装」ではなく正式な不合格

Holdout A receiptは一回評価を保持している。

| 指標 | 結果 |
|---|---:|
| evaluation run | 1 |
| machine failure | 1 |
| distribution | FAIL |
| naturalness | 5 / 14 |
| non-template | 1 / 14 |
| overclaim absence | 13 / 14 |
| v2 clearly better | 5 / 14 |
| same | 3 / 14 |
| v1 clearly better | 6 / 14 |
| overall | `STOP` |

`human_review`はcase・variantを隠した3 context majorityであり、`independent_external_reviewer=false`である。したがって外部人間QAとは呼ばない。ただしmachine failure、distribution failure、paired基準未達だけでも`STOP`は変わらない。

凍結済みStep 8／9 testには、結果を示す意図的REDが2件と、検査文字列が自分自身へ一致するtest defectが1件ある。既存testを直すとprotocol hashを壊すため変更せず、新しい監査testでASTを使い、Holdout runnerの実呼び出しが0件であることを固定した。

### 5.2 Step 9以降

Step 9を実行しなかったことは正しい。Step 10〜13について過去に「実装した」と表現したことは誤りであり、正確には「featureは未実装・未実行、停止guard／receiptだけ実装」である。

Step 12の実機4件は無駄ではない。canonical v1の画面baselineと、Mashの読感証拠として有効である。ただしv2の実機合格証拠ではない。

## 6. 推測・因果仮説

以下は確認済み事実そのものではなく、複数の事実をつないだ最も整合的な因果仮説である。

1. Step 3がv1 required moveへ寄り、入力固有の関係・評価変化・次の意図・Emlis自身の受け取りをContent層で十分に選ばなかった。
2. Step 4が文構成variationを実質的に作れず、Step 5は少ない汎用referent／predicate／terminalで不足内容を文章化した。
3. Step 6が本文意味ではなくmetadataを信頼し、汎用文を棄却できなかった。Soft scoreはanchorを加点し、入力再掲をさらに選びやすくした。
4. Step 7はcase別証拠のない集計と事後閾値で、この構造欠陥をgreenに見せた。
5. Step 8の非template 1 / 14、自然さ5 / 14、v1優位6 / 14として、未使用入力で欠陥が顕在化した。

この因果は監査証拠と整合するが、各層を置換した対照実験はしていないため、唯一の原因だとは断定しない。

## 7. 華恋の意見

このv2は、Step 8でたまたま失敗したのではない。Step 3で意味を落とし、Step 6でその欠落を検出できず、Step 7で完了と判断した時点で、商品評価へ進める状態ではなかった。

「人間の言葉を雑に処理しない」というCocolonの思想に照らすと、入力語を引用して文法的な短文にできることは成功ではない。ユーザーが置いた複数の意味を区別し、Emlisがどこを受け取ったかを固有に返せなければ、形を変えた復唱である。Mashの「1・2では改善を感じたが、3・4でだめだと思った」という読感は、今回の構造監査と矛盾しない。

華恋は、現行v2へ語句やscoreを追加して延命すべきではないと判断する。必要なのは別versionとして、次を同時に再設計することである。

1. v1 required moveに従属しないContent選択
2. semantic obligationをContent Unitから最終本文まで追跡するcontract
3. `felt_response`をSurfaceの汎用句ではなく意味unitとして成立させる責任分離
4. 複数のsentence group／読み順を実際に作るdiscourse planner
5. 本文意味を検査するHard Gateと、14 Gateすべてのnegative mutation
6. 実装前に根拠付きで固定した分布上限
7. case別・理由付き・再現可能なDevelopment review
8. 既知になったA/Bを再利用しない、新しい独立Holdout

## 8. 今回修正した範囲と、修正しなかった範囲

今回修正したのは次である。

- 全Stepの正確な状態を持つbody-free監査receipt
- Step 3／4／6の欠陥を現行sourceから再現する監査test
- 凍結testの文字列自己一致を、履歴を壊さずASTで補正する監査test
- 誤って完了・実装と読める過去結果資料への監査訂正
- 本監査報告書

変更していないもの:

- v1 production owner
- v2の4 production module
- runtime source
- public API、DB、RN contract
- Development／Holdout fixture本文
- Step 0〜9のfreeze／receipt／一回評価protocol
- 実機証拠

これは修正放棄ではない。設計が明記したHoldout後停止条件を守り、既知のHoldoutへ合わせた後付け最適化を「修正」と呼ばないための境界である。

## 9. 次に必要な判断

次のsource変更には、現行v2を停止済みの歴史として保持し、**新versionの詳細設計と新しい独立Holdout cohortを作ることへの明示的な着手指示**が必要である。

華恋の推奨は、モデル非使用条件をいったん維持したまま上記8点を新versionで再設計し、Developmentで意味coverageを証明できなければHoldoutを開かず停止する進め方である。そこで成立しない場合に初めて、モデル非使用条件そのものの上限をMashと再判断する。

## 10. 検証結果

- 新規全Step監査test: 7 / 7 PASS
- NLS v2 Step 0〜13の全zero-argument test: 62 PASS / 3 FAIL
- 3 FAILの内訳:
  - Holdout Aを`pass`と要求する凍結acceptance test: 1件。実receiptが`STOP`なので意図どおりRED
  - Holdout Bを`pass`と要求する凍結acceptance test: 1件。実receiptが`not_evaluated`なので意図どおりRED
  - Holdout runner禁止文字列がassertion自身へ一致する凍結test defect: 1件。ASTによる実呼び出し数は0
- 未分類FAIL: 0
- `compileall`: PASS
- JSON parse: PASS
- 既存freeze／receipt、v2 source、runtime sourceのlive SHA-256: 全一致
