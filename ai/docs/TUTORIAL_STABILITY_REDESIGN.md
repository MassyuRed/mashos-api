# Tutorial Stability Redesign

## 目的
実機ごとの画面サイズ差・Safe Area 差・スクロール途中の測定ズレ・透過穴タップの不安定さをまとめて解消し、チュートリアルのスポットライト位置と押下動作を安定させる。

## 根本原因
従来実装では、各画面ごとに以下が分散していた。

- `setTimeout(80)` 後に measure
- 必要なら `scrollTo({ animated: true })`
- `setTimeout(260)` 後に再 measure
- スポットライトの穴を通して下層 UI を直接押させる
- `windowHeight` や固定マージンで可視領域を推定する

この方式では、以下の差異でズレが発生しやすい。

- 実機性能差によるアニメーション完了タイミングの差
- Safe Area / 画面高さ / フォントスケール差
- ScrollView の慣性や途中フレームでの測定
- オーバーレイと下層 UI の z-order / hit area の差
- composite component と native view の測定差

## 新アーキテクチャ

### 1. 共通測定レイヤーへ統一
`components/TutorialOverlay.js` に、以下の共通機能を集約した。

- `waitForTutorialFrames(frameCount)`
- `measureTutorialTarget(targetRef, rootRef, options)`
- `buildTutorialViewport(...)`
- `syncTutorialSpotlightTarget(...)`

これにより、各画面は「対象 ref」「スクロール ref」「overlay metrics」を渡すだけで、
同じ測定・スクロール・再測定の流れを利用できる。

### 2. タイマー待ちを廃止し、フレーム待ちへ変更
固定の 80ms / 260ms ではなく、

1. layout 後に 2 フレーム待機
2. 1 回目を measure
3. 必要なら即時スクロール
4. さらに 1〜2 フレーム待機
5. 再 measure

という流れへ変更した。

### 3. チュートリアル自動スクロールは即時化
チュートリアルの補助スクロールは演出より安定性を優先し、
`scrollTo({ animated: false })` に統一した。

これにより「スクロール途中を測って穴がズレる」問題を抑える。

### 4. overlay の見た目と実タップ領域を分離
単一 CTA の action step では、下層 UI を直接押させず、
`TutorialOverlay` がスポットライトの上に透明 `Pressable` を載せる。

- 見た目: 穴で対象が見える
- タップ: overlay 側の proxy press が処理

これにより、端末差によるタップ抜け・z-index 差異を抑える。

### 5. overlay 自身の実レイアウトを可視領域計算に利用
`TutorialOverlay` は自分自身の `onLayout` とカード位置を計測し、
`onMetricsChange` で親へ返す。

親画面はその metrics を使って、

- 上側にどれだけ空間があるか
- 下側にどれだけカードに隠れず表示できるか

を実値ベースで計算する。

### 6. 測定対象は native view に固定
測定対象・ルートになる要素には `collapsable={false}` を付け、
ネイティブ view として残るように統一した。

## 適用範囲

### InputScreen
- 共通測定・再測定へ移行
- overlay metrics 導入
- Step 6 の `OK` を proxy press 化

### MyWebScreen
- 共通測定・再測定へ移行
- overlay metrics 導入
- top / bottom card placement を viewport 計算に反映

### MyModelScreen
- 共通測定・再測定へ移行
- overlay metrics 導入
- Step 16 の `作成する` を proxy press 化
- Step 17 の `Reflections` を proxy press 化
- チュートリアル Reflection 作成モーダルにも同じ基盤を適用
- モーダル内の TextInput focus / 保存ボタンも proxy press 化
- モーダル内 ScrollView のスクロール位置追跡を追加

### MyModelReflectionsScreen
- メイン画面を共通測定・再測定へ移行
- overlay metrics 導入
- `MyModel：自分` セレクタを proxy press 化
- ユーザー選択モーダルにも同じ基盤を適用
- 華恋の行を proxy press 化
- モーダル内 ScrollView のスクロール位置追跡を追加

### FriendsScreen
- 共通測定・再測定へ移行
- overlay metrics 導入
- 完了ボタンを proxy press 化
- 主要ターゲットに `collapsable={false}` を追加

## Proxy press の対応表
- Input Step 6 → `handleOk`
- MyModel Step 16 → `openTutorialCreate`
- MyModel Modal Step 16（入力段階）→ `TextInput.focus()`
- MyModel Modal Step 16（保存段階）→ `saveTutorialReflection`
- MyModel Step 17 → `openReflections`
- Reflections Step 19（切替前）→ `openUserPicker`
- Reflections Picker（華恋行）→ `selectTargetUser(firstUserId)`
- Friends Step 23 → `handleCompleteTutorial`

## 実装上の意図
- スクリーンごとの小手先調整ではなく、共通基盤に寄せる
- 「見た目のスポットライト」と「押せる範囲」を分ける
- window 推定値ではなく、実 layout を使う
- アニメーション完了時間の仮定を置かない

## 今後の拡張ポイント
- 追加 step が増えても ref と action を足せば再利用可能
- `targetTouchPadding` / `targetHitSlop` による step ごとの押下補正
- 必要なら orientation change / font scale change 時の再同期強化
