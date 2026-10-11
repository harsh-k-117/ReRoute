"""contract/__init__.py - re-export of the frozen contract models and function signatures

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 (models ARE the contract: -> OpenAPI -> TypeScript via openapi-typescript) · JSON fixtures
Spec : contract-v1 (frozen 1:00)
"""
from contract.models import *  # noqa: F401,F403
