"""Smoke-тести Streamlit-інтерфейсу без звернення до OpenRouter."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from streamlit.testing.v1 import AppTest
from langgraph.store.memory import InMemoryStore

import todo_agent


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def test_app_loads_with_empty_task_list(monkeypatch) -> None:
    """Головний екран має завантажуватися без реального API-виклику."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-only")

    app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()

    assert not app.exception
    assert app.title[0].value == "Розумний список справ"
    assert app.metric[0].value == "0"
    assert app.info[0].value == "Список порожній. Додайте перше завдання в чаті."


def test_new_session_button_keeps_app_working(monkeypatch) -> None:
    """Скидання сесії має створити нове порожнє сховище без помилок."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-only")
    app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()

    app.button(key="reset_session").click().run()

    assert not app.exception
    assert app.metric[0].value == "0"


def test_chat_sends_current_command_once(monkeypatch) -> None:
    """Поточна команда не повинна дублюватися в історії для моделі."""
    captured_calls: list[dict[str, Any]] = []

    class FakeAgent:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            captured_calls.append(payload)
            return {"messages": [SimpleNamespace(content="Тестову команду виконано.")]}

    def fake_build_agent(api_key: str):
        return FakeAgent(), InMemoryStore()

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-only")
    monkeypatch.setattr(todo_agent, "build_agent", fake_build_agent)
    app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()

    app.chat_input[0].set_value("Додай: купити хліб").run()

    assert not app.exception
    sent_messages = captured_calls[0]["messages"]
    assert [message["content"] for message in sent_messages].count(
        "Додай: купити хліб"
    ) == 1
