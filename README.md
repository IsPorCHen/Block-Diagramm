# Проект: Генератор блок-схем из кода (Block Diagramm)

## Цель

Веб-приложение для автоматической генерации блок-схем из исходного кода на Python, JavaScript и C#.
Визуализация алгоритмов по ГОСТ без ручного рисования.

## Архитектура

```
Пользователь (браузер) ←→ Flask (app/) ←→ Парсеры (app/parsers/)
                                                ↓
                                         FlowchartBuilder
                                                ↓
                                       SVG-рендерер (frontend)
```

**Основная сложность**: три разных языка → три парсера с общей структурой,
но разными подходами к парсингу (Python — встроенный `ast`, JS/C# — ручные
токенизаторы и AST-билдеры). Все парсеры следуют единому интерфейсу
(`BaseParser`) и используют общий `GraphBuilder` для построения блок-схем.

## Файлы

| Файл/Папка | Назначение |
|---|---|
| `app/` | Backend на Flask (фабрика приложения, маршруты, сервисы) |
| `app/main.py` | Точка входа: `create_app()`, настройка путей к templates/static |
| `app/routes.py` | Маршруты: `/` (главная), `/upload` (загрузка файла) |
| `app/config.py` | Конфигурация из переменных окружения (DEBUG, SECRET_KEY, порт) |
| `app/services/` | Бизнес-логика: `FlowchartService`, `ParserFactory` |
| `app/builders/` | `FlowchartBuilder` — построение графа (узлы + связи) |
| `app/models/` | Data-классы: `Flowchart`, `Node`, `Edge` |
| `app/parsers/` | **Ядро проекта** — парсеры для каждого языка |
| `app/parsers/base.py` | `BaseParser` — абстрактный класс, общая логика `_connect_to_end` |
| `app/parsers/core/` | Общие компоненты: `GraphBuilder`, `NodeFactory`, `EdgeFactory` |
| `app/parsers/python/` | Python-парсер (использует `ast`). Файлы: `parser.py`, `handlers.py`, `formatter.py`, `tokenizer.py` |
| `app/parsers/javascript/` | JS-парсер (ручной токенизатор). Файлы: `parser.py`, `handlers.py`, `tokenizer.py`, `ast_builder.py` |
| `app/parsers/csharp/` | C#-парсер (ручной токенизатор). Файлы: `parser.py`, `handlers.py`, `tokenizer.py`, `ast_builder.py` |
| `app/utils/` | `CodeCleaner` — удаление комментариев |
| `static/` | Frontend: `css/style.css`, `js/flowchart-renderer.js`, `js/main.js` |
| `templates/` | `index.html` — главная страница |
| `tests/` | Тесты парсеров (`test_all_parsers.py`, `test_*.py`) и фикстуры (`fixtures/`) |
| `Dockerfile` | Образ для деплоя (Python 3.10-slim) |
| `docker-compose.yml` | Оркестрация (порт 5000, volumes для static/templates) |
| `Makefile` | Команды: `install`, `run`, `docker-build`, `docker-up`, `docker-down` |
| `requirements.txt` | Зависимости: только `Flask==3.1.2` |
| `run.py` | Точка запуска для разработки |

### Структура парсера (единообразная)

Каждый парсер в `app/parsers/{python,javascript,csharp}/` имеет одинаковую структуру:

| Файл | Отвечает за |
|---|---|
| `parser.py` | Основной класс-парсер (наследует `BaseParser`). Точка входа: `parse(code) -> dict`. Собирает AST/токены, вызывает handlers, возвращает `{success, main_flowchart, functions, classes, code}` |
| `handlers.py` | Обработчики конструкций языка (`if`, `for`, `while`, `switch`, `try`, `return` и т.д.). Строят узлы и связи через `GraphBuilder` |
| `tokenizer.py` | Преобразует исходный код в поток токенов (для JS и C#). Для Python используется встроенный `ast` (tokenizer — просто обёртка) |
| `formatter.py` | (только Python) Форматирует AST-узлы в читаемый текст: бинарные операции, вызовы функций, строки, числа |
| `ast_builder.py` | (только JS и C#) Строит AST из токенов: функции, классы, условия, циклы |

**Принцип работы парсера:**

1. Токенизация (или `ast.parse` для Python)
2. Построение AST (для JS/C#) или использование готового `ast`
3. Обход AST → вызов `handlers.process_body()` → добавление узлов в `GraphBuilder`
4. Возврат `Flowchart` в виде `dict` (nodes + edges)
5. Frontend рендерит SVG через `flowchart-renderer.js`

**Протокол передачи данных (frontend ↔ backend):**

- `POST /upload` с файлом (multipart/form-data)
- Ответ: JSON с полями:
  - `main_flowchart`: `{nodes: [], edges: []}`
  - `functions`: `[{name, type, flowchart}]`
  - `classes`: `[{name, type, flowchart}]`
  - `code`: исходный код (для отображения)

## Диагностика: как смотреть логи, если что-то сломалось

### Локальный запуск (без Docker)

```bash
cd ~/dotfiles/projects/Block-Diagramm
source venv/bin/activate
python run.py
```

Логи выводятся в терминал, где запущен сервер.

### Docker-запуск

```bash
# Сборка и запуск
make docker-build
make docker-up

# Просмотр логов
make docker-logs

# Или напрямую
sudo docker compose logs -f
```

### Быстрые проверки при типичных симптомах

| Симптом | Что проверить |
|---|---|
| Страница не открывается (Connection refused) | Запущен ли сервер? `ps aux \| grep python` или `sudo docker ps` |
| Ошибка 500 при загрузке файла | Посмотреть логи сервера: `python run.py` или `sudo docker compose logs` |
| Блок-схема не генерируется (пустые nodes/edges) | Проверить парсер в тестах: `python tests/test_all_parsers.py` |
| Только Python работает, JS/C# — нет | Проверить импорты в `app/parsers/javascript/` и `app/parsers/csharp/` |
| Docker не собирается | Проверить `.dockerignore` (не исключает ли `requirements.txt`), очистить кеш: `sudo docker builder prune -f` |
| Permission denied в Docker | Добавить пользователя в группу docker: `sudo usermod -aG docker $USER && newgrp docker` |

## Тестирование

```bash
# Все тесты парсеров
python tests/test_all_parsers.py

# Отдельные тесты
python tests/test_python_parser.py
python tests/test_js_parser.py
python tests/test_cs_parser.py
```

Ожидаемый вывод:

```
✓ Python: Simple
✓ Python: Complex
✓ JavaScript: Simple
✓ JavaScript: Complex
✓ C#: Simple
✓ C#: Complex
Passed: 6/6
```