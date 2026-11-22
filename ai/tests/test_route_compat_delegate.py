"""Legacy delegation follows the same included route as actual HTTP routing."""
import asyncio
import pytest
from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.testclient import TestClient
from route_compat_delegate import call_registered_route_json, find_registered_route_endpoint


@pytest.mark.parametrize("included", [False, True])
def test_delegate_uses_effective_path_method_and_endpoint_defaults(included):
    app = FastAPI()
    owner = APIRouter() if included else app
    @owner.get("/item")
    async def item(code: str, label: str = Query("default")) -> dict:
        return {"code": code, "label": label}
    if included:
        nested = APIRouter()
        nested.include_router(owner, prefix="/inner")
        app.include_router(nested, prefix="/outer")
    path = "/outer/inner/item" if included else "/item"
    assert find_registered_route_endpoint(app, path=path) is item
    assert find_registered_route_endpoint(app, path=path, method="POST") is None
    assert find_registered_route_endpoint(app, path=path + "/missing") is None
    actual = asyncio.run(call_registered_route_json(app, path=path, detail="synthetic", code="sample"))
    assert actual == TestClient(app).get(path, params={"code": "sample"}).json()
    assert actual == {"code": "sample", "label": "default"}


def test_missing_route_remains_an_error():
    with pytest.raises(HTTPException) as failure:
        asyncio.run(call_registered_route_json(FastAPI(), path="/missing", detail="synthetic"))
    assert failure.value.status_code == 502


def test_real_legacy_profile_url_reaches_canonical_handler_and_preserves_denial(monkeypatch):
    import api_public_profile
    from api_relationship_compat import register_relationship_compat_routes
    app = FastAPI()
    api_public_profile.register_public_profile_routes(app)
    register_relationship_compat_routes(app)
    reached = []
    def deny_before_any_service_access():
        reached.append(True)
        raise HTTPException(status_code=403, detail="synthetic canonical denial")
    monkeypatch.setattr(api_public_profile, "_ensure_supabase_config", deny_before_any_service_access)
    client = TestClient(app)
    canonical = client.get("/public/profile/by-share-code", params={"code": "synthetic"})
    legacy = client.get("/public/profile/by-friend-code", params={"code": "synthetic"})
    assert reached == [True, True]
    assert canonical.status_code == legacy.status_code == 403
    assert canonical.json() == legacy.json() == {"detail": "synthetic canonical denial"}
