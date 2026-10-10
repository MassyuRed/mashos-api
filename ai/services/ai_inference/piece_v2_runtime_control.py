"""Single Piece v2 feature resolver (PCE-7); no activation or environment IO.

An admitted server composition may supply app.state.piece_v2_runtime with
requested and ready boolean maps using the eight existing feature names.
Readiness means the corresponding PCE-7 prerequisites have been established
by that composition; requesting a feature never establishes readiness.
No production composition supplies this state in this development slice.
The projection is advisory to RN; affected operations check this owner again.
"""
from __future__ import annotations

from piece_v2_contract import PieceContractError

PIECE_FEATURE_NAMES = (
    'piece_v2_preview_enabled',
    'piece_v2_save_enabled',
    'piece_v2_owner_read_enabled',
    'piece_v2_public_write_enabled',
    'piece_v2_public_read_enabled',
    'piece_v2_visibility_toggle_enabled',
    'piece_v2_export_enabled',
    'piece_v2_delete_enabled',
)


def resolve_piece_feature_flags(configuration: object = None) -> dict[str, bool]:
    """Return only effective booleans, without modifying or retaining input.

    Missing/invalid values fail closed. Unknown nested names are not projected.
    Each ready bit covers that operation's non-flag prerequisites in PCE-7 §6;
    the dependency lattice below enforces the additional inter-flag conditions.
    Source references, renderer/TTL values and client payloads are not inputs.
    """
    flags = dict.fromkeys(PIECE_FEATURE_NAMES, False)
    if (type(configuration) is not dict
            or set(configuration) != {'requested', 'ready'}
            or type(configuration['requested']) is not dict
            or type(configuration['ready']) is not dict):
        return flags
    requested, ready = configuration['requested'], configuration['ready']
    for name in PIECE_FEATURE_NAMES:
        flags[name] = requested.get(name) is True and ready.get(name) is True
    flags['piece_v2_save_enabled'] &= flags['piece_v2_preview_enabled']
    flags['piece_v2_public_write_enabled'] &= (
        flags['piece_v2_save_enabled'] and flags['piece_v2_public_read_enabled'])
    flags['piece_v2_visibility_toggle_enabled'] &= (
        flags['piece_v2_owner_read_enabled'] and flags['piece_v2_public_read_enabled'])
    flags['piece_v2_export_enabled'] &= flags['piece_v2_owner_read_enabled']
    flags['piece_v2_delete_enabled'] &= flags['piece_v2_owner_read_enabled']
    return flags


def piece_feature_flags_for_app(app: object = None) -> dict[str, bool]:
    """Resolve fresh per application; no process-wide cache or client override."""
    state = getattr(app, 'state', None)
    return resolve_piece_feature_flags(getattr(state, 'piece_v2_runtime', None))


def require_piece_feature_enabled(app: object, name: str) -> None:
    """Reject an unavailable/unknown operation with a body-free stable code."""
    if type(name) is not str or piece_feature_flags_for_app(app).get(name) is not True:
        raise PieceContractError('PIECE_FEATURE_DISABLED')


def validate_piece_preview_runtime(runtime: object) -> tuple[int, str]:
    """Validate the existing server TTL/renderer shape; grant no readiness.

    Shared by composition and every preview POST. Keep the former HTTP owner's
    exact type/range/identifier rules, with no defaults or normalization.
    """
    import re
    if (type(runtime) is not dict
            or set(runtime) != {'ttl_seconds', 'renderer_version'}):
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
    ttl, renderer = runtime['ttl_seconds'], runtime['renderer_version']
    if (type(ttl) is not int or not 0 < ttl <= 2147483647
            or type(renderer) is not str
            or re.fullmatch(r'[A-Za-z0-9_.:\-]{1,128}', renderer) is None):
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
    return ttl, renderer


def create_piece_preview_application(*, preview_requested: bool = False,
                                     preview_ready: bool = False,
                                     preview_runtime: object = None,
                                     owner_read_requested: bool = False,
                                     owner_read_ready: bool = False,
                                     owner_delete_requested: bool = False,
                                     owner_delete_ready: bool = False):
    """Compose existing preview, owner recovery, source and bootstrap handlers.

    This is NOT production app.py, a deployed service, or a clean-cutover
    switch. It never imports/mutates the shared application or mounts the full
    Piece router. No module-level application, environment keys, remote IO,
    new wire contract, or automatic source/preview operation is introduced.

    The caller must independently establish PCE-7 readiness for its explicitly
    authorized target. Requested, TTL and renderer values are not evidence of
    that readiness. Defaults are OFF; there is no default TTL or renderer.
    Owner history/detail have their own requested/ready pair and do not need
    generation, a preview TTL or a current renderer. Owner deletion requires
    its own requested/ready pair AND effective owner read, retaining PCE-7's
    recovery-only state. No save, visibility mutation, public read or export
    operation can be enabled by this composition.
    Actual Auth/DB/device admission and production cutover remain separate.
    """
    requested = dict.fromkeys(PIECE_FEATURE_NAMES, False)
    ready = dict.fromkeys(PIECE_FEATURE_NAMES, False)
    requested['piece_v2_preview_enabled'] = preview_requested is True
    ready['piece_v2_preview_enabled'] = preview_ready is True
    requested['piece_v2_owner_read_enabled'] = owner_read_requested is True
    ready['piece_v2_owner_read_enabled'] = owner_read_ready is True
    requested['piece_v2_delete_enabled'] = owner_delete_requested is True
    ready['piece_v2_delete_enabled'] = owner_delete_ready is True
    configuration = {'requested': requested, 'ready': ready}
    values = None
    if (preview_runtime is not None
            or resolve_piece_feature_flags(configuration)['piece_v2_preview_enabled']):
        values = validate_piece_preview_runtime(preview_runtime)

    # Imports and application construction occur only on an explicit call,
    # after invalid supplied runtime values have been rejected without IO.
    from fastapi import FastAPI
    from api_app_bootstrap import register_app_bootstrap_routes
    from api_piece_v2 import (read_quota, create_preview, mutate_preview_visual, cancel_preview,
                             owner_history, owner_detail, owner_delete)
    from piece_v2_source_ref_http import read_original_source_ref

    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.state.piece_v2_runtime = configuration
    if values is not None:
        ttl, renderer = values
        app.state.piece_preview_runtime = {'ttl_seconds': ttl, 'renderer_version': renderer}
    # Register the preview handlers directly, without a version-dependent
    # included-router wrapper. The full Piece router remains unmounted.
    app.add_api_route('/emotion/piece/source-ref/{saved_input_id}',
                      read_original_source_ref, methods=['GET'])
    app.add_api_route('/emotion/piece/preview', create_preview, methods=['POST'])
    app.add_api_route('/emotion/piece/preview/{preview_id}',
                      mutate_preview_visual, methods=['PATCH'])
    # Existing owner/revision-bound cleanup remains available after preview
    # generation is stopped; cancellation neither saves nor consumes quota.
    app.add_api_route('/emotion/piece/preview/{preview_id}',
                      cancel_preview, methods=['DELETE'])
    register_app_bootstrap_routes(app)
    # Quota uses the existing preview flag and reports saved usage only;
    # can_save is display data, never permission to invoke the save operation.
    app.add_api_route('/emotion/piece/quota', read_quota, methods=['GET'])
    app.add_api_route('/emotion/piece/history', owner_history, methods=['GET'])
    # Keep static paths before the owner-ID path. Shared composition also
    # preserves its additional static legacy paths before this same route.
    app.add_api_route('/emotion/piece/{piece_id}', owner_detail, methods=['GET'])
    app.add_api_route('/emotion/piece/{piece_id}', owner_delete, methods=['DELETE'])
    return app
