from agent.core import Agent

def test_offline_response_is_deterministic():
    assert Agent().respond("hello", offline=True) == "Offline smoke-test response: hello"
