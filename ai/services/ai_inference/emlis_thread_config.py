"""Explicit Q2 development gate; importing it does not load the CMEE author."""
import os

MAX_ANSWER_CHARS = 2000
APPLICATION_EXECUTION_MODE = "DEVELOPMENT_APPLICATION"


def development_enabled():
    return (os.getenv("COCOLON_EMLIS_THREAD_DEVELOPMENT", "") == "true"
            and os.getenv("COCOLON_ENV", "") == "development")
