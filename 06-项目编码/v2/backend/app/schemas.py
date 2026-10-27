from __future__ import annotations
from typing import Literal, Optional

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class ProjectIn(BaseModel):
    name: str
    company_business: Optional[str] = None
    project_background: Optional[str] = None
    progress: Optional[str] = None
    stage: Optional[str] = None
    business_goals: Optional[str] = None
    north_star_metric: Optional[str] = None
    business_process: Optional[str] = None
    target_users: Optional[str] = None
    market_context: Optional[str] = None
    constraints: Optional[str] = None
    owner_id: Optional[str] = None


class RequirementIn(BaseModel):
    project_id: str
    title: str
    original: str
    scenario: Optional[str] = None
    problem: Optional[str] = None
    impact: Optional[str] = None


class RequirementPatch(BaseModel):
    title: Optional[str] = None
    original: Optional[str] = None
    scenario: Optional[str] = None
    authenticity: Optional[Literal["pending", "supported", "contradicted"]] = None
    business_relevance: Optional[Literal["unknown", "direct", "indirect"]] = None
    priority: Optional[Literal["unassessed", "high", "medium", "low"]] = None
    status: Optional[Literal["draft", "clarifying", "review", "pooled", "deferred", "rejected"]] = None
    depth: Optional[int] = Field(None, ge=0, le=6)
    scope_score: Optional[int] = Field(None, ge=0, le=5)
    intensity_score: Optional[int] = Field(None, ge=0, le=5)
    value_score: Optional[int] = Field(None, ge=0, le=5)
    cost_score: Optional[int] = Field(None, ge=0, le=5)
    priority_reason: Optional[str] = None
    problem: Optional[str] = None
    impact: Optional[str] = None
    review_reason: Optional[str] = None


class ClarificationIn(BaseModel):
    question: str
    answer: Optional[str] = None


class EvidenceIn(BaseModel):
    title: str
    content: str
    kind: Optional[str] = None
    source: Optional[str] = None
    supports: Optional[Literal["support", "contradict"]] = "support"


class PublicRequirementIn(BaseModel):
    title: str
    original: str
    scenario: Optional[str] = None
    problem: Optional[str] = None
    impact: Optional[str] = None
    submitter_name: Optional[str] = None
    submitter_department: Optional[str] = None


class UserIn(BaseModel):
    username: str
    name: str
    department_id: Optional[str] = None
    role_ids: list[str] = Field(default_factory=lambda: ["pm"])
    status: Literal["active", "disabled"] = "active"
    password: Optional[str] = None


class UserPatch(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    department_id: Optional[str] = None
    role_ids: Optional[list[str]] = None
    status: Optional[Literal["active", "disabled"]] = None
    password: Optional[str] = None
