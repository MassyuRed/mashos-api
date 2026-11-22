"""Bind verified MAP progress to the claiming worker's task, if there is one."""
from contextlib import contextmanager
from contextvars import ContextVar


class MapJobClaimChanged(Exception):
    """The claim or the queued input revision no longer matches."""


class MapJobClaimUnavailable(Exception):
    """The storage acknowledgement is missing or cannot be verified."""


_callbacks = ContextVar('analysis_map_job_callbacks', default=None)


@contextmanager
def map_job_progress(progress, check):
    token = _callbacks.set((progress, check))
    try:
        yield
    finally:
        _callbacks.reset(token)


async def checkpoint_v24_phase():
    callbacks = _callbacks.get()
    if callbacks is not None:
        await callbacks[0]()


async def check_map_job_owner():
    callbacks = _callbacks.get()
    if callbacks is not None:
        await callbacks[1]()
