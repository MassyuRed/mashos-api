from __future__ import annotations

import os
from typing import Dict, Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from client_compat import extract_client_meta


class AppBootstrapResponse(BaseModel):
    minimum_supported_version: Optional[str] = None
    recommended_version: Optional[str] = None
    maintenance_message: Optional[str] = None
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    client_meta: Dict[str, Optional[str]] = Field(default_factory=dict)


def register_app_bootstrap_routes(app: FastAPI) -> None:
    @app.get("/app/bootstrap", response_model=AppBootstrapResponse)
    async def get_app_bootstrap(request: Request) -> AppBootstrapResponse:
        client_meta = extract_client_meta(request.headers)

        return AppBootstrapResponse(
            minimum_supported_version=(os.getenv("APP_MINIMUM_SUPPORTED_VERSION") or "").strip() or None,
            recommended_version=(os.getenv("APP_RECOMMENDED_VERSION") or "").strip() or None,
            maintenance_message=(os.getenv("APP_MAINTENANCE_MESSAGE") or "").strip() or None,
            feature_flags={
                "account_delete_enabled": True,
                "myweb_mock_enabled": False,
                "today_question_enabled": True,
                "today_question_history_enabled": True,
                "subscription_sales_enabled": (os.getenv("COCOLON_SUBSCRIPTION_SALES_ENABLED") or "true").strip().lower() in {"1", "true", "yes", "on"},
            },
            client_meta=client_meta,
        )
