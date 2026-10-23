from __future__ import annotations
import json, sqlite3, subprocess
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Allowlist:
    recipients: frozenset[str]
    @classmethod
    def load(cls, path: Path) -> "Allowlist":
        return cls(frozenset(str(x) for x in json.loads(path.read_text()).get("recipients", [])))
    def permits(self, recipient: str) -> bool:
        return recipient in self.recipients

class MessagesBridge:
    def __init__(self, allowlist: Allowlist, database: Path | None = None):
        self.allowlist = allowlist
        self.database = database or Path.home() / "Library/Messages/chat.db"

    def recent_messages(self, limit: int = 20) -> list[dict[str, str]]:
        if limit < 1: raise ValueError("limit must be positive")
        with sqlite3.connect(f"file:{self.database}?mode=ro", uri=True) as conn:
            rows = conn.execute("""SELECT message.text, handle.id FROM message
                LEFT JOIN handle ON message.handle_id = handle.ROWID
                WHERE message.text IS NOT NULL ORDER BY message.date DESC LIMIT ?""", (limit,)).fetchall()
        return [{"text": text, "sender": sender or "unknown"} for text, sender in rows]

    def send(self, recipient: str, text: str, *, confirmed: bool = False) -> None:
        if not self.allowlist.permits(recipient): raise PermissionError("recipient is not in the configured allowlist")
        if not confirmed: raise PermissionError("sending requires explicit confirmation")
        if not text.strip(): raise ValueError("text must not be empty")
        script = ('on run argv\n tell application "Messages"\n set targetService to 1st service whose service type is iMessage\n'
                  ' set targetBuddy to buddy (item 1 of argv) of targetService\n send (item 2 of argv) to targetBuddy\n end tell\nend run')
        subprocess.run(["osascript", "-e", script, recipient, text], check=True)
