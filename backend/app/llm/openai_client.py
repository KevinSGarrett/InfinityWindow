from __future__ import annotations

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Singleton OpenAI client
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """
    Lazily create and return a singleton OpenAI client.
    """
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Please add it to your .env file."
            )
        _client = OpenAI(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------

# Built‑in defaults if you don't override via environment variables.
# Your .env already overrides these with high‑end models (gpt‑5.1, gpt‑5‑nano, etc.).
_DEFAULT_MODELS = {
    "auto": "gpt-4.1",
    "fast": "gpt-4.1-mini",
    "deep": "gpt-5.1",
    "budget": "gpt-4.1-nano",
    "research": "o3-deep-research",
    "code": "gpt-5.1-codex",
}


def _get_model_for_mode(mode: str | None) -> str:
    """
    Return the model name for a given logical mode.

    Order of precedence:
      1) Environment variable OPENAI_MODEL_<MODE>  (e.g. OPENAI_MODEL_FAST)
      2) Built‑in defaults in _DEFAULT_MODELS
      3) Fallback to the 'auto' model
    """
    mode_normalized = (mode or "auto").lower()

    env_var_name = f"OPENAI_MODEL_{mode_normalized.upper()}"
    env_value = os.getenv(env_var_name)

    if env_value:
        return env_value

    if mode_normalized in _DEFAULT_MODELS:
        return _DEFAULT_MODELS[mode_normalized]

    # Unknown mode, fall back to AUTO
    return os.getenv("OPENAI_MODEL_AUTO", _DEFAULT_MODELS["auto"])


def _is_responses_model(model: str) -> bool:
    """
    Heuristic: decide whether to call the new Responses API or Chat Completions.

    - Newer 5.x / o3 / o4 / 4o families are best used via Responses API.
    - Older 4.1 / 3.5 families use Chat Completions.
    """
    m = model.lower()

    # Treat all gpt‑5*, o3*, o4*, 4o*, and open‑weight models as Responses API.
    if m.startswith("gpt-5") or m.startswith("o3") or m.startswith("o4"):
        return True
    if m.startswith("gpt-4o"):
        return True
    if m.startswith("gpt-oss-"):
        return True

    # Everything else (gpt‑4.1, 4.1‑nano, 3.5‑turbo, etc.) -> Chat Completions.
    return False


def _extract_text_from_responses(resp) -> str:
    """
    Try to pull a plain text string out of a Responses API result.

    This is written defensively so minor SDK structure changes won't break us.
    """
    # Some SDK versions expose a convenience 'output_text'.
    try:
        output_text = getattr(resp, "output_text", None)
        if isinstance(output_text, str) and output_text.strip():
            return output_text
    except Exception:
        pass

    # Fallback: walk resp.output[0].content[0].text.value style structure.
    try:
        output = getattr(resp, "output", None)
        if output and len(output) > 0:
            first_item = output[0]
            content_list = getattr(first_item, "content", None)
            if content_list and len(content_list) > 0:
                first_content = content_list[0]
                text_obj = getattr(first_content, "text", None)
                if text_obj is not None:
                    # Often there is a .value with the actual string.
                    value = getattr(text_obj, "value", None)
                    if isinstance(value, str) and value.strip():
                        return value
                    # Or text_obj itself may stringify nicely.
                    if isinstance(text_obj, str) and text_obj.strip():
                        return text_obj
    except Exception:
        pass

    # As a last resort, stringify the whole response.
    return str(resp)


def _call_model(
    messages: List[Dict[str, str]],
    model: str,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
) -> str:
    """
    Low‑level helper that actually calls OpenAI.

    - Uses Responses API for modern models (gpt‑5.*, o3.*, o4.*, gpt‑4o*).
    - Uses Chat Completions API for older chat models (gpt‑4.1, gpt‑4.1‑nano, 3.5, etc.).
    - IMPORTANT: we DO NOT send 'temperature' to the Responses API
      (models like gpt‑5‑nano reject it with a 400 error).
    """
    client = get_client()
    use_responses = _is_responses_model(model)

    print(
        f"[LLM] Using OpenAI model '{model}' via "
        f"{'Responses API' if use_responses else 'Chat Completions'}"
    )

    if use_responses:
        # Responses API: do NOT include temperature (some models don't support it).
        kwargs: Dict[str, object] = {
            "model": model,
            "input": messages,
        }
        if max_output_tokens is not None:
            kwargs["max_output_tokens"] = max_output_tokens

        resp = client.responses.create(**kwargs)
        return _extract_text_from_responses(resp)

    # Chat Completions path (classic 4.x / 3.5 models)
    kwargs: Dict[str, object] = {
        "model": model,
        "messages": messages,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    # IMPORTANT: don't send max_tokens at all if it's None
    if max_output_tokens is not None:
        kwargs["max_tokens"] = max_output_tokens

    resp = client.chat.completions.create(**kwargs)
    choice = resp.choices[0]
    content = getattr(choice.message, "content", None)
    return content or ""


def generate_reply_from_history(
    messages: List[Dict[str, str]],
    mode: str = "auto",
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_output_tokens: Optional[int] = None,
) -> str:
    """
    Call OpenAI with the full chat history and return the assistant's reply.

    - If 'model' is provided, we use it directly.
    - Otherwise we choose a model based on 'mode' using _get_model_for_mode.

    Logical modes (all configurable via .env):

      - auto    -> OPENAI_MODEL_AUTO    (you set this to gpt‑5.1)
      - fast    -> OPENAI_MODEL_FAST    (you set this to gpt‑5-nano)
      - deep    -> OPENAI_MODEL_DEEP    (you set this to gpt‑5-pro)
      - budget  -> OPENAI_MODEL_BUDGET  (you set this to gpt‑4.1-nano)
      - research-> OPENAI_MODEL_RESEARCH
      - code    -> OPENAI_MODEL_CODE
    """
    chosen_model = (model or _get_model_for_mode(mode)).strip()

    return _call_model(
        messages=messages,
        model=chosen_model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
