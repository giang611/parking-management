import ast
import pathlib

from fastapi.testclient import TestClient

from business_layer.main import app

FORBIDDEN = {"fastapi", "starlette", "flask", "sqlalchemy", "sqlite3", "psycopg2"}


def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_service_layer_has_no_web_or_db_imports():
    for path in pathlib.Path("business_layer/services").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for n in names:
                assert n.split(".")[0] not in FORBIDDEN, f"{path}: import {n}"
