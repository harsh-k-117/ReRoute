"""P2 verification: keep the independent validator free of engine imports."""

import ast
from pathlib import Path


def test_verify_does_not_import_engine() -> None:
    verify_dir = Path(__file__).parents[3] / "verify"
    for source_path in verify_dir.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            else:
                continue
            assert all(name != "engine" and not name.startswith("engine.") for name in imported), (
                f"{source_path} imports engine"
            )
