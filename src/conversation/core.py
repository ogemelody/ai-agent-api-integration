from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from agent.core import Agent
from bridge.core import InboundMessage, MessageWatermark, MessagesBridge

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CostPolicy:
    max_input_chars: int = 4_000
    max_output_tokens: int = 256
    max_requests_per_run: int = 5
    min_request_interval_seconds: float = 1.0

    def validate(self) -> None:
        if self.max_input_chars < 1 or self.max_output_tokens < 1:
            raise ValueError("input and output limits must be positive")
        if self.max_requests_per_run < 1 or self.min_request_interval_seconds < 0:
            raise ValueError("request budget and interval must be non-negative and usable")


class AgentLike(Protocol):
    def respond(self, message: str, *, offline: bool = False) -> str: ...


@dataclass(frozen=True)
class ProcessingRecord:
    source_id: str
    sender: str | None
    status: str
    reply_text: str | None
    model: str | None
    mode: str | None
    error_category: str | None
    updated_at: float


class ProcessingStateStore:
    """Small local durable queue; it intentionally stores no inbound body."""

    def __init__(self, path: Path):
        self.path = path
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS processing (
                source_id TEXT PRIMARY KEY,
                sender TEXT,
                status TEXT NOT NULL,
                reply_text TEXT,
                model TEXT,
                mode TEXT,
                error_category TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                sent_at REAL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )""")

    def get_metadata(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)", (key, value))

    def claim(self, source_id: str, sender: str | None, now: float | None = None) -> bool:
        timestamp = time.time() if now is None else now
        with self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    "INSERT INTO processing(source_id, sender, status, created_at, updated_at) VALUES (?, ?, 'discovered', ?, ?)",
                    (source_id, sender, timestamp, timestamp),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def set_ignored(self, source_id: str, category: str, now: float | None = None) -> None:
        self._update(source_id, "ignored", error_category=category, now=now)

    def set_failed(self, source_id: str, category: str, now: float | None = None) -> None:
        self._update(source_id, "failed", error_category=category, now=now)

    def set_pending(self, source_id: str, reply_text: str, model: str, mode: str, now: float | None = None) -> None:
        self._update(source_id, "pending_approval", reply_text=reply_text, model=model, mode=mode, now=now)

    def set_sent(self, source_id: str, now: float | None = None) -> None:
        timestamp = time.time() if now is None else now
        self._update(source_id, "sent", now=timestamp, sent_at=timestamp)

    def set_rejected(self, source_id: str, now: float | None = None) -> None:
        self._update(source_id, "rejected", now=now)

    def set_cancelled(self, source_id: str, now: float | None = None) -> None:
        self._update(source_id, "cancelled", now=now)

    def expire_pending(self, cutoff: float, now: float | None = None) -> int:
        timestamp = time.time() if now is None else now
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE processing SET status = 'expired', updated_at = ? WHERE status = 'pending_approval' AND created_at < ?",
                (timestamp, cutoff),
            )
            return cursor.rowcount

    def _update(self, source_id: str, status: str, now: float | None = None, **fields: str | float | None) -> None:
        timestamp = time.time() if now is None else now
        assignments = ["status = ?", "updated_at = ?"]
        values: list[str | float | None] = [status, timestamp]
        for name, value in fields.items():
            assignments.append(f"{name} = ?")
            values.append(value)
        values.append(source_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE processing SET {', '.join(assignments)} WHERE source_id = ?", values)

    def get(self, source_id: str) -> ProcessingRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM processing WHERE source_id = ?", (source_id,)).fetchone()
        return self._record(row) if row else None

    def pending(self) -> list[ProcessingRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM processing WHERE status = 'pending_approval' ORDER BY created_at").fetchall()
        return [self._record(row) for row in rows]

    @staticmethod
    def _record(row: sqlite3.Row) -> ProcessingRecord:
        return ProcessingRecord(
            source_id=row["source_id"], sender=row["sender"], status=row["status"],
            reply_text=row["reply_text"], model=row["model"], mode=row["mode"],
            error_category=row["error_category"], updated_at=row["updated_at"],
        )


class ActivationRequiredError(RuntimeError):
    pass


def _category(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    status_code = getattr(exc, "status_code", None)
    if status_code in (401, 403):
        return "authentication"
    if status_code == 408:
        return "timeout"
    if status_code == 429:
        return "rate_limit"
    if "authentication" in name or "api_key" in name or "apikey" in name or "invalidapi" in name:
        return "authentication"
    if "timeout" in name:
        return "timeout"
    if "rate" in name:
        return "rate_limit"
    if "quota" in name or "billing" in name:
        return "quota"
    if isinstance(exc, ValueError):
        return "invalid_response"
    return "agent_error"


def _redacted_id(source_id: str) -> str:
    return hashlib.sha256(source_id.encode()).hexdigest()[:12]


class ConversationProcessor:
    def __init__(
        self,
        bridge: MessagesBridge,
        agent: AgentLike,
        state: ProcessingStateStore,
        *,
        policy: CostPolicy | None = None,
        offline: bool = False,
        clock=time.monotonic,
    ):
        self.bridge = bridge
        self.agent = agent
        self.state = state
        self.policy = policy or CostPolicy()
        self.policy.validate()
        agent_limit = getattr(getattr(agent, "config", None), "max_output_tokens", None)
        if agent_limit is not None and agent_limit > self.policy.max_output_tokens:
            raise ValueError("agent output limit exceeds conversation cost policy")
        self.offline = offline
        self.clock = clock
        self._requests = 0
        self._last_request: float | None = None

    def is_activated(self) -> bool:
        return self.state.get_metadata("activation_watermark") is not None

    def activate(self) -> MessageWatermark | None:
        """Record the current latest message boundary; do not process history."""
        watermark = self.bridge.latest_message_watermark()
        payload = {"message_id": watermark.message_id, "timestamp": watermark.timestamp} if watermark else {"message_id": "", "timestamp": None}
        self.state.set_metadata("activation_watermark", json.dumps(payload, separators=(",", ":")))
        logger.info("conversation activated watermark_recorded=true")
        return watermark

    def _watermark(self) -> MessageWatermark:
        raw = self.state.get_metadata("activation_watermark")
        if raw is None:
            raise ActivationRequiredError("conversation is not activated; run with --activate before polling")
        return self._decode_watermark(raw, "conversation activation watermark is invalid; activate again")

    @staticmethod
    def _decode_watermark(raw: str, error_message: str) -> MessageWatermark:
        try:
            payload = json.loads(raw)
            return MessageWatermark(str(payload["message_id"]), payload.get("timestamp"))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ActivationRequiredError(error_message) from exc

    def _poll_watermark(self, activation_watermark: MessageWatermark) -> MessageWatermark | None:
        raw = self.state.get_metadata("poll_watermark")
        if raw is None:
            return activation_watermark if activation_watermark.message_id else None
        watermark = self._decode_watermark(raw, "conversation polling watermark is invalid")
        return watermark if watermark.message_id else None

    def _save_poll_watermark(self, watermark: MessageWatermark) -> None:
        self.state.set_metadata(
            "poll_watermark",
            json.dumps(
                {"message_id": watermark.message_id, "timestamp": watermark.timestamp},
                separators=(",", ":"),
            ),
        )

    @staticmethod
    def _after_watermark(message: InboundMessage, watermark: MessageWatermark) -> bool:
        if message.timestamp is not None and watermark.timestamp is not None:
            try:
                current_time, boundary_time = int(message.timestamp), int(watermark.timestamp)
                if current_time != boundary_time:
                    return current_time > boundary_time
            except (TypeError, ValueError):
                if str(message.timestamp) != str(watermark.timestamp):
                    return str(message.timestamp) > str(watermark.timestamp)
        try:
            return int(message.message_id) > int(watermark.message_id)
        except (TypeError, ValueError):
            return message.message_id != watermark.message_id

    def poll(self, limit: int = 20) -> list[ProcessingRecord]:
        if limit < 1:
            raise ValueError("limit must be positive")
        activation_watermark = self._watermark()
        watermark = self._poll_watermark(activation_watermark)
        # CostPolicy limits are per poll invocation, not for the lifetime of the
        # processor object.
        self._requests = 0
        self._last_request = None
        records: list[ProcessingRecord] = []
        for message in self.bridge.inbound_messages(limit, after=watermark):
            record = self._process(message)
            if record is not None:
                records.append(record)
            # Advance only after the row has a durable processing record. If a
            # run stops between rows, the next run re-reads at most one already
            # claimed row rather than silently skipping anything.
            self._save_poll_watermark(MessageWatermark(message.message_id, message.timestamp))
        return records

    def _process(self, message: InboundMessage) -> ProcessingRecord | None:
        existing = self.state.get(message.message_id)
        if existing is not None:
            return existing
        if not message.text.strip():
            self.state.claim(message.message_id, message.sender)
            self.state.set_ignored(message.message_id, "empty_text")
            return self.state.get(message.message_id)
        if message.is_from_me is not False:
            self.state.claim(message.message_id, message.sender)
            self.state.set_ignored(message.message_id, "not_inbound")
            return self.state.get(message.message_id)
        if not message.sender or self.bridge.allowlist.is_local_identity(message.sender):
            self.state.claim(message.message_id, message.sender)
            self.state.set_ignored(message.message_id, "self_reply_or_unknown_sender")
            return self.state.get(message.message_id)
        if not self.bridge.allowlist.permits_sender(message.sender):
            self.state.claim(message.message_id, message.sender)
            self.state.set_ignored(message.message_id, "sender_not_allowed")
            return self.state.get(message.message_id)
        if not self.state.claim(message.message_id, message.sender):
            return self.state.get(message.message_id)
        if len(message.text) > self.policy.max_input_chars:
            self.state.set_failed(message.message_id, "input_limit")
            return self.state.get(message.message_id)
        if self._requests >= self.policy.max_requests_per_run:
            self.state.set_failed(message.message_id, "run_request_limit")
            return self.state.get(message.message_id)
        now = self.clock()
        if self._last_request is not None and now - self._last_request < self.policy.min_request_interval_seconds:
            self.state.set_failed(message.message_id, "request_interval")
            return self.state.get(message.message_id)
        self._requests += 1
        self._last_request = now
        try:
            reply = self.agent.respond(message.text, offline=self.offline)
            if not reply.strip():
                raise ValueError("OpenAI response was empty")
        except Exception as exc:  # categorized and redacted at the boundary
            category = _category(exc)
            self.state.set_failed(message.message_id, category)
            logger.warning("conversation source=%s failed category=%s", _redacted_id(message.message_id), category)
            return self.state.get(message.message_id)
        model = getattr(getattr(self.agent, "config", None), "model", "unknown")
        mode = "offline" if self.offline else "openai_responses"
        self.state.set_pending(message.message_id, reply, model, mode)
        logger.info("conversation source=%s queued status=pending_approval", _redacted_id(message.message_id))
        return self.state.get(message.message_id)

    def approve(self, source_id: str) -> ProcessingRecord:
        record = self.state.get(source_id)
        if record is None or record.status != "pending_approval" or not record.sender or not record.reply_text:
            raise ValueError("source is not an approvable pending reply")
        try:
            self.bridge.send(record.sender, record.reply_text, confirmed=True)
        except Exception as exc:
            category = "send_error"
            self.state.set_failed(source_id, category)
            logger.warning("conversation source=%s failed category=%s", _redacted_id(source_id), category)
            raise RuntimeError("approved Messages handoff failed; no delivery is claimed") from exc
        self.state.set_sent(source_id)
        return self.state.get(source_id)  # type: ignore[return-value]

    def reject(self, source_id: str) -> ProcessingRecord:
        record = self.state.get(source_id)
        if record is None or record.status != "pending_approval":
            raise ValueError("source is not a pending reply")
        self.state.set_rejected(source_id)
        return self.state.get(source_id)  # type: ignore[return-value]

    def cancel(self, source_id: str) -> ProcessingRecord:
        record = self.state.get(source_id)
        if record is None or record.status != "pending_approval":
            raise ValueError("source is not a pending reply")
        self.state.set_cancelled(source_id)
        return self.state.get(source_id)  # type: ignore[return-value]

    def expire_pending(self, max_age_seconds: float, now: float | None = None) -> int:
        if max_age_seconds < 0:
            raise ValueError("max_age_seconds must not be negative")
        timestamp = time.time() if now is None else now
        return self.state.expire_pending(timestamp - max_age_seconds, now=timestamp)
