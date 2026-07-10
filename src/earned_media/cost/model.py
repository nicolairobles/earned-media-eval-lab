from __future__ import annotations

from typing import Any

from ..models import CostTelemetry


class CostMeter:
    def __init__(self, policy: dict[str, Any]):
        llm = policy["llm"]
        self._in_rate = llm["input_usd_per_1m_tokens"] / 1_000_000
        self._out_rate = llm["output_usd_per_1m_tokens"] / 1_000_000
        self.telemetry = CostTelemetry()

    def record_llm_call(self, input_tokens: int, output_tokens: int) -> None:
        t = self.telemetry
        t.llm_calls += 1
        t.llm_input_tokens += input_tokens
        t.llm_output_tokens += output_tokens
        t.estimated_usd = round(
            t.llm_input_tokens * self._in_rate + t.llm_output_tokens * self._out_rate, 6
        )


def monthly_projection(per_release_usd: float, review_queue_per_release: float, policy: dict[str, Any]) -> dict[str, float]:
    cm = policy["cost_model"]
    volume = cm["monthly_release_volume"]
    review_rate = cm["human_review_usd_per_case"]
    llm_monthly = per_release_usd * volume
    review_monthly = review_queue_per_release * review_rate * volume
    return {
        "monthly_release_volume": volume,
        "llm_usd_per_release": round(per_release_usd, 5),
        "llm_usd_monthly": round(llm_monthly, 2),
        "human_review_cases_monthly": round(review_queue_per_release * volume),
        "human_review_usd_monthly": round(review_monthly, 2),
        "total_usd_monthly": round(llm_monthly + review_monthly, 2),
        "total_usd_per_release": round(per_release_usd + review_queue_per_release * review_rate, 5),
    }
