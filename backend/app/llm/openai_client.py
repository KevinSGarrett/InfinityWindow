from __future__ import annotations

import os
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from the .env file in the backend directory
load_dotenv()

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """
    Lazily create and return a singleton OpenAI client.
    """
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Create a .env file in the backend folder and add "
                "OPENAI_API_KEY=your_key_here."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def generate_reply_from_history(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
) -> str:
    """
    Call the OpenAI Chat Completions API with a list of messages.

    Each message should be a dict with:
      - 'role': 'system' | 'user' | 'assistant'
      - 'content': text content

    Returns the assistant's reply text.
    """
    client = get_client()

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )

    return completion.choices[0].message.content or ""
