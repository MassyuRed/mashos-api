"""Application adapter for CMEE relational-map admission and realization."""
from dataclasses import replace
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    SEMANTIC_MAP_PROFILE as PROFILE,
    SEMANTIC_MAP_SCHEMA as SCHEMA,
    SEMANTIC_MAP_MODEL_SCHEMA as MODEL_SCHEMA,
    SEMANTIC_MAP_NODE_KINDS as NODE_KINDS,
    SEMANTIC_MAP_PERSPECTIVES as PERSPECTIVES,
    SEMANTIC_MAP_RELATION_KINDS as RELATION_KINDS,
    SEMANTIC_MAP_MAX_RESPONSE_BYTES as MAX_RESPONSE_BYTES,
    AnalysisSemanticMapError as SemanticMapError,
    AnalysisSemanticMapNoMaterial as SemanticMapNoMaterial,
    _semantic_map_require as _require,
    semantic_map_canonical as _canonical,
    semantic_map_hash as _hash,
    _semantic_map_text as _text,
    _semantic_map_keys as _keys,
    _semantic_map_strings as _strings,
    _semantic_map_strict_object as _strict_object,
    _semantic_map_foundation as _foundation,
    _SEMANTIC_MAP_INSTRUCTION as _INSTRUCTION,
    AnalysisSemanticMapInput as SemanticMapInput,
    prepare_analysis_semantic_map as _prepare_analysis_semantic_map,
)
from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import (
    AnalysisSemanticMapArtifact as SemanticMapArtifact,
    AnalysisSemanticMapOutcome,
    validate_analysis_semantic_projection as validate_semantic_projection,
    analysis_semantic_projection_text as semantic_projection_text,
)


def prepare_semantic_map(owner, snapshot, *, prompt_version=PROFILE):
    from analysis_cumulative_service import _cumulative_model_request
    return _prepare_analysis_semantic_map(_cumulative_model_request(owner, snapshot), snapshot,
        prompt_version=prompt_version)


def build_semantic_map(prepared, response):
    _require(type(prepared) is SemanticMapInput, 'analysis_semantic_input_invalid')
    outcome = MeaningExperienceEngine().generate(prepared.request,
        semantic_input=replace(prepared, response=response))
    _require(type(outcome) is AnalysisSemanticMapOutcome, 'analysis_semantic_outcome_invalid')
    if outcome.artifact is None:
        raise SemanticMapError(outcome.reason_codes[0])
    return outcome.artifact, outcome.coverage

