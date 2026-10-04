import sqlite3
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime

class ExportRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_dataset(self, dataset_id: int) -> dict:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, status, is_test_data, archived, training_eligible FROM annotation_datasets WHERE id = ?", (dataset_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "status": row[2],
            "is_test_data": bool(row[3]),
            "archived": bool(row[4]),
            "training_eligible": bool(row[5])
        }

    def get_eligible_lines(self, dataset_id: int, is_test_export: bool) -> Tuple[List[dict], Dict[str, int]]:
        cur = self.conn.cursor()
        
        # Get all lines for this dataset
        query = """
            SELECT 
                l.id, l.page_id, l.region_id, l.line_order, l.bbox_json, l.baseline_json,
                l.transcription, l.normalized_transcription, l.status,
                l.human_verified, l.bbox_verified, l.baseline_verified, l.reading_order_verified,
                l.transcription_verified, l.duplicate_checked, l.training_eligible,
                l.reviewed_by, l.second_reviewer, l.split_name,
                p.document_id, p.status as page_status, p.human_verified as page_human_verified, p.reading_order_verified as page_ro_verified,
                d.license_status, d.license_reference, d.source_sha256
            FROM annotation_lines l
            JOIN annotation_pages p ON l.page_id = p.id
            JOIN annotation_documents d ON p.document_id = d.id
            WHERE d.dataset_id = ?
        """
        cur.execute(query, (dataset_id,))
        rows = cur.fetchall()
        
        eligible_lines = []
        exclusion_counts = {
            "document_license_rejected": 0,
            "document_license_missing_reference": 0,
            "document_missing_sha256": 0,
            "page_not_locked": 0,
            "page_not_verified": 0,
            "line_not_locked": 0,
            "line_not_verified": 0,
            "line_missing_normalized": 0,
            "line_missing_reviewers": 0,
            "line_same_reviewer": 0,
            "line_not_training_eligible": 0,
            "line_rejected_or_draft": 0
        }
        
        for row in rows:
            line = {
                "id": row[0], "page_id": row[1], "region_id": row[2], "line_order": row[3],
                "bbox_json": json.loads(row[4]) if row[4] else None,
                "baseline_json": json.loads(row[5]) if row[5] else None,
                "transcription": row[6], "normalized_transcription": row[7], "status": row[8],
                "human_verified": bool(row[9]), "bbox_verified": bool(row[10]),
                "baseline_verified": bool(row[11]), "reading_order_verified": bool(row[12]),
                "transcription_verified": bool(row[13]), "duplicate_checked": bool(row[14]),
                "training_eligible": bool(row[15]),
                "reviewed_by": row[16], "second_reviewer": row[17], "split_name": row[18],
                "document_id": row[19], "page_status": row[20], "page_human_verified": bool(row[21]),
                "page_ro_verified": bool(row[22]),
                "doc_license_status": row[23], "doc_license_reference": row[24], "doc_source_sha256": row[25]
            }
            
            # Document Checks
            if line["doc_license_status"] != 'APPROVED':
                exclusion_counts["document_license_rejected"] += 1
                continue
            if not line["doc_license_reference"]:
                exclusion_counts["document_license_missing_reference"] += 1
                continue
            if not line["doc_source_sha256"]:
                exclusion_counts["document_missing_sha256"] += 1
                continue
                
            # Page Checks
            if line["page_status"] != 'LOCKED':
                exclusion_counts["page_not_locked"] += 1
                continue
            if not line["page_human_verified"] or not line["page_ro_verified"]:
                exclusion_counts["page_not_verified"] += 1
                continue
                
            # Line Checks
            if line["status"] in ('DRAFT', 'REJECTED', 'AUTO_PREANNOTATED'):
                exclusion_counts["line_rejected_or_draft"] += 1
                continue
            if line["status"] != 'LOCKED':
                exclusion_counts["line_not_locked"] += 1
                continue
            
            if not (line["human_verified"] and line["bbox_verified"] and line["baseline_verified"] and 
                    line["reading_order_verified"] and line["transcription_verified"] and line["duplicate_checked"]):
                exclusion_counts["line_not_verified"] += 1
                continue
                
            if not is_test_export and not line["training_eligible"]:
                exclusion_counts["line_not_training_eligible"] += 1
                continue
                
            if not line["normalized_transcription"] or line["normalized_transcription"].strip() == "":
                exclusion_counts["line_missing_normalized"] += 1
                continue
                
            if not line["reviewed_by"] or not line["second_reviewer"]:
                exclusion_counts["line_missing_reviewers"] += 1
                continue
                
            if line["reviewed_by"] == line["second_reviewer"]:
                exclusion_counts["line_same_reviewer"] += 1
                continue
                
            eligible_lines.append(line)
            
        return eligible_lines, {k:v for k,v in exclusion_counts.items() if v > 0}

    def create_export_record(self, dataset_id: int, export_type: str, output_path: str, output_sha256: str, is_test_export: bool, user_id: str) -> int:
        cur = self.conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute("""
            INSERT INTO annotation_exports 
            (dataset_id, export_type, status, output_path, output_sha256, is_test_export, created_by, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dataset_id, export_type, 'COMPLETED', output_path, output_sha256, is_test_export, user_id, now, now))
        self.conn.commit()
        return cur.lastrowid
