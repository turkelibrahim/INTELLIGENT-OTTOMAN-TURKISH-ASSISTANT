from typing import Optional, List, Dict
from pydantic import BaseModel

class ExportEligibilityReport(BaseModel):
    dataset_id: int
    dataset_name: str
    is_eligible: bool
    rejection_reasons: List[str]
    eligible_document_count: int
    eligible_page_count: int
    eligible_line_count: int
    excluded_line_count: int
    exclusion_details: Dict[str, int] # Reason -> Count

class ExportMetadata(BaseModel):
    dataset_name: str
    dataset_id: int
    export_id: str
    export_version: str
    created_at: str
    created_by: str
    dataset_status: str
    line_count: int
    page_count: int
    document_count: int
    split_counts: Dict[str, int]
    source_db_fingerprint: str
    export_sha256: str
    exporter_version: str
    pagexml_namespace: str
    kraken_version: str
    training_eligible_count: int
    excluded_count: int

class ExportResponse(BaseModel):
    id: int
    dataset_id: int
    export_type: str
    status: str
    output_path: Optional[str]
    output_sha256: Optional[str]
    is_test_export: bool
    created_by: str
    created_at: str
    completed_at: Optional[str]
    error_message: Optional[str]
