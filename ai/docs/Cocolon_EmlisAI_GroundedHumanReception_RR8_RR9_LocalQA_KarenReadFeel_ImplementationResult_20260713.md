# Grounded Human Reception RR8 / RR9 実装結果

作成日: 2026-07-13  
対象: `mashos-api_6(101).zip` を起点としたローカル実装  
進行権限: `none`

## 1. 対象と根拠

### 確認した事実

- 入力アーカイブの SHA-256 は `76db9ab95858200f84a504a087e9a4b1736ad246f4a951404e71fb2baa044039`。
- 添付物のうち RR8 / RR9 を定義している設計書は `Cocolon_EmlisAI_R8_GroundedHumanReception_ResponseDepth_RichnessRepair_DetailedDesign_ImplementationOrder_20260712(1).md` で、SHA-256 は `bef049a1751e636dc05bc065c90e297ab5bded23208bfd52523f8e36ae0c22f4`。
- 指定名の `...DistinctnessRepair...md` は今回の添付物と作業ツリー内には存在しない。
- 上記設計書の RR8 は automated QA の実行順と合格条件を、RR9 は可視本文を 13 軸で再読することを要求している。

### 推測

- 指定名と実在名の差は、同じ R8 修復系列における設計書の改題または後継化によるものと判断した。RR8 / RR9 の章名が一致し、今回参照可能な定義が一意だったため、この設計書を実装根拠とした。

### 華恋の意見

- 名前だけを合わせて別の仕様を推定するより、実在する章本文、完了条件、前後の RR7 / RR10 接続まで拘束して実装する方が、作業の連続性を守れる。

## 2. 実装した内容

### RR8. Local automated QA

- exact8、同一入力を二巡させる same16、独立した unseen12 の三 cohort を固定した。
- 次を機械判定する body-free QA helper を追加した。
  - exact sentence duplicate
  - closing stem / terminal lexeme / sentence skeleton / opening strategy の集中
  - rich input の一文終了率
  - short input の水増し
  - meaningful support の未利用
  - clipped anchor
  - depth proportionality、move distinctness、非列挙性
  - 可視本文 SHA-256
- exact8 observation hash、depth target、API / DB / RN 境界、raw body 非収録、source snapshot 拘束をテスト化した。
- local QA receipt を source snapshot、fixture hash、cohort 指標、実行結果へ拘束した。

### RR9. 華恋 local Product Read Feel 再実行

- exact8 と unseen 代表 1 件の合計 9 件について、設計書 §17.11 の 13 軸を可視本文そのものから再評価した。
- 各 case の visible surface SHA-256、全軸判定、fatal reason、human verdict を receipt へ固定した。
- 自動判定と人読判定を分離し、`technical pass is product pass = false`、`progression_authority = none` を維持した。
- RR9 receipt validator は、空の case 集合、human pass と fatal reason の矛盾、自動判定の人読結果への転用、進行権限の混入を拒否する。

### RR8 / RR9 で発見し、必要最小限修正した本体挙動

| 修正 | 根拠 | 必要性 |
|---|---|---|
| lived change の選択を、同一 nucleus の明示的な肯定評価へ拘束 | 別 topic の肯定語が、増悪・負担増を `うれしい変化` に誤接続し得た | 意味選択と安全境界を守るため |
| 方向が曖昧な変化は neutral reception、明示評価がある変化だけ felt glad に分離 | `増えた` は常に改善を意味しない | Emlis の感情を入力以上に捏造しないため |
| self-denial recovery の counter Move を、入力に grounded counter がある場合だけ必須化 | felt のみの自己否定入力で存在しない反対意思を作り、Gate と recovery が矛盾した | groundedness と fail-closed を両立するため |
| anchor 短縮を語境界・句境界で行い、中途切断と省略記号依存を排除 | 可視本文に mid-token clipping が出た | 商品面の自然さと referent 明瞭性を守るため |
| multi-move 文の努力表現と counter 表現を文法的に修正 | QA / 人読で不自然な格接続と、未根拠の継続意思を確認した | 人間的受容と安全境界を両立するため |
| primary Move が差し替わった後に follow profile を再計算 | 差し替え前の profile が残り、Move と surface policy がずれる可能性があった | Plan と実現責任を一致させるため |

## 3. 検証結果

### 確認した事実

| cohort | 件数 | depth 分布 | 完全重複 | closing 最大集中 | skeleton 最大集中 | rich 一文 | short 水増し | support 未利用 | 判定 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| exact8 | 8 | minimal 2 / focused 2 / layered 4 | 0 | 2 | 2 | 0 | 0 | 0 | PASS |
| same16 | 16 | minimal 4 / focused 4 / layered 8 | 0 | 4 | 4 | 0 | 0 | 0 | PASS |
| unseen12 | 12 | minimal 5 / focused 4 / layered 3 | 0 | 2 | 5 | 0 | 0 | 0 | PASS |

- observation hash は exact8 の 8 / 8 で既存値と一致した。
- exact8 depth target は 8 / 8 で一致した。
- RR0〜RR8 の順序付き contract test は 17 files / 223 tests PASS。
- RR9 validator は 1 file / 7 tests PASS。
- relevant backend regression は 22 files / 342 tests PASS。
- compile と JSON parse は PASS。
- failure は 0。warning は既存の Pydantic V1 `root_validator` deprecation 1 件のみ。
- public API contract、DB contract、RN visible contract の変更はない。
- RR9 は 9 cases × 13 axes の全項目が human pass。visible packet SHA-256 は `8f12108a1a5265852dce3d315d604b9e11eff0fe0c49dceaf02d4b8cf066c5b6`。
- 本体 owner 5 ファイルの source snapshot SHA-256 は `ed9d7463778909c97115096345d25d6ce260d21ed737a72d7c06ccd8e08687ac`。

### 推測・ローカル校正

- same16 / unseen12 の集中上限は、設計書が exact8 に示す比率を cohort 件数へ比例させて ceiling したローカル受入基準である。設計書そのものの新しい正本閾値ではない。
- opening strategy の上限は、意味責任を保った決定的 surface の偏りを検知するためのローカル校正である。
- repository に専用 static type checker 設定がないため、RR8 の type 確認は contract / unit / import / compile の組合せで行った。
- local human pass は、現行 surface が RR9 の商品読感軸へ到達したことを示す。一方で実機表示、通信経路、scroll / clipping を証明するものではない。

### 華恋の意見

- もっとも重要な改善は、`変化を認める` と `うれしいと感じる` を分けたこと。受け止めの温度は、強く肯定すれば上がるのではなく、入力が許す方向にだけ Emlis 自身の反応を置くことで生まれる。
- B の明示的な自己評価には温かい felt response が合う。対して I6-C01 のように方向が曖昧な変化は neutral に留める方が、その人の経験を上書きしない。
- A / I6-S03 は一文のまま水増しせず、B / C / I6-L03 / I6-C01 は意味機会に応じて広がり、D / I6-D02 は安全 Move を保持している。RR9 の範囲では、深さの量ではなく受容責任の違いとして読める。
- 旧 R6 receipt は当時の source に対する履歴証拠であり、今回の source に対する RR9 判定の代用にはしない。

## 4. この作業だけでは完結しない確認

今回は local RR8 / RR9 までであり、実機結果も進行判断も生成していない。次は Mash 様側で次を行う必要がある。

1. RR10: A / B / I6-L03 / I6-D02 の代表 4 件を実機で確認する。
2. 生 body SHA-256 と local expected visible hash の一致、二段表示、depth、clipping / scroll を記録する。
3. 代表 4 件が全件 PASS の場合だけ RR11 exact8 実機再確認へ進む。
4. exact8 の実機結果と Mash 様自身の Product Read Feel 判定を記録する。
5. その証拠を基に、別途 R8 進行判断を行う。

現時点の固定値は次の通り。

```text
actual_device_result_included = false
representative4_actual_device_status = not_run
exact8_actual_device_status = not_run
progression_authority = none
valid_for_progression = false
```

