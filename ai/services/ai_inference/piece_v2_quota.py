"""Piece v2 body-free quota read/projection, NOT terminal save admission.

The atomic SQL owner re-reads profiles and the ledger under locks. This pure
projection consumes a server-read count and aware server time; it neither reads
old published rows nor writes quota. The HTTP owner supplies authenticated
identity and the existing guarded service-role RPC transport.
"""
from __future__ import annotations

from datetime import datetime
from types import MappingProxyType
from uuid import UUID
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


async def read_piece_quota(*, authenticated_user_id: str, post_rpc) -> dict:
    """Read a body-free DB snapshot, without reserving or admitting a save.

    The service-only function reads the plan and immutable usage with one DB
    timestamp/snapshot. A concurrent save, plan change or month rollover may
    supersede this display; terminal SQL remains authoritative.
    """
    try:
        owner = str(UUID(authenticated_user_id))
        if not UUID(owner).int:
            raise ValueError
        response = await post_rpc('piece_read_quota_v2',
            {'p_owner_user_id': owner}, timeout=8.0)
        if response.status_code != 200:
            raise ValueError
        value = response.json()
        if (type(value) is not dict
                or set(value) != {'subscription_tier', 'saved_count', 'server_now'}
                or type(value['subscription_tier']) is not str
                or value['subscription_tier'] not in SAVE_LIMITS
                or type(value['saved_count']) is not int
                or not 0 <= value['saved_count'] <= 9223372036854775807
                or type(value['server_now']) is not str
                or len(value['server_now']) > 64):
            raise ValueError
        server_now = datetime.fromisoformat(value['server_now'].replace('Z', '+00:00'))
        return project_piece_quota(server_tier=value['subscription_tier'],
            saved_count=value['saved_count'], server_now=server_now)
    except Exception:
        # Missing RPC, denied read and malformed ACK never become free/zero.
        # The request guard retains OFF through this closed error mapping.
        # BaseException (including task cancellation) deliberately propagates.
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE') from None


def project_piece_plan_capabilities(*, server_tier: str) -> dict:
    """PCE-6 plan display only; eligible formats remain the artifact's list.

    Neither this table nor quota.can_save authorizes a feature or a mutation.
    Return fresh lists so the response cannot mutate the plan definition.
    """
    if type(server_tier) is not str or server_tier not in SAVE_LIMITS:
        raise PieceContractError('PIECE_TEMPORARILY_UNAVAILABLE')
    return {
        'format_selection': {'free': 'fixed', 'plus': 'automatic',
                             'premium': 'eligible_choice'}[server_tier],
        'theme_ids': ['soft_paper'] if server_tier == 'free' else ['soft_paper', 'quiet_night'],
        'aspect_ratios': ['4:5', '9:16'] if server_tier == 'premium' else ['4:5'],
        'branding_modes': (['required_small'] if server_tier == 'free' else
                           ['required_subtle', 'off'] if server_tier == 'premium' else ['required_subtle']),
    }
