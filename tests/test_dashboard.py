from fastapi.testclient import TestClient
from dashboard.main import app
client = TestClient(app)

def auth():
    t = client.post("/login", json={"email":"ada@example.com","password":"pass-ada"}).json()["token"]
    return {"Authorization": f"Bearer {t}"}

def test_crud_filter_page():
    h = auth()
    client.post("/metrics", json={"name":"cpu","value":11}, headers=h)
    client.post("/metrics", json={"name":"cpu","value":22}, headers=h)
    client.post("/metrics", json={"name":"ram","value":40}, headers=h)
    page = client.get("/metrics?limit=1", headers=h).json()
    assert page["total"] >= 3 and len(page["items"]) == 1
    assert all(i["name"]=="cpu" for i in client.get("/metrics?name=cpu", headers=h).json()["items"])
    assert client.get("/charts", headers=h).json()["series"]

def test_auth():
    assert client.get("/metrics").status_code == 401
