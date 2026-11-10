import os

from agent.core import Agent, load_openai_api_key_from_dotenv

def test_offline_response_is_deterministic():
    assert Agent().respond("hello", offline=True) == "Offline smoke-test response: hello"


def test_live_response_uses_responses_api():
    class Responses:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return type("Result", (), {"output_text": "safe reply"})()

    class Client:
        def __init__(self):
            self.responses = Responses()

    client = Client()
    result = Agent(client=client).respond("hello")
    assert result == "safe reply"
    assert client.responses.calls == [{
        "model": "gpt-4o-mini",
        "instructions": Agent().config.system_prompt,
        "input": "hello",
        "max_output_tokens": 256,
    }]


def test_project_dotenv_loads_key_without_overriding_environment(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text("OPENAI_API_KEY='mock-key-never-printed'\n")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert load_openai_api_key_from_dotenv(tmp_path) is True
    assert os.environ["OPENAI_API_KEY"] == "mock-key-never-printed"

    monkeypatch.setenv("OPENAI_API_KEY", "preexisting-key")
    dotenv.write_text("OPENAI_API_KEY=second-key\n")
    assert load_openai_api_key_from_dotenv(tmp_path) is True
    assert os.environ["OPENAI_API_KEY"] == "preexisting-key"
