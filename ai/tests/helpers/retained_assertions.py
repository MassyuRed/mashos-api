"""Run independent checks after a mismatch without turning the test green.

Only explicitly wrapped checks continue. Setup, product exceptions and other
assertions stay fatal. Original expressions and expected values are retained.
"""
from contextvars import ContextVar
from functools import wraps
import json
import inspect

_current = ContextVar("retained_assertions")


def continue_assertions(test):
    @wraps(test)
    def run(*args, **kwargs):
        state = {"checks": 0, "failures": [], "completed": False}
        token = _current.set(state)
        try:
            result = test(*args, **kwargs)
            state["completed"] = True
        except BaseException as error:
            if state["failures"]:
                error.add_note("Earlier retained assertion failures:\n" + "\n\n".join(state["failures"]))
            raise
        finally:
            _current.reset(token)
            print("RETAINED_ASSERTIONS " + json.dumps({
                "test": test.__name__, "checks": state["checks"],
                "failures": len(state["failures"]), "completed": state["completed"],
            }))
        if state["failures"]:
            raise AssertionError("Retained assertion failures:\n" + "\n\n".join(state["failures"]))
        return result
    return run


def retained_assertion(evaluate, expression, message=None, *, evaluation_errors=()):
    state = _current.get()
    state["checks"] += 1
    # Only a call site's explicitly named text-lookup error may continue.
    # Other evaluation exceptions remain fatal, including product errors.
    error = None
    try:
        passed = bool(evaluate())
    except evaluation_errors as caught:
        passed = False
        error = type(caught).__name__ + ": " + str(caught)
    if passed:
        return
    frame = inspect.currentframe().f_back
    location = f"{frame.f_code.co_filename}:{frame.f_lineno}"
    context = {key: value for key, value in frame.f_locals.items()
               if key in {"follow", "body", "original", "changed", "old", "new", "nominal", "phrase", "replacement", "clauses", "index"}
               and (isinstance(value, (str, int, bool)) or
                    isinstance(value, (list, tuple)) and all(isinstance(x, str) for x in value))}
    state["failures"].append(location + ": " + expression + (
        "\n" + str(message()) if message is not None else "") + (
        "\nEvaluation error retained: " + error if error else "") +
        "\nAssertion context: " + json.dumps(context, ensure_ascii=False))
