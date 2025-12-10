from __future__ import annotations

import os
import re
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Singleton OpenAI client
_client: Optional[OpenAI] = None
_stub_client: Optional[object] = None


def _make_stub_client() -> object:
    """
    Lightweight stub for CI/LLM_MODE=stub so tests don't require real API keys.
    Provides minimal embeddings + chat/responses surfaces used in this codebase.
    """

    class _StubEmbeddingItem:
        def __init__(self, value: List[float]) -> None:
            self.embedding = value

    class _StubEmbeddings:
        def create(self, model: str, input):
            texts = input if isinstance(input, list) else [input]
            data = [
                _StubEmbeddingItem([float(len(str(t))) % 7, 0.0, 1.0])
                for t in texts
            ]
            return type("Resp", (), {"data": data})

    class _StubChatCompletions:
        def create(self, **kwargs):
            choice = type(
                "Choice",
                (),
                {"message": type("Msg", (), {"content": "stubbed reply"})()},
            )
            usage = type(
                "Usage",
                (),
                {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            )()
            return type("Resp", (), {"choices": [choice], "usage": usage})

    class _StubChat:
        def __init__(self):
            self.completions = _StubChatCompletions()

    class _StubResponses:
        def create(self, **kwargs):
            text_obj = type("Text", (), {"value": "stubbed reply"})()
            content = type("Content", (), {"text": text_obj})()
            output_item = type("Output", (), {"content": [content]})()
            usage = type(
                "Usage",
                (),
                {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )()
            return type("Resp", (), {"output": [output_item], "usage": usage})

    class _StubClient:
        def __init__(self):
            self.embeddings = _StubEmbeddings()
            self.chat = _StubChat()
            self.responses = _StubResponses()

    return _StubClient()


def get_client() -> OpenAI:
    """
    Lazily create and return a singleton OpenAI client.
    """
    global _client, _stub_client
    if os.getenv("LLM_MODE", "").lower() == "stub":
        if _stub_client is None:
            _stub_client = _make_stub_client()
        return _stub_client  # type: ignore[return-value]

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
# Your .env likely overrides these with high‑end models (gpt‑5.1, gpt‑5-mini, etc.).
_DEFAULT_MODELS: Dict[str, str] = {
    "auto": "gpt-4.1",
    "fast": "gpt-4.1-mini",
    "deep": "gpt-5.1",
    "budget": "gpt-4.1-nano",
    "research": "o3-deep-research",
    "code": "gpt-5.1-codex",
}

_CODE_HINTS = (
    "```",
    "class ",
    "def ",
    "function ",
    "const ",
    "let ",
    "var ",
    "import ",
    "#include",
    "public ",
    "private ",
    "interface ",
    "=>",
)

_RESEARCH_HINTS = (
    "research",
    "investigate",
    "compare",
    "analysis",
    "literature review",
    "survey",
    "whitepaper",
    "case study",
    "statistical",
    "market",
    "sources",
    "citations",
    "reference",
)

_PLANNING_HINTS = (
    "roadmap",
    "multi-quarter",
    "multi quarter",
    "milestone",
    "milestones",
    "timeline",
    "rollbacks",
    "rollback",
    "schema evolution",
    "system design",
    "architecture",
    "ingestion pipeline",
    "telemetry",
    "strategy",
    "plan for",
)

_LLM_TELEMETRY_AUTO_ROUTES: Dict[str, int] = defaultdict(int)
_LLM_RECENT_AUTO_ROUTES: deque[Dict[str, Any]] = deque(maxlen=20)
_LLM_TELEMETRY: Dict[str, Any] = {
    "auto_routes": _LLM_TELEMETRY_AUTO_ROUTES,
    "fallback_attempts": 0,
    "fallback_success": 0,
    "latest_auto_route": None,
    "recent_auto_routes": _LLM_RECENT_AUTO_ROUTES,
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


def _extract_last_user_prompt(messages: List[Dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content") or ""
            if isinstance(content, str):
                return content
    if messages:
        fallback = messages[-1].get("content") or ""
        if isinstance(fallback, str):
            return fallback
    return ""


def _infer_auto_submode(
    messages: List[Dict[str, str]]
) -> Tuple[str, str]:
    """
    Lightweight heuristic that decides which logical mode auto should route to.
    Returns (mode, reason).
    """
    prompt = _extract_last_user_prompt(messages)
    lowered = prompt.lower()
    stripped_len = len(prompt.strip())
    newline_count = prompt.count("\n")

    history_chars = sum(
        len(str(m.get("content") or ""))
        for m in messages
        if isinstance(m.get("content"), str)
    )
    user_turns = sum(
        1 for m in messages if (m.get("role") or "").lower() == "user"
    )
    total_turns = len(messages)

    code_signals: List[str] = []
    has_code_block = "```" in prompt
    if has_code_block:
        code_signals.append("code fences")

    patch_markers = bool(re.search(r"(diff --git|@@ |\+\+\+|---|\bapply_patch\b)", prompt))
    if patch_markers:
        code_signals.append("diff/patch text")

    file_path_mention = bool(
        re.search(
            r"[A-Za-z0-9_./\\-]+\.(py|ts|tsx|js|jsx|java|go|rb|rs|c|cpp|h|cs|sql|md|mdx|json|yml|yaml|ini|cfg|toml|sh|ps1)",
            prompt,
        )
    )
    if file_path_mention:
        code_signals.append("file paths")

    terminal_like = bool(
        re.search(r"\b(git|npm|pnpm|yarn|pip|docker|kubectl|make|pytest|uvicorn)\b", lowered)
    )
    if terminal_like:
        code_signals.append("terminal/command text")

    stacktrace_like = "traceback" in lowered or "exception" in lowered
    if stacktrace_like:
        code_signals.append("errors/traceback")

    code_keywords = any(hint in lowered for hint in _CODE_HINTS)
    if code_keywords and not code_signals:
        code_signals.append("code keywords")

    if code_signals:
        return "code", "; ".join(code_signals)

    research_hits = any(term in lowered for term in _RESEARCH_HINTS)
    very_long_prompt = stripped_len > 1600 or newline_count > 12
    very_long_history = history_chars > 8000 or total_turns > 30
    short_prompt = stripped_len < 220 and newline_count <= 2
    if research_hits or very_long_prompt or (very_long_history and not short_prompt):
        reasons: List[str] = []
        if research_hits:
            reasons.append("research keywords")
        if very_long_prompt or very_long_history:
            reasons.append("very long prompt/history")
        return "research", "; ".join(reasons)

    planning_hits = [term for term in _PLANNING_HINTS if term in lowered]
    if planning_hits:
        return "deep", f"planning keywords ({', '.join(planning_hits[:2])})"

    task_keywords = (
        "todo",
        "to-do",
        "task",
        "tasks",
        "status",
        "update",
        "progress",
        "blocker",
        "blockers",
        "standup",
        "stand-up",
        "eta",
    )
    doc_keywords = (
        "doc",
        "docs",
        "documentation",
        "readme",
        "spec",
        "design",
        "memo",
        "wiki",
        "memory",
        "notes",
    )
    file_keywords = (
        "repo",
        "repository",
        "file",
        "folder",
        "path",
        "directory",
        "fs ",
        "fs/",
        "stack trace",
        "logs",
        "terminal",
        "shell",
    )

    has_tasks = any(term in lowered for term in task_keywords)
    has_docs = any(term in lowered for term in doc_keywords)
    has_files = any(term in lowered for term in file_keywords)

    if short_prompt:
        reasons = ["short prompt"]
        if has_tasks:
            reasons.append("task/status keywords")
        elif has_docs or has_files:
            reasons.append("light context only")
        return "fast", "; ".join(reasons)

    long_history = history_chars > 2400 or user_turns > 8 or total_turns > 12
    multi_paragraph = newline_count >= 6 or stripped_len > 600

    if long_history or multi_paragraph or (has_docs and stripped_len > 220) or (
        has_files and stripped_len > 220
    ):
        reasons: List[str] = []
        if long_history:
            reasons.append("long history")
        if multi_paragraph:
            reasons.append("multi-paragraph prompt")
        if has_docs:
            reasons.append("docs/memory references")
        if has_files:
            reasons.append("files/terminal context")
        return "deep", "; ".join(reasons)

    if stripped_len < 220 and newline_count <= 2:
        reasons = ["short prompt"]
        if has_tasks:
            reasons.append("task/status keywords")
        elif has_docs or has_files:
            reasons.append("light context only")
        return "fast", "; ".join(reasons)

    return "deep", "default (balanced prompt)"


def _record_auto_route(route: str, reason: Optional[str] = None) -> None:
    _LLM_TELEMETRY_AUTO_ROUTES[route] += 1
    decision = {
        "route": route,
        "reason": reason or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _LLM_TELEMETRY["latest_auto_route"] = decision
    recent = _LLM_TELEMETRY.get("recent_auto_routes")
    if isinstance(recent, deque):
        recent.appendleft(decision)


def get_llm_telemetry(reset: bool = False) -> Dict[str, Any]:
    snapshot = {
        "auto_routes": dict(_LLM_TELEMETRY_AUTO_ROUTES),
        "fallback_attempts": int(_LLM_TELEMETRY["fallback_attempts"]),
        "fallback_success": int(_LLM_TELEMETRY["fallback_success"]),
        "latest_auto_route": _LLM_TELEMETRY.get("latest_auto_route"),
        "recent_auto_routes": list(_LLM_RECENT_AUTO_ROUTES),
    }
    if reset:
        reset_llm_telemetry()
    return snapshot


def reset_llm_telemetry() -> None:
    _LLM_TELEMETRY_AUTO_ROUTES.clear()
    _LLM_TELEMETRY["fallback_attempts"] = 0
    _LLM_TELEMETRY["fallback_success"] = 0
    _LLM_TELEMETRY["latest_auto_route"] = None
    _LLM_RECENT_AUTO_ROUTES.clear()


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


def _extract_text_from_responses(resp: Any) -> str:
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


# ---------------------------------------------------------------------------
# Pricing (cost estimation)
# ---------------------------------------------------------------------------

# Pricing per 1K tokens for common models (in USD).
# Derived from the official OpenAI API pricing table for GPT‑5.* models. 
#
# NOTE: These are *inference* prices (not fine‑tuning).
#       If you use different models, unknown models will show $0 cost unless
#       you extend the mapping or add env‑based overrides.
_MODEL_PRICING_PER_1K: Dict[str, Tuple[float, float]] = {
    # canonical_name: (input_price_per_1k, output_price_per_1k)
    "gpt-5.1": (1.250 / 1000.0, 10.000 / 1000.0),       # $1.25 in / $10 out per 1M
    "gpt-5-mini": (0.250 / 1000.0, 2.000 / 1000.0),     # $0.25 in / $2.00 out per 1M
    "gpt-5-nano": (0.050 / 1000.0, 0.400 / 1000.0),     # $0.05 in / $0.40 out per 1M
    "gpt-5-pro": (15.000 / 1000.0, 120.000 / 1000.0),   # $15 in / $120 out per 1M
    # You can extend this dict for other models (4.1, 4o, etc.) if desired.
}


def _canonical_model_for_pricing(model: str) -> Optional[str]:
    """
    Map raw model ids to a canonical key in _MODEL_PRICING_PER_1K.
    """
    m = model.lower()

    # Direct matches first
    for key in _MODEL_PRICING_PER_1K.keys():
        if m == key:
            return key

    # Handle common prefixes/variants
    if m.startswith("gpt-5.1") or m.startswith("gpt-5-codex"):
        return "gpt-5.1"
    if "nano" in m or m.startswith("gpt-5-nano"):
        return "gpt-5-nano"
    if "mini" in m or m.startswith("gpt-5-mini"):
        return "gpt-5-mini"
    if "pro" in m or m.startswith("gpt-5-pro"):
        return "gpt-5-pro"

    # Unknown -> no pricing
    return None


def estimate_cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    """
    Estimate USD cost for a call based on model + token usage.

    - Uses per‑1K token pricing from _MODEL_PRICING_PER_1K.
    - Returns 0.0 if the model is unknown or usage is missing.
    """
    if (tokens_in or 0) <= 0 and (tokens_out or 0) <= 0:
        return 0.0

    canonical = _canonical_model_for_pricing(model)
    if canonical is None:
        # Unknown model family: treat as 0 cost unless you extend the mapping.
        return 0.0

    price_in_per_1k, price_out_per_1k = _MODEL_PRICING_PER_1K[canonical]

    # Convert tokens to 1K‑token units
    cost_in = (tokens_in / 1000.0) * price_in_per_1k
    cost_out = (tokens_out / 1000.0) * price_out_per_1k
    return float(cost_in + cost_out)


# ---------------------------------------------------------------------------
# Low‑level call helper
# ---------------------------------------------------------------------------


def _call_model(
    messages: List[Dict[str, str]],
    model: str,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    usage_out: Optional[Dict[str, Any]] = None,
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

    # We'll fill these from resp.usage when available
    tokens_in = 0
    tokens_out = 0
    total_tokens = 0

    if use_responses:
        # Responses API: do NOT include temperature (some models don't support it).
        kwargs: Dict[str, object] = {
            "model": model,
            "input": messages,
        }
        if max_output_tokens is not None:
            kwargs["max_output_tokens"] = max_output_tokens

        resp = client.responses.create(**kwargs)
        text = _extract_text_from_responses(resp)

        # Try to read usage.input_tokens / usage.output_tokens / usage.total_tokens
        try:
            usage = getattr(resp, "usage", None)
            if usage is not None:
                tokens_in = int(getattr(usage, "input_tokens", 0) or 0)
                tokens_out = int(getattr(usage, "output_tokens", 0) or 0)
                total_tokens = int(
                    getattr(usage, "total_tokens", 0)
                    or (tokens_in + tokens_out)
                )
        except Exception:
            # Don't break the call if usage isn't available
            pass

        if usage_out is not None:
            usage_out.clear()
            usage_out["model"] = model
            usage_out["tokens_in"] = tokens_in
            usage_out["tokens_out"] = tokens_out
            usage_out["total_tokens"] = total_tokens
            usage_out["cost_estimate"] = estimate_cost_usd(
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )

        return text

    # Chat Completions path (classic 4.x / 3.5 models)
    kwargs_cc: Dict[str, object] = {
        "model": model,
        "messages": messages,
    }
    if temperature is not None:
        kwargs_cc["temperature"] = temperature
    # IMPORTANT: don't send max_tokens at all if it's None
    if max_output_tokens is not None:
        kwargs_cc["max_tokens"] = max_output_tokens

    resp = client.chat.completions.create(**kwargs_cc)
    choice = resp.choices[0]
    content = getattr(choice.message, "content", None) or ""

    # Try to read usage.prompt_tokens / usage.completion_tokens / usage.total_tokens
    try:
        usage = getattr(resp, "usage", None)
        if usage is not None:
            tokens_in = int(getattr(usage, "prompt_tokens", 0) or 0)
            tokens_out = int(getattr(usage, "completion_tokens", 0) or 0)
            total_tokens = int(
                getattr(usage, "total_tokens", 0)
                or (tokens_in + tokens_out)
            )
    except Exception:
        pass

    if usage_out is not None:
        usage_out.clear()
        usage_out["model"] = model
        usage_out["tokens_in"] = tokens_in
        usage_out["tokens_out"] = tokens_out
        usage_out["total_tokens"] = total_tokens
        usage_out["cost_estimate"] = estimate_cost_usd(
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

    return content


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------


def generate_reply_from_history(
    messages: List[Dict[str, str]],
    mode: str = "auto",
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_output_tokens: Optional[int] = None,
    usage_out: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Call OpenAI with the full chat history and return the assistant's reply.

    - If 'model' is provided, we use it directly.
    - Otherwise we choose a model based on 'mode' using _get_model_for_mode.

    Logical modes (all configurable via .env):

      - auto     -> OPENAI_MODEL_AUTO
      - fast     -> OPENAI_MODEL_FAST
      - deep     -> OPENAI_MODEL_DEEP
      - budget   -> OPENAI_MODEL_BUDGET
      - research -> OPENAI_MODEL_RESEARCH
      - code     -> OPENAI_MODEL_CODE

    If 'usage_out' is provided, it will be populated with:
      {
        "model": <model name>,
        "tokens_in": <int>,
        "tokens_out": <int>,
        "total_tokens": <int>,
        "cost_estimate": <float USD>
      }
    """
    normalized_mode = (mode or "auto").lower()
    routed_mode = normalized_mode

    if model is None and normalized_mode == "auto":
        inferred_mode, inferred_reason = _infer_auto_submode(messages)
        routed_mode = inferred_mode or "deep"
        _record_auto_route(routed_mode, inferred_reason)
        print(
            f"[LLM] Auto mode heuristics routed this prompt to '{routed_mode}' ({inferred_reason})."
        )
        if usage_out is not None:
            usage_out["auto_mode"] = routed_mode
            usage_out["auto_reason"] = inferred_reason

    chosen_model = (model or _get_model_for_mode(routed_mode)).strip()

    candidate_models: List[str] = [chosen_model]
    if model is None:
        # Allow graceful fallback if the primary mode-specific model is unavailable.
        fallback_auto = os.getenv(
            "OPENAI_MODEL_AUTO", _DEFAULT_MODELS.get("auto", "gpt-4.1")
        )
        if fallback_auto and fallback_auto not in candidate_models:
            candidate_models.append(fallback_auto)

        # Include a lightweight, broadly available model as a last resort.
        safety_net = os.getenv("OPENAI_MODEL_FAST", _DEFAULT_MODELS.get("fast"))
        if safety_net and safety_net not in candidate_models:
            candidate_models.append(safety_net)

    last_error: Optional[Exception] = None
    fallback_used_in_this_call = False
    for idx, candidate in enumerate(candidate_models):
        try:
            result = _call_model(
                messages=messages,
                model=candidate,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                usage_out=usage_out,
            )
            if fallback_used_in_this_call and idx > 0:
                _LLM_TELEMETRY["fallback_success"] += 1
            return result
        except Exception as err:  # noqa: BLE001
            last_error = err
            if idx < len(candidate_models) - 1:
                fallback_used_in_this_call = True
                _LLM_TELEMETRY["fallback_attempts"] += 1
            print(
                f"[LLM] Model '{candidate}' failed ({err!r}); "
                "trying next fallback if available."
            )

    # If every candidate failed, bubble up the last error so the caller can surface it.
    if last_error is not None:
        raise last_error

    # Should never happen, but keep mypy happy.
    raise RuntimeError("LLM routing failed with no usable model candidates.")
