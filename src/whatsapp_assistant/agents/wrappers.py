"""Error-handling decorators for ADK tool functions.

Ported from dls-chatbot: instead of letting a tool raise (which the agent
sees as an opaque error), return a structured {"success": False, "error": ...}
dict the agent can reason about and relay/retry.
"""

import functools
import traceback
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
AF = TypeVar("AF", bound=Callable[..., Awaitable[Any]])


def may_fail(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stack_trace": traceback.format_exc(limit=5),
            }

    return wrapper  # type: ignore[return-value]


def may_fail_async(func: AF) -> AF:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stack_trace": traceback.format_exc(limit=5),
            }

    return wrapper  # type: ignore[return-value]
