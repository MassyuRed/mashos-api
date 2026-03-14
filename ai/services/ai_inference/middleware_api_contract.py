from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request

from api_contract_registry import API_CONTRACT_POLICY_VERSION, find_contract_entry_for_request

REQUEST_ID_HEADER = "X-Cocolon-Request-Id"
POLICY_VERSION_HEADER = "X-Cocolon-Api-Policy-Version"
CONTRACT_ID_HEADER = "X-Cocolon-Contract-Id"
DEPRECATED_HEADER = "X-Cocolon-Deprecated"
REPLACEMENT_HEADER = "X-Cocolon-Replacement"


def install_api_contract_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _api_contract_headers(request: Request, call_next):
        request_id = str(uuid4())
        request.state.cocolon_request_id = request_id

        response = await call_next(request)
        response.headers.setdefault(REQUEST_ID_HEADER, request_id)
        response.headers.setdefault(POLICY_VERSION_HEADER, API_CONTRACT_POLICY_VERSION)

        contract = find_contract_entry_for_request(request)
        if contract is not None:
            response.headers.setdefault(CONTRACT_ID_HEADER, contract.contract_id)
            response.headers.setdefault(DEPRECATED_HEADER, "true" if contract.deprecated else "false")
            if contract.replacement:
                response.headers.setdefault(REPLACEMENT_HEADER, contract.replacement)

        return response