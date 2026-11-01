import httpx

from app.core.config import settings


class ProviderNotConfigured(Exception):
    pass


class ProviderRequestError(Exception):
    pass


async def generate_reply(system_prompt: str, history: list[dict[str, str]]) -> str:
    if not settings.ai_api_key or not settings.ai_model:
        raise ProviderNotConfigured("برای فعال‌کردن چت، AI_API_KEY و AI_MODEL را در فایل backend/.env تنظیم کن.")

    base_url = settings.ai_base_url.rstrip("/")
    endpoint = f"{base_url}/chat/completions"
    payload = {
        "model": settings.ai_model,
        "messages": [{"role": "system", "content": system_prompt}, *history],
        "temperature": 0.85,
    }
    headers = {"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            if isinstance(answer, list):
                answer = "".join(part.get("text", "") for part in answer if isinstance(part, dict))
            if not isinstance(answer, str) or not answer.strip():
                raise ProviderRequestError("مدل پاسخ متنی معتبری برنگرداند.")
            return answer.strip()
    except ProviderNotConfigured:
        raise
    except ProviderRequestError:
        raise
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise ProviderRequestError(f"ارتباط با سرویس هوش مصنوعی ناموفق بود: {exc}") from exc
