from types import SimpleNamespace

from llm_withtools import check_for_tool_use


def test_check_for_tool_use_returns_none_when_openai_response_has_no_function_calls():
    response = SimpleNamespace(output=[SimpleNamespace(type="message")])

    assert check_for_tool_use(response, model="o3-mini-2025-01-31") is None
