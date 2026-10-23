from __future__ import annotations
import json
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Allowlist:
    recipients: frozenset[str]
    @classmethod
    def load(cls, path: Path) -> "Allowlist":
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"could not read allowlist: {exc}") from exc
        recipients = data.get("recipients") if isinstance(data, dict) else None
        if not isinstance(recipients, list) or not all(isinstance(item, str) and item.strip() for item in recipients):
            raise ValueError("allowlist must contain a 'recipients' list of non-empty strings")
        return cls(frozenset(item.strip() for item in recipients))
    def permits(self, recipient: str) -> bool:
        return recipient in self.recipients

class MessagesBridge:
    def __init__(self, allowlist: Allowlist, database: Path | None = None):
        self.allowlist = allowlist
        self.database = database or Path.home() / "Library/Messages/chat.db"

    def recent_messages(self, limit: int = 20) -> list[dict[str, str]]:
        if limit < 1: raise ValueError("limit must be positive")
        try:
            with sqlite3.connect(f"file:{self.database}?mode=ro", uri=True) as conn:
                rows = conn.execute("""SELECT message.text, handle.id FROM message
                    LEFT JOIN handle ON message.handle_id = handle.ROWID
                    WHERE message.text IS NOT NULL ORDER BY message.date DESC LIMIT ?""", (limit,)).fetchall()
        except sqlite3.Error as exc:
            raise PermissionError("could not read Messages database; grant this terminal/app Full Disk Access and retry") from exc
        return [{"text": text, "sender": sender or "unknown"} for text, sender in rows]

    def send(self, recipient: str, text: str, *, confirmed: bool = False) -> None:
        if not self.allowlist.permits(recipient): raise PermissionError("recipient is not in the configured allowlist")
        if not confirmed: raise PermissionError("sending requires explicit confirmation")
        if not text.strip(): raise ValueError("text must not be empty")
        script = ('on run argv\n tell application "Messages"\n set targetService to 1st service whose service type is iMessage\n'
                  ' set targetBuddy to buddy (item 1 of argv) of targetService\n send (item 2 of argv) to targetBuddy\n end tell\nend run')
        try:
            subprocess.run(["osascript", "-e", script, recipient, text], check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError("Messages handoff failed; no delivery is claimed") from exc
