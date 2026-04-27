# -*- coding: utf-8 -*-
"""Legacy MyWeb report compat facade.

The current owner is ``api_analysis_reports``. This module intentionally keeps
only forwarding aliases for legacy imports while the runtime body lives in the
current Analysis owner.
"""

from __future__ import annotations

import sys
import types

import api_analysis_reports as _current

MyWebEnsureRequest = _current.MyWebEnsureRequest
MyWebEnsureItem = _current.MyWebEnsureItem
MyWebEnsureResponse = _current.MyWebEnsureResponse
MyWebReportRecord = _current.MyWebReportRecord
MyWebReadyReportsResponse = _current.MyWebReadyReportsResponse
MyWebReportDetailResponse = _current.MyWebReportDetailResponse
AnalysisEnsureRequest = _current.AnalysisEnsureRequest
AnalysisEnsureItem = _current.AnalysisEnsureItem
AnalysisEnsureResponse = _current.AnalysisEnsureResponse
AnalysisReportRecord = _current.AnalysisReportRecord
AnalysisReadyReportsResponse = _current.AnalysisReadyReportsResponse
AnalysisReportDetailResponse = _current.AnalysisReportDetailResponse
register_analysis_report_routes = _current.register_analysis_report_routes


def register_myweb_report_routes(app):
    """Delegate legacy registration to the current Analysis report owner."""
    return _current.register_analysis_report_routes(app)


class _CompatModule(types.ModuleType):
    def __getattr__(self, name: str):
        return getattr(_current, name)

    def __setattr__(self, name: str, value):
        if not name.startswith("__"):
            try:
                setattr(_current, name, value)
            except Exception:
                pass
        return super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CompatModule


def __getattr__(name: str):
    return getattr(_current, name)


__all__ = [
    "MyWebEnsureRequest",
    "MyWebEnsureItem",
    "MyWebEnsureResponse",
    "MyWebReportRecord",
    "MyWebReadyReportsResponse",
    "MyWebReportDetailResponse",
    "AnalysisEnsureRequest",
    "AnalysisEnsureItem",
    "AnalysisEnsureResponse",
    "AnalysisReportRecord",
    "AnalysisReadyReportsResponse",
    "AnalysisReportDetailResponse",
    "register_analysis_report_routes",
    "register_myweb_report_routes",
]
