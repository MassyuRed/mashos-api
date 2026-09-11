"""Private Q2 store. One RPC is one short Postgres transaction; no retries.

The caller supplies a verified user ID, never an ID from a request body.
No exception includes PostgREST response text or a source-bearing payload.
"""
from __future__ import annotations

import httpx
from supabase_client import sb_post_rpc


class ThreadStoreError(Exception):
    def __init__(self, code: str, status: int = 503, *, transient: bool = False):
        super().__init__(code)
        self.code, self.status, self.transient = code, status, transient


class EmlisThreadStore:
    async def _rpc(self, name, payload):
        try:
            response = await sb_post_rpc(name, payload, timeout=8.0)
        except (httpx.TransportError, httpx.TimeoutException):
            raise ThreadStoreError("save_result_unknown") from None
        if response.status_code >= 300:
            try:
                code = response.json().get("code", "")
            except (ValueError, AttributeError):
                code = ""
            if code == "P0002":
                raise ThreadStoreError("thread_unavailable", 404)
            if code in {"40001", "23505", "23503"}:
                raise ThreadStoreError("thread_conflict", 409)
            # Only explicit DB rollback/unavailability codes prove retryability.
            # A generic 5xx or timeout can be a successful commit with lost ACK.
            if code in {"57P01", "57P02", "57P03", "53300"}:
                raise ThreadStoreError("storage_temporarily_unavailable", transient=True)
            raise ThreadStoreError("save_result_unknown")
        try:
            return response.json()
        except ValueError:
            raise ThreadStoreError("save_result_unknown") from None

    async def read(self, user_id, *, input_id=None, thread_id=None):
        result = await self._rpc("emlis_thread_read", {
            "p_user_id": user_id, "p_input_id": input_id, "p_thread_id": thread_id})
        if not isinstance(result, dict):
            raise ThreadStoreError("thread_unavailable", 404)
        return result

    async def commit(self, user_id, snapshot, next_state, events, *, finishing_attempt=None):
        old = snapshot.get("thread") or {}
        result = await self._rpc("emlis_thread_commit", {
            "p_user_id": user_id, "p_input_id": snapshot["original"]["id"],
            "p_thread_id": next_state["id"], "p_expected_revision": old.get("revision", 0),
            "p_source_snapshot": snapshot["original"], "p_access_tier": snapshot["tier"],
            "p_next": next_state, "p_events": events, "p_finishing_attempt": finishing_attempt})
        if not isinstance(result, dict) or not result.get("thread"):
            raise ThreadStoreError("save_result_unknown")
        return result
