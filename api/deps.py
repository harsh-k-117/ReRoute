"""FastAPI dependencies for the current in-memory session."""

from .store import SessionStore, default_store

_store = default_store()


def get_store() -> SessionStore:
    return _store
