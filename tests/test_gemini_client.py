import pytest
from apps.explanations.llm.base import LLMError, LLMRateLimited
from apps.explanations.llm.gemini import GeminiClient


class FakeResponse:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body, headers or {}

    def json(self):
        if self._body is None:
            raise ValueError
        return self._body


@pytest.fixture
def client():
    return GeminiClient("key", "gemini-3.5-flash", "https://example.test/v1beta", 5, 100, 0.2)

def patch_post(monkeypatch, response, calls=None):
    def fake(url, json, headers, timeout):
        if calls is not None:
            calls.append((url, json, headers, timeout))
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr("apps.explanations.llm.gemini.requests.post", fake)

def test_request_shape_and_text_extraction(client, monkeypatch):
    calls = []
    body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "hidden", "thought": True}, {"text": '{"answer":"hi"}'}]}}]}
    patch_post(monkeypatch, FakeResponse(200, body), calls)
    assert client.generate_json("sys", "prompt") == '{"answer":"hi"}'
    url, sent, headers, timeout = calls[0]
    assert url == "https://example.test/v1beta/models/gemini-3.5-flash:generateContent"
    assert headers == {"x-goog-api-key": "key"} and timeout == 5
    assert sent["generationConfig"]["responseMimeType"] == "application/json"
    assert sent["systemInstruction"]["parts"][0]["text"] == "sys"

def test_429_per_minute_with_retry_delay(client, monkeypatch):
    body = {"error": {"details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "34s"}]}}
    patch_post(monkeypatch, FakeResponse(429, body))
    with pytest.raises(LLMRateLimited) as info:
        client.generate_json("s", "p")
    assert info.value.retry_after == 34.0 and info.value.daily is False

def test_429_daily_quota_detected(client, monkeypatch):
    body = {"error": {"details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure",
            "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}}
    patch_post(monkeypatch, FakeResponse(429, body))
    with pytest.raises(LLMRateLimited) as info:
        client.generate_json("s", "p")
    assert info.value.daily is True

@pytest.mark.parametrize("response", [
    FakeResponse(500, {}), FakeResponse(200, {"candidates": []}), FakeResponse(200, {"promptFeedback": {}}),
    FakeResponse(200, {"candidates": [{"finishReason": "SAFETY"}]}),
    FakeResponse(200, {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "{"}]}}]}),
    FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "  "}]}}]}),
])
def test_bad_responses_raise_llm_error(client, monkeypatch, response):
    patch_post(monkeypatch, response)
    with pytest.raises(LLMError):
        client.generate_json("s", "p")

def test_network_error_wrapped(client, monkeypatch):
    import requests
    patch_post(monkeypatch, requests.ConnectionError("boom"))
    with pytest.raises(LLMError):
        client.generate_json("s", "p")
