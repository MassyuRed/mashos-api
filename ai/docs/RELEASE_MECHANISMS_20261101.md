# 11/1 リリース機構の実装記録

品質反復にRNのビルド・実機確認を毎回要求しない。11/1は機構・配布・運用と初回接続、11/2〜11/6はサーバー側の品質改善というMashの指示を維持する。

## この変更

- 公開プロフィールのvisibility取得がHTTP失敗した場合は502にし、公開既定値で本人情報を返さない。正常な設定未作成・非公開・コード非公開の既存方針は維持。
- Pieceの既存共有app compositionへ `GET /emotion/piece/{piece_id}/export` を追加。独立した `export_requested` / `export_ready` とowner-readを要求し、現時点の本人の保存済みartifactだけ返す。停止前後のIO確認、非再生成、quota非消費、no-storeを保持。
- RNは同じexport読取を準備時・Photos/Share直前に使い、piece ID、row version、本文/content/recipe hash、rendererの一致を確認する。画像の外部持出し後は回収不能という案内を表示する。

## 検証

共通公開APIとPieceの実ASGI compositionを、合成Auth・HTTP/DB応答で検査。Python3.12.14、FastAPI0.162.0、httpx0.28.1、pytest8.4.1の隔離環境で以下284 PASS / FAIL0 / SKIP0。

```
ai/tests/test_public_profile_visibility.py
ai/tests/piece_v2/test_b14a_piece_preview_composition.py
ai/tests/piece_v2/test_b14a_piece_v2_runtime_control.py
ai/tests/piece_v2/test_b12_shared_preview_composition.py
```

正常artifact、export/owner-read停止、未認証・他人・削除、読取中の停止、既存preview/save/history/deleteと通常共有APIを含む。実Supabase保存・本人端末・Photos/Share成功の代用ではない。

## 配置時点と残作業

この記録時点のRenderは `3577d7fdeb19158ef5e675f51960652a52c24487` のまま。新API配置、新RN配布、実モデルHTTPS提供口、実Auth→4B→DB保存→同本文再読は未完。exportの実機成功も未完。iOS専用rendererをAndroid対応済みとは数えない。

週間8タスクのうち、本人原入力/補足/訂正と返答/分析材料の分離、Plusの関連履歴選択、Analysis累積/月次snapshotは別の未完作業として継続する。上記変更を8タスク全完了や公開可能状態とは報告しない。料金680円/1480円の実ストア請求設定・両OS配布・月追加1万円内の本番提供方式・申請Console確認も残る。
