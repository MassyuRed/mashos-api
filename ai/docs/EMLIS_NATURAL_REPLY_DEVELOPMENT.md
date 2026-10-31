# Emlis 本人宛の通常応答 — 2026-10-31

## 範囲と現在地

Mashが承認した通常入力→自然な返答→保存→非生成の再読のsource準備。Q3の既存SQL・公開DTOを再利用し、private `natural_reply.v1`だけを追加した。新profileは初回本人宛本文のみ。観測用5段packet、意味checkpoint、3種類の可視本文を必須にしない。分析材料は`NOT_GENERATED`であり、返答を本人の事実へ逆流させない。

10/31後続で固定4Bの実18生成と、実本文2件の隔離SQL保存・別service instance再読を確認した（末尾の実測記録）。本番HTTP・配置・新RN配布・本人端末は未実施。Free/Plusの実4B品質、Plus全蓄積からの関連履歴検索、新profileの任意問い・補足・frame訂正の反映、分析材料の生成・採用は未完成。既存本人履歴3/6件の原文受渡しの検査は、その完成とは別。過去記録にも既存Safety ownerを適用し、別Safety/自己否定の記録は通常返信の材料から除外する。過去の危機を今回の状態として扱わない。

## 接続

`emotion submit`で原入力が保存された後、`emlis_ai_reply_service`が共有`emlis_thread_factory`を使う。新profileの場合、admissionから同一の強参照taskで実行し、submit外側3秒による取消から分離する。公開metaの既存`rejection_reasons`にある`thread_reply_pending`は、書込可・provider構成有効の時だけ返す。既存サニタイザを通過することを検査済み。

`EmlisThreadService`はsource/Safetyを確認し、HTTP前のSTARTED、受信した本文のRECEIVED、最終OBSERVATIONをSQL CASで保存する。同sourceへの再取得を禁止。受信保存のACK不明は同attempt/source/context/本文のfresh readが成立した場合だけ回収し、新HTTPを起こさない。最終保存の明確なrollbackは、期限内の明示retryで保存済receiptを使う。結果不明・timeout・取消から自動再生成しない。

thread attemptとnatural処理全体は既存30秒期限。HTTPは最大25秒、GPU提供口にも23秒の単調時計StoppingCriteriaを置く。DBは期限後commitを拒否する。期限内完了・10秒応答の実測成功を意味しない。

非緊急自己否定と別Safety対応を通常providerへ送らない。新profileの専用応答は未接続で、成功した普通の返事へ置換しない。検査で見つかった「自分なんていないほうがいい。」の既存判定漏れは、明示文末形だけ既存self-denial matcherへ補足。明示否定・場所の文を誤昇格しない検査を追加した。

RNは既存DTOの`current_observation.text`を無加工表示する。通常submitのpending時だけ未作成待機を許し、表示中・foreground・同owner/attempt・処理中だけGETする。35秒は新しい自動GETを始める期間の上限で、既存GETの通信期限とは別。失敗・閉じる・owner変更では停止し、共有POST controllerをpollからabortしない。履歴の未作成を新しい生成待ちと扱わない。

## 明示的な構成

既存`COCOLON_EMLIS_THREAD_MODE`とrelease/read/write条件を維持する。その上で、サーバ側にのみ次を設定する。

- `EMLIS_AI_RESPONSE_PROFILE=natural_reply.v1`
- `EMLIS_NATURAL_REPLY_ENDPOINT`：自己hostのHTTPS `/v1/chat/completions`
- `EMLIS_NATURAL_REPLY_MODEL`：提供口の明示model名と完全一致
- `EMLIS_NATURAL_REPLY_API_KEY`：提供口と共有する秘密値。GitHub・端末へ保存しない

provider設定欠落中も保存済本文のGETは可能、新profileの書込は不可。旧threadの保存profile・旧本文・既存問い回答を変更しない。別providerへのfallbackなし。新しい依存・SQL/migration・料金/quota変更なし。

## GPU停止中に準備した提供口

`ai/tools/serve_emlis_natural_reply.py`は既存local cacheだけを使う本人限定probe。Qwen/Qwen3.5-4Bの固定revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`、既存transformers5.19.0/peft0.21.2/accelerate1.15.0/safetensors0.8.0。`HF_HUB_OFFLINE=TRANSFORMERS_OFFLINE=1`を要求し、学習・downloadをしない。CPU検証ではモデルを読み込んでいない。

baseと比べる保存候補はfit38のad8b：weights SHA256 `ad8b89e8974df9bfe7e804b8f67bbaac59e6cbb37042c3254fb58ffb64230d0a`、config SHA256 `ef4b1aef621fb4e234ce6a05601efb62a987c3cf5d40f3995ca1b72200bab145`。直近focus29の初期値として回収済みであり、新ed298856を自動採用しないためこの一つに限定する。品質優位を認定した選択ではない。56対象・112 tensor/3,833,856 paramsの保存/読込一致、非学習を起動時に確認する。後続実測で、このloaderのGPU読込・56対象/112 tensor/3,833,856 params一致・非学習を確認した。

HTTPは認証、同時1件、読込前からのSIGALRMによるprocess hard上限・明示回数上限、context8192/max_new2048、nonthinking、非sampling、EOS完了を条件にする。23秒StoppingCriteriaはtoken境界の判定で、一つのforwardの途中を止める保証ではない。process hard上限とは区別する。期限終了/打切りは成功本文にしない。提供口自身はGPUを停止・再起動・削除せず、常時host契約を決めない。モデル読込には既存学習loaderの固定情報を使用し、後続でloader/direct生成は成立したが、HTTP経由の実GPU疎通は別途必要。

以下は後続実測前の案（実結果と変更は末尾）：追加学習0、baseと保存fit38一つで8入力×2=最大16生成、採用候補の通常接続・保存再読を最大2生成、合計最大18。旧5種類は型を参照し、正解例文への一致を要求せず、未使用3入力を混ぜる。8入力の原文は実行前に固定し、固定応答集や学習教師へ採用しない。GPUの現在単価・接続・実行条件を確認し、準備/読込/保持/回収込みの時間・費用を具体化してから起動する。旧runの承認は再利用しない。

## 検証

- APIの新profile23件、既存Q2/Q3 application54件、既存Safety9件＝重複なし86成功。内訳のうち81件を同一実行、履歴3tier/途中pauseの追加4件と未接続frameを黙って落とさない1件を別実行。実Q3 SQL/RPCは隔離PGlite、provider/HTTP/Authは合成を含む。
- 提供口の実local HTTP 1件成功：認証拒否・不正model拒否・一回生成・回数上限拒否を同じ検査で確認。さらに読込処理を模した子processのhard deadline終了1件成功。GPUは0。
- RN現行34件は29成功/5失敗、変更前31件も26成功/同じ5失敗。新規3件と今回の関連5件は8/8成功。残る5件は旧Piece呼出し文字列期待1、AppRuntimeのreact-native mock欠落3、metro実行依存未用意1。未成功を全suite成功へ変換しない。
- 81件実行以前の2失敗は、自己否定の判定漏れとfactoryの旧DI互換漏れ。修復後の対象19件成功、さらに上記81件/追加4件で確認。pytest初期の素材不足（巨大sourceのcontents空、plugin/fixture不足）は原本取得を補い、製品修正の成功件数に数えない。
- 独立した読取レビューでSTARTED/ACK回収/owner/旧profile/待機表示を点検・修復。実4B本文品質・実機・正式商品受入れの判定ではない。

稼働読取：既存Render serviceはautoDeploy OFF・linked main、Piece private factoryのstartCommandを維持。Supabaseの既存thread/event列をread-only確認。今回のGPU・課金・重み変更・DB書込・配置・build・配布・main mergeは0。正式0/3・54.50％を再採点しない。


## 2026-10-31 後続実測 — 実18生成と隔離SQL保存再読

Mashの新Pod利用・Googleログインからの作業継続指示で、Pod `10o4zhfktg9nc1`/RTX PRO4000 Blackwell24GBへ直接Jupyter接続。空の新Podへ既存固定4依存・公式固定base revision・回収済fit38/ad8bを復元した。Torch2.8.0+cu128/SM120/BF16、既存loader/adapter56対象・112 tensor一致を実測。復元は学習ではなく、重み更新0。固定済み8入力×base/fit38の16生成は全EOS、約0.825〜3.427秒/生成だった。読込・通信・SQLを含む通常30秒の成立ではない。

全16本文をrootと独立read-only監査で読んだ。baseには否定を未完了へ変える本文と本人原文の全文貼返し、fit38には相手の発言を相手の感情へ変える本文と本人の一人称へなり替わる本文があり、両候補とも全体の最低線未達。短い自然な受取りは浅さだけでは不合格にしていない。未記載の可能性補完と、未確定を断定する違反も区別した。

残2生成は、元予定の新入力NR09/10をNOT_RUNとして、共通指示の最小修正後のfit38 NR02/07へ振替え。修正NR02は友人の感情追加が残存。NR07は本人への主語を修復したが、Emlisの「私」使用と不自然な自己感情報告が残った。2件を品質合格にせず、実験指示の製品source採用を取り消し、`natural_reply.py`はbea4ed1fと同一本文へ復帰。元16・修正2・両指示/sourceは非公開原本へ保持した。

元16件のうち妥当なfit38 NR01/08の実本文を使い、原材料JSON全文一致後に既存service/Q3実SQLへmanual bridgeで保存。保存2件、同Python process内の別service instanceでGET4回、既存start2回の同一本文/event・source各1回・OBSERVATION各1・分析NOT_GENERATEDを確認した。GPU時とSQL時のsource prefixは別で、新prefixへ束縛した手動artifact受渡し。追加生成・本番HTTP・API/DB process再起動・実Auth/本番Supabase/RN/本人端末成功ではない。実際に呼ぶHTTP sourceと30秒の端から端の確認は残る。

関連23検証成功（3.54秒/既存warning1）。今回の実測はTECHNICAL_CREDITで、商品採用・正式0/3・54.50％は変えない。共通1500秒枠のsetup前〜終了確認1142.077秒、当該窓の$0.58/h按分約$0.1840。レンタル開始からの総請求額・終了後保持等は未測定。終了後probe processなし/GPU2MiB・0％/ad8bとconfig不変。GPU Stop/restart/delete0、Render/本番DB/RN/main/配置/配布変更0。

非公開原本：`cocolon-natural-reply-actual-20261031.zip`、Library `libfile_0831a417bae0819196da4401cef8fd70`、SHA256 `121d0145b3ad46a09a709469a3e9dc3abde465386e8badeb2005b152c9d49fa7`、60member。raw/messages/元・修正source/予算/実環境/全失敗/SQL再読/終了確認を保持。正解文への一致や追加学習は使用していない。

今回18回の実行は閉鎖し、自動再開しない。次は追加学習に戻らず、学習前4Bへ主体・感情所有とEmlis一人称を保つ最小案を具体化する。修正後8件合格・通常接続・本人端末の完成に換算しない。STRUCTURE_MAP_DELTA_NONE（製品sourceと責務の追加変更なし）。
