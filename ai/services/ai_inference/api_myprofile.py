# -*- coding: utf-8 -*-
"""Legacy MyProfile aggregate compat facade.

Runtime body now lives in current Self Structure / Connect / Follow Graph
owners. This module forwards legacy imports while DB/table names remain
MyProfile-compatible until the DB rename phase.
"""

from __future__ import annotations

import sys
import types

import api_self_structure as _self_structure
import api_connect as _connect
import api_follow_graph as _follow_graph

MyProfileRequestCreateBody = _self_structure.MyProfileRequestCreateBody
MyProfileRequestCreateResponse = _self_structure.MyProfileRequestCreateResponse
MyProfileRequestActionResponse = _self_structure.MyProfileRequestActionResponse
MyProfileLinkBody = _self_structure.MyProfileLinkBody
MyProfileRemoveFollowerBody = _self_structure.MyProfileRemoveFollowerBody
MyProfileLinkActionResponse = _self_structure.MyProfileLinkActionResponse
MyProfileFollowStatsResponse = _self_structure.MyProfileFollowStatsResponse
MyProfileFollowListItem = _self_structure.MyProfileFollowListItem
MyProfileFollowListResponse = _self_structure.MyProfileFollowListResponse
MyProfileLookupResponse = _self_structure.MyProfileLookupResponse
MyProfileFollowRequestCancelBody = _self_structure.MyProfileFollowRequestCancelBody
MyProfileFollowRequestIdBody = _self_structure.MyProfileFollowRequestIdBody
MyProfileIncomingFollowRequestItem = _self_structure.MyProfileIncomingFollowRequestItem
MyProfileIncomingFollowRequestsResponse = _self_structure.MyProfileIncomingFollowRequestsResponse
MyProfileOutgoingFollowRequestItem = _self_structure.MyProfileOutgoingFollowRequestItem
MyProfileOutgoingFollowRequestsResponse = _self_structure.MyProfileOutgoingFollowRequestsResponse
MyProfileLatestEnsureResponse = _self_structure.MyProfileLatestEnsureResponse
MyProfileLatestStatusResponse = _self_structure.MyProfileLatestStatusResponse
MyProfileMonthlyEnsureBody = _self_structure.MyProfileMonthlyEnsureBody
MyProfileMonthlyEnsureResponse = _self_structure.MyProfileMonthlyEnsureResponse
SelfStructureLatestEnsureResponse = _self_structure.SelfStructureLatestEnsureResponse
SelfStructureLatestStatusResponse = _self_structure.SelfStructureLatestStatusResponse
SelfStructureMonthlyEnsureBody = _self_structure.SelfStructureMonthlyEnsureBody
SelfStructureMonthlyEnsureResponse = _self_structure.SelfStructureMonthlyEnsureResponse


def register_myprofile_legacy_request_routes(app):
    return _self_structure.register_myprofile_legacy_request_routes(app)


def register_self_structure_routes(app):
    return _self_structure.register_self_structure_routes(app)


def register_connect_routes(app):
    return _connect.register_connect_routes(app)


def register_follow_graph_routes(app):
    return _follow_graph.register_follow_graph_routes(app)


def register_myprofile_routes(app):
    register_connect_routes(app)
    register_myprofile_legacy_request_routes(app)
    register_follow_graph_routes(app)
    register_self_structure_routes(app)


_TARGET_MODULES = (_self_structure, _connect, _follow_graph)


class _CompatModule(types.ModuleType):
    def __getattr__(self, name: str):
        for module in _TARGET_MODULES:
            try:
                return getattr(module, name)
            except AttributeError:
                continue
        raise AttributeError(name)

    def __setattr__(self, name: str, value):
        if not name.startswith("__"):
            for module in _TARGET_MODULES:
                if hasattr(module, name):
                    try:
                        setattr(module, name, value)
                    except Exception:
                        pass
        return super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CompatModule


def __getattr__(name: str):
    for module in _TARGET_MODULES:
        try:
            return getattr(module, name)
        except AttributeError:
            continue
    raise AttributeError(name)


__all__ = [
    "MyProfileRequestCreateBody",
    "MyProfileRequestCreateResponse",
    "MyProfileRequestActionResponse",
    "MyProfileLinkBody",
    "MyProfileRemoveFollowerBody",
    "MyProfileLinkActionResponse",
    "MyProfileFollowStatsResponse",
    "MyProfileFollowListItem",
    "MyProfileFollowListResponse",
    "MyProfileLookupResponse",
    "MyProfileFollowRequestCancelBody",
    "MyProfileFollowRequestIdBody",
    "MyProfileIncomingFollowRequestItem",
    "MyProfileIncomingFollowRequestsResponse",
    "MyProfileOutgoingFollowRequestItem",
    "MyProfileOutgoingFollowRequestsResponse",
    "MyProfileLatestEnsureResponse",
    "MyProfileLatestStatusResponse",
    "MyProfileMonthlyEnsureBody",
    "MyProfileMonthlyEnsureResponse",
    "SelfStructureLatestEnsureResponse",
    "SelfStructureLatestStatusResponse",
    "SelfStructureMonthlyEnsureBody",
    "SelfStructureMonthlyEnsureResponse",
    "register_myprofile_legacy_request_routes",
    "register_self_structure_routes",
    "register_connect_routes",
    "register_follow_graph_routes",
    "register_myprofile_routes",
]
