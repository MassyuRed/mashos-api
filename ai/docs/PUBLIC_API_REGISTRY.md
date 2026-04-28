# Cocolon Public API Registry

Policy version: `2026-04-20.myprofile-lookup.v1`

This registry is generated from `api_contract_registry.py` and is the canonical public-route reference.
Deprecated rows remain listed until their compatibility window is closed.

| Method | Path | Contract ID | Deprecated | Replacement | Notes |
|---|---|---|---|---|---|
| GET | `/app/bootstrap` | `app.bootstrap.v1` | `false` |  | Runtime guardrail / maintenance switch |
| GET | `/app/startup` | `app.startup.v1` | `false` |  | Auth-required startup bundle for unread / popup / lightweight prefetch only; Home hydration moved to /home/state |
| GET | `/home/state` | `home.state.v1` | `false` |  | Auth-required Home hydration bundle (input summary + global summary + notices + today question + reflection quota); app.startup intentionally excludes heavy Home counters |
| POST | `/emotion/submit` | `emotion.submit.v1` | `false` |  | Legacy payloads must remain accepted; input_feedback.comment_text stays stable while input_feedback.emlis_ai remains additive-only across observation-kernel metadata expansions |
| GET | `/emotion/reflection/quota` | `emotion.reflection.quota.v1` | `true` | /emotion/piece/quota | Current-month publish quota / capability probe for Home reflection flow |
| POST | `/emotion/reflection/preview` | `emotion.reflection.preview.v1` | `true` | /emotion/piece/preview | Preview-only reflection generation; does not canonical-save Home input |
| POST | `/emotion/reflection/publish` | `emotion.reflection.publish.v1` | `true` | /emotion/piece/publish | Publishes a preview draft and reuses Home write fan-out / cache invalidation |
| POST | `/emotion/reflection/cancel` | `emotion.reflection.cancel.v1` | `true` | /emotion/piece/cancel | Cancels a preview draft without mutating canonical Home input state |
| GET | `/input/summary` | `input.summary.v1` | `false` |  |  |
| GET | `/account/profile/me` | `account.profile.me.read.v1` | `false` |  |  |
| GET | `/account/display-name/availability` | `account.display_name.availability.v1` | `false` |  | Self-edit display name preflight availability check |
| PATCH | `/account/profile/me` | `account.profile.me.patch.v1` | `false` |  |  |
| POST | `/account/delete` | `account.delete.v1` | `false` |  | Delete lifecycle is server-owned |
| GET | `/account/profile` | `account.profile.read.v1` | `false` |  |  |
| GET | `/account/visibility/me` | `account.visibility.me.read.v1` | `false` |  |  |
| PATCH | `/account/visibility/me` | `account.visibility.me.patch.v1` | `false` |  |  |
| GET | `/account/status` | `account.status.read.v1` | `false` |  |  |
| GET | `/account/profile-create` | `account.profile_create.read.v1` | `false` |  | Account screen ProfileCreate summary surface |
| GET | `/friends/feed` | `friends.feed.read.v1` | `true` | /emotion-log/feed |  |
| GET | `/friends/manage` | `friends.manage.read.v1` | `true` |  | Retired compatibility route |
| GET | `/friends/unread-status` | `friends.unread.status.v1` | `true` | /emotion-log/unread-status |  |
| POST | `/friends/unread/read-feed` | `friends.unread.read_feed.v1` | `true` | /emotion-log/unread/read-feed |  |
| POST | `/friends/unread/read-requests` | `friends.unread.read_requests.v1` | `true` | /follow/requests/read |  |
| GET | `/emotion-log/feed` | `emotion_log.feed.read.v1` | `false` |  | Current EmotionLog feed replacement for legacy /friends/feed |
| GET | `/emotion-log/unread-status` | `emotion_log.unread.status.v1` | `false` |  | Current EmotionLog unread replacement for legacy /friends/unread-status |
| POST | `/emotion-log/unread/read-feed` | `emotion_log.unread.read_feed.v1` | `false` |  | Current EmotionLog feed read marker |
| GET | `/report-reads/status` | `report_reads.status.v1` | `false` |  |  |
| POST | `/report-reads/mark` | `report_reads.mark.v1` | `false` |  |  |
| GET | `/report-reads/myweb-unread-status` | `report_reads.myweb_unread.v1` | `true` | /report-reads/analysis-unread-status | Unread badge tracks publish-governed MyWeb artifacts only |
| GET | `/myweb/home-summary` | `myweb.home_summary.v1` | `true` | /analysis/home-summary |  |
| GET | `/myweb/reports/{report_id}/weekly-days` | `myweb.report.weekly_days.v1` | `true` | /analysis/reports/{report_id}/weekly-days | Detail is readable only for publish-governed weekly reports |
| GET | `/myprofile/reports/history` | `myprofile.reports.history.v1` | `true` | /self-structure/reports/history | History excludes non-publishable self-structure rows |
| GET | `/myprofile/latest/status` | `myprofile.latest.status.v1` | `true` | /self-structure/latest/status | Lightweight latest self-structure version probe for in-app banner polling |
| GET | `/myprofile/reports/{report_id}` | `myprofile.reports.detail.v1` | `true` | /self-structure/reports/{report_id} | Detail is readable only for publishable self-structure rows |
| DELETE | `/emotion/history/{emotion_id}` | `emotion.history.delete.v1` | `false` |  |  |
| GET | `/myprofile/follow-list` | `myprofile.follow_list.v1` | `true` | /follow/list |  |
| GET | `/myprofile/lookup` | `myprofile.lookup.v1` | `true` | /connect/lookup | Exact-match Connect ID lookup for in-app search/follow only; no display_name or Share ID fallback |
| GET | `/mymodel/qna/detail` | `mymodel.qna.detail.v1` | `true` | /piece/detail |  |
| GET | `/mymodel/qna/echoes/history` | `mymodel.qna.echoes.history.v1` | `true` | /piece/resonances/history |  |
| GET | `/mymodel/qna/discoveries/history` | `mymodel.qna.discoveries.history.v1` | `true` |  | Retired compatibility route |
| POST | `/activity/login` | `activity.login.v1` | `false` |  | Client login heartbeat / streak touch |
| GET | `/today-question/current` | `today_question.current.v1` | `false` |  |  |
| GET | `/today-question/status` | `today_question.status.v1` | `false` |  | Lightweight Today Question popup/badge state without question body or choices |
| POST | `/today-question/answers` | `today_question.answers.create.v1` | `false` |  |  |
| GET | `/today-question/history` | `today_question.history.list.v1` | `false` |  |  |
| PATCH | `/today-question/history/{answer_id}` | `today_question.history.patch.v1` | `false` |  |  |
| GET | `/today-question/settings` | `today_question.settings.read.v1` | `false` |  |  |
| PATCH | `/today-question/settings` | `today_question.settings.patch.v1` | `false` |  |  |
| GET | `/notices/current` | `notice.current.v1` | `false` |  |  |
| GET | `/notices/history` | `notice.history.list.v1` | `false` |  |  |
| POST | `/notices/read` | `notice.read.mark.v1` | `false` |  |  |
| POST | `/notices/popup-seen` | `notice.popup_seen.mark.v1` | `false` |  |  |
| GET | `/report-distribution/settings` | `report_distribution.settings.read.v1` | `false` |  | Bundled MyWeb/MyProfile distribution push settings |
| PATCH | `/report-distribution/settings` | `report_distribution.settings.patch.v1` | `false` |  | Bundled MyWeb/MyProfile distribution push settings |
| GET | `/emotion/history/search` | `emotion.history.search.read.v1` | `false` |  |  |
| POST | `/emotion/history/search` | `emotion.history.search.query.v1` | `false` |  |  |
| POST | `/emotion/secret` | `emotion.secret.update.v1` | `false` |  |  |
| POST | `/friends/request` | `friends.request.v1` | `true` | /follow/request |  |
| POST | `/friends/requests/{request_id}/accept` | `friends.requests.accept.v1` | `true` | /follow/requests/{request_id}/accept |  |
| POST | `/friends/requests/{request_id}/reject` | `friends.requests.reject.v1` | `true` | /follow/requests/{request_id}/reject |  |
| POST | `/friends/requests/{request_id}/cancel` | `friends.requests.cancel.v1` | `true` | /follow/requests/{request_id}/cancel |  |
| POST | `/friends/remove` | `friends.remove.v1` | `true` | /follow/remove |  |
| GET | `/friends/notification-settings` | `friends.notification_settings.read.v1` | `true` | /emotion-notifications/settings |  |
| POST | `/friends/notification-settings/{friend_user_id}` | `friends.notification_settings.update.v1` | `true` | /emotion-notifications/settings/{friend_user_id} |  |
| GET | `/emotion-notifications/settings` | `emotion_notifications.settings.read.v1` | `false` |  | Current EmotionNotification settings read surface |
| POST | `/emotion-notifications/settings/{friend_user_id}` | `emotion_notifications.settings.update.v1` | `false` |  | Current EmotionNotification settings update surface |
| GET | `/global_summary` | `global_summary.read.v1` | `false` |  | Daily app-wide aggregate counters; current JST day prefers synchronous refresh, historical days prefer READY artifacts, legacy table/RPC fallback retained |
| GET | `/profile-create/questions` | `profile.create.questions.v1` | `false` |  |  |
| POST | `/profile-create/answers` | `profile.create.answers.v1` | `false` |  |  |
| POST | `/mymodel/infer` | `mymodel.infer.v1` | `false` |  |  |
| GET | `/mymodel/qna/discoveries/reflections` | `mymodel.qna.discoveries.reflections.v1` | `true` |  | Retired compatibility route |
| GET | `/mymodel/qna/echoes/reflections` | `mymodel.qna.echoes.reflections.v1` | `false` |  |  |
| GET | `/mymodel/qna/list` | `mymodel.qna.list.v1` | `false` |  |  |
| GET | `/mymodel/qna/unread` | `mymodel.qna.unread.v1` | `false` |  |  |
| GET | `/mymodel/qna/unread-status` | `mymodel.qna.unread_status.v1` | `false` |  | MyModel Home reflections unread aggregated across self + followed owners |
| POST | `/mymodel/qna/view` | `mymodel.qna.view.v1` | `false` |  |  |
| POST | `/mymodel/qna/echoes/submit` | `mymodel.qna.echoes.submit.v1` | `false` |  |  |
| POST | `/mymodel/qna/echoes/delete` | `mymodel.qna.echoes.delete.v1` | `false` |  |  |
| POST | `/mymodel/qna/discoveries/submit` | `mymodel.qna.discoveries.submit.v1` | `true` |  | Retired compatibility route |
| POST | `/mymodel/qna/discoveries/delete` | `mymodel.qna.discoveries.delete.v1` | `true` |  | Retired compatibility route |
| GET | `/mymodel/recommend/users` | `mymodel.recommend.users.v1` | `true` | /nexus/recommend/users |  |
| POST | `/myprofile/follow` | `myprofile.follow.v1` | `true` | /follow/create |  |
| GET | `/myprofile/follow-requests/incoming` | `myprofile.follow_requests.incoming.v1` | `true` | /follow/requests/incoming |  |
| GET | `/myprofile/follow-requests/outgoing` | `myprofile.follow_requests.outgoing.v1` | `true` | /follow/requests/outgoing |  |
| POST | `/myprofile/follow-request/cancel` | `myprofile.follow_request.cancel.v1` | `true` | /follow/request/cancel |  |
| POST | `/myprofile/follow-requests/approve` | `myprofile.follow_requests.approve.v1` | `true` | /follow/requests/approve |  |
| POST | `/myprofile/follow-requests/reject` | `myprofile.follow_requests.reject.v1` | `true` | /follow/requests/reject |  |
| GET | `/myprofile/follow-stats` | `myprofile.follow_stats.v1` | `true` | /follow/stats |  |
| POST | `/myprofile/unfollow` | `myprofile.unfollow.v1` | `true` | /follow/delete |  |
| POST | `/myprofile/remove-follower` | `myprofile.remove_follower.v1` | `true` | /follow/remove-follower |  |
| POST | `/myprofile/monthly/ensure` | `myprofile.monthly.ensure.v1` | `true` | /self-structure/monthly/ensure | On-demand self-structure generation trigger |
| GET | `/myweb/reports/ready` | `myweb.reports.ready.v1` | `true` | /analysis/reports/ready | Shared publish governance + tier retention window |
| POST | `/myweb/reports/ensure` | `myweb.reports.ensure.v1` | `true` | /analysis/reports/ensure | On-demand MyWeb report generation trigger |
| GET | `/ranking/emotions` | `ranking.emotions.v1` | `false` |  |  |
| GET | `/ranking/input_count` | `ranking.input_count.v1` | `false` |  |  |
| GET | `/ranking/input_length` | `ranking.input_length.v1` | `false` |  |  |
| GET | `/ranking/login_streak` | `ranking.login_streak.v1` | `false` |  |  |
| GET | `/ranking/mymodel_questions` | `ranking.mymodel_questions.v1` | `true` |  | Retired compatibility route |
| GET | `/ranking/mymodel_resonances` | `ranking.mymodel_resonances.v1` | `true` | /ranking/piece_resonances |  |
| GET | `/ranking/mymodel_discoveries` | `ranking.mymodel_discoveries.v1` | `true` |  | Retired compatibility route |
| GET | `/subscription/bootstrap` | `subscription.bootstrap.v1` | `false` |  | Runtime subscription sales / plan config; plans may include additive emlis_ai metadata and marketing lines |
| GET | `/analysis/home-summary` | `analysis.home_summary.v1` | `false` |  |  |
| POST | `/analysis/reports/ensure` | `analysis.reports.ensure.v1` | `false` |  | Analysis core reportValidity meta is additive under content_json.reportValidity; no diagnosis or overclaim output |
| GET | `/analysis/reports/ready` | `analysis.reports.ready.v1` | `false` |  | Read-side contract may include additive content_json.reportValidity meta |
| GET | `/analysis/reports/{report_id}` | `analysis.reports.detail.v1` | `false` |  | Detail may include additive content_json.reportValidity meta |
| GET | `/analysis/reports/{report_id}/weekly-days` | `analysis.report.weekly_days.v1` | `false` |  |  |
| GET | `/report-reads/analysis-unread-status` | `report_reads.analysis_unread.v1` | `false` |  |  |
| GET | `/self-structure/latest/status` | `self_structure.latest.status.v1` | `false` |  |  |
| GET | `/self-structure/latest` | `self_structure.latest.v1` | `false` |  | Latest self-structure meta may include additive reportValidity |
| POST | `/self-structure/monthly/ensure` | `self_structure.monthly.ensure.v1` | `false` |  | Self-structure reports attach additive content_json.reportValidity meta |
| GET | `/self-structure/reports/history` | `self_structure.reports.history.v1` | `false` |  |  |
| GET | `/self-structure/reports/{report_id}` | `self_structure.reports.detail.v1` | `false` |  | Detail meta may include additive reportValidity |
| GET | `/connect/lookup` | `connect.lookup.v1` | `false` |  |  |
| POST | `/follow/request` | `follow.request.v1` | `false` |  |  |
| POST | `/follow/requests/{request_id}/accept` | `follow.requests.accept.v1` | `false` |  |  |
| POST | `/follow/requests/{request_id}/reject` | `follow.requests.reject.v1` | `false` |  |  |
| POST | `/follow/requests/{request_id}/cancel` | `follow.requests.cancel.v1` | `false` |  |  |
| POST | `/follow/remove` | `follow.remove.v1` | `false` |  |  |
| POST | `/follow/create` | `follow.create.v1` | `false` |  |  |
| POST | `/follow/delete` | `follow.delete.v1` | `false` |  |  |
| POST | `/follow/remove-follower` | `follow.remove_follower.v1` | `false` |  |  |
| GET | `/follow/stats` | `follow.stats.v1` | `false` |  |  |
| GET | `/follow/list` | `follow.list.v1` | `false` |  |  |
| GET | `/follow/requests/incoming` | `follow.requests.incoming.v1` | `false` |  |  |
| GET | `/follow/requests/outgoing` | `follow.requests.outgoing.v1` | `false` |  |  |
| POST | `/follow/request/cancel` | `follow.request.cancel.v1` | `false` |  |  |
| POST | `/follow/requests/approve` | `follow.requests.approve.v1` | `false` |  |  |
| POST | `/follow/requests/reject` | `follow.requests.reject.simple.v1` | `false` |  |  |
| POST | `/follow/requests/read` | `follow.requests.read.v1` | `false` |  |  |
| GET | `/public/profile/by-share-code` | `public.profile.by_share_code.v1` | `false` |  |  |
| GET | `/emotion/piece/quota` | `emotion.piece.quota.v1` | `false` |  |  |
| POST | `/emotion/piece/preview` | `emotion.piece.preview.v1` | `false` |  | Emotion input -> Piece preview; piece_text is the current display answer while reflection_text remains compat; visibility/generation/transform/safety metadata is additive |
| POST | `/emotion/piece/publish` | `emotion.piece.publish.v1` | `false` |  | Publishes an existing preview draft by status transition only; publish must not regenerate or alter piece_text |
| POST | `/emotion/piece/cancel` | `emotion.piece.cancel.v1` | `false` |  |  |
| GET | `/nexus/pieces` | `nexus.pieces.list.v1` | `false` |  |  |
| GET | `/nexus/pieces/unread-status` | `nexus.pieces.unread_status.v1` | `false` |  |  |
| GET | `/nexus/pieces/{q_instance_id}` | `nexus.pieces.detail.v1` | `false` |  |  |
| GET | `/nexus/history/resonances` | `nexus.history.resonances.v1` | `false` |  |  |
| GET | `/nexus/recommend/users` | `nexus.recommend.users.v1` | `false` |  |  |
| GET | `/nexus/emotion-log` | `nexus.emotion_log.v1` | `false` |  | Nexus Home-side EmotionLog preview proxy |
| GET | `/nexus/emotion-ranking` | `nexus.emotion_ranking.v1` | `false` |  | Nexus Home-side emotion ranking preview proxy |
| GET | `/piece/library` | `piece.library.v1` | `false` |  |  |
| GET | `/piece/unread` | `piece.unread.v1` | `false` |  |  |
| GET | `/piece/unread-status` | `piece.unread_status.v1` | `false` |  |  |
| GET | `/piece/detail` | `piece.detail.v1` | `false` |  |  |
| POST | `/piece/view` | `piece.view.v1` | `false` |  |  |
| POST | `/piece/resonance` | `piece.resonance.v1` | `false` |  |  |
| GET | `/piece/resonances/pieces` | `piece.resonances.pieces.v1` | `false` |  |  |
| POST | `/piece/resonances/submit` | `piece.resonances.submit.v1` | `false` |  |  |
| POST | `/piece/resonances/delete` | `piece.resonances.delete.v1` | `false` |  |  |
| GET | `/piece/resonances/history` | `piece.resonances.history.v1` | `false` |  |  |
| GET | `/ranking/piece_resonances` | `ranking.piece_resonances.v1` | `false` |  |  |
| GET | `/ranking/piece_views` | `ranking.piece_views.v1` | `false` |  |  |
| GET | `/subscription/me` | `subscription.me.v1` | `false` |  |  |
| POST | `/subscription/update` | `subscription.update.v1` | `false` |  | Client purchase sync / tier refresh |
