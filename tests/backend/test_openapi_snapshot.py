"""
Locks the published API contract. If you change an endpoint or model on
purpose, regenerate the snapshot and review the diff:

    cd server && UPDATE_OPENAPI_SNAPSHOT=1 uv run pytest ../tests/backend/test_openapi_snapshot.py -c ../tests/pytest.ini
"""
import json
import os
from pathlib import Path

from main import app

SNAPSHOT = Path(__file__).parent / "openapi.snapshot.json"


def test_openapi_matches_snapshot():
    current = json.loads(json.dumps(app.openapi()))
    if os.getenv("UPDATE_OPENAPI_SNAPSHOT") == "1":
        SNAPSHOT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
    assert current == json.loads(SNAPSHOT.read_text()), (
        "API contract changed. If intended, regenerate the snapshot (see module docstring) and review the diff."
    )
