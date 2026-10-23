from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class AgentConfig:
    model: str = "gpt-4o-mini"
    system_prompt: str = ("You are a concise, helpful personal assistant. Do not claim to have sent "
        "messages, changed files, or installed apps unless a verified tool result says so.")

class Agent:
    def __init__(self, config: AgentConfig | None = None, client=None):
        self.config = config or AgentConfig()
        self.client = client

    def respond(self, message: str, *, offline: bool = False) -> str:
        if not message.strip():
            raise ValueError("message must not be empty")
        if offline:
            return f"Offline smoke-test response: {message.strip()}"
        if self.client is None:
            from openai import OpenAI
            self.client = OpenAI()
        result = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "system", "content": self.config.system_prompt},
                      {"role": "user", "content": message.strip()}],
        )
        return result.choices[0].message.content or ""
