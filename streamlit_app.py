"""Streamlit-інтерфейс для TODO-агента на LangChain і LangGraph."""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from todo_agent import TASKS_NAMESPACE, build_agent


PAGE_TITLE = "TODO Agent"
OPENROUTER_KEY_NAME = "OPENROUTER_API_KEY"
LEGACY_SECRET_NAME = "HomeWorkOpenRouter_KEY"
WELCOME_MESSAGE = (
    "Вітаю! Я допоможу керувати списком справ. "
    "Напишіть, наприклад: **«Додай: купити хліб»**."
)
SUGGESTIONS = {
    ":material/add_task: Додати приклад": "Додай: купити хліб",
    ":material/list_alt: Показати список": "Покажи всі завдання",
    ":material/pending_actions: Що залишилось?": "Що залишилось?",
}


st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=":material/check_circle:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Для локального запуску з VS Code читаємо змінні з .env.
# У Streamlit Community Cloud ключ надходить через st.secrets.
load_dotenv()


def load_api_key() -> str | None:
    """Завантажити ключ зі Streamlit Secrets або environment variables."""
    try:
        secret = st.secrets.get(OPENROUTER_KEY_NAME) or st.secrets.get(
            LEGACY_SECRET_NAME
        )
    except (FileNotFoundError, KeyError):
        secret = None

    value = (
        secret
        or os.getenv(OPENROUTER_KEY_NAME)
        or os.getenv(LEGACY_SECRET_NAME)
    )
    return value.strip() if value else None


def initialize_session(api_key: str) -> None:
    """Створити окремого агента та сховище для поточної сесії браузера."""
    agent, store = build_agent(api_key)
    st.session_state.agent = agent
    st.session_state.store = store
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MESSAGE}
    ]


def reset_session(api_key: str) -> None:
    """Очистити чат і завдання поточної сесії."""
    st.session_state.pop("quick_command", None)
    initialize_session(api_key)


def readable_error(error: Exception) -> str:
    """Перетворити типові помилки API на зрозумілі повідомлення."""
    details = str(error)
    lowered = details.lower()

    if "401" in details or "unauthorized" in lowered or "user not found" in lowered:
        return (
            "OpenRouter відхилив ключ. Перевірте значення секрету "
            f"`{OPENROUTER_KEY_NAME}` у `.streamlit/secrets.toml` або `.env`."
        )
    if "402" in details or "credits" in lowered:
        return "На балансі OpenRouter недостатньо коштів для виклику Grok 4.6."
    if "429" in details or "rate limit" in lowered:
        return "Перевищено ліміт запитів OpenRouter. Спробуйте трохи пізніше."

    return "Не вдалося виконати команду. Перевірте підключення та журнал термінала."


def run_agent() -> str:
    """Передати всю історію діалогу агенту та повернути його останню відповідь."""
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]

    result: dict[str, Any] = st.session_state.agent.invoke(
        {"messages": history}
    )
    answer = result["messages"][-1].content

    if isinstance(answer, str):
        return answer
    return str(answer)


st.title("Розумний список справ", icon=":material/check_circle:")
st.caption("TODO-агент на LangChain, LangGraph та OpenRouter · модель Grok 4.6")

api_key = load_api_key()
if not api_key:
    st.error(
        f"Не знайдено ключ OpenRouter. Додайте `{OPENROUTER_KEY_NAME}`.",
        icon=":material/key:",
    )
    st.code(
        f'{OPENROUTER_KEY_NAME} = "sk-or-v1-..."',
        language="toml",
    )
    st.caption(
        "Збережіть ключ у `.env` або `.streamlit/secrets.toml` і "
        "перезапустіть застосунок."
    )
    st.stop()

if "agent" not in st.session_state or "store" not in st.session_state:
    initialize_session(api_key)


with st.sidebar:
    st.subheader("Про застосунок", icon=":material/info:")
    st.badge("Grok 4.6", icon=":material/smart_toy:", color="violet")
    st.caption("Провайдер: OpenRouter")
    st.caption("Памʼять: LangGraph InMemoryStore")
    st.divider()
    st.button(
        "Нова сесія",
        key="reset_session",
        icon=":material/restart_alt:",
        help="Очистити чат і всі завдання поточної сесії.",
        width="stretch",
        on_click=reset_session,
        args=(api_key,),
    )
    st.caption(
        "Завдання зберігаються між викликами агента, але очищаються після "
        "перезапуску сервера або створення нової сесії."
    )


chat_area, tasks_area = st.columns([1.65, 1], gap="large")

with chat_area:
    st.subheader("Діалог з агентом", icon=":material/chat:")

    quick_prompt: str | None = None
    if len(st.session_state.messages) == 1:
        selected = st.pills(
            "Швидкі команди",
            options=list(SUGGESTIONS),
            key="quick_command",
            label_visibility="collapsed",
            width="stretch",
        )
        if selected:
            quick_prompt = SUGGESTIONS[selected]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    typed_prompt = st.chat_input(
        "Напишіть команду українською…",
        key="todo_chat_input",
        submit_mode="disable",
    )
    prompt = typed_prompt or quick_prompt

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.status(
                ":shimmer[Опрацьовую команду]",
                expanded=False,
                type="compact",
            ) as status:
                try:
                    answer = run_agent()
                    status.update(
                        label="Готово",
                        state="complete",
                        expanded=False,
                    )
                except Exception as error:
                    answer = readable_error(error)
                    status.update(
                        label="Не вдалося виконати команду",
                        state="error",
                        expanded=False,
                    )

            st.markdown(answer)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )
        st.rerun()


with tasks_area:
    st.subheader("Поточні завдання", icon=":material/checklist:")
    records = st.session_state.store.search(TASKS_NAMESPACE, limit=1000)
    st.metric(
        "Усього завдань",
        len(records),
        icon=":material/task_alt:",
        border=True,
    )

    if records:
        for index, record in enumerate(records, start=1):
            task_text = record.value.get("title", "Без назви")
            with st.container(border=True):
                st.markdown(f"**{index}. {task_text}**")
                st.caption(f"ID: `{record.key}`")
    else:
        st.info(
            "Список порожній. Додайте перше завдання в чаті.",
            icon=":material/inbox:",
        )

    with st.expander("Приклади команд", icon=":material/lightbulb:"):
        st.markdown(
            "- `Додай: купити хліб`\n"
            "- `Покажи всі завдання`\n"
            "- `Видали завдання про хліб`\n"
            "- `Що залишилось?`"
        )
