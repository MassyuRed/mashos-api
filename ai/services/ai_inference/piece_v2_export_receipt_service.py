"""B13-B receipt for a verified client-rendered image, before any OS action.

The server authenticates the owner and binds the client-declared PNG hash to
the current saved artifact. It never receives PNG bytes or attests delivery.
"""
from datetime import datetime
from hashlib import sha256
import re
from uuid import UUID

from piece_v2_contract import PieceContractError, canonical_sha256_hex

VERSION = 'piece.export_receipt.v1'
ACK_HEADER = 'X-Piece-Export-Receipt'
ACK_VALUE = '1'
RENDERERS = ('piece.rn_bitmap_renderer.ios.v1', 'piece.rn_bitmap_renderer.ios.v2')
PROFILES = {'png_1080x1350_srgb_v1': 1350, 'png_1080x1920_srgb_v1': 1920}
FIXED = {
    'receipt_version': VERSION, 'visual_catalog_version': 'piece.visual_catalog.v1',
    'layout_policy_version': 'piece.long_text_layout.v1', 'renderer_family': 'rn_native',
    'export_contract_version': 'piece.export_contract.v1', 'mime_type': 'image/png',
    'persistent_server_asset': False, 'body_free': True,
}
FIELDS = set(FIXED) | {'piece_id', 'piece_text_hash', 'visual_recipe_hash', 'renderer_version',
                      'output_profile', 'width', 'height', 'asset_sha256', 'generated_at'}
STATUSES = {'PIECE_REQUEST_INVALID': 400, 'PIECE_AUTH_REQUIRED': 401, 'PIECE_NOT_FOUND': 404,
            'PIECE_CONFLICT': 409, 'PIECE_TEMPORARILY_UNAVAILABLE': 503, 'PIECE_FEATURE_DISABLED': 503}
RPC = 'piece_record_export_receipt_v2'


def _fail(code='PIECE_REQUEST_INVALID'):
    raise PieceContractError(code) from None


def _uuid(value, code):
    try:
        parsed = UUID(value)
        if parsed.int and str(parsed) == value:
            return value
    except (ValueError, TypeError, AttributeError):
        pass
    _fail(code)


async def save_export_receipt(*, rpc, owner, piece_id, key, value):
    _uuid(piece_id, 'PIECE_REQUEST_INVALID')
    if not isinstance(key, str) or not re.fullmatch(r'[0-9a-f]{32}', key):
        _fail()
    if type(value) is not dict or set(value) != FIELDS | {'expected_row_version'}:
        _fail()
    if any(type(value[k]) is not type(expected) or value[k] != expected for k, expected in FIXED.items()):
        _fail()
    if (value['piece_id'] != 'piece:' + piece_id or type(value['expected_row_version']) is not int
            or not 1 <= value['expected_row_version'] <= 9007199254740991
            or value['renderer_version'] not in RENDERERS
            or type(value['output_profile']) is not str or value['output_profile'] not in PROFILES
            or type(value['width']) is not int or value['width'] != 1080
            or type(value['height']) is not int or value['height'] != PROFILES[value['output_profile']]
            or any(type(value[k]) is not str or not re.fullmatch(r'[0-9a-f]{64}', value[k])
                   for k in ('piece_text_hash', 'visual_recipe_hash', 'asset_sha256'))):
        _fail()
    generated_at = value['generated_at']
    try:
        if type(generated_at) is not str or not re.fullmatch(
                r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z', generated_at):
            _fail()
        datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
    except ValueError:
        _fail()

    result = await rpc(RPC, {
        'p_owner_user_id': owner, 'p_piece_id': piece_id,
        'p_expected_row_version': value['expected_row_version'],
        'p_idempotency_key_hash': sha256(('piece.export_receipt.v1:' + key).encode('ascii')).hexdigest(),
        'p_request_identity_hash': canonical_sha256_hex(value),
        'p_piece_text_hash': value['piece_text_hash'], 'p_visual_recipe_hash': value['visual_recipe_hash'],
        'p_asset_sha256': value['asset_sha256'], 'p_renderer_version': value['renderer_version'],
        'p_output_profile': value['output_profile'],
    })
    if type(result) is not dict or set(result) != {'export_id'}:
        _fail('PIECE_TEMPORARILY_UNAVAILABLE')
    export_id = _uuid(result['export_id'], 'PIECE_TEMPORARILY_UNAVAILABLE')
    return {'export_id': export_id, **{k: value[k] for k in sorted(FIELDS)}}
