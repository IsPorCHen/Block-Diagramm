# Проект: Генератор блок-схем из кода (Block Diagramm)

## Цель

Веб-приложение для автоматической генерации блок-схем из исходного кода на Python, JavaScript, C# и Go.
Визуализация алгоритмов по ГОСТ без ручного рисования.

## Бэкенд (Backend)

### Файлы

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
| `app/parsers/golang/` | Go-парсер (в разработке). Файлы: `parser.py`, `handlers.py`, `tokenizer.py`, `ast_builder.py` |
| `app/utils/` | `CodeCleaner` — удаление комментариев |
| `tests/` | Тесты парсеров (`test_all_parsers.py`, `test_*.py`) и фикстуры (`fixtures/`) |
| `requirements.txt` | Зависимости: `Flask==3.1.2`, `gunicorn==21.2.0` |
| `run.py` | Точка запуска для разработки |

### Структура парсера (единообразная)

Каждый парсер в `app/parsers/{python,javascript,csharp,golang}/` имеет одинаковую структуру:

| Файл | Отвечает за |
|---|---|
| `parser.py` | Основной класс-парсер (наследует `BaseParser`). Точка входа: `parse(code) -> dict`. Собирает AST/токены, вызывает handlers, возвращает `{success, main_flowchart, functions, classes, code}` |
| `handlers.py` | Обработчики конструкций языка (`if`, `for`, `while`, `switch`, `try`, `return` и т.д.). Строят узлы и связи через `GraphBuilder` |
| `tokenizer.py` | Преобразует исходный код в поток токенов (для JS, C#, Go). Для Python используется встроенный `ast` (tokenizer — просто обёртка) |
| `formatter.py` | (только Python) Форматирует AST-узлы в читаемый текст: бинарные операции, вызовы функций, строки, числа |
| `ast_builder.py` | (только JS, C#, Go) Строит AST из токенов: функции, классы, условия, циклы |

**Принцип работы парсера:**

1. Токенизация (или `ast.parse` для Python)
2. Построение AST (для JS/C#/Go) или использование готового `ast`
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

---

## Фронтенд (Frontend)

### Обзор

Фронтенд построен на **Vanilla JavaScript** без фреймворков для максимальной производительности и минимального размера. Основная задача — интерактивный просмотр блок-схем с возможностью масштабирования, панорамирования и экспорта в PNG.

### Файлы

| Файл | Назначение | Размер |
|---|---|---|
| `templates/index.html` | Главная страница: загрузка файлов, отображение блок-схем, исходный код | ~100 строк |
| `static/css/style.css` | Стили: адаптивный дизайн, темная/светлая тема, анимации | ~300 строк |
| `static/js/flowchart-renderer.js` | **Ядро рендеринга**: SVG-рендерер блок-схем, расчёт позиций, отрисовка узлов и связей | ~600 строк |
| `static/js/main.js` | **Управление UI**: загрузка файлов, взаимодействие с сервером, управление панелями, экспорт PNG | ~300 строк |

### Компоненты интерфейса

#### 1. Загрузка файлов (`main.js`)

- **Drag & Drop**: перетаскивание файлов в область загрузки
- **Клик**: выбор файла через системный диалог
- **Валидация**: проверка расширения (`.py`, `.js`, `.cs`, `.go`) и размера (< 1MB)
- **Поддержка**: мультиязычность (Python, JavaScript, C#, Go)

#### 2. Отображение блок-схем (`flowchart-renderer.js`)

**Поддерживаемые типы узлов**:

| Тип | Форма | Цвет | Назначение |
|---|---|---|---|
| `start` | Скругленный прямоугольник | Синий | Начало алгоритма |
| `end` | Круг | Синий | Конец алгоритма |
| `process` | Прямоугольник | Голубой | Операция/действие |
| `input` | Параллелограмм | Голубой | Ввод данных |
| `output` | Параллелограмм | Голубой | Вывод данных |
| `condition` | Ромб | Голубой | Условный оператор (if/else) |
| `loop` | Шестиугольник | Голубой | Цикл (for/while) |
| `method` | Скругленный прямоугольник | Голубой | Метод класса |
| `class_start` | Скругленный прямоугольник | Синий | Начало класса |
| `try_start` | Прямоугольник (пунктир) | Голубой | Блок try |
| `except` | Прямоугольник (пунктир) | Голубой | Блок except |
| `finally` | Прямоугольник (пунктир) | Голубой | Блок finally |

**Типы связей (стрелки)**:

| Тип | Цвет | Назначение |
|---|---|---|
| `default` | Синий | Обычная связь |
| `yes` | Зеленый | Ветка "да" в условии |
| `no` | Красный | Ветка "нет" в условии |
| `loop_back` | Фиолетовый | Обратная связь цикла |
| `loop_exit` | Оранжевый | Выход из цикла |
| `exception` | Красный | Исключение (try/catch) |
| `from_no` | Красный | Продолжение ветки "нет" |
| `fan_{N}` | Синий | Веер от класса к методам |

**Интерактивность**:

- **Масштабирование**: колёсико мыши (20%–500%)
- **Панорамирование**: перетаскивание ЛКМ
- **Кнопки управления**: Увеличить (+), Уменьшить (–), Сбросить (⟲)
- **Экспорт**: Скачать PNG (сохраняет текущий вид)

**Алгоритм расстановки узлов**:

1. **Поиск стартового узла**: `start` или первый узел
2. **Рекурсивный обход**: вычисление позиций для всех узлов
3. **Особые случаи**:
   - **Условие (if)**: "да" → вниз, "нет" → вправо
   - **Цикл (loop)**: тело → вниз, выход → вправо, обратная связь → слева
   - **Класс**: поля → блок полей, методы → веером внизу
4. **Выравнивание**: автоматическое центрирование и отступы

#### 3. Панели управления (`main.js`)

- **Панель блок-схемы**: заголовок, кнопки управления, область просмотра
- **Множественные схемы**: отдельные панели для main, классов, функций, методов
- **Зум-индикатор**: отображение текущего масштаба (в правом нижнем углу)

#### 4. Отображение исходного кода

- **Подсветка**: моноширинный шрифт, тёмная тема
- **Синхронизация**: автоматическое обновление при генерации

### Взаимодействие с бэкендом

```javascript
// Отправка файла
fetch('/upload', {
    method: 'POST',
    body: formData
})

// Получение данных
{
    main_flowchart: { nodes: [...], edges: [...] },
    functions: [{ name, type, flowchart }],
    classes: [{ name, type, flowchart }],
    code: "исходный код"
}
```

### Стилизация

**Цветовая схема:**

| Роль | Цвет | HEX |
|---|---|---|
| Основной | Синий | `#2563eb` |
| Успех | Зелёный | `#10b981` |
| Ошибка | Красный | `#ef4444` |
| Фон | Светло-серый | `#f8fafc` |
| Текст | Тёмно-серый | `#1e293b` |
| Границы | Светло-серый | `#e2e8f0` |

**Адаптивность:**

- Мобильные устройства: уменьшенные отступы и размеры
- Десктоп: полноэкранный режим
- SVG: масштабируемая векторная графика

### Требования к браузеру

- Современные браузеры: Chrome, Firefox, Safari, Edge (последние 2 версии)
- Поддержка: ES6+, SVG, Canvas (для экспорта PNG)
- Размер: ~200 KB (JS + CSS)

## Как запустить

### В браузере (онлайн)

<https://block-diagramm-1.onrender.com/>

### Локальный запуск (без Docker)

```bash
cd ~/dotfiles/projects/Block-Diagramm
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

### Docker-запуск

```bash
# Сборка и запуск
make docker-build
make docker-up

# Просмотр логов
make docker-logs
```

## Диагностика: как смотреть логи, если что-то сломалось

### Локальный запуск (без Docker)

Логи выводятся в терминал, где запущен сервер.

### Docker-запуск

```bash
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
| SVG не отображается | Проверить консоль браузера (F12) на ошибки JavaScript |
| Экспорт PNG не работает | Проверить, что SVG содержит корректные данные, включен ли CORS |

## Разработка и расширение

### Добавление нового языка

1. Создать папку `app/parsers/newlang/`
2. Реализовать 4 файла:
   - `tokenizer.py` — лексер
   - `ast_builder.py` — построение AST
   - `handlers.py` — обработка конструкций
   - `parser.py` — основной класс
3. Добавить в `app/parsers/__init__.py`
4. Добавить в `ParserFactory`
5. Добавить расширение в `setFile()` (frontend)

### Добавление нового типа узла

1. Добавить в `drawNode()` (`flowchart-renderer.js`)
2. Добавить в `getNodeFullHeight()` (расчёт высоты)
3. Добавить в `getBottomPoint()`/`getTopPoint()` (точки входа/выхода)
4. Обновить стили в `style.css` (опционально)

## Структура проекта (полная)

```
block_diagramm/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Flask приложение
│   ├── config.py               # Конфигурация
│   ├── routes.py               # Маршруты
│   ├── services/               # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── flowchart_service.py
│   │   └── parser_factory.py
│   ├── parsers/                # Парсеры языков
│   │   ├── __init__.py
│   │   ├── base_parser.py      # Абстрактный класс
│   │   ├── python/
│   │   ├── javascript/
│   │   ├── csharp/
│   │   └── golang/             # (в разработке)
│   ├── models/                 # Модели данных
│   │   ├── __init__.py
│   │   └── flowchart.py
│   ├── builders/               # Строители блок-схем
│   │   ├── __init__.py
│   │   └── flowchart_builder.py
│   └── utils/                  # Утилиты
│       ├── __init__.py
│       └── code_cleaner.py
├── static/                     # Статические файлы (frontend)
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── flowchart-renderer.js
│       └── main.js
├── templates/                  # Шаблоны (frontend)
│   └── index.html
├── tests/                      # Тесты
│   ├── __init__.py
│   ├── test_all_parsers.py
│   ├── test_python_parser.py
│   ├── test_js_parser.py
│   ├── test_cs_parser.py
│   └── fixtures/               # Тестовые файлы
│       ├── test_python_simple.py
│       ├── test_python_complex.py
│       ├── test_javascript_simple.js
│       ├── test_javascript_complex.js
│       ├── test_csharp_simple.cs
│       └── test_csharp_complex.cs
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── requirements.txt
├── Makefile
├── run.py
└── README.md
```

