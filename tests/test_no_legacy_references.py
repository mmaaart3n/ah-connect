"""Ensure legacy gist-based references are not present."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent

FORBIDDEN_PATTERNS = [
    "jabbink",
    "8bfa44bdfc535d696b340c46d228fdd1",
    "Appie/8.22.3",
    "secure/oauth/authorize",
    "ah_shopping",
    "clientId: appie",
]

ALLOWED_PATH_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}


def _iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.name == "test_no_legacy_references.py":
            continue
        if any(part in ALLOWED_PATH_PARTS for part in path.parts):
            continue
        if path.suffix in {".png", ".pyc", ".git"}:
            continue
        try:
            yield path
        except OSError:
            continue


def test_no_legacy_references_in_project():
    violations = []
    for path in _iter_text_files():
        try:
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in content:
                violations.append(f"{path}: {pattern}")
    assert not violations, "Legacy references found:\n" + "\n".join(violations)
