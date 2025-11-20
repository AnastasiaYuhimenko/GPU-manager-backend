# GPU Manager Backend

Backend сервис для управления GPU ресурсами.

## Требования

- Python >= 3.14
- uv (для управления зависимостями)

## Установка

```bash
uv sync
```

## Запуск

### Режим разработки

```bash
uv run fastapi dev app/main.py
```

Сервер будет доступен по адресу: http://localhost:8000

## API Документация

После запуска сервера документация будет доступна по адресам:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Документация проекта

Подробная документация проекта доступна в директории [`docs/`](docs/README.md):

* [User Stories](docs/README.md) - описание функциональных требований