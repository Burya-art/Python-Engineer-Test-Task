# Friends List Bot

FastAPI + aiogram + AWS (S3 + DynamoDB) + Docker + LLM (mock/OpenAI)

---

## Технології
- **FastAPI** — бекенд
- **aiogram 3** — Telegram-бот
- **AWS S3** — фото
- **AWS DynamoDB** — мета-дані
- **LLM** — OpenAI (або мок)
- **Pytest** — тести

---

## Запуск (Docker)

```bash

docker compose up --build

Запуск локально

# Бекенд
uvicorn app.main:app --reload

# Бот
python bot/main.py

Тести 

docker compose run --rm tests
```

```bash

.env

TELEGRAM_BOT_TOKEN=...
BACKEND_BASE_URL=http://backend:8000

AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=testtask-friends-photos
DYNAMODB_TABLE_NAME=FriendsTable

LLM_PROVIDER=mock
```

Команди в Telegram

@friends_list893_bot

/addfriend — додати друга

/list — список

/friend <id> — деталі

/ask <id> <питання> — запит до LLM