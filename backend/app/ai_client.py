import json
import time

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"


class AIConnectivityError(Exception):
    """Raised when the OpenRouter connectivity test fails."""


KANBAN_SYSTEM_PROMPT = """
You are an AI assistant for a Kanban board.
You must ALWAYS respond with valid JSON and nothing else.

Required JSON shape:
{
  "assistant_response": "short helpful response to the user",
  "operations": [
    {
      "type": "rename_column",
      "columnId": "col-id",
      "title": "New column title"
    },
    {
      "type": "create_card",
      "columnId": "col-id",
      "title": "Card title",
      "details": "Card details",
      "cardId": "optional-card-id"
    },
    {
      "type": "update_card",
      "cardId": "card-id",
      "title": "optional new title",
      "details": "optional new details"
    },
    {
      "type": "move_card",
      "cardId": "card-id",
      "toColumnId": "col-id",
      "beforeCardId": "optional-target-card-id"
    },
    {
      "type": "delete_card",
      "cardId": "card-id"
    }
  ]
}

Rules:
- operations must be an array (use [] when no changes needed)
- only include operations that are needed
- do not include markdown
- do not include explanation outside JSON
""".strip()


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


def _post_openrouter(
    payload: dict[str, object],
    headers: dict[str, str],
    retries: int = 3,
) -> httpx.Response:
    last_response: httpx.Response | None = None

    for attempt in range(retries):
        try:
            with httpx.Client(timeout=45) as client:
                response = client.post(
                    OPENROUTER_URL,
                    headers=headers,
                    content=json.dumps(payload),
                )
        except httpx.HTTPError as error:
            raise AIConnectivityError("OpenRouter request failed.") from error

        last_response = response

        if response.status_code != 429:
            return response

        if attempt < retries - 1:
            time.sleep(1 + attempt)

    if last_response is None:
        raise AIConnectivityError("OpenRouter request failed.")
    return last_response


def _parse_json_output(content: str) -> dict[str, object]:
    text = content.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise AIConnectivityError("Model returned invalid structured output.") from error

    if not isinstance(parsed, dict):
        raise AIConnectivityError("Model returned invalid structured output.")

    return parsed


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

    response = _post_openrouter(payload=payload, headers=headers)

    if response.status_code >= 400:
        raise AIConnectivityError("OpenRouter request failed.")

    try:
        response_json = response.json()
    except ValueError as error:
        raise AIConnectivityError("OpenRouter returned invalid JSON.") from error

    if not isinstance(response_json, dict):
        raise AIConnectivityError("OpenRouter response JSON was malformed.")

    return _extract_content(response_json)


def run_kanban_chat(
    api_key: str,
    board_data: dict[str, object],
    history: list[dict[str, str]],
    message: str,
) -> dict[str, object]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": KANBAN_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Current board JSON:\n"
                f"{json.dumps(board_data, ensure_ascii=True)}"
            ),
        },
    ]

    for entry in history:
        role = entry.get("role")
        content = entry.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = _post_openrouter(payload=payload, headers=headers)

    if response.status_code >= 400:
        raise AIConnectivityError("OpenRouter request failed.")

    try:
        response_json = response.json()
    except ValueError as error:
        raise AIConnectivityError("OpenRouter returned invalid JSON.") from error

    if not isinstance(response_json, dict):
        raise AIConnectivityError("OpenRouter response JSON was malformed.")

    content = _extract_content(response_json)
    return _parse_json_output(content)
