"""
Orchestrator Layer — Pydantic Schemas
All data contracts for the pipeline are defined here.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ─── Status Enums ─────────────────────────────────────────────────────────────

class ModelStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    EXPERIMENTAL = "EXPERIMENTAL"


class StepStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class InvestigationStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


# ─── Modality & Evidence Schemas ──────────────────────────────────────────────

class ModalityEnum(str, Enum):
    OPTICAL_RGB = "OPTICAL_RGB"
    OPTICAL_MULTISPECTRAL = "OPTICAL_MULTISPECTRAL"
    SAR = "SAR"
    PANCHROMATIC = "PANCHROMATIC"
    DEM = "DEM"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class ModalityResult(BaseModel):
    modality: ModalityEnum
    confidence: float
    evidence: list[str]


class ConfidenceStatus(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    CALIBRATED_PROBABILITY = "CALIBRATED_PROBABILITY"
    QUALITATIVE = "QUALITATIVE"
    UNVERIFIED = "UNVERIFIED"
    FAILED = "FAILED"


class EvidenceStrength(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_confidence: float | None = None
    data_quality: str | None = None
    spatial_consistency: str | None = None
    evidence_strength: str | None = None
    confidence_status: ConfidenceStatus


# ─── Input Schemas ────────────────────────────────────────────────────────────

class ImageManifest(BaseModel):
    """Metadata about a single uploaded image."""
    file_id: str
    filename: str
    file_path: str
    format: str
    width_px: int
    height_px: int
    band_count: int
    dtype: str
    crs_wkt: str | None = None
    crs_epsg: int | None = None
    affine_transform: list[float] | None = None
    bounds: dict | None = None
    gsd_x: float | None = None
    gsd_y: float | None = None
    nodata_value: float | None = None
    band_descriptions: list[str] = Field(default_factory=list)
    band_wavelengths: list[float] = Field(default_factory=list)
    modality: ModalityResult
    sensor: str | None = None
    acquisition_date: datetime | None = None
    is_geospatial: bool
    quality_flags: list[str] = Field(default_factory=list)
    validation_status: str | None = None


class InputManifest(BaseModel):
    """Validated, enriched description of a user's investigation request."""
    query: str
    images: list[ImageManifest]
    image_count: int = Field(default=0)
    is_bitemporal: bool = Field(default=False)
    is_cross_modal: bool = Field(default=False)

    def model_post_init(self, __context: Any) -> None:
        self.image_count = len(self.images)
        modalities = [img.modality.modality for img in self.images]
        unique_modalities = set(modalities)
        
        self.is_bitemporal = (
            self.image_count == 2 and len(unique_modalities) == 1
        )
        self.is_cross_modal = (
            self.image_count == 2 and len(unique_modalities) == 2
        )


class CompatibilityReport(BaseModel):
    is_compatible: bool
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    resolution_ratio: float | None = None
    overlap_percentage: float | None = None


# ─── Plan Schemas ─────────────────────────────────────────────────────────────

class TaskType(str, Enum):
    SINGLE_IMAGE_VQA = "single_image_vqa"
    SINGLE_IMAGE_CAPTION = "single_image_caption"
    SINGLE_IMAGE_GROUNDING = "single_image_grounding"
    SCENE_CLASSIFICATION = "scene_classification"
    CHANGE_DETECTION = "change_detection"
    CHANGE_VQA = "change_vqa"
    CROSS_MODAL_ANALYSIS = "cross_modal_analysis"
    GEOSPATIAL_MEASUREMENT = "geospatial_measurement"
    COMPOSITE = "composite"
    UNSUPPORTED = "unsupported"


class PlanStep(BaseModel):
    step_id: str
    tool_id: str
    task_type: str
    description: str
    depends_on: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    image_index: int | None = None


class InvestigationPlan(BaseModel):
    plan_id: str
    query: str
    task_classification: str
    plan_rationale: str
    steps: list[PlanStep]
    estimated_duration_seconds: int = 60


# ─── Execution Schemas ────────────────────────────────────────────────────────

class ExecutedStep(BaseModel):
    step_id: str
    tool_id: str
    status: StepStatus
    input_summary: str
    output_summary: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    retry_count: int = 0
    output_type: str = "text"
    raw_output: Any = None
    confidence: float | None = None
    strength: EvidenceStrength | None = None


# ─── Evidence Schemas ─────────────────────────────────────────────────────────

class FindingType(str, Enum):
    TEXT = "text"
    MEASUREMENT = "measurement"
    CLASSIFICATION = "classification"
    MASK = "mask"
    BBOX = "bbox"
    CHANGE_MAP = "change_map"
    RASTER_STATS = "raster_stats"


class EvidenceFinding(BaseModel):
    model_config = {"protected_namespaces": ()}
    finding_id: str
    type: FindingType
    value: Any
    source_model: str
    strength: EvidenceStrength | None = None
    visual_evidence: str | None = None
    visual_evidence_path: str | None = None
    provenance: str
    source_step_id: str | None = None
    input_file_ids: list[str] = Field(default_factory=list)
    spatial_reference: str | None = None
    calculation_metadata: dict[str, Any] | None = None
    method: str | None = None
    model_version: str | None = None


class ConflictRecord(BaseModel):
    finding_ids: list[str]
    description: str
    impact: str | None = None


class ExecutionTrace(BaseModel):
    trace_id: str
    timestamp_start: datetime
    timestamp_end: datetime | None = None
    plan: InvestigationPlan
    executed_steps: list[ExecutedStep]
    steps_planned: int = 0
    steps_executed: int = 0
    steps_succeeded: int = 0
    steps_failed: int = 0


class EvidencePackage(BaseModel):
    request_id: str
    query: str
    findings: list[EvidenceFinding]
    conflicts: list[ConflictRecord] = Field(default_factory=list)
    overall_confidence: float | str = "MEDIUM"
    data_quality_flags: list[str] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)
    models_used: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    total_inference_time_ms: int = 0
    trace: ExecutionTrace


# ─── Report Schemas ───────────────────────────────────────────────────────────

class Report(BaseModel):
    """Synthesised investigation report with 13-section structure."""
    executive_summary: str | None = None
    narrative: str
    observations: list[str] = Field(default_factory=list)
    spatial_findings: str | None = None
    temporal_findings: str | None = None
    sar_evidence: str | None = None
    cross_modal_analysis: str | None = None
    methodology: str
    limitations: list[str]
    confidence_summary: str
    data_quality: str | None = None
    conflicts_identified: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    recommendations: str | None = None


# ─── Response Schemas ─────────────────────────────────────────────────────────

class InvestigationResponse(BaseModel):
    job_id: str
    status: InvestigationStatus
    report: Report
    evidence: list[EvidenceFinding]
    trace: ExecutionTrace
