from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


class CropBBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class KeyResult(BaseModel):
    rank: int
    id_model_ref: Optional[str] = None
    type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    orientation: Optional[str] = None
    head_color: Optional[str] = None
    visual_state: Optional[str] = None
    patentada: bool = False
    compatibility_tags: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    explain_text: str = ""
    crop_bbox: Optional[CropBBox] = None


class ManufacturerHint(BaseModel):
    found: bool
    name: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class DebugInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    processing_time_ms: int = 0
    model_version: str = "unknown"


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    input_id: str
    timestamp: str
    manufacturer_hint: ManufacturerHint
    results: List[KeyResult] = Field(..., min_length=3, max_length=3)
    low_confidence: bool
    high_confidence: bool
    should_store_sample: bool
    storage_probability: float = Field(default=0.75, ge=0.0, le=1.0)
    current_samples_for_candidate: int = 0
    manual_correction_hint: Dict[str, List[str]] = Field(
        default_factory=lambda: {"fields": ["marca", "modelo", "tipo", "orientacion", "ocr_text"]}
    )
    debug: DebugInfo


class FeedbackRequest(BaseModel):
    input_id: str
    selected_id: Optional[str] = None
    chosen_rank: Optional[int] = None
    correction: bool = False
    manual_data: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    status: str
    version: str
    timestamp: str
    model_version: Optional[str] = None
    labels_count: Optional[int] = None
    uptime_s: Optional[int] = None
    region: Optional[str] = None
    build_sha: Optional[str] = None
