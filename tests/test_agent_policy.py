"""Перевірки системної політики TODO-агента."""

from todo_agent import OUT_OF_SCOPE_RESPONSE, SYSTEM_PROMPT


def test_system_prompt_restricts_agent_to_todo_scope() -> None:
    """Промпт має забороняти відповіді та інструменти для сторонніх тем."""
    assert "не відповідай на нього по суті" in SYSTEM_PROMPT
    assert "не використовуй інструменти" in SYSTEM_PROMPT
    assert "не шукай інформацію" in SYSTEM_PROMPT
    assert OUT_OF_SCOPE_RESPONSE in SYSTEM_PROMPT


def test_system_prompt_distinguishes_question_from_task_text() -> None:
    """Стороннє питання можна зберегти як завдання, але не розв'язувати."""
    assert "Яка столиця Франції?" in SYSTEM_PROMPT
    assert "Додай: дізнатися столицю Франції" in SYSTEM_PROMPT
