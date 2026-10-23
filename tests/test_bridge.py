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

def test_send_invokes_macos_handoff_only_after_gates(tmp_path, monkeypatch):
    path = tmp_path / "allow.json"; path.write_text(json.dumps({"recipients": ["a"]}))
    calls = []
    monkeypatch.setattr("bridge.core.subprocess.run", lambda args, check: calls.append((args, check)))
    MessagesBridge(Allowlist.load(path)).send("a", "hi", confirmed=True)
    assert calls and calls[0][0][0] == "osascript"
    assert calls[0][0][-2:] == ["a", "hi"]

def test_allowlist_validation_and_database_error_are_actionable(tmp_path):
    malformed = tmp_path / "malformed.json"; malformed.write_text(json.dumps({"recipients": [""]}))
    with pytest.raises(ValueError, match="recipients"):
        Allowlist.load(malformed)
    allow = tmp_path / "allow.json"; allow.write_text(json.dumps({"recipients": ["a"]}))
    with pytest.raises(PermissionError, match="Full Disk Access"):
        MessagesBridge(Allowlist.load(allow), tmp_path / "missing.db").recent_messages()
