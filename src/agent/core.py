from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path


def load_openai_api_key_from_dotenv(project_root: Path | None = None) -> bool:
    """Load only OPENAI_API_KEY from a project-root .env without overriding env."""
    root = project_root or Path(__file__).resolve().parents[2]
    dotenv_path = root / ".env"
    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[7:].lstrip()
        key, separator, value = stripped.partition("=")
        if separator and key.strip() == "OPENAI_API_KEY":
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if value:
                os.environ.setdefault("OPENAI_API_KEY", value)
                return True
    return False

@dataclass(frozen=True)
class AgentConfig:
    model: str = "gpt-4o-mini"
    max_output_tokens: int = 256
    system_prompt: str = ("You are a concise, helpful personal assistant. Do not claim to have sent "
        "messages, changed files, or installed apps unless a verified tool result says so.")

class Agent:
    def __init__(self, config: AgentConfig | None = None, client=None):
        self.config = config or AgentConfig()
        self.client = client

    def respond(self, message: str, *, offline: bool = False) -> str:
        if not message.strip():
            raise ValueError("message must not be empty")
        if self.config.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
        if offline:
            return f"Offline smoke-test response: {message.strip()}"
        if self.client is None:
            from openai import OpenAI
            self.client = OpenAI()
        result = self.client.responses.create(
            model=self.config.model,
            instructions=self.config.system_prompt,
            input=message.strip(),
            max_output_tokens=self.config.max_output_tokens,
        )
        response_text = getattr(result, "output_text", None)
        if response_text is None:
            raise ValueError("OpenAI response did not contain output text")
        return response_text.strip()
