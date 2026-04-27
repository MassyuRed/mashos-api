# -*- coding: utf-8 -*-
"""Legacy MyWeb read compat facade.

The current owner is ``api_analysis_reads``. This module intentionally contains
no runtime body; legacy imports are forwarded to the current Analysis owner
while DB/table/wire names remain MyWeb-compatible until the DB rename phase.
"""

from __future__ import annotations

import sys
import types

import api_analysis_reads as _current

# Public response/request models used by legacy compat routes and tests.
MyWebWeeklySummary = _current.MyWebWeeklySummary
MyWebMonthlySummary = _current.MyWebMonthlySummary
MyWebInputStatusSummary = _current.MyWebInputStatusSummary
MyWebHomeSummaryResponse = _current.MyWebHomeSummaryResponse
MyWebWeeklyDay = _current.MyWebWeeklyDay
MyWebWeeklyDaysResponse = _current.MyWebWeeklyDaysResponse
AnalysisWeeklySummary = _current.AnalysisWeeklySummary
AnalysisMonthlySummary = _current.AnalysisMonthlySummary
AnalysisInputStatusSummary = _current.AnalysisInputStatusSummary
AnalysisHomeSummaryResponse = _current.AnalysisHomeSummaryResponse
AnalysisWeeklyDay = _current.AnalysisWeeklyDay
AnalysisWeeklyDaysResponse = _current.AnalysisWeeklyDaysResponse
get_myweb_home_summary_payload_for_user = _current.get_myweb_home_summary_payload_for_user
get_analysis_home_summary_payload_for_user = _current.get_analysis_home_summary_payload_for_user
register_analysis_read_routes = _current.register_analysis_read_routes


def register_myweb_read_routes(app):
    """Delegate legacy registration to the current Analysis read owner."""
    return _current.register_analysis_read_routes(app)


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
    "MyWebWeeklySummary",
    "MyWebMonthlySummary",
    "MyWebInputStatusSummary",
    "MyWebHomeSummaryResponse",
    "MyWebWeeklyDay",
    "MyWebWeeklyDaysResponse",
    "AnalysisWeeklySummary",
    "AnalysisMonthlySummary",
    "AnalysisInputStatusSummary",
    "AnalysisHomeSummaryResponse",
    "AnalysisWeeklyDay",
    "AnalysisWeeklyDaysResponse",
    "get_myweb_home_summary_payload_for_user",
    "get_analysis_home_summary_payload_for_user",
    "register_analysis_read_routes",
    "register_myweb_read_routes",
]
