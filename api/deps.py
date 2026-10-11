"""FastAPI dependencies for the current in-memory session."""

from .store import SessionStore, default_store

_store = default_store()


def get_store() -> SessionStore:
    return _store


def set_store(store: SessionStore) -> None:
    """Replace the active session store (used by upload confirm)."""
    global _store  # noqa: PLW0603
    _store = store
