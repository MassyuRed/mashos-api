# 11/1 リリース機構の実装記録

後続実装：natural専用の関連履歴RPC、原入力/複数回答/本人訂正の別材料化、権限・source失効時のtimeline本文抑止、Analysisの最大3補足対応と先行補足/訂正文間の矛盾照合、選択adapter SHA対指定を追加。実SQLを使うローカル検証63件とAnalysis177件はPASS。固定baseの実4B HTTPS1callは後述の契約成功。6701で本人実Auth→固定4B→実DB FINAL保存1件→同じ記録から同じ返事の再表示を確認。生成品質の合格ではない。初回接続時はRender744336c0を維持し、最新のUI接続用1296eaea配置結果は後述。累積/月次当時snapshot・月追加1万円内の常時提供方式は未完。

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

11/1にAPI `744336c0de999e271a755b441394f382548829ab` を既存Renderへ指定commitで配置し、`dep-dbj853ou01pc73enjrt0` は00:08:08 UTCにLive。RN `6675b4ed` のiOS run41254631100/#66/BUILD_NUMBER6601はArchive/IPA/TestFlight Upload成功後、Apple90683の写真利用目的文不足で拒否・配布不可。RNb8a43e5aで両keyと実Archive検査を修正し、run41260929560/#67/6701は全工程success・Apple処理通過・内部テスト中、Mashが起動を確認。実Auth→4B→DB保存→同本文再読は後述の本人確認で完了。exportの実機成功も未完。iOS専用rendererをAndroid対応済みとは数えない。

週間8タスクのうち、本人原入力/補足/訂正の別材料化とPlus権利内関連履歴選択は後述のsource/DBで実装済み。初回1件の実4B/本人実機/保存再読は完了。品質改善と本人補足/訂正からの新しい観測材料生成は未完。Analysis累積/月次snapshotも未完として継続する。上記変更を8タスク全完了や公開可能状態とは報告しない。料金680円/1480円の実ストア請求設定・両OS配布・月追加1万円内の本番提供方式・申請Console確認も残る。

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

GitHub/Google認証の継続許可後、RN6675b4edで新iOS run41254631100を起動。Archive/IPA/Upload to TestFlight/全job success、実ログBUILD_NUMBER=6601。この6601は後続Apple90683で配布不可。修正後の6701で内部配布と本人通常入力を確認。

Mashの明示承認後、新Pod6i2aa1nj683s8y/RTX3090×1/$0.51/hのHTTP8888,8000を保存/resetし環境を復元。Python3.12.3/torch2.8.0+cu128、隔離venvのtransformers5.19.0/peft0.21.2/accelerate1.15.0/safetensors0.8.0、提供tool SHA d3b7a04e38769485da995c8323aaaaf4426ff5273fcba6dff578ada85bdb77b6、base固定revision851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0aの2shardを照合。専用Bearerの値はchat/公開source/logに出さない。鍵なしHTTPS POST401、既存SelfHostedNaturalReplySourceの架空材料1callは7.771秒/42文字でHTTP/model/schema/EOS/本文形式の契約成功、再試行0。本人Auth/DB/実機や品質採用の成功ではない。

Render環境変数更新pluginがautoDeploy OFFでもmain2d2f06dの配置dep-dbj8pt49v7es739dsefgを起動し、00:52:20 UTC update_failed（create_application ImportError）。既存Live744336c0は維持。744336c0を指定し直したdep-dbj8rik9v7es739e00q0は00:55:48 UTC Live、health/bootstrap200・threads/export trueを確認。今後のenv操作はDashboard Save and deployで既存artifactを使い、main起動を避ける。

6601はApple側の90683で配布不可とMash画像/認証後のAppStoreConnectで確認。RNb8a43e5aはNSPhotoLibraryUsageDescriptionと既存Add目的文の両方を宣言し、Archive実appの2key非空検査をUpload前へ追加。新iOS#67/run41260929560/job124713864844は01:38:35 UTCにArchive/実物目的文検査/IPA/Uploadを含めsuccess。Apple処理を通過し暗号化情報を保存後、既存内部グループで6701「テスト中」を確認、Mashが6701起動を確認。

モデルHTTP serverは00:51:54 UTCから1477秒で停止、所有process不在・GPU1MiB/0％を確認。新PodのStop/新規作成/削除/チャージは華恋0。残り最大3要求/300秒だけを新配布候補の初回確認へ残す。APIはMODE=read_only＋natural_reply.v1を維持し、同source744336c0/既存artifactのdep-dbj96l67bikc73ep8hugが01:18:55 UTC Live。保存済みreaderをlegacyへ戻さない。実DBの本文/owner/inputIDなし集計では、00:55:48 UTC以降のnatural更新/FINAL保存/active/CALL_STARTEDは全0件。この段階の通常実Auth→4B→DB保存→本人同本文再読は未完で、後続の6701確認で完了した。月追加1万円内の常時提供は未完。

今回product source/公開contractの追加変更なし、STRUCTURE_MAP_DELTA_NONE。詳しい本人初回確認/8task残件はRNの最新weekly第9回§37。


## 11/1 6701の本人初回保存・再読の結果

Mashから6701起動の回答を受け、API744336c0の既存artifactをMODE=developmentへ反映。dep-dbj9lvh42hec73cd65ugは01:51:36 UTC Live。モデルは同固定base/同専用Bearerで01:51:45 UTCに最大3要求300秒で再開。本人へ通知送信を避けた感情入力1件→返事を閉じる→同じ記録の「Emlisの返事を開く」を案内し、同じ返事が表示されたとの回答を受領した。

Supabaseのnatural_reply.v1の本文/owner/inputIDを返さない集計で、01:52:16 UTCのFINAL/CALL_STARTED/active全0から、01:53:53 UTCに更新1/FINAL1/CALL_STARTED1/active0。再読回答後01:57:04 UTCにも同じ1/1/1/0を確認。保存済みFINAL artifact.schema_versionはcocolon.emlis.recipient_reply.v1。初回実Auth→モデル→DB保存→本人同本文再読の配線を確認し、synthetic1call/合成テストや品質採用と混同しない。

FINAL保存・active0を確認後01:54:48 UTCにモデルserverを停止要求。再開は切上げ184秒、先行1477秒との合計1661秒で承認済み1800秒以内。所有model process不在・GPU1MiB/0％を確認。Podは稼働中($0.51/h)、華恋のStop/新規作成/削除/チャージ0。学習0・候補品質反復0。

最終read_onlyはdep-dbj9pqvb9u1s73de4160（01:59:49 UTC Live、source744336c0）で反映し、画面reload後の保存値read_onlyも照合した。先行dep-dbj9o1flk1mc738ksqgg（01:55:59 UTC Live）は後の保存値確認でdevelopmentのままと判明したため、編集値を入力/確定して保存し直した。Liveだけでmode反映済みとせず、最終保存値まで確認した。11/2〜11/6はサーバー側品質改善、候補ごとのRN再ビルドは不要、最終候補のみ接続という指示を維持。Piece実機/OS出力、Android、課金実ストア、累積/月次snapshot、常時提供原価、申請Console/更新契約の本人確認、旧V4 metrics19失敗は残る。詳細はRN weekly第9回§37。追加product source/DB/依存変更0、STRUCTURE_MAP_DELTA_NONE。


## 11/1 応答ポップアップからのPiece作成接続

Mashの明示UI指示（RN weekly第9回§38）に合わせ、新natural FINALを既存のoriginal-only Piece作成へ接続した。従来のhandoffはMEANING_UPDATE必須で、新naturalが意図的に保存しない意味checkpointを要求して422となっていた。natural_reply.v1/Q3だけを別検査し、同本人/同原本、FINAL/NOT_GENERATED/no active・answer・meaning、現在OBSERVATION、保存CALL_STARTED→RECEIVED、同observationと同attemptの成功finishを照合する。正規の保存再試行でreceiptが旧attemptの場合は保持する。recipient本文は整合照合だけに使い、Pieceの素材/lineageへ流さず、元memo/memo_actionと完全原本JSONを既存作者へ渡す。

自然profileの履歴は保存済みguard指定のrelated_contextへ揃えた。新migration20261101022630_piece_natural_reply_context.sqlは既存issue/save/visual-changeの3RPCに限り、context呼出しと旧365/3650日の追加上限をnaturalだけ現在の権利へ合わせる。旧Q3、本人/原本/版、lock順、待機後の時計、保存枠、feedback照合、関数owner/ACLは保持する。新table/公開API/DTO/依存/モデル設定は追加しない。

対象検証175 PASS/FAIL0/SKIP0（PGlite0.5.8の実SQL＋合成Auth/provider）。既存natural保存/再読、旧handoff/source HTTP、新natural原本投影、3tierの保存cohort、Premium4000日前、後からの新記録で非置換、receipt再保存を含む。Pieceの実SQL preview/visual/saveは3tier成功、原本/使用履歴の編集・削除後は3操作×3tierの9拒否、関数3本のservice_role限定を確認。ネイティブPostgreSQL並行実行/本人端末/画像品質の合格ではない。RNの対象209検査も成功し、通常footer2ボタン/両入口/一回要求/閉じる/本人・focus・runtime変化と保存回復保持を確認した。無関係なMetro bundle検査は今回のローカル対象から除いた。

配置前の実DBは3RPCが旧contextを使用し、全3本SECURITY DEFINER/search_path=pg_catalog、anon/authenticated実行不可・service_role実行可と確認。migration適用/API指定版配置/iOS新buildとApple内部配布の結果は後続へ記録する。GPUはMashから停止報告を受領し、華恋の再起動・学習・実provider呼出し0。


## 実DB適用・指定API配置・6801の内部配布

RN `ef9f7bfca874734d6fdb937f94bccac32bcb7de0` のiOS #68/run41266287100/job124729659513は02:55:28 UTCまでに全工程success。実署名Archive、写真Usage/Add両keyの実物検査、IPA export、TestFlight uploadが成功。App Store Connectで1.0(6801)のApple処理通過を確認し、既存実装と同じ暗号化情報を保存。中断後はdialog消失を確認して再送せず、既存内部グループ「Emlis テスト版配布」のbuild一覧で6801「テスト中」を確認した。テスター追加/外部配布/App Store公開は0。新UIの本人端末での表示・Piece作成/保存/OS出力は未確認で、6701の初回生成/同本文再読確認とは区別する。

Supabase `piece_natural_reply_context` migrationの適用successを確認。既存3RPCのnatural context/現在権利ガード、SECURITY DEFINER/search_path=pg_catalog、anon/authenticated実行不可・service_role実行可を実metadataで再照合。advisor分類別件数は前後不変（既存警告は未解消、全件同一bytesという意味ではない）。本人本文の追加読取/probe保存は0。

API `1296eaea589a09fe91f84689c6d55d67e577ec23` の指定commit配置 `dep-dbjafelg1s2s73f6mah0` は02:46:53 UTC Live。healthz200/ok、app/bootstrap200、Piece private5ON/public3OFF、保存済みCOCOLON_EMLIS_THREAD_MODE=read_onlyを確認。配置後app error logsは取得範囲で0件（既存起動warningの解消ではない）。natural profile/専用endpoint/modelと既存free resource/autoDeploy OFFを維持し、新規有料resource/plan/GPU起動/provider実呼出し/学習0。

同headの自動CIはJS契約/iOS canvas/Pods/Android source・exportがsuccess。iOS metricsは既存V4 output_v4_*の19失敗（1/20成功）が残る。既存native129/129、V9 46/46、bitmap44/44は成功。前source963944bbとのnative metrics実装/検査差分0で、今回の対象RN209 PASSとは分けて記録する。全CI成功やPiece本人画像の受入れとはしない。

全体現在地/全体構造/全file地図/EmlisとPieceのcurrent map/Piece正本入口/API既存運用記録へ同じ現在状態を反映。残る8タスク・累積/月次snapshot・Android実配布・実ストア料金/購入/復元・月追加1万円内の本番常時提供・申請Console/本人基本機能一巡は、今回のUI修正で完了へ変更しない。11/2〜11/6はサーバー側品質改善、候補ごとのRN再build不要、最終候補だけ接続という配分を維持する。


## 11/1 6801本人確認後のPiece生成状況

RN weekly第9回§39。Mashは応答popupを指示通りと確認。一方Pieceはsource-ref取得200→preview422で未作成（03:11:14/17 UTC、Supabase errors0）。native preview見出しが時計と重なるためRNの既存Modal内に専用SafeAreaProvider/全4edgeを追加し、機能全体を未提供とする古い固定案内も修復。対象RN231 PASS、新配布/本人座標確認は同§39へ。

API1296eaeaのnatural引継ぎは稼働しているが、preview生成は4Bを呼ばず既存CMEEの有限Piece作者を使用。CPU架空対応価値観文は生成成功、通常の動作確認メモはexpression_meaning_not_admittedを再現。一般入力対応は未完成。本人の厳密な内部拒否理由は本文未取得のため未特定。今回API製品source/DB/flags/deploy/生成基準の変更0、GPU再起動/実モデル呼出し0。原文画像貼付や拒否緩和で完成扱いしない。

## 11/1 第9回§41/§43 — ユーザー本文だけのPieceとEmlis画像ブランド

先行APIba0de502はLiveで、本人が記録した本文だけを必要に応じて整形し、選択感情の説明文は画像本文へ加えない。private selection contextと原本/evidenceは保持する。7001の画像生成/本人一覧/Photos保存はMash本人確認済み。

§43候補は既定のpublic renderer ios.v1=Cocolonを維持し、compiled v2対応iOSのexact X-Piece-Renderer headerだけをpreferred ios.v2=Emlis/allowed(v1,v2)へ交渉する。旧/欠落/未知headerは既定版。preview serviceのfirst issue/並行issue返却/同key再読/visualとsave serviceの初回/保存済み再送は保存rowのrendererを検査・保持する。preferred版への再生成/上書きはしない。renderer/TTL設定なしの既存専用visual/save compositionは互換Noneを保ち、新規発行には従来どおりruntimeを必須とする。recipe内部ID cocolon_text_mark/version1/DB schema/保存JSON・hash・枠/公開制御は不変、migrationなし。

対象4fileのPython255 PASS/11 native SQL deselected（隔離DBが必要なためこのローカル実行では未実行）/既存warning1。交渉・旧preview再読・visual版保持・新旧保存/保存済み再送拒否を合成Auth/実ASGIと実serviceで検査した。RNはv1/v2のbrand測定/完成後保持/export token-binding経路を検査。新API指定配置・署名build/Apple処理/既存内部配布は後続。旧V4 metrics19失敗・legacy canvas失敗/原因未確定を解消した変更ではない。GPU再起動/新実provider呼出し/DBデータ変更0。


### §43 追加CIでのfixture補正

API3407402の実PostgreSQL CI41283428092はreviewed issuanceのHTTP27 FAIL/105 PASSで停止した。新allowed_renderersを拒む旧test wrapperのexact kwargs集合が原因で、実service/RPC前に503となった。集合へ新引数を追加し既定集合をexact照合、新v1/v2の実SQL初回発行/同key非生成再読/旧client未知v2拒否も追加した。製品3sourceは3407402から変更なし、再CI結果は後続。Render dep-dbjebcflk1mc7390mnr0は3407402で07:11:03 UTC Live。新署名buildはRN7464f858/#71/run41283646380で進行中。

## 11/4 — Pieceの画像書き出し記録候補

既存の本人専用exportを使い、対応iOSのアプリがPNGの寸法・sRGB・ハッシュを確認した場合に、OSへ渡す前の画像生成記録を残す。GETのJSONは維持し、対応アプリと有効なAPIだけが `X-Piece-Export-Receipt: 1` で確認する。POSTは本文、画像、端末内のファイル位置、共有先を受け取らない。APIは本人と現行の版・本文ハッシュ・描画レシピを確認し、SQLが同じ行をロックしてハッシュと形式を照合する。書き出し記録は画像作成までの記録で、写真保存や外部サービスへの送信の結果は含まない。

移行 `20261104002458_piece_v2_export_receipt.sql` は既存の `piece_export_receipts` にハッシュ2項目とservice-role専用RPCを追加する。同じ本人・キー・内容を再送すると同じ記録IDを返し、同じキーで内容が異なる場合は拒否する。既存行の書換なし。

`export_receipt_ready` の既定値はfalse。後の配置でこの経路を有効にする場合は、DB移行とRPC/権限の確認、対応APIの配置、明示的なready設定の順に行う。対応版への切替前は従来のexportを使用する。途中で対応状態が変わった書き出しはOSに渡さず、改めて準備する。旧APIへの切戻し時には、旧factoryがこの引数を受け取らないため起動引数から除く。今回の作業では本番DB適用・Render配置・有効化は未実施。

11/4の読取では、Renderのmashos-apiはmain・自動配置OFF。Supabaseには既存のPiece行とRLS有効の書き出し記録テーブルがあり、新配色制約・画像ハッシュ欄・書き出しRPCはまだない。移行履歴の版番号には既存の適用時に採番したものがあるため、まとめ反映の際は対象の2 SQLを個別に照合する。

| アプリとAPIの組合せ | 動作 |
|---|---|
| 旧アプリ＋対応API | 従来の配色と書き出しを使用。既存2配色の履歴を読み出す。 |
| 対応アプリ＋旧API、新配色の保存前 | 既存の作成POSTで適格な形式を選ぶ。APIが返す従来の配色を表示し、従来の書き出しを使用。 |
| 対応アプリ＋対応API、記録OFF | 先に配色SQLを適用した環境で拡張配色を提供。従来の書き出しを使用。 |
| 対応iOSアプリ＋対応API、記録ON | 対応画像の出力確認と書き出し記録を経て、OSへ渡す。 |


新配色の保存が始まった後は、配色対応前のAPIへ戻すと、旧配色と新配色が混ざった本人履歴が503になることを合成データで再現した。書き出し記録を切り戻す場合は、配色を理解する `26e1be3f6e62c766dd3abe183bfce23217a9c84c` 以降を候補とする。同版では対応アプリが両配色を再読し、旧アプリへは従来配色を返した。
