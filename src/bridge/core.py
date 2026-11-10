from __future__ import annotations
import json
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Allowlist:
    recipients: frozenset[str]
    senders: frozenset[str] = frozenset()
    local_identities: frozenset[str] = frozenset()
    @classmethod
    def load(cls, path: Path) -> "Allowlist":
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"could not read allowlist: {exc}") from exc
        recipients = data.get("recipients") if isinstance(data, dict) else None
        if not isinstance(recipients, list) or not all(isinstance(item, str) and item.strip() for item in recipients):
            raise ValueError("allowlist must contain a 'recipients' list of non-empty strings")
        senders = data.get("senders", [])
        local_identities = data.get("local_identities", [])
        for name, values in (("senders", senders), ("local_identities", local_identities)):
            if not isinstance(values, list) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ValueError(f"allowlist '{name}' must be a list of non-empty strings")
        return cls(
            recipients=frozenset(item.strip() for item in recipients),
            senders=frozenset(item.strip() for item in senders),
            local_identities=frozenset(item.strip() for item in local_identities),
        )
    def permits(self, recipient: str) -> bool:
        return recipient in self.recipients

    def permits_sender(self, sender: str) -> bool:
        return sender in self.senders

    def is_local_identity(self, sender: str) -> bool:
        return sender in self.local_identities


@dataclass(frozen=True)
class InboundMessage:
    message_id: str
    text: str
    sender: str | None
    timestamp: int | str | None
    is_from_me: bool | None


@dataclass(frozen=True)
class MessageWatermark:
    message_id: str
    timestamp: int | str | None

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

    def inbound_messages(
        self,
        limit: int = 20,
        *,
        after: MessageWatermark | None = None,
    ) -> list[InboundMessage]:
        """Return bounded message records without filtering away unsafe rows.

        The conversation layer deliberately applies the inbound and self-reply
        policy in Python so missing direction metadata fails closed.
        """
        if limit < 1:
            raise ValueError("limit must be positive")
        try:
            with sqlite3.connect(f"file:{self.database}?mode=ro", uri=True) as conn:
                query = """SELECT message.ROWID, message.text, handle.id,
                    message.date, message.is_from_me
                    FROM message LEFT JOIN handle ON message.handle_id = handle.ROWID
                    WHERE message.text IS NOT NULL"""
                parameters: list[object] = []
                if after is not None:
                    try:
                        row_id = int(after.message_id)
                    except (TypeError, ValueError) as exc:
                        raise ValueError("message watermark ID must be an integer") from exc
                    if after.timestamp is None:
                        query += " AND message.date IS NULL AND message.ROWID > ?"
                        parameters.append(row_id)
                    else:
                        query += " AND (message.date > ? OR (message.date = ? AND message.ROWID > ?))"
                        parameters.extend([after.timestamp, after.timestamp, row_id])
                query += " ORDER BY message.date ASC, message.ROWID ASC LIMIT ?"
                parameters.append(limit)
                rows = conn.execute(query, parameters).fetchall()
        except sqlite3.Error as exc:
            raise PermissionError("could not read Messages database; grant this terminal/app Full Disk Access and retry") from exc
        return [
            InboundMessage(
                message_id=str(row[0]),
                text=row[1],
                sender=row[2],
                timestamp=row[3],
                is_from_me=(bool(row[4]) if row[4] is not None else None),
            )
            for row in rows
        ]

    def latest_message_watermark(self) -> MessageWatermark | None:
        """Return the latest text row used to establish an activation boundary."""
        try:
            with sqlite3.connect(f"file:{self.database}?mode=ro", uri=True) as conn:
                row = conn.execute("""SELECT message.ROWID, message.date FROM message
                    WHERE message.text IS NOT NULL
                    ORDER BY message.date DESC, message.ROWID DESC LIMIT 1""").fetchone()
        except sqlite3.Error as exc:
            raise PermissionError("could not read Messages database; grant this terminal/app Full Disk Access and retry") from exc
        return MessageWatermark(str(row[0]), row[1]) if row else None

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
