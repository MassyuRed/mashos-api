"""Single application route selection; importing it never loads the author."""
import os

MAX_ANSWER_CHARS = 2000
APPLICATION_EXECUTION_MODE = "EMLIS_APPLICATION"


def development_enabled():
    return (os.getenv("COCOLON_EMLIS_THREAD_DEVELOPMENT", "") == "true"
            and os.getenv("COCOLON_ENV", "") == "development")


def application_mode():
    # Before the first cutover the default remains I5. After cutover, pause
    # with read_only, never legacy: saved corrections require this reader.
    value = os.getenv("COCOLON_EMLIS_THREAD_MODE", "").strip().lower()
    if not value:
        return "development" if development_enabled() else "legacy"
    if value == "active" and os.getenv("COCOLON_EMLIS_THREAD_RELEASE_APPROVED", "") != "true":
        return "read_only"
    if value == "development" and not development_enabled():
        return "read_only"
    return value if value in {"legacy", "development", "active", "read_only"} else "read_only"


def read_enabled():
    return application_mode() != "legacy"


def writes_enabled():
    return application_mode() in {"development", "active"}
