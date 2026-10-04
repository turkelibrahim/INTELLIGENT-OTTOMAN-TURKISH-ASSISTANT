import sqlite3
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
        # Proper aggregation query instead of mock
        cur = self.conn.execute("SELECT name, target_verified_lines FROM annotation_datasets WHERE id = ?", (dataset_id,))
        row = cur.fetchone()
        if not row: return {}
        
        target = row["target_verified_lines"] or 0
        
        # Count documents, pages, regions, lines
        docs = self.conn.execute("SELECT COUNT(*) as c FROM annotation_documents WHERE dataset_id = ?", (dataset_id,)).fetchone()["c"]
        pages = self.conn.execute("SELECT COUNT(p.id) as c FROM annotation_pages p JOIN annotation_documents d ON p.document_id = d.id WHERE d.dataset_id = ?", (dataset_id,)).fetchone()["c"]
        regions = self.conn.execute("SELECT COUNT(r.id) as c FROM annotation_regions r JOIN annotation_pages p ON r.page_id = p.id JOIN annotation_documents d ON p.document_id = d.id WHERE d.dataset_id = ?", (dataset_id,)).fetchone()["c"]
        
        # Group line counts by status
        line_counts = self.conn.execute("""
            SELECT l.status, COUNT(l.id) as c 
            FROM annotation_lines l 
            JOIN annotation_regions r ON l.region_id = r.id 
            JOIN annotation_pages p ON r.page_id = p.id 
            JOIN annotation_documents d ON p.document_id = d.id 
            WHERE d.dataset_id = ?
            GROUP BY l.status
        """, (dataset_id,)).fetchall()
        
        counts = {r["status"]: r["c"] for r in line_counts}
        total_lines = sum(counts.values())
        human_verified = counts.get("HUMAN_VERIFIED", 0)
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": row["name"],
            "target_verified_lines": target,
            "total_documents": docs, "total_pages": pages, "total_regions": regions, "total_lines": total_lines,
            "draft_lines": counts.get("DRAFT", 0), 
            "auto_preannotated_lines": counts.get("AUTO_PREANNOTATED", 0), 
            "in_review_lines": counts.get("IN_REVIEW", 0),
            "needs_correction_lines": counts.get("NEEDS_CORRECTION", 0), 
            "human_verified_lines": human_verified, 
            "double_reviewed_lines": counts.get("DOUBLE_REVIEWED", 0),
            "locked_lines": counts.get("LOCKED", 0), 
            "rejected_lines": counts.get("REJECTED", 0), 
            "verified_training_eligible_lines": counts.get("VERIFIED_TRAINING_ELIGIBLE", 0),
            "remaining_to_target": max(0, target - human_verified)
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
