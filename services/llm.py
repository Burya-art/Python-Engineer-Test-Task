# services/llm.py

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# --- Налаштування ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()  # "openai", "mock"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Мок-відповідь як в ТЗ ---
MOCK_RESPONSE = "Основні ризики в цій професії: висока конкуренція, необхідність постійного навчання, ризик вигорання."

# --- Адаптер LLM строго по ТЗ ---
async def ask_llm(profession: str, description: str | None, question: str) -> str:
    """
    Строго по ТЗ: формує короткий безпечний промпт, звертається до LLM
    або повертає мок-відповідь
    """
    # Промпт строго по ТЗ: короткий, безпечний, обрізаний контекст
    prompt = f"Професія: {profession}. "
    if description:
        prompt += f"Опис: {description}. "
    prompt += f"Питання: {question}. Відповідь українською, коротко."

    if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        return await _ask_openai(prompt)
    else:
        # Мок-відповідь строго по ТЗ
        return MOCK_RESPONSE


async def _ask_openai(prompt: str) -> str:
    """Реальний запит до OpenAI API"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 150
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            # При любой ошибке возвращаем мок-ответ как в ТЗ
            return MOCK_RESPONSE