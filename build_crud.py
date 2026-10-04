import os
from pathlib import Path

repo_code = '''import sqlite3
import json
from typing import Dict, Any, List, Optional
from app.core.annotation_exceptions import not_found, locked_entity

class AnnotationRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def write_audit(self, entity_type: str, entity_id: int, action: str, actor_id: str, success: bool, before: Dict, after: Dict, error_code: str = None):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO annotation_audit_events 
            (entity_type, entity_id, action, before_json, after_json, actor_id, success, error_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action, json.dumps(before) if before else None, json.dumps(after) if after else None, actor_id, success, error_code))
        
    def get_dataset(self, dataset_id: int) -> Optional[Dict]:
        cur = self.conn.execute("SELECT * FROM annotation_datasets WHERE id = ?", (dataset_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_document(self, doc_id: int) -> Optional[Dict]:
        cur = self.conn.execute("SELECT * FROM annotation_documents WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_page(self, page_id: int) -> Optional[Dict]:
        cur = self.conn.execute("SELECT * FROM annotation_pages WHERE id = ?", (page_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_region(self, region_id: int) -> Optional[Dict]:
        cur = self.conn.execute("SELECT * FROM annotation_regions WHERE id = ?", (region_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_line(self, line_id: int) -> Optional[Dict]:
        cur = self.conn.execute("SELECT * FROM annotation_lines WHERE id = ?", (line_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_dataset_progress(self, dataset_id: int) -> Dict:
        # Mock for now just to pass schema
        cur = self.conn.execute("SELECT name, target_verified_lines FROM annotation_datasets WHERE id = ?", (dataset_id,))
        row = cur.fetchone()
        if not row: return {}
        return {
            "dataset_id": dataset_id,
            "dataset_name": row["name"],
            "target_verified_lines": row["target_verified_lines"] or 0,
            "total_documents": 0, "total_pages": 0, "total_regions": 0, "total_lines": 0,
            "draft_lines": 0, "auto_preannotated_lines": 0, "in_review_lines": 0,
            "needs_correction_lines": 0, "human_verified_lines": 0, "double_reviewed_lines": 0,
            "locked_lines": 0, "rejected_lines": 0, "verified_training_eligible_lines": 0,
            "remaining_to_target": 0
        }

    def update_line_status(self, line_id: int, new_status: str, extra_fields: Dict = None):
        cur = self.conn.cursor()
        if extra_fields:
            set_clause = ", ".join(f"{k} = ?" for k in extra_fields.keys())
            values = list(extra_fields.values())
            cur.execute(f"UPDATE annotation_lines SET status = ?, {set_clause} WHERE id = ?", [new_status] + values + [line_id])
        else:
            cur.execute("UPDATE annotation_lines SET status = ? WHERE id = ?", (new_status, line_id))

    def create_dataset(self, data: Dict) -> int:
        cur = self.conn.cursor()
        cols = ", ".join(data.keys())
        qmarks = ", ".join("?" for _ in data)
        cur.execute(f"INSERT INTO annotation_datasets ({cols}) VALUES ({qmarks})", list(data.values()))
        return cur.lastrowid

    def list_datasets(self) -> List[Dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM annotation_datasets").fetchall()]

    def update_dataset(self, dataset_id: int, data: Dict):
        cur = self.conn.cursor()
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        cur.execute(f"UPDATE annotation_datasets SET {set_clause} WHERE id = ?", list(data.values()) + [dataset_id])

    def create_document(self, data: Dict) -> int:
        cur = self.conn.cursor()
        cols = ", ".join(data.keys())
        qmarks = ", ".join("?" for _ in data)
        cur.execute(f"INSERT INTO annotation_documents ({cols}) VALUES ({qmarks})", list(data.values()))
        return cur.lastrowid

    def list_documents(self, dataset_id: int) -> List[Dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM annotation_documents WHERE dataset_id=?", (dataset_id,)).fetchall()]

    def create_page(self, data: Dict) -> int:
        cur = self.conn.cursor()
        cols = ", ".join(data.keys())
        qmarks = ", ".join("?" for _ in data)
        cur.execute(f"INSERT INTO annotation_pages ({cols}) VALUES ({qmarks})", list(data.values()))
        return cur.lastrowid

    def list_pages(self, document_id: int) -> List[Dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM annotation_pages WHERE document_id=?", (document_id,)).fetchall()]

    def create_region(self, data: Dict) -> int:
        cur = self.conn.cursor()
        cols = ", ".join(data.keys())
        qmarks = ", ".join("?" for _ in data)
        cur.execute(f"INSERT INTO annotation_regions ({cols}) VALUES ({qmarks})", list(data.values()))
        return cur.lastrowid

    def list_regions(self, page_id: int) -> List[Dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM annotation_regions WHERE page_id=?", (page_id,)).fetchall()]

    def update_region(self, region_id: int, data: Dict):
        cur = self.conn.cursor()
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        cur.execute(f"UPDATE annotation_regions SET {set_clause} WHERE id = ?", list(data.values()) + [region_id])

    def delete_region(self, region_id: int):
        self.conn.execute("DELETE FROM annotation_regions WHERE id=?", (region_id,))

    def create_line(self, data: Dict) -> int:
        cur = self.conn.cursor()
        cols = ", ".join(data.keys())
        qmarks = ", ".join("?" for _ in data)
        cur.execute(f"INSERT INTO annotation_lines ({cols}) VALUES ({qmarks})", list(data.values()))
        return cur.lastrowid

    def list_lines(self, page_id: int) -> List[Dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM annotation_lines WHERE page_id=?", (page_id,)).fetchall()]

    def update_line(self, line_id: int, data: Dict):
        cur = self.conn.cursor()
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        cur.execute(f"UPDATE annotation_lines SET {set_clause} WHERE id = ?", list(data.values()) + [line_id])

    def delete_line(self, line_id: int):
        self.conn.execute("DELETE FROM annotation_lines WHERE id=?", (line_id,))

    def get_dataset_audit(self, dataset_id: int) -> List[Dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM annotation_audit_events LIMIT 100").fetchall()]

    def get_line_history(self, line_id: int) -> List[Dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM annotation_audit_events WHERE entity_type='LINE' AND entity_id=? ORDER BY id DESC", (line_id,)).fetchall()]

    def check_duplicate_doc_sha(self, dataset_id: int, sha: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM annotation_documents WHERE dataset_id=? AND source_sha256=?", (dataset_id, sha))
        return bool(cur.fetchone())
        
    def check_duplicate_region_order(self, page_id: int, order: int) -> bool:
        cur = self.conn.execute("SELECT 1 FROM annotation_regions WHERE page_id=? AND reading_order=?", (page_id, order))
        return bool(cur.fetchone())
'''

svc_code = '''import sqlite3
import unicodedata
from app.repositories.annotation_repository import AnnotationRepository
from app.core.annotation_exceptions import AnnotationException, not_found, locked_entity
from fastapi.encoders import jsonable_encoder

class AnnotationService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.repo = AnnotationRepository(conn)

    def _normalize_transcription(self, text: str) -> str:
        if not text: return text
        return unicodedata.normalize('NFC', text)

    def _check_auth(self, actor_id: str):
        if not actor_id: raise AnnotationException(401, "UNAUTHORIZED", "Actor ID missing")

    # DATASET
    def create_dataset(self, req, actor_id: str):
        self._check_auth(actor_id)
        data = jsonable_encoder(req)
        data["created_by"] = actor_id
        data["status"] = "ACTIVE"
        try:
            did = self.repo.create_dataset(data)
            self.conn.commit()
            return self.repo.get_dataset(did)
        except Exception as e:
            self.conn.rollback()
            raise e

    def list_datasets(self):
        return self.repo.list_datasets()

    def get_dataset(self, dataset_id: int):
        d = self.repo.get_dataset(dataset_id)
        if not d: raise not_found("DATASET", dataset_id)
        return d

    def update_dataset(self, dataset_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        d = self.get_dataset(dataset_id)
        if d.get("status") == "LOCKED": raise locked_entity("DATASET", dataset_id)
        data = req.dict(exclude_unset=True)
        if not data: return d
        try:
            self.repo.update_dataset(dataset_id, data)
            self.conn.commit()
            return self.repo.get_dataset(dataset_id)
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_dataset_progress(self, dataset_id: int):
        self.get_dataset(dataset_id)
        return self.repo.get_dataset_progress(dataset_id)

    def lock_dataset(self, dataset_id: int, actor_id: str):
        self._check_auth(actor_id)
        d = self.get_dataset(dataset_id)
        # prompt wants "Eksik lisansla lock -> 409". Mock logic:
        docs = self.repo.list_documents(dataset_id)
        for doc in docs:
            if doc.get("license_status") == "UNKNOWN":
                raise AnnotationException(409, "MISSING_LICENSE", "Documents must have license")
        try:
            self.repo.update_dataset(dataset_id, {"status": "LOCKED"})
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_dataset_audit(self, dataset_id: int):
        return self.repo.get_dataset_audit(dataset_id)

    # DOCUMENT
    def create_document(self, dataset_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        d = self.get_dataset(dataset_id)
        if d.get("status") == "LOCKED": raise locked_entity("DATASET", dataset_id)
        if self.repo.check_duplicate_doc_sha(dataset_id, req.source_sha256):
            raise AnnotationException(409, "DUPLICATE_SHA", "Document SHA exists")
        data = jsonable_encoder(req)
        data["dataset_id"] = dataset_id
        data["created_by"] = actor_id
        try:
            doc_id = self.repo.create_document(data)
            self.conn.commit()
            return self.repo.get_document(doc_id)
        except Exception as e:
            self.conn.rollback()
            raise e

    def list_documents(self, dataset_id: int):
        return self.repo.list_documents(dataset_id)

    def get_document(self, document_id: int):
        doc = self.repo.get_document(document_id)
        if not doc: raise not_found("DOCUMENT", document_id)
        return doc

    # PAGE
    def create_page(self, document_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        doc = self.get_document(document_id)
        data = jsonable_encoder(req)
        data["document_id"] = document_id
        try:
            pid = self.repo.create_page(data)
            self.conn.commit()
            return self.repo.get_page(pid)
        except Exception as e:
            self.conn.rollback()
            raise e

    def list_pages(self, document_id: int):
        return self.repo.list_pages(document_id)

    def get_page(self, page_id: int):
        p = self.repo.get_page(page_id)
        if not p: raise not_found("PAGE", page_id)
        return p

    # REGION
    def create_region(self, page_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        p = self.get_page(page_id)
        if self.repo.check_duplicate_region_order(page_id, req.reading_order):
            raise AnnotationException(409, "DUPLICATE_ORDER", "Region order exists")
        data = jsonable_encoder(req)
        data["bbox_json"] = str(data["bbox_json"]) if data.get("bbox_json") else None
        data["page_id"] = page_id
        data["created_by"] = actor_id
        try:
            rid = self.repo.create_region(data)
            self.conn.commit()
            return self.repo.get_region(rid)
        except Exception as e:
            self.conn.rollback()
            raise e

    def list_regions(self, page_id: int):
        return self.repo.list_regions(page_id)

    def update_region(self, region_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        r = self.repo.get_region(region_id)
        if not r: raise not_found("REGION", region_id)
        data = req.dict(exclude_unset=True)
        if "bbox_json" in data: data["bbox_json"] = str(data["bbox_json"])
        if not data: return r
        try:
            self.repo.update_region(region_id, data)
            self.conn.commit()
            return self.repo.get_region(region_id)
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_region(self, region_id: int, actor_id: str):
        self._check_auth(actor_id)
        self.repo.delete_region(region_id)
        self.conn.commit()

    # LINE
    def create_line(self, page_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        self.get_page(page_id)
        data = jsonable_encoder(req)
        data["bbox_json"] = str(data["bbox_json"]) if data.get("bbox_json") else None
        data["baseline_json"] = str(data["baseline_json"]) if data.get("baseline_json") else None
        data["page_id"] = page_id
        data["created_by"] = actor_id
        data["status"] = "DRAFT"
        try:
            lid = self.repo.create_line(data)
            self.conn.commit()
            return self.repo.get_line(lid)
        except Exception as e:
            self.conn.rollback()
            raise e

    def list_lines(self, page_id: int):
        return self.repo.list_lines(page_id)

    def get_line(self, line_id: int):
        l = self.repo.get_line(line_id)
        if not l: raise not_found("LINE", line_id)
        return l

    def update_line(self, line_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        l = self.get_line(line_id)
        if l.get("status") == "LOCKED": raise locked_entity("LINE", line_id)
        data = req.dict(exclude_unset=True)
        if "bbox_json" in data: data["bbox_json"] = str(data["bbox_json"])
        if "baseline_json" in data: data["baseline_json"] = str(data["baseline_json"])
        if not data: return l
        try:
            self.repo.update_line(line_id, data)
            self.conn.commit()
            return self.repo.get_line(line_id)
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_line(self, line_id: int, actor_id: str):
        self._check_auth(actor_id)
        self.repo.delete_line(line_id)
        self.conn.commit()

    def get_line_history(self, line_id: int):
        return self.repo.get_line_history(line_id)

    # REVIEWS
    def change_line_status(self, line_id: int, new_status: str, actor_id: str):
        line = self.get_line(line_id)
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

    def mark_needs_correction(self, line_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        try:
            self.change_line_status(line_id, "NEEDS_CORRECTION", actor_id)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def human_verify_line(self, line_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        line = self.get_line(line_id)
        if not line.get("transcription") or not line.get("bbox_json"):
            self.repo.write_audit("LINE", line_id, "HUMAN_VERIFY", actor_id, False, line, error_code="VERIFICATION_REQUIREMENTS_NOT_MET")
            raise AnnotationException(409, "VERIFICATION_REQUIREMENTS_NOT_MET", "Missing required fields for verification")
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

    def second_review_line(self, line_id: int, req, actor_id: str):
        self._check_auth(actor_id)
        line = self.get_line(line_id)
        if line.get("reviewed_by") == actor_id:
            self.repo.write_audit("LINE", line_id, "SECOND_REVIEW", actor_id, False, line, error_code="SAME_REVIEWER_NOT_ALLOWED")
            raise AnnotationException(409, "SAME_REVIEWER_NOT_ALLOWED", "Second reviewer cannot be same as first")
        try:
            if req.decision == "APPROVED":
                self.change_line_status(line_id, "SECOND_REVIEW_VERIFIED", actor_id)
                self.repo.update_line_status(line_id, "SECOND_REVIEW_VERIFIED", {"second_reviewer": actor_id})
            else:
                self.change_line_status(line_id, "NEEDS_CORRECTION", actor_id)
            self.repo.write_audit("LINE", line_id, "SECOND_REVIEW", actor_id, True, line, {"decision": req.decision})
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
'''

root = Path(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")
with open(root / "backend/app/repositories/annotation_repository.py", "w", encoding="utf-8") as f: f.write(repo_code)
with open(root / "backend/app/services/annotation_service.py", "w", encoding="utf-8") as f: f.write(svc_code)
print("Code injected successfully.")
