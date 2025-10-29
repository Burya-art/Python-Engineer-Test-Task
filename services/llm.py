# services/llm.py

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# --- Налаштування ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()  # "openai", "mock"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Мок-відповідь ---
MOCK_RESPONSE = (
    "Основні ризики в цій професії:\n"
    "• Висока конкуренція\n"
    "• Постійне навчання\n"
    "• Ризик вигорання"
)

# --- Адаптер LLM ---
async def ask_llm(profession: str, description: str | None, question: str) -> str:
    prompt = f"Професія: {profession}"
    if description:
        prompt += f" ({description})"
    prompt += f"\nПитання: {question}\nВідповідай коротко, українською, без вступів."

    if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        return await _ask_openai(prompt)
    else:
        return MOCK_RESPONSE


async def _ask_openai(prompt: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",  # Фіксована модель
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
        except httpx.HTTPStatusError as e:
            # OpenAI повертає JSON з помилкою
            try:
                error = e.response.json().get("error", {}).get("message", "")
                return f"Помилка OpenAI: {error}"
            except:
                return f"Помилка OpenAI: HTTP {e.response.status_code}"
        except Exception as e:
            return f"Помилка LLM: {str(e)}"