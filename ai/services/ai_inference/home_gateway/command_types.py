from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Mapping, Optional, Tuple

HomeCommandName = Literal[
    "emotion.submit",
    "today_question.answer.create",
    "notice.read",
    "notice.popup_seen",
    "emotion.reflection.publish",
]


@dataclass(frozen=True)
class HomeCommandContext:
    user_id: str
    source: str = "home"
    requested_at: Optional[str] = None


@dataclass(frozen=True)
class HomeCommand:
    name: HomeCommandName
    payload: Mapping[str, Any] = field(default_factory=dict)
    context: Optional[HomeCommandContext] = None


@dataclass(frozen=True)
class HomeDispatchAction:
    family: str
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HomeDispatchPlan:
    command_name: HomeCommandName
    actions: Tuple[HomeDispatchAction, ...] = ()


@dataclass(frozen=True)
class HomeCacheInvalidationPlan:
    response_keys: Tuple[str, ...] = ()
    startup_snapshot: bool = False


@dataclass(frozen=True)
class HomeGatewayPlan:
    command: HomeCommand
    dispatch: HomeDispatchPlan
    cache_invalidation: HomeCacheInvalidationPlan


@dataclass(frozen=True)
class HomeCommandResult:
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HomeGatewayExecution:
    plan: HomeGatewayPlan
    result: HomeCommandResult
