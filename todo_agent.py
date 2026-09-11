"""TODO-агент на LangChain / LangGraph із пам'яттю InMemoryStore."""

import uuid

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter
from langgraph.config import get_store
from langgraph.store.memory import InMemoryStore


# Окремий простір імен для всіх TODO-завдань у сховищі.
TASKS_NAMESPACE = ("todo_tasks",)
OUT_OF_SCOPE_RESPONSE = (
    "Я можу допомогти лише з керуванням вашим списком справ: "
    "додаванням, переглядом і видаленням завдань."
)


@tool
def add_task(task: str) -> str:
    """Додати нове завдання до TODO-списку.

    Args:
        task: Текст завдання, яке потрібно додати.
    """
    store = get_store()
    task_text = task.strip()

    if not task_text:
        return "Не вдалося додати порожнє завдання."

    # Кожне завдання отримує власний унікальний UUID.
    task_id = str(uuid.uuid4())
    store.put(
        TASKS_NAMESPACE,
        task_id,
        {"title": task_text},
    )

    return f'Завдання "{task_text}" було успішно додано. ID: {task_id}'


@tool
def list_tasks() -> str:
    """Показати всі завдання, збережені в TODO-списку."""
    store = get_store()
    tasks = store.search(TASKS_NAMESPACE, limit=1000)

    if not tasks:
        return "Список завдань порожній."

    lines = ["Ось усі ваші завдання:"]
    for number, item in enumerate(tasks, start=1):
        title = item.value.get("title", "Без назви")
        lines.append(f"{number}. {title} [ID: {item.key}]")

    return "\n".join(lines)


@tool
def delete_task(task_id: str) -> str:
    """Видалити завдання з TODO-списку за його повним ID.

    Args:
        task_id: Повний UUID завдання, отриманий через list_tasks.
    """
    store = get_store()
    normalized_id = task_id.strip()
    item = store.get(TASKS_NAMESPACE, normalized_id)

    if item is None:
        return f"Завдання з ID {normalized_id} не знайдено."

    title = item.value.get("title", "Без назви")
    store.delete(TASKS_NAMESPACE, normalized_id)

    return f'Завдання "{title}" було успішно видалено.'


SYSTEM_PROMPT = f"""
Ти — уважний TODO-асистент. Спілкуйся українською мовою.

Правила роботи:
1. Для додавання завдання завжди використовуй add_task.
2. Передавай до add_task лише текст самого завдання — без слова «Додай»,
   двокрапки та зайвих лапок.
3. Для перегляду завдань або відповіді на питання «Що залишилось?»
   завжди використовуй list_tasks.
4. delete_task приймає лише повний UUID завдання.
5. Якщо користувач просить видалити завдання за назвою, темою або описом,
   спочатку виклич list_tasks, знайди відповідний повний ID,
   а потім виклич delete_task.
6. Ніколи не вигадуй ID.
7. Якщо знайдено кілька схожих завдань, попроси користувача уточнити вибір.
8. Якщо відповідного завдання немає, повідом про це.
9. Після виконання дії дай коротку й зрозумілу відповідь українською.
10. Твоя єдина сфера роботи — керування TODO-списком: додавання,
    перегляд і видалення завдань, а також короткі уточнення щодо використання
    цих функцій.
11. Якщо запит не стосується безпосередньо TODO-списку,
    не відповідай на нього по суті; не використовуй інструменти;
    не шукай інформацію і не намагайся доповнювати відповідь власними знаннями.
12. На будь-який запит поза дозволеною сферою відповідай тільки так:
    «{OUT_OF_SCOPE_RESPONSE}»
13. Якщо користувач просить додати завдання, текст завдання може стосуватися
    будь-якої теми. У такому разі додай його як звичайне завдання, але не
    відповідай на питання, записане в тексті завдання.
14. Приклад: на запит «Яка столиця Франції?» відмовся за правилом 12, а на
    запит «Додай: дізнатися столицю Франції» використай add_task.
""".strip()


def build_agent(api_key: str):
    """Створити TODO-агента та окреме сховище для поточної сесії.

    Args:
        api_key: Повний API key OpenRouter.

    Returns:
        Кортеж (agent, store). Обидва об'єкти потрібно зберігати
        у st.session_state, щоб вони не втрачалися між rerun Streamlit.
    """
    normalized_key = api_key.strip()

    if not normalized_key:
        raise ValueError("OpenRouter API key не може бути порожнім.")

    store = InMemoryStore()
    model = ChatOpenRouter(
        model="x-ai/grok-4.6",
        api_key=normalized_key,
        temperature=0,
    )

    agent = create_agent(
        model=model,
        tools=[add_task, list_tasks, delete_task],
        system_prompt=SYSTEM_PROMPT,
        store=store,
    )

    return agent, store


__all__ = [
    "TASKS_NAMESPACE",
    "OUT_OF_SCOPE_RESPONSE",
    "SYSTEM_PROMPT",
    "add_task",
    "list_tasks",
    "delete_task",
    "build_agent",
]
