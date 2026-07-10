from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Label = Literal["true_pickup", "partial_pickup", "not_pickup", "needs_review"]
Route = Literal["auto_accept", "needs_review", "reject", "suppress"]


class Release(BaseModel):
    release_id: str
    title: str
    body: str
    company: str
    products: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    event: str = ""
    release_date: str
    industry: str = ""


class Article(BaseModel):
    article_id: str
    release_id: str
    url: str
    title: str
    body: str
    outlet: str
    domain: str
    publish_date: Optional[str] = None
    crawl_timestamp: str = ""


class EditorialLabel(BaseModel):
    release_id: str
    article_id: str
    label: Label
    rationale: str
    reviewer: str = "editorial-1"
    confidence: Literal["high", "medium", "low"] = "high"


class Evidence(BaseModel):
    snippet: str
    reason: str


class ScoreBreakdown(BaseModel):
    similarity_score: float
    entity_match_score: float
    novelty_score: float
    source_quality_score: float
    timeliness_score: float
    evidence_score: float


class CostTelemetry(BaseModel):
    embedding_calls: int = 0
    llm_calls: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    estimated_usd: float = 0.0


class AgentReview(BaseModel):
    label: Label
    confidence: Literal["high", "medium", "low"]
    rationale: str
    evidence_faithful: bool
    overclaim_risk: bool
    reviewer: Literal["gemini", "heuristic"]


class PairScore(BaseModel):
    release_id: str
    article_id: str
    url: str
    title: str
    outlet: str
    publish_date: Optional[str]
    breakdown: ScoreBreakdown
    earned_media_score: float
    predicted_label: Label
    confidence_band: Literal["high", "medium", "low"]
    route: Route
    duplicate_of: Optional[str] = None
    evidence: list[Evidence] = Field(default_factory=list)
    agent_review: Optional[AgentReview] = None
    policy_flags: list[str] = Field(default_factory=list)


class EarnedMediaReport(BaseModel):
    release_id: str
    release_title: str
    company: str
    release_date: str
    pairs: list[PairScore]
    accepted_pickups: int
    review_queue: int
    rejected: int
    suppressed: int
    duplicate_adjusted_pickup_count: int
    earned_media_score: float
    cost: CostTelemetry
    scoring_version: str
    generated_at: str
