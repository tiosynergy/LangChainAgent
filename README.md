# TODO Agent — Streamlit UI

Вебінтерфейс для TODO-агента на LangChain / LangGraph із моделлю
`x-ai/grok-4.6` через OpenRouter.

## Можливості

- додавання, перегляд і видалення завдань природною українською мовою;
- окремий `InMemoryStore` для кожної Streamlit-сесії;
- чат-історія та панель поточних завдань;
- швидкі команди для демонстрації;
- безпечне завантаження API key зі змінних середовища або Streamlit Secrets.

## Запуск у VS Code

Рекомендована версія Python — 3.12. У Python 3.14 LangChain наразі може
показувати попередження про сумісність із Pydantic v1.

Відкрийте цю папку у VS Code та виконайте в PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Оберіть один зі способів зберігання ключа.

### Варіант 1 — `.env` для локальної розробки у VS Code

```powershell
Copy-Item .env.example .env
```

У файлі `.env`:

```dotenv
OPENROUTER_API_KEY=sk-or-v1-...
```

### Варіант 2 — Streamlit Secrets

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Відкрийте `.streamlit/secrets.toml` і замініть приклад на повний ключ
OpenRouter:

```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
```

Для сумісності застосунок також розпізнає стару назву
`HomeWorkOpenRouter_KEY`. Файли `.env` і `secrets.toml` додані до
`.gitignore` та не повинні потрапляти до GitHub.

Запустіть застосунок:

```powershell
python -m streamlit run streamlit_app.py
```

Також можна відкрити панель **Run and Debug** у VS Code та вибрати
`Streamlit: TODO Agent`.

Перевірка інтерфейсу без реального запиту до OpenRouter:

```powershell
python -m pytest
```

## Структура

```text
.
|-- streamlit_app.py
|-- todo_agent.py
|-- .env.example
|-- requirements.txt
|-- requirements-dev.txt
|-- tests/
|   `-- test_streamlit_app.py
|-- .streamlit/
|   |-- config.toml
|   `-- secrets.toml.example
`-- .vscode/
    `-- launch.json
```

## Обмеження пам'яті

`InMemoryStore` зберігає завдання між rerun у межах поточної сесії.
Після перезапуску сервера або завершення сесії список буде втрачено.
Для постійного зберігання потрібен database-backed store.
