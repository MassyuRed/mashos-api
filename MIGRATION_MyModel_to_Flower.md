# Migration: MyModel → Flower (MashOS Core)

## 目的
- `mymodelCore.ts` が「花の演出」を担っており命名が実態と乖離していたため、
  **`flowerCore.ts`** にリネーム。公開APIも `MashOS.flower.*` に統一。

## 変更点
- 新規: `flowerCore.ts`（`annotate` / `analyze` を提供）
- 置換: `index.ts` で `MashOS.mymodel` → `MashOS.flower`（**`MashOS.mymodel` は非推奨エイリアスを暫定残置**）
- 型: `Feature` を `'input' | 'myweb' | 'flower'` に変更
- 設定例: `config.example.ts` の `perFeature.flower` を追加（`mymodel` を削除）

## 互換性
- 既存コードの `MashOS.mymodel.annotate()/analyze()` は動作しますが、
  **実行時に deprecation warning** が表示されます。早めに以下へ置換してください。
  - `MashOS.mymodel.annotate(data)` → `MashOS.flower.annotate(data)`
  - `MashOS.mymodel.analyze(emotions, memo)` → `MashOS.flower.analyze(emotions, memo)`

## 例：一括置換
- VSCode 検索置換（正規表現）:  
  - `MashOS\.mymodel\.` → `MashOS.flower.`

## 注意
- `app.py` の MyModel API は **テキスト応答のAI** であり、`flowerCore.ts` とは別レイヤーです。
- 将来的に alias を削除予定：CI で WARNING をエラー化する前に移行を完了してください。
