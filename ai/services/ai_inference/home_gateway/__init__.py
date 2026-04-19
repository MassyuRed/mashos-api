"""Home write gateway for the national system.

Phase 2 keeps existing public routes intact and moves canonical write-side
execution behind a shared internal gateway.
"""

from .cache_invalidator import (
    HomeCacheInvalidationPlan,
    build_cache_invalidation_plan,
    execute_cache_invalidation,
)
from .command_gateway import (
    HomeCommandGateway,
    execute_home_command,
    plan_home_command,
)
from .command_types import (
    HomeCommand,
    HomeCommandContext,
    HomeCommandName,
    HomeCommandResult,
    HomeDispatchAction,
    HomeDispatchPlan,
    HomeGatewayExecution,
    HomeGatewayPlan,
)
from .dispatch_planner import build_dispatch_plan

__all__ = [
    "HomeCacheInvalidationPlan",
    "HomeCommand",
    "HomeCommandContext",
    "HomeCommandGateway",
    "HomeCommandName",
    "HomeCommandResult",
    "HomeDispatchAction",
    "HomeDispatchPlan",
    "HomeGatewayExecution",
    "HomeGatewayPlan",
    "build_cache_invalidation_plan",
    "build_dispatch_plan",
    "execute_cache_invalidation",
    "execute_home_command",
    "plan_home_command",
]
