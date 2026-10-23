import json, sqlite3
import pytest
from bridge.core import Allowlist, MessagesBridge

def test_allowlist_and_read_only_messages(tmp_path):
    allowlist = tmp_path / "allow.json"; allowlist.write_text(json.dumps({"recipients": ["a"]}))
    db = tmp_path / "chat.db"; conn = sqlite3.connect(db)
    conn.executescript("CREATE TABLE message (text TEXT, handle_id INTEGER, date INTEGER); CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);")
    conn.execute("INSERT INTO handle(ROWID, id) VALUES (1, 'a')"); conn.execute("INSERT INTO message VALUES ('hi', 1, 1)"); conn.commit(); conn.close()
    assert MessagesBridge(Allowlist.load(allowlist), db).recent_messages() == [{"text": "hi", "sender": "a"}]

def test_send_requires_allowlist_and_confirmation(tmp_path):
    path = tmp_path / "allow.json"; path.write_text(json.dumps({"recipients": ["a"]})); bridge = MessagesBridge(Allowlist.load(path), tmp_path / "missing.db")
    with pytest.raises(PermissionError): bridge.send("a", "hi")
    with pytest.raises(PermissionError): bridge.send("b", "hi", confirmed=True)
