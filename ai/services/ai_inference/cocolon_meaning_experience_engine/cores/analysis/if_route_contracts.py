"""Pure IF inputs; lifecycle callers authenticate and load the saved base map.

Simulation material is authored by the person. A derived map or an AI answer
must never be wrapped in this type as if it were new person-authored evidence.
"""
from __future__ import annotations

from dataclasses import dataclass

from ...contracts import EngineStatus


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisSimulationSource:
    source_id: str
    owner_scope: str
    text: str
    source_version: str = '1'
    source_role: str = 'SIMULATION_SESSION_MATERIAL'


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisIfRouteRequest:
    request_id: str
    authenticated_owner_scope: str
    base_observed_map_ref: str
    base_route_ref: str
    branch_point_id: str
    base_projection_json: str
    base_private_evidence_json: str
    base_source_guard: str = ''
    branch_intent: AnalysisSimulationSource | None = None
    constraints: tuple[AnalysisSimulationSource, ...] = ()
    requested_candidate_count: int = 1
    constraints_confirmed: bool = False
    scenario_choices: tuple[AnalysisSimulationSource, ...] = ()
    analysis_if_policy_version: str = 'analysis.if.user-choices.v1'
    core_id: str = 'analysis'
    product_job: str = 'MAP_AND_EXPLORE'
    operation: str = 'ANALYSIS_IF_ROUTE'


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisIfRouteOutcome:
    status: EngineStatus
    reason_codes: tuple[str, ...]
    artifact: object | None = None
    clarification_json: str = 'null'
    automatic_progression: bool = False

    @property
    def clarification_request(self):
        import json
        return json.loads(self.clarification_json)


@dataclass(frozen=True, slots=True, repr=False)
class AnalysisIfModelPrepared:
    request: AnalysisIfRouteRequest
    request_ref: str
    messages_json: str
    base_seed_json: str

    def messages(self):
        import json
        return json.loads(self.messages_json)
