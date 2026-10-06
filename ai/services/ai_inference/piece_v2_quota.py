"""Piece v2 body-free quota projection, NOT terminal save admission.

The atomic SQL owner re-reads profiles and the ledger under locks. This pure
projection consumes a server-read count and aware server time; it neither reads
old published rows nor writes quota. No HTTP route is registered here.
"""
from __future__ import annotations

from datetime import datetime
from types import MappingProxyType
from zoneinfo import ZoneInfo

from piece_v2_contract import PieceContractError

SAVE_LIMITS = MappingProxyType({'free': 5, 'plus': 30, 'premium': None})
_JST = ZoneInfo('Asia/Tokyo')


def project_piece_quota(*, server_tier: str, saved_count: int, server_now: datetime) -> dict:
    if type(saved_count) is not int or saved_count < 0:
        raise PieceContractError('PIECE_REQUEST_INVALID', 'quota_count')
    if not isinstance(server_now, datetime) or server_now.utcoffset() is None:
        raise PieceContractError('PIECE_REQUEST_INVALID', 'server_time')
    tier = server_tier if isinstance(server_tier, str) and server_tier in SAVE_LIMITS else 'free'
    limit = SAVE_LIMITS[tier]
    return {
        'contract_version': 'piece.quota_consumption.v1',
        'subscription_tier': tier,
        'month_key': server_now.astimezone(_JST).strftime('%Y-%m'),
        'save_limit': limit,
        'saved_count': saved_count,
        'remaining_count': None if limit is None else max(0, limit - saved_count),
        'can_save': limit is None or saved_count < limit,
    }
