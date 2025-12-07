from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ModelPricing:
    """Pricing in USD per 1M tokens."""
    input_per_million: float
    output_per_million: float


# Approximate prices – tweak as needed. Values are USD per 1M tokens.
# Add/adjust to match your billing; unknown models return 0.0.
PRICING: Dict[str, ModelPricing] = {
    "gpt-5.1": ModelPricing(
        input_per_million=1.25,
        output_per_million=10.00,
    ),
    "gpt-5-pro": ModelPricing(
        input_per_million=2.50,
        output_per_million=18.00,
    ),
    "gpt-5-nano": ModelPricing(
        input_per_million=0.05,
        output_per_million=0.20,
    ),
    "gpt-5.1-codex": ModelPricing(
        input_per_million=1.50,
        output_per_million=12.00,
    ),
    "gpt-4.1": ModelPricing(
        input_per_million=5.00,
        output_per_million=15.00,
    ),
    "gpt-4.1-mini": ModelPricing(
        input_per_million=0.15,
        output_per_million=0.60,
    ),
}


def estimate_call_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """
    Estimate USD cost for a single LLM call given a model + token counts.

    If the model is unknown, we return 0.0 rather than raising.
    """
    info = PRICING.get(model)
    if not info:
        return 0.0

    cost_in = (tokens_in / 1_000_000.0) * info.input_per_million
    cost_out = (tokens_out / 1_000_000.0) * info.output_per_million
    return cost_in + cost_out
