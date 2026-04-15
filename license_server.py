import os
from flask import Flask, request, jsonify
import sqlite3, secrets, string

app = Flask(__name__)
DB = "keys.db"
SECRET = "abcd1234"  # schimba asta

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS keys (
            code TEXT PRIMARY KEY,
            hwid TEXT,
            active INTEGER DEFAULT 1,
            used INTEGER DEFAULT 0
        )""")

@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    code = data.get("code", "").strip().upper()
    hwid = data.get("hwid", "")

    with get_db() as db:
        row = db.execute("SELECT * FROM keys WHERE code = ?", (code,)).fetchone()

        if not row:
            return jsonify({"ok": False, "reason": "Cod invalid."})
        if not row["active"]:
            return jsonify({"ok": False, "reason": "Cod dezactivat."})
        if row["used"] and row["hwid"] != hwid:
            return jsonify({"ok": False, "reason": "Cod folosit pe alt PC."})

        if not row["used"]:
            db.execute("UPDATE keys SET used=1, hwid=? WHERE code=?", (hwid, code))

        return jsonify({"ok": True})

@app.route("/gen", methods=["POST"])
def gen_key():
    if request.headers.get("X-Secret") != SECRET:
        return jsonify({"ok": False}), 403

    code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    with get_db() as db:
        db.execute("INSERT INTO keys (code) VALUES (?)", (code,))
    return jsonify({"ok": True, "code": code})

@app.route("/revoke", methods=["POST"])
def revoke():
    if request.headers.get("X-Secret") != SECRET:
        return jsonify({"ok": False}), 403

    code = request.json.get("code", "").strip().upper()
    with get_db() as db:
        db.execute("UPDATE keys SET active=0 WHERE code=?", (code,))
    return jsonify({"ok": True})

@app.route("/list", methods=["GET"])
def list_keys():
    if request.headers.get("X-Secret") != SECRET:
        return jsonify({"ok": False}), 403

    with get_db() as db:
        rows = db.execute("SELECT code, hwid, active, used FROM keys").fetchall()
    return jsonify({"ok": True, "keys": [dict(r) for r in rows]})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)
