# Cocolon Public API Registry

Policy version: `2026-03-20.mymodel-qna-unread-status.v1`

This policy revision adds `/mymodel/qna/unread-status` so the MyModel Home Reflections
NEW badge stays API-owned across the viewer's accessible reflection set (self + followed
owners), while preserving the single-target `/mymodel/qna/unread` contract.

| Method | Path | Contract ID | Deprecated | Replacement | Notes |
|---|---|---|---|---|---|
| GET | `/app/bootstrap` | `app.bootstrap.v1` | `false` |  | Runtime guardrail / maintenance switch |
| GET | `/app/startup` | `app.startup.v1` | `false` |  | Auth-required startup bundle for unread / popup / lightweight prefetch only; Home hydration moved to `/home/state` |
| GET | `/home/state` | `home.state.v1` | `false` |  | Auth-required Home hydration bundle (input summary + global summary + notices + today question + reflection quota); `/app/startup` intentionally excludes heavy Home counters |
| POST | `/emotion/submit` | `emotion.submit.v1` | `false` |  | Legacy payloads must remain accepted; `input_feedback.comment_text` stays stable while `input_feedback.emlis_ai` remains additive-only across observation-kernel metadata expansions |
| GET | `/emotion/reflection/quota` | `emotion.reflection.quota.v1` | `false` |  | Current-month publish quota / capability probe for Home reflection flow |
| POST | `/emotion/reflection/preview` | `emotion.reflection.preview.v1` | `false` |  | Preview-only reflection generation; does not canonical-save Home input |
| POST | `/emotion/reflection/publish` | `emotion.reflection.publish.v1` | `false` |  | Publishes a preview draft and reuses Home write fan-out / cache invalidation |
| POST | `/emotion/reflection/cancel` | `emotion.reflection.cancel.v1` | `false` |  | Cancels a preview draft without mutating canonical Home input state |
| GET | `/input/summary` | `input.summary.v1` | `false` |  |  |
| GET | `/account/profile/me` | `account.profile.me.read.v1` | `false` |  |  |
| GET | `/account/display-name/availability` | `account.display_name.availability.v1` | `false` |  | Self-edit display name preflight availability check |
| PATCH | `/account/profile/me` | `account.profile.me.patch.v1` | `false` |  |  |
| POST | `/account/delete` | `account.delete.v1` | `false` |  | Delete lifecycle is server-owned |
| GET | `/account/profile` | `account.profile.read.v1` | `false` |  |  |
| GET | `/account/visibility/me` | `account.visibility.me.read.v1` | `false` |  |  |
| PATCH | `/account/visibility/me` | `account.visibility.me.patch.v1` | `false` |  |  |
| GET | `/account/status` | `account.status.read.v1` | `false` |  |  |
| GET | `/friends/feed` | `friends.feed.read.v1` | `false` |  |  |
| GET | `/friends/manage` | `friends.manage.read.v1` | `false` |  |  |
| GET | `/friends/unread-status` | `friends.unread.status.v1` | `false` |  |  |
| POST | `/friends/unread/read-feed` | `friends.unread.read_feed.v1` | `false` |  |  |
| POST | `/friends/unread/read-requests` | `friends.unread.read_requests.v1` | `false` |  |  |
| GET | `/report-reads/status` | `report_reads.status.v1` | `false` |  |  |
| POST | `/report-reads/mark` | `report_reads.mark.v1` | `false` |  |  |
| GET | `/report-reads/myweb-unread-status` | `report_reads.myweb_unread.v1` | `false` |  | Unread badge tracks publish-governed MyWeb artifacts only |
| GET | `/myweb/home-summary` | `myweb.home_summary.v1` | `false` |  |  |
| GET | `/myweb/reports/{report_id}/weekly-days` | `myweb.report.weekly_days.v1` | `false` |  | Detail is readable only for publish-governed weekly reports |
| GET | `/myprofile/reports/history` | `myprofile.reports.history.v1` | `false` |  | History excludes non-publishable self-structure rows |
| GET | `/myprofile/latest/status` | `myprofile.latest.status.v1` | `false` |  | Lightweight latest self-structure version probe for in-app banner polling |
| GET | `/myprofile/reports/{report_id}` | `myprofile.reports.detail.v1` | `false` |  | Detail is readable only for publishable self-structure rows |
| DELETE | `/emotion/history/{emotion_id}` | `emotion.history.delete.v1` | `false` |  |  |
| GET | `/myprofile/follow-list` | `myprofile.follow_list.v1` | `false` |  |  |
| GET | `/mymodel/qna/detail` | `mymodel.qna.detail.v1` | `false` |  |  |
| GET | `/mymodel/qna/echoes/history` | `mymodel.qna.echoes.history.v1` | `false` |  |  |
| GET | `/mymodel/qna/discoveries/history` | `mymodel.qna.discoveries.history.v1` | `false` |  |  |
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
| POST | `/friends/request` | `friends.request.v1` | `false` |  |  |
| POST | `/friends/requests/{request_id}/accept` | `friends.requests.accept.v1` | `false` |  |  |
| POST | `/friends/requests/{request_id}/reject` | `friends.requests.reject.v1` | `false` |  |  |
| POST | `/friends/requests/{request_id}/cancel` | `friends.requests.cancel.v1` | `false` |  |  |
| POST | `/friends/remove` | `friends.remove.v1` | `false` |  |  |
| GET | `/friends/notification-settings` | `friends.notification_settings.read.v1` | `false` |  |  |
| POST | `/friends/notification-settings/{friend_user_id}` | `friends.notification_settings.update.v1` | `false` |  |  |
| GET | `/global_summary` | `global_summary.read.v1` | `false` |  | Daily app-wide aggregate counters; READY artifact preferred, legacy table/RPC fallback during migration |
| GET | `/profile-create/questions` | `profile.create.questions.v1` | `false` |  |  |
| POST | `/profile-create/answers` | `profile.create.answers.v1` | `false` |  |  |
| POST | `/mymodel/infer` | `mymodel.infer.v1` | `false` |  |  |
| GET | `/mymodel/qna/discoveries/reflections` | `mymodel.qna.discoveries.reflections.v1` | `false` |  |  |
| GET | `/mymodel/qna/echoes/reflections` | `mymodel.qna.echoes.reflections.v1` | `false` |  |  |
| GET | `/mymodel/qna/list` | `mymodel.qna.list.v1` | `false` |  |  |
| GET | `/mymodel/qna/unread` | `mymodel.qna.unread.v1` | `false` |  |  |
| GET | `/mymodel/qna/unread-status` | `mymodel.qna.unread_status.v1` | `false` |  | MyModel Home reflections unread aggregated across self + followed owners |
| POST | `/mymodel/qna/view` | `mymodel.qna.view.v1` | `false` |  |  |
| POST | `/mymodel/qna/echoes/submit` | `mymodel.qna.echoes.submit.v1` | `false` |  |  |
| POST | `/mymodel/qna/echoes/delete` | `mymodel.qna.echoes.delete.v1` | `false` |  |  |
| POST | `/mymodel/qna/discoveries/submit` | `mymodel.qna.discoveries.submit.v1` | `false` |  |  |
| POST | `/mymodel/qna/discoveries/delete` | `mymodel.qna.discoveries.delete.v1` | `false` |  |  |
| GET | `/mymodel/recommend/users` | `mymodel.recommend.users.v1` | `false` |  |  |
| POST | `/myprofile/follow` | `myprofile.follow.v1` | `false` |  |  |
| GET | `/myprofile/follow-requests/incoming` | `myprofile.follow_requests.incoming.v1` | `false` |  |  |
| GET | `/myprofile/follow-requests/outgoing` | `myprofile.follow_requests.outgoing.v1` | `false` |  |  |
| POST | `/myprofile/follow-request/cancel` | `myprofile.follow_request.cancel.v1` | `false` |  |  |
| POST | `/myprofile/follow-requests/approve` | `myprofile.follow_requests.approve.v1` | `false` |  |  |
| POST | `/myprofile/follow-requests/reject` | `myprofile.follow_requests.reject.v1` | `false` |  |  |
| GET | `/myprofile/follow-stats` | `myprofile.follow_stats.v1` | `false` |  |  |
| POST | `/myprofile/unfollow` | `myprofile.unfollow.v1` | `false` |  |  |
| POST | `/myprofile/remove-follower` | `myprofile.remove_follower.v1` | `false` |  |  |
| POST | `/myprofile/monthly/ensure` | `myprofile.monthly.ensure.v1` | `false` |  | On-demand self-structure generation trigger |
| GET | `/myweb/reports/ready` | `myweb.reports.ready.v1` | `false` |  | Shared publish governance + tier retention window |
| POST | `/myweb/reports/ensure` | `myweb.reports.ensure.v1` | `false` |  | On-demand MyWeb report generation trigger |
| GET | `/ranking/emotions` | `ranking.emotions.v1` | `false` |  |  |
| GET | `/ranking/input_count` | `ranking.input_count.v1` | `false` |  |  |
| GET | `/ranking/input_length` | `ranking.input_length.v1` | `false` |  |  |
| GET | `/ranking/login_streak` | `ranking.login_streak.v1` | `false` |  |  |
| GET | `/ranking/mymodel_questions` | `ranking.mymodel_questions.v1` | `false` |  |  |
| GET | `/ranking/mymodel_resonances` | `ranking.mymodel_resonances.v1` | `false` |  |  |
| GET | `/ranking/mymodel_discoveries` | `ranking.mymodel_discoveries.v1` | `false` |  |  |
| GET | `/subscription/bootstrap` | `subscription.bootstrap.v1` | `false` |  | Runtime subscription sales / plan config; `plans.*.emlis_ai` metadata is additive-only and may expand with server-owned capability hints |
| GET | `/subscription/me` | `subscription.me.v1` | `false` |  |  |
| POST | `/subscription/update` | `subscription.update.v1` | `false` |  | Client purchase sync / tier refresh |

All routes in this registry are governed as additive-only v1 contracts.
Breaking changes must move to a new route/version instead of mutating these contracts in place.
