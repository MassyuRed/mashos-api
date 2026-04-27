from __future__ import annotations

"""Legacy MyProfile report-read compat façade.

The current Self Structure report history/detail routes live in
``api_self_structure_reports.py``. This module keeps the legacy MyProfile-named
response models and registrar for compatibility during the rename-safe phase.
"""

from api_self_structure_reports import (
    SelfStructureReportDetailItem as MyProfileReportDetailItem,
    SelfStructureReportDetailResponse as MyProfileReportDetailResponse,
    SelfStructureReportHistoryItem as MyProfileReportHistoryItem,
    SelfStructureReportHistoryResponse as MyProfileReportHistoryResponse,
    register_self_structure_report_routes as register_myprofile_report_read_routes,
)

__all__ = [
    "MyProfileReportHistoryItem",
    "MyProfileReportHistoryResponse",
    "MyProfileReportDetailItem",
    "MyProfileReportDetailResponse",
    "register_myprofile_report_read_routes",
]
