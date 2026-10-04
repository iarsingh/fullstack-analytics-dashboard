from fastapi import FastAPI, Header, HTTPException
from dashboard.store import add, chart, listing, login, seed, user
app = FastAPI(title="Full-Stack Analytics Dashboard")
seed()

def current(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing token")
    email = user(authorization.removeprefix("Bearer ").strip())
    if not email:
        raise HTTPException(401, "invalid token")
    return email

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/login")
def post_login(body: dict):
    tok = login(body.get("email"), body.get("password") or "")
    if not tok:
        raise HTTPException(401, "bad credentials")
    return {"token": tok}

@app.post("/metrics")
def post_metric(body: dict, authorization: str | None = Header(default=None)):
    email = current(authorization)
    if not isinstance(body.get("name"), str) or not isinstance(body.get("value"), (int, float)) or isinstance(body.get("value"), bool):
        raise HTTPException(422, "name and numeric value required")
    return {"id": add(email, body["name"], body["value"])}

@app.get("/metrics")
def get_metrics(name: str | None = None, limit: int = 20, offset: int = 0, authorization: str | None = Header(default=None)):
    return listing(current(authorization), name, limit, offset)

@app.get("/charts")
def get_charts(authorization: str | None = Header(default=None)):
    return chart(current(authorization))
