"""
Cross-service contracts. Any service that produces or consumes one of
these objects imports from here rather than redefining its own shape —
this is what lets Phase 5's scanner, Phase 7's planner, and Phase 8's
patch generator be built independently without drifting apart.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class DetectedDepedency(BaseModel):
    framework : str
    version : str
    ecosystem : Literal['npm','pip']
    source_file : str

class ApiStatus(str,Enum):
    RECOMMENDED = "recommended"
    DEPRECATED = 'deprecated'
    REMOVED = 'removed'


class ChangeType(str, Enum):
    DEPRECATED = "DEPRECATED"
    REMOVED = "REMOVED"
    RENAMED = "RENAMED"
    SIGNATURE_CHANGED = "SIGNATURE_CHANGED"
    BEHAVIOR_CHANGED = "BEHAVIOR_CHANGED"
    CONFIG_CHANGED = "CONFIG_CHANGED"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"



class KnowledgeGraphEntry(BaseModel):
    framework: str
    introduced_in: str | None = None
    deprecated_in: str | None = None
    removed_in: str | None = None
    api_name: str
    status: ApiStatus
    replacement: str | None = None
    change_type: ChangeType
    severity: Severity
    detection_pattern: str          # regex or tree-sitter query used by the analyzer
    migration_hint: str             # short human-readable instruction
    doc_url: str | None = None


# ---------------------------------------------------------------- Phase 5/6
class Finding(BaseModel):
    file_path: str
    line: int
    api_name: str
    matched_text: str
    change_type: ChangeType
    severity: Severity
    replacement: str | None
    migration_hint: str
    doc_url: str | None = None


class RepoScanResult(BaseModel):
    repo_url: str
    commit_sha: str | None
    framework: str
    detected_version: str
    files_scanned: int
    findings: list[Finding]
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------- Phase 7
class PlannedChange(BaseModel):
    api: str
    replacement: str | None
    risk: Severity
    files: list[str]
    migration_type: ChangeType
    automatic: bool   # can the template/LLM engine generate this patch automatically?

class MigrationPlan(BaseModel):
    source_version:str
    target_version:str

    framework:str
    changes:list[PlannedChange]

    @property
    def automatic_count(self) -> int:
        return sum(1 for c in self.changes if c.automatic)

    @property
    def manual_count(self) -> int : 
        return len(self.changes) - self.automatic_count



# ---------------------------------------------------------------- Phase 8
class Patch(BaseModel):
    file_path: str
    diff: str                  # unified diff format, for human review
    new_content: str | None = None  # full transformed file content; None when skipped (manual review)
    explanation: str
    source: Literal["template", "llm"]
    doc_url: str | None = None


# ---------------------------------------------------------------- Phase 9
class VerificationStage(BaseModel):
    name: Literal["install", "lint", "typecheck", "build", "test"]
    passed: bool
    output_tail: str           # last N lines of stdout/stderr, for debugging


class VerificationResult(BaseModel):
    passed: bool
    stages: list[VerificationStage]
    attempt: int


# ---------------------------------------------------------------- Phase 9 (confidence)
class ConfidenceBreakdown(BaseModel):
    official_source: float
    version_certainty: float
    graph_agreement: float
    static_analysis: float
    rule_match: float
    build_result: float
    tests: float

    @computed_field  # type: ignore[misc]
    @property
    def total(self) -> float:
        return round(
            self.official_source + self.version_certainty + self.graph_agreement
            + self.static_analysis + self.rule_match + self.build_result + self.tests,
            1,
        )


# ---------------------------------------------------------------- Final report
class MigrationReport(BaseModel):
    repo_url: str
    framework: str
    source_version: str
    target_version: str
    files_analyzed: int
    plan: MigrationPlan
    patches: list[Patch]
    verification: VerificationResult
    confidence: ConfidenceBreakdown
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
