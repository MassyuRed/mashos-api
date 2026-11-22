"""HTTP authentication and person-input boundaries, with lifecycle I/O isolated."""
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import FastAPI, HTTPException
import httpx

import api_analysis_if_routes as api


OWNER = str(UUID(int=1))
ARTIFACT = str(UUID(int=10))
IF_PATH = "/analysis/if-route/scenario-sets"
SAVED_PATH = "/analysis/saved-route-intents"


def if_body(**changes):
    return {
        "base_observed_map_ref": "artifact:" + "a" * 32 + "@1",
        "branch_point_id": "node:work-choice",
        "branch_intent_text": "私は明日は休憩を取りたい。",
        "idempotency_key": "person-selected-branch-1",
        **changes,
    }


def saved_body(**changes):
    return {
        "source_scenario_set_ref": "scenario-set:" + "b" * 32 + "@1",
        "selected_scenario_ref": "analysis-if-scenario:" + "c" * 32 + "@1",
        "idempotency_key": "person-saved-direction-1",
        **changes,
    }


class AnalysisIfApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = SimpleNamespace(**{
            name: AsyncMock(return_value={"status": "ok"})
            for name in ("create_scenario_set", "save_intent", "list_artifacts",
                         "get_artifact", "delete_artifact")
        })

        async def auth(authorization):
            if authorization != "Bearer valid":
                raise HTTPException(401, "authentication_required")
            return OWNER

        self.auth = patch.object(api, "_require_user_id", side_effect=auth)
        self.auth.start()
        app = FastAPI()
        api.register_analysis_if_routes(app, service=self.service)
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://synthetic")

    async def asyncTearDown(self):
        await self.client.aclose()
        self.auth.stop()

    async def request(self, method, path, **kwargs):
        return await self.client.request(
            method, path, headers={"Authorization": "Bearer valid"}, **kwargs)

    async def test_all_if_and_saved_operations_require_auth_before_lifecycle_io(self):
        for root, body in ((IF_PATH, if_body()), (SAVED_PATH, saved_body())):
            for method, path, kwargs in (
                ("POST", root, {"json": body}),
                ("GET", root, {}),
                ("GET", root + "/" + ARTIFACT, {}),
                ("DELETE", root + "/" + ARTIFACT, {}),
            ):
                response = await self.client.request(method, path, **kwargs)
                self.assertEqual(response.status_code, 401, response.text)
                self.assertEqual(response.headers["cache-control"], "private, no-store")
        for operation in vars(self.service).values():
            operation.assert_not_awaited()

    async def test_create_passes_authenticated_owner_and_untouched_person_fields(self):
        body = if_body(constraint_texts=["午後に予定がある。"],
                       constraints_confirmed=True, requested_candidate_count=2,
                       scenario_choice_texts=["朝に休憩する。", "夕方に休憩する。"])
        safe = {"status": "GENERATED", "projection": {
            "wire_kind": "watashi.if-route-set.v1", "selection_policy": "PARALLEL_NOT_RANKED"}}
        self.service.create_scenario_set.return_value = safe
        response = await self.request("POST", IF_PATH, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), safe)
        self.assertEqual(response.headers["cache-control"], "private, no-store")
        self.service.create_scenario_set.assert_awaited_once_with(OWNER, body)

    async def test_missing_intent_is_delivered_to_analysis_clarification_owner(self):
        body = if_body(branch_intent_text=None)
        pending = {"status": "QUESTION_PENDING", "artifact": None,
                   "clarification_request": {"target": "branch_intent"}}
        self.service.create_scenario_set.return_value = pending
        response = await self.request("POST", IF_PATH, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), pending)
        self.service.create_scenario_set.assert_awaited_once_with(OWNER, {
            **body, "constraint_texts": [], "requested_candidate_count": 1,
            "constraints_confirmed": False, "scenario_choice_texts": [],
        })

    async def test_explicit_saved_selection_and_optional_note_have_separate_namespace(self):
        body = saved_body(user_note="この方向を考えてみたい。")
        response = await self.request("POST", SAVED_PATH, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.service.save_intent.assert_awaited_once_with(OWNER, body)
        self.service.create_scenario_set.assert_not_awaited()

    async def test_body_cannot_supply_owner_tier_private_base_or_generated_graph(self):
        for path, body in ((IF_PATH, if_body()), (SAVED_PATH, saved_body())):
            for field, value in (
                ("user_id", str(UUID(int=2))), ("owner_scope", "other"),
                ("subscription_tier", "premium"), ("base_projection_json", "{}"),
                ("base_private_evidence_json", "{}"), ("base_source_guard", "forged"),
                ("scenario_graphs", []),
            ):
                response = await self.request("POST", path, json={**body, field: value})
                self.assertEqual(response.status_code, 422, (field, response.text))
        self.service.create_scenario_set.assert_not_awaited()
        self.service.save_intent.assert_not_awaited()

    async def test_strict_person_input_and_candidate_bounds_reject_before_service(self):
        for changes in (
            {"branch_intent_text": "  "}, {"branch_intent_text": 1},
            {"constraint_texts": [""]}, {"constraint_texts": ["制約"] * 11},
            {"scenario_choice_texts": ["候補"] * 4},
            {"requested_candidate_count": 0}, {"requested_candidate_count": 4},
            {"requested_candidate_count": True}, {"requested_candidate_count": "2"},
            {"constraints_confirmed": "true"}, {"idempotency_key": " "},
        ):
            response = await self.request("POST", IF_PATH, json=if_body(**changes))
            self.assertEqual(response.status_code, 422, (changes, response.text))
        for note in (" ", "あ" * 2001, False):
            response = await self.request("POST", SAVED_PATH, json=saved_body(user_note=note))
            self.assertEqual(response.status_code, 422, response.text)
        self.service.create_scenario_set.assert_not_awaited()
        self.service.save_intent.assert_not_awaited()

    async def test_read_and_delete_only_use_authorized_lifecycle_namespace(self):
        for root, kind in ((IF_PATH, "scenario_set"), (SAVED_PATH, "saved_intent")):
            listed = await self.request("GET", root + "?limit=12&offset=24")
            self.assertEqual(listed.status_code, 200, listed.text)
            self.service.list_artifacts.assert_awaited_with(
                OWNER, kind=kind, limit=12, offset=24)
            detail = await self.request("GET", root + "/" + ARTIFACT)
            self.assertEqual(detail.status_code, 200, detail.text)
            self.service.get_artifact.assert_awaited_with(OWNER, kind, ARTIFACT)
            deleted = await self.request("DELETE", root + "/" + ARTIFACT)
            self.assertEqual(deleted.status_code, 200, deleted.text)
            self.service.delete_artifact.assert_awaited_with(OWNER, kind, ARTIFACT)
            for response in (listed, detail, deleted):
                self.assertEqual(response.headers["cache-control"], "private, no-store")
        self.service.create_scenario_set.assert_not_awaited()
        self.service.save_intent.assert_not_awaited()

    async def test_invalid_page_or_artifact_identity_never_reaches_storage(self):
        for root in (IF_PATH, SAVED_PATH):
            for suffix in ("?limit=0", "?limit=101", "?offset=-1", "?offset=10001",
                           "/not-an-artifact-uuid"):
                response = await self.request("GET", root + suffix)
                self.assertEqual(response.status_code, 422, response.text)
        self.service.list_artifacts.assert_not_awaited()
        self.service.get_artifact.assert_not_awaited()

    async def test_service_access_rejection_is_not_replaced_by_a_generated_result(self):
        self.service.get_artifact.side_effect = HTTPException(403, "analysis_if_unavailable")
        response = await self.request("GET", IF_PATH + "/" + ARTIFACT)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "analysis_if_unavailable"})
        self.assertEqual(response.headers["cache-control"], "private, no-store")
        self.service.create_scenario_set.assert_not_awaited()
