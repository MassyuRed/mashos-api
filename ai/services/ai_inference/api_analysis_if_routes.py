"""Authenticated IF/Saved application routes; private sources stay server-side.

The lifecycle service resolves the owned base map and current entitlement. The
HTTP body can provide the person's choices, never a graph, tier or DB guard.
Reading/deleting calls the lifecycle owner directly, not the meaning engine.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Query, Response
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from api_account_visibility import _require_user_id


def _nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("nonblank_value_required")
    return value


PersonText = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=2000),
    AfterValidator(_nonblank),
]
Reference = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=256),
    AfterValidator(_nonblank),
]
OperationKey = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=128),
    AfterValidator(_nonblank),
]


class IfScenarioSetBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    base_observed_map_ref: Reference
    branch_point_id: Reference
    branch_intent_text: PersonText | None = None
    constraint_texts: list[PersonText] = Field(default_factory=list, max_length=10)
    requested_candidate_count: int = Field(default=1, ge=1, le=3)
    constraints_confirmed: bool = False
    scenario_choice_texts: list[PersonText] = Field(default_factory=list, max_length=3)
    idempotency_key: OperationKey


class SavedRouteIntentBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    source_scenario_set_ref: Reference
    selected_scenario_ref: Reference
    user_note: PersonText | None = None
    idempotency_key: OperationKey


def register_analysis_if_routes(app: FastAPI, *, service=None) -> None:
    if service is None:
        import analysis_if_route_service as service

    async def call(response, authorization, operation, *args, **kwargs):
        response.headers["Cache-Control"] = "private, no-store"
        try:
            owner = await _require_user_id(authorization)
            # The service returns its closed safe application envelope. No raw
            # base snapshot or private artifact is serialized by this module.
            return await operation(owner, *args, **kwargs)
        except HTTPException as exc:
            exc.headers = {**(exc.headers or {}), "Cache-Control": "private, no-store"}
            raise

    @app.post("/analysis/if-route/scenario-sets")
    async def create_if_scenario_set(
        body: IfScenarioSetBody,
        response: Response,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        return await call(response, authorization, service.create_scenario_set,
                          body.model_dump())

    @app.get("/analysis/if-route/scenario-sets")
    async def list_if_scenario_sets(
        response: Response,
        limit: int = Query(default=60, ge=1, le=100),
        offset: int = Query(default=0, ge=0, le=10000),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        return await call(response, authorization, service.list_artifacts,
                          kind="scenario_set", limit=limit, offset=offset)

    @app.get("/analysis/if-route/scenario-sets/{artifact_id}")
    async def get_if_scenario_set(
        artifact_id: UUID,
        response: Response,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        return await call(response, authorization, service.get_artifact,
                          "scenario_set", str(artifact_id))

    @app.delete("/analysis/if-route/scenario-sets/{artifact_id}")
    async def delete_if_scenario_set(
        artifact_id: UUID,
        response: Response,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        return await call(response, authorization, service.delete_artifact,
                          "scenario_set", str(artifact_id))

    @app.post("/analysis/saved-route-intents")
    async def create_saved_route_intent(
        body: SavedRouteIntentBody,
        response: Response,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        return await call(response, authorization, service.save_intent,
                          body.model_dump())

    @app.get("/analysis/saved-route-intents")
    async def list_saved_route_intents(
        response: Response,
        limit: int = Query(default=60, ge=1, le=100),
        offset: int = Query(default=0, ge=0, le=10000),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        return await call(response, authorization, service.list_artifacts,
                          kind="saved_intent", limit=limit, offset=offset)

    @app.get("/analysis/saved-route-intents/{artifact_id}")
    async def get_saved_route_intent(
        artifact_id: UUID,
        response: Response,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        return await call(response, authorization, service.get_artifact,
                          "saved_intent", str(artifact_id))

    @app.delete("/analysis/saved-route-intents/{artifact_id}")
    async def delete_saved_route_intent(
        artifact_id: UUID,
        response: Response,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> dict:
        return await call(response, authorization, service.delete_artifact,
                          "saved_intent", str(artifact_id))
