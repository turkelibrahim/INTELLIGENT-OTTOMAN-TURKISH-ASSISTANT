import os
from pathlib import Path

root = Path(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")

def w(path, code):
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Created {path}")

# ------------------------------------------------
# EXCEPTIONS
# ------------------------------------------------
exceptions_code = '''from fastapi import HTTPException, status

class AnnotationException(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str, details: list = None, entity_type: str = None, entity_id: int = None):
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": details or [],
                    "entity_type": entity_type,
                    "entity_id": entity_id
                }
            }
        )

def not_found(entity_type: str, entity_id: int):
    return AnnotationException(404, "ANNOTATION_NOT_FOUND", f"{entity_type} {entity_id} not found", entity_type=entity_type, entity_id=entity_id)

def locked_entity(entity_type: str, entity_id: int):
    return AnnotationException(409, "LOCKED_ENTITY", f"{entity_type} {entity_id} is locked", entity_type=entity_type, entity_id=entity_id)
'''
w("backend/app/core/annotation_exceptions.py", exceptions_code)

# ------------------------------------------------
# REPOSITORY
# ------------------------------------------------
repo_code = '''import sqlite3
import json
from typing import List, Dict, Any, Optional

class AnnotationRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def write_audit(self, entity_type: str, entity_id: int, action: str, actor_id: str, success: bool, before: dict = None, after: dict = None, error_code: str = None):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO annotation_audit_events 
            (entity_type, entity_id, action, before_json, after_json, actor_id, success, error_code, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (entity_type, entity_id, action, json.dumps(before) if before else None, json.dumps(after) if after else None, actor_id, success, error_code))
        
    def get_dataset(self, dataset_id: int):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM annotation_datasets WHERE id = ?", (dataset_id,))
        return dict(cur.fetchone()) if cur.fetchone() else None

    def create_dataset(self, data: dict):
        cur = self.conn.cursor()
        keys = list(data.keys())
        keys.append('created_at')
        keys.append('updated_at')
        vals = list(data.values())
        vals.append(None) # datetime created_at logic can be in DB trigger or explicitly passed, we pass explicit
        
        cols = ", ".join(data.keys()) + ", created_at, updated_at"
        qmarks = ", ".join(["?"] * (len(data) + 2))
        
        query = f"INSERT INTO annotation_datasets ({cols}) VALUES ({qmarks})"
        values = list(data.values()) + ["datetime('now')", "datetime('now')"]
        
        # Real insert uses standard bind
        real_qmarks = ", ".join(["?"] * len(data))
        real_query = f"INSERT INTO annotation_datasets ({', '.join(data.keys())}, created_at, updated_at) VALUES ({real_qmarks}, datetime('now'), datetime('now'))"
        
        cur.execute(real_query, tuple(data.values()))
        return cur.lastrowid
        
    def get_line(self, line_id: int):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM annotation_lines WHERE id = ?", (line_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_line_status(self, line_id: int, new_status: str, fields: dict = None):
        cur = self.conn.cursor()
        if not fields:
            fields = {}
        fields["status"] = new_status
        fields["updated_at"] = "datetime('now')"
        
        set_clause = []
        vals = []
        for k, v in fields.items():
            if v == "datetime('now')":
                set_clause.append(f"{k} = datetime('now')")
            else:
                set_clause.append(f"{k} = ?")
                vals.append(v)
        vals.append(line_id)
        
        query = f"UPDATE annotation_lines SET {', '.join(set_clause)} WHERE id = ?"
        cur.execute(query, tuple(vals))

    def get_dataset_progress(self, dataset_id: int):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 
                d.id as dataset_id, d.name as dataset_name, d.target_verified_lines,
                (SELECT count(*) FROM annotation_documents WHERE dataset_id = d.id) as total_documents,
                (SELECT count(*) FROM annotation_pages p JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id) as total_pages,
                (SELECT count(*) FROM annotation_regions r JOIN annotation_pages p ON r.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id) as total_regions,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id) as total_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.status='DRAFT') as draft_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.status='AUTO_PREANNOTATED') as auto_preannotated_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.status='IN_REVIEW') as in_review_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.status='NEEDS_CORRECTION') as needs_correction_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.status='HUMAN_VERIFIED') as human_verified_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.status='SECOND_REVIEW_VERIFIED') as double_reviewed_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.status='LOCKED') as locked_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.status='REJECTED') as rejected_lines,
                (SELECT count(*) FROM annotation_lines l JOIN annotation_pages p ON l.page_id = p.id JOIN annotation_documents doc ON p.document_id = doc.id WHERE doc.dataset_id = d.id AND l.training_eligible = 1 AND l.status IN ('SECOND_REVIEW_VERIFIED', 'LOCKED') AND d.is_test_data = 0 AND d.legacy_dataset_id IS NOT 2) as verified_training_eligible_lines
            FROM annotation_datasets d
            WHERE d.id = ?
        """, (dataset_id,))
        row = cur.fetchone()
        if not row: return None
        res = dict(row)
        res["remaining_to_target"] = max(0, res["target_verified_lines"] - res["verified_training_eligible_lines"])
        return res
'''
w("backend/app/repositories/annotation_repository.py", repo_code)

# ------------------------------------------------
# SERVICE
# ------------------------------------------------
svc_code = '''import sqlite3
import unicodedata
from app.repositories.annotation_repository import AnnotationRepository
from app.core.annotation_exceptions import AnnotationException, not_found, locked_entity

class AnnotationService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.repo = AnnotationRepository(conn)

    def _normalize_transcription(self, text: str) -> str:
        if not text: return text
        return unicodedata.normalize('NFC', text)

    def change_line_status(self, line_id: int, new_status: str, actor_id: str):
        line = self.repo.get_line(line_id)
        if not line: raise not_found("LINE", line_id)
        
        if line.get("status") == "LOCKED":
            self.repo.write_audit("LINE", line_id, "STATUS_CHANGE", actor_id, False, line, error_code="LOCKED_ENTITY")
            raise locked_entity("LINE", line_id)
            
        allowed = {
            "DRAFT": ["IN_REVIEW", "REJECTED"],
            "AUTO_PREANNOTATED": ["IN_REVIEW", "REJECTED"],
            "IN_REVIEW": ["NEEDS_CORRECTION", "HUMAN_VERIFIED", "REJECTED"],
            "NEEDS_CORRECTION": ["IN_REVIEW", "REJECTED"],
            "HUMAN_VERIFIED": ["SECOND_REVIEW_VERIFIED", "REJECTED"],
            "SECOND_REVIEW_VERIFIED": ["LOCKED", "REJECTED"],
            "REJECTED": []
        }
        
        current = line.get("status", "DRAFT")
        if new_status not in allowed.get(current, []):
            self.repo.write_audit("LINE", line_id, "STATUS_CHANGE", actor_id, False, line, error_code="INVALID_STATE_TRANSITION")
            raise AnnotationException(409, "INVALID_STATE_TRANSITION", f"Cannot transition from {current} to {new_status}")
            
        self.repo.update_line_status(line_id, new_status)
        self.repo.write_audit("LINE", line_id, "STATUS_CHANGE", actor_id, True, line, {"status": new_status})

    def human_verify(self, line_id: int, actor_id: str):
        line = self.repo.get_line(line_id)
        if not line: raise not_found("LINE", line_id)
        
        if not line.get("transcription") or not line.get("bbox_json"):
            self.repo.write_audit("LINE", line_id, "HUMAN_VERIFY", actor_id, False, line, error_code="VERIFICATION_REQUIREMENTS_NOT_MET")
            raise AnnotationException(422, "VERIFICATION_REQUIREMENTS_NOT_MET", "Missing required fields for verification")
            
        try:
            self.change_line_status(line_id, "HUMAN_VERIFIED", actor_id)
            fields = {
                "human_verified": 1,
                "bbox_verified": 1,
                "transcription_verified": 1,
                "reviewed_by": actor_id,
                "reviewed_at": "datetime('now')",
                "normalized_transcription": self._normalize_transcription(line.get("transcription"))
            }
            self.repo.update_line_status(line_id, "HUMAN_VERIFIED", fields)
            self.repo.write_audit("LINE", line_id, "HUMAN_VERIFY", actor_id, True, line, fields)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def second_review(self, line_id: int, actor_id: str, decision: str):
        line = self.repo.get_line(line_id)
        if not line: raise not_found("LINE", line_id)
        
        if line.get("reviewed_by") == actor_id:
            self.repo.write_audit("LINE", line_id, "SECOND_REVIEW", actor_id, False, line, error_code="SAME_REVIEWER_NOT_ALLOWED")
            raise AnnotationException(409, "SAME_REVIEWER_NOT_ALLOWED", "Second reviewer cannot be the same as first reviewer")
            
        try:
            if decision == "APPROVED":
                self.change_line_status(line_id, "SECOND_REVIEW_VERIFIED", actor_id)
                self.repo.update_line_status(line_id, "SECOND_REVIEW_VERIFIED", {"second_reviewer": actor_id, "second_reviewed_at": "datetime('now')"})
            else:
                self.change_line_status(line_id, "NEEDS_CORRECTION", actor_id)
            self.repo.write_audit("LINE", line_id, "SECOND_REVIEW", actor_id, True, line, {"decision": decision})
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
            
    def get_progress(self, dataset_id: int):
        return self.repo.get_dataset_progress(dataset_id)
'''
w("backend/app/services/annotation_service.py", svc_code)

# ------------------------------------------------
# ROUTER
# ------------------------------------------------
router_code = '''import sqlite3
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.schemas.annotation import (
    AnnotationDatasetCreate, AnnotationDatasetResponse, AnnotationDatasetProgressResponse,
    HumanVerificationRequest, SecondReviewRequest
)
from app.services.annotation_service import AnnotationService
from app.db.database import get_db

router = APIRouter()

def get_service(db = Depends(get_db)):
    # Assuming get_db yields a raw sqlite connection or sqlalchemy session
    # If sqlalchemy, we get the raw DBAPI connection via db.connection().connection 
    # For safety in tests, we expect raw sqlite3.Connection here via override
    conn = db
    if not isinstance(conn, sqlite3.Connection):
        # sqlalchemy wrapper extract
        conn = db.connection().connection.connection
    return AnnotationService(conn)

def get_actor_id(x_actor_id: Optional[str] = Header(None)):
    if not x_actor_id:
        return "system"
    return x_actor_id

@router.get("/datasets/{dataset_id}/progress", response_model=AnnotationDatasetProgressResponse)
def get_dataset_progress(dataset_id: int, svc: AnnotationService = Depends(get_service)):
    prog = svc.get_progress(dataset_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return prog

@router.post("/lines/{line_id}/verify")
def human_verify_line(line_id: int, req: HumanVerificationRequest, svc: AnnotationService = Depends(get_service), actor_id: str = Depends(get_actor_id)):
    svc.human_verify(line_id, actor_id)
    return {"status": "success"}

@router.post("/lines/{line_id}/second-review")
def second_review_line(line_id: int, req: SecondReviewRequest, svc: AnnotationService = Depends(get_service), actor_id: str = Depends(get_actor_id)):
    svc.second_review(line_id, actor_id, req.decision)
    return {"status": "success"}
'''
w("backend/app/api/routes/annotation.py", router_code)
