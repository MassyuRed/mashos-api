from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "services", ROOT / "services" / "ai_inference"):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import subscription_projection as sp


def _purchase(store: str, owner_hint: str | None) -> sp.VerifiedPurchase:
    return sp.VerifiedPurchase(
        store=store,
        product_id="synthetic.plus",
        plan_code="plus",
        status="active",
        verification_status="verified",
        store_ref="synthetic-store-ref",
        purchase_token="synthetic-token" if store == "android" else None,
        transaction_id="synthetic-transaction",
        original_transaction_id="synthetic-original" if store == "ios" else None,
        expires_at="2027-01-01T00:00:00+00:00",
        app_user_id_hint=owner_hint,
    )


@pytest.fixture
def storage_calls(monkeypatch):
    calls = []

    async def absent(*args, **kwargs):
        calls.append(("read", args, kwargs))
        return None

    async def insert(table, payload):
        calls.append(("insert", table, payload))
        return payload

    async def project(user_id):
        calls.append(("project", user_id))
        return {"user_id": user_id}

    monkeypatch.setattr(sp, "find_purchase_claim", absent)
    monkeypatch.setattr(sp, "find_entitlement_by_store_ref", absent)
    monkeypatch.setattr(sp, "insert_row", insert)
    monkeypatch.setattr(sp, "project_profile_tier", project)
    return calls


@pytest.mark.parametrize("store", ["ios", "android"])
def test_store_verified_owner_mismatch_stops_before_storage(store, storage_calls):
    with pytest.raises(sp.PurchaseOwnershipConflictError):
        asyncio.run(sp.persist_verified_purchase(
            user_id="synthetic-B",
            verified_purchase=_purchase(store, "synthetic-A"),
        ))

    assert storage_calls == []


@pytest.mark.parametrize("store", ["ios", "android"])
@pytest.mark.parametrize("owner_hint", ["synthetic-A", None])
def test_matching_owner_and_legacy_missing_hint_preserve_persistence(store, owner_hint, storage_calls):
    result = asyncio.run(sp.persist_verified_purchase(
        user_id="synthetic-A",
        verified_purchase=_purchase(store, owner_hint),
    ))

    inserts = [call for call in storage_calls if call[0] == "insert"]
    assert [call[1] for call in inserts] == [sp.CLAIMS_TABLE, sp.ENTITLEMENTS_TABLE]
    assert [call[2]["user_id"] for call in inserts] == ["synthetic-A", "synthetic-A"]
    assert storage_calls[-1] == ("project", "synthetic-A")
    assert result == {"user_id": "synthetic-A"}


@pytest.mark.parametrize("store", ["ios", "android"])
def test_legacy_missing_hint_keeps_existing_claim_owner_boundary(store, storage_calls, monkeypatch):
    async def existing_claim(**kwargs):
        storage_calls.append(("claim_read", kwargs))
        return {"id": 1, "user_id": "synthetic-B"}

    monkeypatch.setattr(sp, "find_purchase_claim", existing_claim)

    with pytest.raises(sp.PurchaseOwnershipConflictError):
        asyncio.run(sp.persist_verified_purchase(
            user_id="synthetic-A",
            verified_purchase=_purchase(store, None),
        ))

    assert [call[0] for call in storage_calls] == ["claim_read"]


@pytest.mark.parametrize("store", ["ios", "android"])
def test_matching_uuid_owner_ignores_uuid_text_case(store, storage_calls):
    user_id = "abcdef01-2345-4678-9abc-def012345678"
    result = asyncio.run(sp.persist_verified_purchase(
        user_id=user_id,
        verified_purchase=_purchase(store, user_id.upper()),
    ))
    assert result == {"user_id": user_id}
    assert [call[2]["user_id"] for call in storage_calls if call[0] == "insert"] == [user_id, user_id]


@pytest.mark.parametrize("owner_hint,user_id", [
    ("abcdef01-2345-4678-9abc-def012345678", "abcdef02-2345-4678-9abc-def012345678"),
    ("synthetic-A", "synthetic-a"),
])
def test_different_uuid_and_opaque_case_difference_remain_distinct(owner_hint, user_id, storage_calls):
    with pytest.raises(sp.PurchaseOwnershipConflictError):
        asyncio.run(sp.persist_verified_purchase(
            user_id=user_id,
            verified_purchase=_purchase("ios", owner_hint),
        ))
    assert storage_calls == []
