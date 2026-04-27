from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from fastapi import Request

API_CONTRACT_POLICY_VERSION = "2026-04-20.myprofile-lookup.v1"

REQUEST_POLICY_ADDITIVE_ONLY = "additive-only"
RESPONSE_POLICY_ADDITIVE_ONLY = "additive-only"
OWNER_PUBLIC_API = "public-api"


@dataclass(frozen=True)
class ApiContractEntry:
    method: str
    path: str
    contract_id: str
    owner: str
    request_policy: str
    response_policy: str
    deprecated: bool = False
    replacement: Optional[str] = None
    notes: Optional[str] = None


PUBLIC_API_CONTRACTS: Tuple[ApiContractEntry, ...] = (
    ApiContractEntry('GET', '/app/bootstrap', 'app.bootstrap.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Runtime guardrail / maintenance switch'),
    ApiContractEntry('GET', '/app/startup', 'app.startup.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Auth-required startup bundle for unread / popup / lightweight prefetch only; Home hydration moved to /home/state'),
    ApiContractEntry('GET', '/home/state', 'home.state.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Auth-required Home hydration bundle (input summary + global summary + notices + today question + reflection quota); app.startup intentionally excludes heavy Home counters'),
    ApiContractEntry('POST', '/emotion/submit', 'emotion.submit.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Legacy payloads must remain accepted; input_feedback.comment_text stays stable while input_feedback.emlis_ai remains additive-only across observation-kernel metadata expansions'),
    ApiContractEntry('GET', '/emotion/reflection/quota', 'emotion.reflection.quota.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Current-month publish quota / capability probe for Home reflection flow', deprecated=True, replacement='/emotion/piece/quota'),
    ApiContractEntry('POST', '/emotion/reflection/preview', 'emotion.reflection.preview.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Preview-only reflection generation; does not canonical-save Home input', deprecated=True, replacement='/emotion/piece/preview'),
    ApiContractEntry('POST', '/emotion/reflection/publish', 'emotion.reflection.publish.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Publishes a preview draft and reuses Home write fan-out / cache invalidation', deprecated=True, replacement='/emotion/piece/publish'),
    ApiContractEntry('POST', '/emotion/reflection/cancel', 'emotion.reflection.cancel.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Cancels a preview draft without mutating canonical Home input state', deprecated=True, replacement='/emotion/piece/cancel'),
    ApiContractEntry('GET', '/input/summary', 'input.summary.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/account/profile/me', 'account.profile.me.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/account/display-name/availability', 'account.display_name.availability.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Self-edit display name preflight availability check'),
    ApiContractEntry('PATCH', '/account/profile/me', 'account.profile.me.patch.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/account/delete', 'account.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Delete lifecycle is server-owned'),
    ApiContractEntry('GET', '/account/profile', 'account.profile.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/account/visibility/me', 'account.visibility.me.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('PATCH', '/account/visibility/me', 'account.visibility.me.patch.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/account/status', 'account.status.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/friends/feed', 'friends.feed.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/emotion-log/feed'),
    ApiContractEntry('GET', '/friends/manage', 'friends.manage.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, notes='Retired compatibility route'),
    ApiContractEntry('GET', '/friends/unread-status', 'friends.unread.status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/emotion-log/unread-status'),
    ApiContractEntry('POST', '/friends/unread/read-feed', 'friends.unread.read_feed.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/emotion-log/unread/read-feed'),
    ApiContractEntry('POST', '/friends/unread/read-requests', 'friends.unread.read_requests.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/requests/read'),
    ApiContractEntry('GET', '/report-reads/status', 'report_reads.status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/report-reads/mark', 'report_reads.mark.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/report-reads/myweb-unread-status', 'report_reads.myweb_unread.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Unread badge tracks publish-governed MyWeb artifacts only', deprecated=True, replacement='/report-reads/analysis-unread-status'),
    ApiContractEntry('GET', '/myweb/home-summary', 'myweb.home_summary.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/analysis/home-summary'),
    ApiContractEntry('GET', '/myweb/reports/{report_id}/weekly-days', 'myweb.report.weekly_days.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Detail is readable only for publish-governed weekly reports', deprecated=True, replacement='/analysis/reports/{report_id}/weekly-days'),
    ApiContractEntry('GET', '/myprofile/reports/history', 'myprofile.reports.history.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='History excludes non-publishable self-structure rows', deprecated=True, replacement='/self-structure/reports/history'),
    ApiContractEntry('GET', '/myprofile/latest/status', 'myprofile.latest.status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Lightweight latest self-structure version probe for in-app banner polling', deprecated=True, replacement='/self-structure/latest/status'),
    ApiContractEntry('GET', '/myprofile/reports/{report_id}', 'myprofile.reports.detail.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Detail is readable only for publishable self-structure rows', deprecated=True, replacement='/self-structure/reports/{report_id}'),
    ApiContractEntry('DELETE', '/emotion/history/{emotion_id}', 'emotion.history.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/myprofile/follow-list', 'myprofile.follow_list.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/list'),
    ApiContractEntry('GET', '/myprofile/lookup', 'myprofile.lookup.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Exact-match Connect ID lookup for in-app search/follow only; no display_name or Share ID fallback', deprecated=True, replacement='/connect/lookup'),
    ApiContractEntry('GET', '/mymodel/qna/detail', 'mymodel.qna.detail.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/piece/detail'),
    ApiContractEntry('GET', '/mymodel/qna/echoes/history', 'mymodel.qna.echoes.history.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/piece/resonances/history'),
    ApiContractEntry('GET', '/mymodel/qna/discoveries/history', 'mymodel.qna.discoveries.history.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, notes='Retired compatibility route'),
    ApiContractEntry('POST', '/activity/login', 'activity.login.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Client login heartbeat / streak touch'),
    ApiContractEntry('GET', '/today-question/current', 'today_question.current.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/today-question/status', 'today_question.status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Lightweight Today Question popup/badge state without question body or choices'),
    ApiContractEntry('POST', '/today-question/answers', 'today_question.answers.create.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/today-question/history', 'today_question.history.list.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('PATCH', '/today-question/history/{answer_id}', 'today_question.history.patch.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/today-question/settings', 'today_question.settings.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('PATCH', '/today-question/settings', 'today_question.settings.patch.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/notices/current', 'notice.current.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/notices/history', 'notice.history.list.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/notices/read', 'notice.read.mark.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/notices/popup-seen', 'notice.popup_seen.mark.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/report-distribution/settings', 'report_distribution.settings.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Bundled MyWeb/MyProfile distribution push settings'),
    ApiContractEntry('PATCH', '/report-distribution/settings', 'report_distribution.settings.patch.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Bundled MyWeb/MyProfile distribution push settings'),
    ApiContractEntry('GET', '/emotion/history/search', 'emotion.history.search.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/emotion/history/search', 'emotion.history.search.query.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/emotion/secret', 'emotion.secret.update.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/friends/request', 'friends.request.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/friends/requests/{request_id}/accept', 'friends.requests.accept.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/friends/requests/{request_id}/reject', 'friends.requests.reject.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/friends/requests/{request_id}/cancel', 'friends.requests.cancel.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/friends/remove', 'friends.remove.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/friends/notification-settings', 'friends.notification_settings.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/friends/notification-settings/{friend_user_id}', 'friends.notification_settings.update.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/global_summary', 'global_summary.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Daily app-wide aggregate counters; current JST day prefers synchronous refresh, historical days prefer READY artifacts, legacy table/RPC fallback retained'),
    ApiContractEntry('GET', '/profile-create/questions', 'profile.create.questions.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/profile-create/answers', 'profile.create.answers.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/infer', 'mymodel.infer.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/discoveries/reflections', 'mymodel.qna.discoveries.reflections.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, notes='Retired compatibility route'),
    ApiContractEntry('GET', '/mymodel/qna/echoes/reflections', 'mymodel.qna.echoes.reflections.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/list', 'mymodel.qna.list.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/unread', 'mymodel.qna.unread.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/unread-status', 'mymodel.qna.unread_status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='MyModel Home reflections unread aggregated across self + followed owners'),
    ApiContractEntry('POST', '/mymodel/qna/view', 'mymodel.qna.view.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/qna/echoes/submit', 'mymodel.qna.echoes.submit.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/qna/echoes/delete', 'mymodel.qna.echoes.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/qna/discoveries/submit', 'mymodel.qna.discoveries.submit.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, notes='Retired compatibility route'),
    ApiContractEntry('POST', '/mymodel/qna/discoveries/delete', 'mymodel.qna.discoveries.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, notes='Retired compatibility route'),
    ApiContractEntry('GET', '/mymodel/recommend/users', 'mymodel.recommend.users.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/nexus/recommend/users'),
    ApiContractEntry('POST', '/myprofile/follow', 'myprofile.follow.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/create'),
    ApiContractEntry('GET', '/myprofile/follow-requests/incoming', 'myprofile.follow_requests.incoming.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/requests/incoming'),
    ApiContractEntry('GET', '/myprofile/follow-requests/outgoing', 'myprofile.follow_requests.outgoing.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/requests/outgoing'),
    ApiContractEntry('POST', '/myprofile/follow-request/cancel', 'myprofile.follow_request.cancel.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/request/cancel'),
    ApiContractEntry('POST', '/myprofile/follow-requests/approve', 'myprofile.follow_requests.approve.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/requests/approve'),
    ApiContractEntry('POST', '/myprofile/follow-requests/reject', 'myprofile.follow_requests.reject.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/requests/reject'),
    ApiContractEntry('GET', '/myprofile/follow-stats', 'myprofile.follow_stats.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/stats'),
    ApiContractEntry('POST', '/myprofile/unfollow', 'myprofile.unfollow.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/delete'),
    ApiContractEntry('POST', '/myprofile/remove-follower', 'myprofile.remove_follower.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/follow/remove-follower'),
    ApiContractEntry('POST', '/myprofile/monthly/ensure', 'myprofile.monthly.ensure.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/self-structure/monthly/ensure', notes='On-demand self-structure generation trigger'),
    ApiContractEntry('GET', '/myweb/reports/ready', 'myweb.reports.ready.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/analysis/reports/ready', notes='Shared publish governance + tier retention window'),
    ApiContractEntry('POST', '/myweb/reports/ensure', 'myweb.reports.ensure.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/analysis/reports/ensure', notes='On-demand MyWeb report generation trigger'),
    ApiContractEntry('GET', '/ranking/emotions', 'ranking.emotions.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/input_count', 'ranking.input_count.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/input_length', 'ranking.input_length.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/login_streak', 'ranking.login_streak.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/mymodel_questions', 'ranking.mymodel_questions.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, notes='Retired compatibility route'),
    ApiContractEntry('GET', '/ranking/mymodel_resonances', 'ranking.mymodel_resonances.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, replacement='/ranking/piece_resonances'),
    ApiContractEntry('GET', '/ranking/mymodel_discoveries', 'ranking.mymodel_discoveries.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, deprecated=True, notes='Retired compatibility route'),
    ApiContractEntry('GET', '/subscription/bootstrap', 'subscription.bootstrap.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Runtime subscription sales / plan config; plans may include additive emlis_ai metadata and marketing lines'),
    ApiContractEntry('GET', '/analysis/home-summary', 'analysis.home_summary.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/analysis/reports/ensure', 'analysis.reports.ensure.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/analysis/reports/ready', 'analysis.reports.ready.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/analysis/reports/{report_id}', 'analysis.reports.detail.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/analysis/reports/{report_id}/weekly-days', 'analysis.report.weekly_days.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/report-reads/analysis-unread-status', 'report_reads.analysis_unread.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/self-structure/latest/status', 'self_structure.latest.status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/self-structure/latest', 'self_structure.latest.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/self-structure/monthly/ensure', 'self_structure.monthly.ensure.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/self-structure/reports/history', 'self_structure.reports.history.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/self-structure/reports/{report_id}', 'self_structure.reports.detail.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/connect/lookup', 'connect.lookup.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/request', 'follow.request.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/requests/{request_id}/accept', 'follow.requests.accept.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/requests/{request_id}/reject', 'follow.requests.reject.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/requests/{request_id}/cancel', 'follow.requests.cancel.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/remove', 'follow.remove.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/create', 'follow.create.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/delete', 'follow.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/remove-follower', 'follow.remove_follower.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/follow/stats', 'follow.stats.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/follow/list', 'follow.list.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/follow/requests/incoming', 'follow.requests.incoming.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/follow/requests/outgoing', 'follow.requests.outgoing.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/request/cancel', 'follow.request.cancel.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/requests/approve', 'follow.requests.approve.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/requests/reject', 'follow.requests.reject.simple.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/follow/requests/read', 'follow.requests.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/public/profile/by-share-code', 'public.profile.by_share_code.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/emotion/piece/quota', 'emotion.piece.quota.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/emotion/piece/preview', 'emotion.piece.preview.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/emotion/piece/publish', 'emotion.piece.publish.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/emotion/piece/cancel', 'emotion.piece.cancel.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/nexus/pieces', 'nexus.pieces.list.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/nexus/pieces/unread-status', 'nexus.pieces.unread_status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/nexus/pieces/{q_instance_id}', 'nexus.pieces.detail.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/nexus/history/resonances', 'nexus.history.resonances.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/nexus/recommend/users', 'nexus.recommend.users.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/piece/library', 'piece.library.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/piece/unread', 'piece.unread.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/piece/unread-status', 'piece.unread_status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/piece/detail', 'piece.detail.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/piece/view', 'piece.view.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/piece/resonance', 'piece.resonance.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/piece/resonances/pieces', 'piece.resonances.pieces.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/piece/resonances/submit', 'piece.resonances.submit.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/piece/resonances/delete', 'piece.resonances.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/piece/resonances/history', 'piece.resonances.history.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/piece_resonances', 'ranking.piece_resonances.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/piece_views', 'ranking.piece_views.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/subscription/me', 'subscription.me.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/subscription/update', 'subscription.update.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Client purchase sync / tier refresh'),
)


_CONTRACTS_BY_ROUTE: Dict[Tuple[str, str], ApiContractEntry] = {
    (entry.method.upper(), entry.path): entry for entry in PUBLIC_API_CONTRACTS
}


def iter_public_api_contracts() -> Tuple[ApiContractEntry, ...]:
    return PUBLIC_API_CONTRACTS


def get_contract_entry(*, method: str, path: str) -> Optional[ApiContractEntry]:
    return _CONTRACTS_BY_ROUTE.get((str(method or "").upper(), str(path or "")))


def _request_route_path(request: Request) -> Optional[str]:
    route = request.scope.get("route")
    if route is None:
        return None
    for attr in ("path", "path_format"):
        value = getattr(route, attr, None)
        if isinstance(value, str) and value:
            return value
    return None


def find_contract_entry_for_request(request: Request) -> Optional[ApiContractEntry]:
    return get_contract_entry(method=request.method, path=_request_route_path(request) or "")


def contract_route_keys() -> Tuple[Tuple[str, str], ...]:
    return tuple(_CONTRACTS_BY_ROUTE.keys())


def contract_ids() -> Tuple[str, ...]:
    return tuple(entry.contract_id for entry in PUBLIC_API_CONTRACTS)
