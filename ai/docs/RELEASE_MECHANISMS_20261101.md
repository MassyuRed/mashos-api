# 11/1 リリース機構の実装記録

後続実装：natural専用の関連履歴RPC、原入力/複数回答/本人訂正の別材料化、権限・source失効時のtimeline本文抑止、Analysisの最大3補足対応と先行補足/訂正文間の矛盾照合、選択adapter SHA対指定を追加。実SQLを使うローカル検証63件とAnalysis177件はPASS。実4B生成・実機は未実施。Renderは後述の744336c0をLive配置済み。累積/月次当時snapshot・月追加1万円内の常時提供方式は未完。

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

11/1にAPI `744336c0de999e271a755b441394f382548829ab` を既存Renderへ指定commitで配置し、`dep-dbj853ou01pc73enjrt0` は00:08:08 UTCにLive。RN `6675b4ed` のiOS run41254631100/#66/BUILD_NUMBER6601はArchive/IPA/TestFlight Uploadまで成功。Apple処理/配布対象・端末導入、実モデルHTTPS提供口、実Auth→4B→DB保存→同本文再読は未完。exportの実機成功も未完。iOS専用rendererをAndroid対応済みとは数えない。

週間8タスクのうち、本人原入力/補足/訂正の別材料化とPlus権利内関連履歴選択は後述のsource/DBで実装済み。実4B/本人実機・新しい観測材料生成は未完。Analysis累積/月次snapshotも未完として継続する。上記変更を8タスク全完了や公開可能状態とは報告しない。料金680円/1480円の実ストア請求設定・両OS配布・月追加1万円内の本番提供方式・申請Console確認も残る。

## 後続 — 履歴/補足・候補読込の機構

`20261101010000_emlis_natural_related_context.sql` は旧Q3 contextを維持し、新naturalだけが全閲覧権利内の先行記録から文字n-gram一致で関連候補を最大Plus3/Premium6件選ぶ。Plus365日の既存閲覧権利は維持。Premiumの余分な3650日探索制限を外す。保存時はowner/原文MD5/thread revision/権利/順序/CASを再確認し、再読時は保存guardの同じIDだけを再取得する。生成後に別記録が増えても保存本文を再検索で失効させない。変更で無効になった過去threadは候補から除き、古い補足を新原文へ付けない。旧Q3の保存profileは現在設定を継承しない。

モデル材料では原入力、順番付き本人ANSWER、本人frame訂正を別欄にする。AIの問いは回答を読む文脈として明示し、生成済み観測/返答は本人事実へ使わない。本人の補足・訂正にも既存Safetyを適用し、対象外の過去資料は補足だけでなく記録全体を除く。権限変更/参照元編集・削除で無効になったnatural本文はcurrentだけでなくtimelineからも除く。

Analysisの保存source adapterは最大3回答を全ID/round/owner束縛で保持する。compilerは同じ記録の先行する有効な原入力/補足/置換文と矛盾照合し、二重訂正、補足そのものへの未解決訂正、解釈未対応を成功へ変えない。累積更新や当時の月次保存寿命を完成させた変更ではない。

提供toolは `--adapter-weights-sha256` / `--adapter-config-sha256` を対で受け、選択候補の保存hashをロード前後に検査する。未指定は旧fit38固定、base revision/依存/112tensor/値一致/非学習/18要求・1800秒/23秒生成上限は保持。重みや指示を同じAPI契約内で更新するたびにRNをビルドする必要はない。新候補を自動採用せず、常時GPU提供/新しい費用契約へ切り替えない。

検証：PGlite0.5.8の実Q2/Q3+新migration/実Python store/serviceを使用し、合成providerでnatural/Q3/提供toolの63 PASS / FAIL0 / SKIP0。Free除外、直近枠より古い関連選択、Premium4000日前、Plus権利、保存cohort固定、履歴/ANSWER revision/tier変更拒否、旧Q3再読、3回答・訂正・Safety・service専用権限、adapter identityとHTTP上限を含む。Analysisは新複数回答・既存保存/保存再読、既存verticalの補足/訂正関連177 PASS / FAIL0 / SKIP0、無関係なvertical425件は未実行。合成providerの結果を実モデル品質・本人実機へ換算しない。

実DB定義を照会し、変更前emlis_thread_commitの本文が旧migrationの7580文字と完全一致することを確認した後、Supabaseへmigrationを適用した（成功）。新RPC存在、service_roleのみ実行可、anon/authenticated実行不可、natural保存guardの存在を実DB metadataで確認。ユーザーデータへのprobe生成/保存は行っていない。稼働APIの更新は下記の通り完了。

## 11/1 配置・送信の実結果

Renderの既存service `srv-d4ppfpm3jp1c73952bj0` はAPI744336c0/dep-dbj853ou01pc73enjrt0をLive確認。main/autoDeploy OFFと既存factory commandを保ち、export_requested/export_readyだけ追加ON。preview/save/owner-read/export/owner-deleteの各pair ON、public-write/public-read/visibility-toggle OFF。renderer ios.v1/TTL600秒を保持。pluginにstart command/source指定操作がないためDashboardで保存/指定commit deployし、新serviceや有料planは作成していない。

公開healthz200/ok、app/bootstrap200と上記flag、新exportの未認証GET401・emotion.piece.export.v2/PIECE_AUTH_REQUIRED・no-storeを実HTTP確認。配置開始後に取得したapp error logsは0件。本人データへのprobe保存は未実行。API7bbb4661のAnalysis CI41253745568もsuccess（1634 PASS＋12020 subtests、owner1 PASS・194 deselected、合成保存再読success）。

GitHub/Google認証の継続許可後、RN6675b4edで新iOS run41254631100を起動。Archive/IPA/Upload to TestFlight/全job success、実ログBUILD_NUMBER=6601。Apple処理/配布対象、本人導入/通常操作は未確認。

Runpodの既存Pod10o4zhfktg9nc1は停止中・GPU割当先利用不可。開始表示$0.57/h、残高$5.73、container50GB/persistent storageなし。同型新Podへの自動移行は自動承認審査が新資源・データ移動・追加課金の可能性を理由に拒否し未実行。新Pod/GPU起動/学習/生成0。既存cacheの存否、実Connect HTTPS、専用Bearer、Render natural profile/endpoint/model/key設定は未完。月追加1万円内の常時提供は未成立。

今回product source/公開contractの追加変更なし、STRUCTURE_MAP_DELTA_NONE。詳しい本人端末/8task残件と次の許可対象はRNの最新weekly第9回§34。
