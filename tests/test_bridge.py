import json, sqlite3
import pytest
from bridge.core import Allowlist, MessageWatermark, MessagesBridge

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


def test_inbound_messages_include_stable_id_and_direction(tmp_path):
    path = tmp_path / "allow.json"
    path.write_text(json.dumps({"recipients": ["sender"], "senders": ["sender"]}))
    db = tmp_path / "chat.db"
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE message (text TEXT, handle_id INTEGER, date INTEGER, is_from_me INTEGER);
        CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);
    """)
    conn.execute("INSERT INTO handle(ROWID, id) VALUES (1, 'sender')")
    conn.execute("INSERT INTO message VALUES ('hello', 1, 42, 0)")
    conn.commit(); conn.close()
    messages = MessagesBridge(Allowlist.load(path), db).inbound_messages()
    assert messages[0].message_id == "1"
    assert messages[0].sender == "sender"
    assert messages[0].is_from_me is False


def test_inbound_messages_uses_date_rowid_cursor_for_chronological_pagination(tmp_path):
    allowlist = Allowlist(frozenset({"sender"}), frozenset({"sender"}))
    db = tmp_path / "chat.db"
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE message (text TEXT, handle_id INTEGER, date INTEGER, is_from_me INTEGER);
        CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);
    """)
    conn.execute("INSERT INTO handle(ROWID, id) VALUES (1, 'sender')")
    conn.executemany(
        "INSERT INTO message(text, handle_id, date, is_from_me) VALUES (?, 1, ?, 0)",
        [("old", 10), ("first", 20), ("second", 20), ("new", 30)],
    )
    conn.commit(); conn.close()

    bridge = MessagesBridge(allowlist, db)
    page = bridge.inbound_messages(limit=2, after=MessageWatermark("1", 10))
    assert [(item.text, item.timestamp) for item in page] == [("first", 20), ("second", 20)]
    next_page = bridge.inbound_messages(limit=2, after=MessageWatermark(page[-1].message_id, page[-1].timestamp))
    assert [item.text for item in next_page] == ["new"]
