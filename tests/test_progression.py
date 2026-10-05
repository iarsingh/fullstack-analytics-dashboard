from dashboard.progression import fullstack

def test_fullstack_paginates():
    metrics = [{"owner": "ada", "name": "cpu", "value": 1}, {"owner": "ada", "name": "cpu", "value": 3}]
    out = fullstack("ada", metrics, limit=1, offset=0)
    assert out["total"] == 2 and len(out["items"]) == 1
    assert "fastapi" in out["stack"]

