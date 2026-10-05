# fullstack-analytics-dashboard — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does fullstack-analytics-dashboard address, and what can you demonstrate?

React → FastAPI → SQLite → Docker. Auth, metric CRUD, filters, charts, OpenAPI `/docs`.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/dashboard/main.py`](src/dashboard/main.py): Implementation or supporting configuration.
- [`src/dashboard/store.py`](src/dashboard/store.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`web/src/App.tsx`](web/src/App.tsx): User interface code/assets.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`tests/test_dashboard.py`](tests/test_dashboard.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.
- [`README.md`](README.md): Project explanations or operating notes.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `listing` and explain the decision it makes?

The main walkthrough here is `listing(owner, name=None, limit=20, offset=0)` in [`src/dashboard/store.py`](src/dashboard/store.py#L46).

```python
def listing(owner, name=None, limit=20, offset=0):
    limit, offset = max(1, min(int(limit), 100)), max(0, int(offset))
    if name:
        items = CONN.execute("SELECT * FROM metrics WHERE owner=? AND name=? ORDER BY id DESC LIMIT ? OFFSET ?", (owner, name, limit, offset)).fetchall()
        total = CONN.execute("SELECT COUNT(*) FROM metrics WHERE owner=? AND name=?", (owner, name)).fetchone()[0]
    else:
        items = CONN.execute("SELECT * FROM metrics WHERE owner=? ORDER BY id DESC LIMIT ? OFFSET ?", (owner, limit, offset)).fetchall()
        total = CONN.execute("SELECT COUNT(*) FROM metrics WHERE owner=?", (owner,)).fetchone()[0]
    return {"items": [dict(x) for x in items], "total": total, "limit": limit, "offset": offset}
```

The implementation calls `CONN.execute`, `CONN.execute('SELECT * FROM metrics WHERE owner=? AND name=? ORDER BY id DESC LIMIT ? OFFSET ?', (owner, name, limit, offset)).fetchall`, `CONN.execute('SELECT * FROM metrics WHERE owner=? ORDER BY id DESC LIMIT ? OFFSET ?', (owner, limit, offset)).fetchall`, `CONN.execute('SELECT COUNT(*) FROM metrics WHERE owner=? AND name=?', (owner, name)).fetchone`, `CONN.execute('SELECT COUNT(*) FROM metrics WHERE owner=?', (owner,)).fetchone`, `dict`, `int`, `max`, `min`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `user` have?

`user(tok)` is defined in [`src/dashboard/store.py`](src/dashboard/store.py#L26).

Its return expressions include:

- `email`
- `None`

It uses `f'{email}|{exp}'.encode`, `hmac.compare_digest`, `hmac.new`, `hmac.new(SECRET, body, 'sha256').hexdigest`, `int`, `time.time`, `tok.split`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `HTTPException(401, 'missing token')` in [`src/dashboard/main.py`](src/dashboard/main.py#L8).
- `HTTPException(401, 'invalid token')` in [`src/dashboard/main.py`](src/dashboard/main.py#L11).
- `HTTPException(401, 'bad credentials')` in [`src/dashboard/main.py`](src/dashboard/main.py#L22).
- `HTTPException(422, 'name and numeric value required')` in [`src/dashboard/main.py`](src/dashboard/main.py#L29).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_dashboard.py`](tests/test_dashboard.py#L9) contains `test_crud_filter_page`:

```python
def test_crud_filter_page():
    h = auth()
    client.post("/metrics", json={"name":"cpu","value":11}, headers=h)
    client.post("/metrics", json={"name":"cpu","value":22}, headers=h)
    client.post("/metrics", json={"name":"ram","value":40}, headers=h)
    page = client.get("/metrics?limit=1", headers=h).json()
    assert page["total"] >= 3 and len(page["items"]) == 1
    assert all(i["name"]=="cpu" for i in client.get("/metrics?name=cpu", headers=h).json()["items"])
    assert client.get("/charts", headers=h).json()["series"]
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/dashboard/main.py`](src/dashboard/main.py#L15).
- `POST /login` → `post_login` in [`src/dashboard/main.py`](src/dashboard/main.py#L19).
- `POST /metrics` → `post_metric` in [`src/dashboard/main.py`](src/dashboard/main.py#L26).
- `GET /metrics` → `get_metrics` in [`src/dashboard/main.py`](src/dashboard/main.py#L33).
- `GET /charts` → `get_charts` in [`src/dashboard/main.py`](src/dashboard/main.py#L37).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. How would you investigate data ownership and persistence?

Trace the data/configuration files and the code that reads or writes them in the component table. Identify which files are examples, which records are mutable, and which external store is actually configured. I would document those facts before discussing retention, backup, or tenant isolation.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `listing`?

In [`src/dashboard/store.py`](src/dashboard/store.py#L46), `listing(owner, name=None, limit=20, offset=0)` receives the inputs. The function computes these intermediate values:

- `limit, offset = (max(1, min(int(limit), 100)), max(0, int(offset)))`

Its result is defined by:

- `{'items': [dict(x) for x in items], 'total': total, 'limit': limit, 'offset': offset}`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/dashboard/store.py`](src/dashboard/store.py#L46) branches on:

- `name`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 14. What does `web/src/App.tsx` own?

[`web/src/App.tsx`](web/src/App.tsx) defines `App`.

Trace these definitions and imports to explain the module boundary. Relative imports identify project code; package imports should be checked against the nearest manifest.
