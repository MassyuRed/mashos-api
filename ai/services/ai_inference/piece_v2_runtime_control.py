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
