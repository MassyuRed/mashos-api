from __future__ import annotations

from pathlib import Path

from fastapi.routing import APIRoute

from api_contract_registry import API_CONTRACT_POLICY_VERSION, contract_ids, contract_route_keys, get_contract_entry, iter_public_api_contracts


REQUIRED_PUBLIC_V1_ROUTE_KEYS = {
    ('GET', '/app/bootstrap'),
    ('POST', '/emotion/submit'),
    ('GET', '/input/summary'),
    ('GET', '/account/profile/me'),
    ('GET', '/account/display-name/availability'),
    ('PATCH', '/account/profile/me'),
    ('POST', '/account/delete'),
    ('GET', '/account/profile'),
    ('GET', '/account/visibility/me'),
    ('PATCH', '/account/visibility/me'),
    ('GET', '/account/status'),
    ('GET', '/friends/feed'),
    ('GET', '/friends/manage'),
    ('GET', '/friends/unread-status'),
    ('POST', '/friends/unread/read-feed'),
    ('POST', '/friends/unread/read-requests'),
    ('GET', '/report-reads/status'),
    ('POST', '/report-reads/mark'),
    ('GET', '/report-reads/myweb-unread-status'),
    ('GET', '/myweb/home-summary'),
    ('GET', '/myweb/reports/{report_id}/weekly-days'),
    ('GET', '/myprofile/reports/history'),
    ('GET', '/myprofile/latest/status'),
    ('GET', '/myprofile/reports/{report_id}'),
    ('DELETE', '/emotion/history/{emotion_id}'),
    ('GET', '/myprofile/follow-list'),
    ('GET', '/mymodel/qna/detail'),
    ('GET', '/mymodel/qna/echoes/history'),
    ('GET', '/mymodel/qna/discoveries/history'),
    ('POST', '/activity/login'),
    ('GET', '/today-question/current'),
    ('GET', '/today-question/status'),
    ('POST', '/today-question/answers'),
    ('GET', '/today-question/history'),
    ('PATCH', '/today-question/history/{answer_id}'),
    ('GET', '/today-question/settings'),
    ('PATCH', '/today-question/settings'),
    ('GET', '/notices/current'),
    ('GET', '/notices/history'),
    ('POST', '/notices/read'),
    ('POST', '/notices/popup-seen'),
    ('GET', '/report-distribution/settings'),
    ('PATCH', '/report-distribution/settings'),
    ('GET', '/emotion/history/search'),
    ('POST', '/emotion/history/search'),
    ('POST', '/emotion/secret'),
    ('POST', '/friends/request'),
    ('POST', '/friends/requests/{request_id}/accept'),
    ('POST', '/friends/requests/{request_id}/reject'),
    ('POST', '/friends/requests/{request_id}/cancel'),
    ('POST', '/friends/remove'),
    ('GET', '/friends/notification-settings'),
    ('POST', '/friends/notification-settings/{friend_user_id}'),
    ('GET', '/global_summary'),
    ('GET', '/mymodel/create/questions'),
    ('POST', '/mymodel/create/answers'),
    ('POST', '/mymodel/infer'),
    ('GET', '/mymodel/qna/discoveries/reflections'),
    ('GET', '/mymodel/qna/echoes/reflections'),
    ('GET', '/mymodel/qna/holders'),
    ('GET', '/mymodel/qna/list'),
    ('GET', '/mymodel/qna/trending'),
    ('GET', '/mymodel/qna/unread'),
    ('GET', '/mymodel/qna/unread-status'),
    ('POST', '/mymodel/qna/view'),
    ('POST', '/mymodel/qna/echoes/submit'),
    ('POST', '/mymodel/qna/echoes/delete'),
    ('POST', '/mymodel/qna/discoveries/submit'),
    ('POST', '/mymodel/qna/discoveries/delete'),
    ('GET', '/mymodel/recommend/users'),
    ('POST', '/myprofile/follow'),
    ('GET', '/myprofile/follow-requests/incoming'),
    ('GET', '/myprofile/follow-requests/outgoing'),
    ('POST', '/myprofile/follow-request/cancel'),
    ('POST', '/myprofile/follow-requests/approve'),
    ('POST', '/myprofile/follow-requests/reject'),
    ('GET', '/myprofile/follow-stats'),
    ('POST', '/myprofile/unfollow'),
    ('POST', '/myprofile/remove-follower'),
    ('POST', '/myprofile/monthly/ensure'),
    ('GET', '/myweb/reports/ready'),
    ('POST', '/myweb/reports/ensure'),
    ('GET', '/ranking/emotions'),
    ('GET', '/ranking/input_count'),
    ('GET', '/ranking/input_length'),
    ('GET', '/ranking/login_streak'),
    ('GET', '/ranking/mymodel_questions'),
    ('GET', '/ranking/mymodel_resonances'),
    ('GET', '/ranking/mymodel_discoveries'),
    ('GET', '/subscription/bootstrap'),
    ('GET', '/subscription/me'),
    ('POST', '/subscription/update'),
}


def _route_map(app):
    routes = {}
    for route in app.router.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or set():
            if method in {"GET", "POST", "PATCH", "DELETE"}:
                routes[(method, route.path)] = route
    return routes


def test_policy_version_is_fixed():
    assert API_CONTRACT_POLICY_VERSION == "2026-03-20.mymodel-qna-unread-status.v1"


def test_registry_has_unique_contract_ids_and_routes():
    ids = list(contract_ids())
    assert len(ids) == len(set(ids))

    keys = list(contract_route_keys())
    assert len(keys) == len(set(keys))


def test_registry_covers_phase6c_required_public_routes():
    missing = sorted(REQUIRED_PUBLIC_V1_ROUTE_KEYS.difference(set(contract_route_keys())))
    assert not missing, f"Required public contract routes missing from registry: {missing}"


def test_registry_routes_exist_in_fastapi_app(app_module):
    route_map = _route_map(app_module.app)
    missing = [f"{entry.method} {entry.path}" for entry in iter_public_api_contracts() if (entry.method, entry.path) not in route_map]
    assert not missing, f"Missing routes in FastAPI app: {missing}"


def test_registry_routes_have_response_models(app_module):
    route_map = _route_map(app_module.app)
    missing = []
    for entry in iter_public_api_contracts():
        route = route_map[(entry.method, entry.path)]
        if route.response_model is None:
            missing.append(f"{entry.method} {entry.path}")
    assert not missing, f"Routes missing response_model: {missing}"


def test_public_registry_doc_mentions_all_registered_routes():
    doc = (Path(__file__).resolve().parents[2] / "docs" / "PUBLIC_API_REGISTRY.md").read_text(encoding="utf-8")
    for entry in iter_public_api_contracts():
        assert f"`{entry.path}`" in doc, entry.path
        assert f"`{entry.contract_id}`" in doc, entry.contract_id



def test_legacy_profilecreate_discovery_routes_are_marked_deprecated():
    trending = get_contract_entry(method="GET", path="/mymodel/qna/trending")
    holders = get_contract_entry(method="GET", path="/mymodel/qna/holders")

    assert trending is not None
    assert trending.deprecated is True
    assert trending.replacement == "/nexus/reflections"

    assert holders is not None
    assert holders.deprecated is True
    assert holders.replacement == "/nexus/reflections"
