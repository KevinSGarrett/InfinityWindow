from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ModelPricing:
    """Pricing in USD per 1M tokens."""
    input_per_million: float
    output_per_million: float


# Approximate prices – tweak as needed
PRICING: Dict[str, ModelPricing] = {
    # Adjust these to whatever you're actually paying
    "gpt-5.1": ModelPricing(
        input_per_million=1.25,
        output_per_million=10.00,
    ),
    "gpt-4.1": ModelPricing(
        input_per_million=5.00,
        output_per_million=15.00,
    ),
    "gpt-4.1-mini": ModelPricing(
        input_per_million=0.15,
        output_per_million=0.60,
    ),
    # You can add more entries here later (gpt-5-nano, etc.)
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
