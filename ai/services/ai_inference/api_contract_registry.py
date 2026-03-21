from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from fastapi import Request

API_CONTRACT_POLICY_VERSION = "2026-03-20.mymodel-qna-unread-status.v1"

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
    ApiContractEntry('POST', '/emotion/submit', 'emotion.submit.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Legacy payloads must remain accepted'),
    ApiContractEntry('GET', '/input/summary', 'input.summary.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/account/profile/me', 'account.profile.me.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/account/display-name/availability', 'account.display_name.availability.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Self-edit display name preflight availability check'),
    ApiContractEntry('PATCH', '/account/profile/me', 'account.profile.me.patch.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/account/delete', 'account.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Delete lifecycle is server-owned'),
    ApiContractEntry('GET', '/account/profile', 'account.profile.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/account/visibility/me', 'account.visibility.me.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('PATCH', '/account/visibility/me', 'account.visibility.me.patch.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/account/status', 'account.status.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/friends/feed', 'friends.feed.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/friends/manage', 'friends.manage.read.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/friends/unread-status', 'friends.unread.status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/friends/unread/read-feed', 'friends.unread.read_feed.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/friends/unread/read-requests', 'friends.unread.read_requests.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/report-reads/status', 'report_reads.status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/report-reads/mark', 'report_reads.mark.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/report-reads/myweb-unread-status', 'report_reads.myweb_unread.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Unread badge tracks publish-governed MyWeb artifacts only'),
    ApiContractEntry('GET', '/myweb/home-summary', 'myweb.home_summary.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/myweb/reports/{report_id}/weekly-days', 'myweb.report.weekly_days.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Detail is readable only for publish-governed weekly reports'),
    ApiContractEntry('GET', '/myprofile/reports/history', 'myprofile.reports.history.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='History excludes non-publishable self-structure rows'),
    ApiContractEntry('GET', '/myprofile/latest/status', 'myprofile.latest.status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Lightweight latest self-structure version probe for in-app banner polling'),
    ApiContractEntry('GET', '/myprofile/reports/{report_id}', 'myprofile.reports.detail.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Detail is readable only for publishable self-structure rows'),
    ApiContractEntry('DELETE', '/emotion/history/{emotion_id}', 'emotion.history.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/myprofile/follow-list', 'myprofile.follow_list.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/detail', 'mymodel.qna.detail.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/echoes/history', 'mymodel.qna.echoes.history.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/discoveries/history', 'mymodel.qna.discoveries.history.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/activity/login', 'activity.login.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Client login heartbeat / streak touch'),
    ApiContractEntry('GET', '/deep_insight/questions', 'deep_insight.questions.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/deep_insight/answers', 'deep_insight.answers.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/today-question/current', 'today_question.current.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
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
    ApiContractEntry('GET', '/mymodel/create/questions', 'mymodel.create.questions.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/create/answers', 'mymodel.create.answers.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/infer', 'mymodel.infer.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/discoveries/reflections', 'mymodel.qna.discoveries.reflections.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/echoes/reflections', 'mymodel.qna.echoes.reflections.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/holders', 'mymodel.qna.holders.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/list', 'mymodel.qna.list.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/trending', 'mymodel.qna.trending.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/unread', 'mymodel.qna.unread.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/qna/unread-status', 'mymodel.qna.unread_status.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='MyModel Home reflections unread aggregated across self + followed owners'),
    ApiContractEntry('POST', '/mymodel/qna/view', 'mymodel.qna.view.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/qna/echoes/submit', 'mymodel.qna.echoes.submit.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/qna/echoes/delete', 'mymodel.qna.echoes.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/qna/discoveries/submit', 'mymodel.qna.discoveries.submit.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/mymodel/qna/discoveries/delete', 'mymodel.qna.discoveries.delete.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/mymodel/recommend/users', 'mymodel.recommend.users.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/myprofile/follow', 'myprofile.follow.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/myprofile/follow-requests/incoming', 'myprofile.follow_requests.incoming.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/myprofile/follow-requests/outgoing', 'myprofile.follow_requests.outgoing.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/myprofile/follow-request/cancel', 'myprofile.follow_request.cancel.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/myprofile/follow-requests/approve', 'myprofile.follow_requests.approve.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/myprofile/follow-requests/reject', 'myprofile.follow_requests.reject.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/myprofile/follow-stats', 'myprofile.follow_stats.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/myprofile/unfollow', 'myprofile.unfollow.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/myprofile/remove-follower', 'myprofile.remove_follower.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('POST', '/myprofile/monthly/ensure', 'myprofile.monthly.ensure.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='On-demand self-structure generation trigger'),
    ApiContractEntry('GET', '/myweb/reports/ready', 'myweb.reports.ready.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Shared publish governance + tier retention window'),
    ApiContractEntry('POST', '/myweb/reports/ensure', 'myweb.reports.ensure.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='On-demand MyWeb report generation trigger'),
    ApiContractEntry('GET', '/ranking/emotions', 'ranking.emotions.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/input_count', 'ranking.input_count.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/input_length', 'ranking.input_length.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/login_streak', 'ranking.login_streak.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/mymodel_questions', 'ranking.mymodel_questions.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/mymodel_resonances', 'ranking.mymodel_resonances.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/ranking/mymodel_discoveries', 'ranking.mymodel_discoveries.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY),
    ApiContractEntry('GET', '/subscription/bootstrap', 'subscription.bootstrap.v1', OWNER_PUBLIC_API, REQUEST_POLICY_ADDITIVE_ONLY, RESPONSE_POLICY_ADDITIVE_ONLY, notes='Runtime subscription sales / plan config'),
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
