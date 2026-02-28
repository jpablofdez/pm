import json

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"


class AIConnectivityError(Exception):
    """Raised when the OpenRouter connectivity test fails."""


def _extract_content(response_json: dict[str, object]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AIConnectivityError("OpenRouter response did not include choices.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise AIConnectivityError("OpenRouter response choice was malformed.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise AIConnectivityError("OpenRouter response message was missing.")

    content = message.get("content")
    if isinstance(content, str):
        if not content.strip():
            raise AIConnectivityError("Model response was empty.")
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        joined = "\n".join(text_parts).strip()
        if joined:
            return joined

    raise AIConnectivityError("OpenRouter response content was not usable.")


def run_connectivity_prompt(api_key: str, prompt: str = "2+2") -> str:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                OPENROUTER_URL,
                headers=headers,
                content=json.dumps(payload),
            )
    except httpx.HTTPError as error:
        raise AIConnectivityError("OpenRouter request failed.") from error

    if response.status_code >= 400:
        raise AIConnectivityError("OpenRouter request failed.")

    try:
        response_json = response.json()
    except ValueError as error:
        raise AIConnectivityError("OpenRouter returned invalid JSON.") from error

    if not isinstance(response_json, dict):
        raise AIConnectivityError("OpenRouter response JSON was malformed.")

    return _extract_content(response_json)
