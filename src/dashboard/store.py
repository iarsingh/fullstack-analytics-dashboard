import hashlib, hmac, os, sqlite3, time
SECRET = b"dash-secret"
CONN = sqlite3.connect("file:dash?mode=memory&cache=shared", uri=True, check_same_thread=False)
CONN.row_factory = sqlite3.Row

def init():
    CONN.execute("CREATE TABLE IF NOT EXISTS users(email TEXT PRIMARY KEY, salt BLOB, hash BLOB)")
    CONN.execute("CREATE TABLE IF NOT EXISTS metrics(id INTEGER PRIMARY KEY, owner TEXT, name TEXT, value REAL)")
    CONN.commit()

def _h(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 120000)

def seed():
    init()
    if CONN.execute("SELECT 1 FROM users WHERE email='ada@example.com'").fetchone():
        return
    salt = os.urandom(16)
    CONN.execute("INSERT INTO users VALUES (?,?,?)", ("ada@example.com", salt, _h("pass-ada", salt)))
    CONN.commit()

def token(email):
    body = f"{email}|{int(time.time())+3600}".encode()
    return body.decode() + "|" + hmac.new(SECRET, body, "sha256").hexdigest()

def user(tok):
    try:
        email, exp, sig = tok.split("|")
        body = f"{email}|{exp}".encode()
        if hmac.compare_digest(sig, hmac.new(SECRET, body, "sha256").hexdigest()) and int(exp) >= time.time():
            return email
    except (ValueError, TypeError):
        return None

def login(email, password):
    row = CONN.execute("SELECT salt, hash FROM users WHERE email=?", (email,)).fetchone()
    if not row or not hmac.compare_digest(row["hash"], _h(password, row["salt"])):
        return None
    return token(email)

def add(owner, name, value):
    cur = CONN.execute("INSERT INTO metrics(owner,name,value) VALUES (?,?,?)", (owner, name, float(value)))
    CONN.commit()
    return cur.lastrowid

def listing(owner, name=None, limit=20, offset=0):
    limit, offset = max(1, min(int(limit), 100)), max(0, int(offset))
    if name:
        items = CONN.execute("SELECT * FROM metrics WHERE owner=? AND name=? ORDER BY id DESC LIMIT ? OFFSET ?", (owner, name, limit, offset)).fetchall()
        total = CONN.execute("SELECT COUNT(*) FROM metrics WHERE owner=? AND name=?", (owner, name)).fetchone()[0]
    else:
        items = CONN.execute("SELECT * FROM metrics WHERE owner=? ORDER BY id DESC LIMIT ? OFFSET ?", (owner, limit, offset)).fetchall()
        total = CONN.execute("SELECT COUNT(*) FROM metrics WHERE owner=?", (owner,)).fetchone()[0]
    return {"items": [dict(x) for x in items], "total": total, "limit": limit, "offset": offset}

def chart(owner):
    rows = CONN.execute("SELECT name, AVG(value) m FROM metrics WHERE owner=? GROUP BY name", (owner,)).fetchall()
    return {"series": [{"name": x["name"], "mean": round(x["m"], 4)} for x in rows]}
