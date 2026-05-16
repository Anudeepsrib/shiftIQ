from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetails


class HealthResponse(BaseModel):
    status: str
    migrators: List[str]


class AnalyzeRequest(BaseModel):
    path: str = Field(..., description="Path to a file or project directory under an allowed workspace root")
    migration_type: str = Field(default="react-hooks", description="Migration type identifier")
    include_confidence: bool = Field(default=False, description="Include static confidence scoring")


class MigrateRequest(AnalyzeRequest):
    dry_run: bool = Field(default=True, description="If True, preview changes without writing to disk")


class MigrateResultItem(BaseModel):
    file: str
    changed: bool = False
    applied: bool = False
    error: Optional[str] = None


class MigrateResponse(BaseModel):
    migration_type: str
    dry_run: bool
    total_candidates: int
    results: List[MigrateResultItem]


class ComplianceScanRequest(BaseModel):
    path: str = Field(..., description="Path to a project directory under an allowed workspace root")
    include_raw: bool = Field(default=False, description="Include raw sensitive matches if explicitly enabled")


class RollbackRequest(BaseModel):
    path: str = Field(default=".", description="Project path under an allowed workspace root")
    checkpoint_id: str = Field(..., description="Checkpoint ID to restore")
    dry_run: bool = Field(default=False, description="Preview rollback without changing files")


class PluginInfoSchema(BaseModel):
    name: str
    description: str
    version: str
    supported_extensions: List[str]
    tags: List[str]
    source: str
