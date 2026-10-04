import os
import json
import hashlib
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
from fastapi import HTTPException

from app.repositories.export_repository import ExportRepository
from app.schemas.export import ExportEligibilityReport, ExportMetadata

EXPORT_ROOT = Path("exports/annotation").resolve()

def secure_path(base: Path, subpath: str) -> Path:
    # Aşama 11 - Path Güvenliği
    if ".." in subpath or subpath.startswith("/") or subpath.startswith("\\") or ":" in subpath:
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    target = (base / subpath).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    return target

class ExportService:
    def __init__(self, db_conn):
        self.db = db_conn
        self.repo = ExportRepository(db_conn)

    def _check_eligibility(self, dataset_id: int, is_test_export: bool) -> Tuple[dict, List[dict], Dict[str, int]]:
        ds = self.repo.get_dataset(dataset_id)
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found")
            
        reasons = []
        if ds["status"] != "LOCKED":
            reasons.append("Dataset is not LOCKED")
        if ds["is_test_data"] and not is_test_export:
            reasons.append("Test dataset cannot be exported for production training")
        if ds["archived"]:
            reasons.append("Dataset is archived")
        if not is_test_export and not ds["training_eligible"]:
            reasons.append("Dataset is not training eligible")
            
        if reasons:
            raise HTTPException(status_code=409, detail=f"Dataset not eligible for export: {', '.join(reasons)}")
            
        lines, exclusions = self.repo.get_eligible_lines(dataset_id, is_test_export)
        if not lines:
            raise HTTPException(status_code=409, detail="No eligible lines found for export")
            
        return ds, lines, exclusions

    def check_eligibility_report(self, dataset_id: int, is_test_export: bool) -> ExportEligibilityReport:
        try:
            ds, lines, exclusions = self._check_eligibility(dataset_id, is_test_export)
            is_eligible = True
            reasons = []
        except HTTPException as e:
            if "Dataset not eligible" in e.detail or "No eligible lines" in e.detail:
                is_eligible = False
                reasons = [e.detail]
                ds = self.repo.get_dataset(dataset_id)
                lines = []
                exclusions = {}
            else:
                raise e
                
        doc_ids = set(l["document_id"] for l in lines)
        page_ids = set(l["page_id"] for l in lines)
        
        return ExportEligibilityReport(
            dataset_id=dataset_id,
            dataset_name=ds["name"] if ds else "Unknown",
            is_eligible=is_eligible,
            rejection_reasons=reasons,
            eligible_document_count=len(doc_ids),
            eligible_page_count=len(page_ids),
            eligible_line_count=len(lines),
            excluded_line_count=sum(exclusions.values()),
            exclusion_details=exclusions
        )

    def _generate_page_xml(self, page_id: int, lines: List[dict], image_path: str, w: int, h: int) -> str:
        xml = []
        xml.append('<?xml version="1.0" encoding="UTF-8"?>')
        xml.append('<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">')
        xml.append('    <Metadata>')
        xml.append(f'        <Creator>Ottoman Assistant</Creator>')
        xml.append(f'        <Created>{datetime.utcnow().isoformat()}</Created>')
        xml.append(f'        <LastChange>{datetime.utcnow().isoformat()}</LastChange>')
        xml.append('    </Metadata>')
        
        img_name = Path(image_path).name
        xml.append(f'    <Page imageFilename="{img_name}" imageWidth="{w}" imageHeight="{h}">')
        
        # Group lines by region
        regions = {}
        for l in lines:
            regions.setdefault(l["region_id"], []).append(l)
            
        # We need region bbox. Since we only have line bbox in this query, we can compute region bbox from lines.
        for r_id, rlines in regions.items():
            if not rlines: continue
            # use 0 if bbox is missing just to avoid errors on corrupt/mock data
            min_x = min([l["bbox_json"]["x"] if l.get("bbox_json") else 0 for l in rlines])
            min_y = min([l["bbox_json"]["y"] if l.get("bbox_json") else 0 for l in rlines])
            max_x = max([l["bbox_json"]["x"] + l["bbox_json"]["width"] if l.get("bbox_json") else 10 for l in rlines])
            max_y = max([l["bbox_json"]["y"] + l["bbox_json"]["height"] if l.get("bbox_json") else 10 for l in rlines])
            
            xml.append(f'        <TextRegion id="region_{r_id}">')
            xml.append(f'            <Coords points="{min_x},{min_y} {max_x},{min_y} {max_x},{max_y} {min_x},{max_y}"/>')
            
            # Sort lines by line_order
            rlines.sort(key=lambda x: x["line_order"] if x.get("line_order") is not None else 0)
            
            for l in rlines:
                xml.append(f'            <TextLine id="line_{l["id"]}">')
                if l.get("bbox_json"):
                    lx = l["bbox_json"]["x"]
                    ly = l["bbox_json"]["y"]
                    lw = l["bbox_json"]["width"]
                    lh = l["bbox_json"]["height"]
                    xml.append(f'                <Coords points="{lx},{ly} {lx+lw},{ly} {lx+lw},{ly+lh} {lx},{ly+lh}"/>')
                else:
                    xml.append(f'                <Coords points="0,0 10,0 10,10 0,10"/>')
                
                if l.get("baseline_json"):
                    bl = l["baseline_json"]
                    if isinstance(bl, list):
                        bp = " ".join([f"{pt.get('x',0)},{pt.get('y',0)}" for pt in bl])
                    else:
                        bp = f"{bl.get('x1',0)},{bl.get('y1',0)} {bl.get('x2',0)},{bl.get('y2',0)}"
                    xml.append(f'                <Baseline points="{bp}"/>')
                
                xml.append('                <TextEquiv>')
                text = unicodedata.normalize('NFC', l["transcription"]) if l.get("transcription") else ""
                text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                xml.append(f'                    <Unicode>{text}</Unicode>')
                xml.append('                </TextEquiv>')
                xml.append('            </TextLine>')
                
            xml.append(f'        </TextRegion>')
            
        xml.append('    </Page>')
        xml.append('</PcGts>')
        return "\n".join(xml)

    def export_pagexml(self, dataset_id: int, is_test_export: bool, user_id: str) -> dict:
        try:
            ds, lines, exclusions = self._check_eligibility(dataset_id, is_test_export)
        except HTTPException as e:
            cur = self.db.cursor()
            cur.execute("""
                INSERT INTO annotation_audit_events 
                (entity_type, entity_id, action, actor_id, success, created_at, error_code)
                VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
            """, ("dataset", dataset_id, "export.pagexml", user_id, 0, str(e.detail)))
            self.db.commit()
            raise e
        
        export_id = f"exp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{dataset_id}"
        out_dir = secure_path(EXPORT_ROOT, f"{ds['name']}/{export_id}")
        os.makedirs(out_dir, exist_ok=True)
        
        xml_dir = out_dir / "pagexml"
        img_dir = out_dir / "images"
        os.makedirs(xml_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)
        
        # In a real app we'd fetch image dimensions and copy images.
        # Since we mock image_path in DB, we'll write XML and skip image copy if missing.
        pages = {}
        for l in lines:
            pages.setdefault(l["page_id"], []).append(l)
            
        # Get page info (we need width/height)
        cur = self.db.cursor()
        cur.execute("SELECT id, image_path, image_width, image_height FROM annotation_pages WHERE id IN ({})".format(','.join('?'*len(pages))), list(pages.keys()))
        pinfo = {r[0]: r for r in cur.fetchall()}
        
        xml_hashes = {}
        for p_id, plines in pages.items():
            pi = pinfo[p_id]
            xml = self._generate_page_xml(p_id, plines, pi[1], pi[2], pi[3])
            xml_path = xml_dir / f"page_{p_id}.xml"
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml)
            xml_hashes[f"page_{p_id}.xml"] = hashlib.sha256(xml.encode('utf-8')).hexdigest()
            
        # Write metadata
        meta = ExportMetadata(
            dataset_name=ds["name"],
            dataset_id=dataset_id,
            export_id=export_id,
            export_version="1.0",
            created_at=datetime.utcnow().isoformat(),
            created_by=user_id,
            dataset_status=ds["status"],
            line_count=len(lines),
            page_count=len(pages),
            document_count=len(set(l["document_id"] for l in lines)),
            split_counts={},
            source_db_fingerprint="mock_fp",
            export_sha256="",
            exporter_version="1.0",
            pagexml_namespace="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15",
            kraken_version="7",
            training_eligible_count=len(lines),
            excluded_count=sum(exclusions.values())
        )
        
        # Compute export sha256
        h = hashlib.sha256()
        for xh in sorted(xml_hashes.values()):
            h.update(xh.encode())
        meta.export_sha256 = h.hexdigest()
        
        with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
            f.write(meta.model_dump_json(indent=2))
            
        # Record in DB
        self.repo.create_export_record(dataset_id, "PAGEXML", str(out_dir), meta.export_sha256, is_test_export, user_id)
        
        cur = self.db.cursor()
        cur.execute("""
            INSERT INTO annotation_audit_events 
            (entity_type, entity_id, action, actor_id, success, created_at, before_json, after_json, error_code)
            VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?, ?)
        """, ("dataset", dataset_id, "export.pagexml", user_id, 1, None, json.dumps(meta.model_dump()), None))
        self.db.commit()
        
        return meta.model_dump()
        
    def export_kraken(self, dataset_id: int, is_test_export: bool, user_id: str) -> dict:
        # First generate the PAGE XML and metadata
        meta_dict = self.export_pagexml(dataset_id, is_test_export, user_id)
        export_id = meta_dict["export_id"]
        ds_name = meta_dict["dataset_name"]
        
        out_dir = secure_path(EXPORT_ROOT, f"{ds_name}/{export_id}")
        manifest_dir = out_dir / "manifests"
        os.makedirs(manifest_dir, exist_ok=True)
        
        # Read the lines again from DB
        _, lines, _ = self._check_eligibility(dataset_id, is_test_export)
        
        # Group pages by split based on lines (assuming all lines in a page have same split)
        splits = {
            "TRAIN": [],
            "INTERNAL_VALIDATION": [],
            "DEVELOPMENT_TEST": [],
            "FINAL_HOLDOUT_TEST": []
        }
        
        pages = {}
        for l in lines:
            pages.setdefault(l["page_id"], set()).add(l["split_name"] or "TRAIN")
            
        split_counts = {k: 0 for k in splits.keys()}
        
        for p_id, p_splits in pages.items():
            if len(p_splits) > 1:
                raise HTTPException(status_code=409, detail=f"Page {p_id} has conflicting splits: {p_splits}")
            
            s = list(p_splits)[0]
            if is_test_export and s in ("FINAL_HOLDOUT_TEST", "DEVELOPMENT_TEST"):
                s = "TRAIN" # test exports fold everything except holdouts to train, actually if test_export, just ignore split leak rules.
            
            # Aşama 6 Split Leakage Checks (simplified):
            if s == "FINAL_HOLDOUT_TEST" and not is_test_export:
                # Production holdout goes to final_holdout
                splits["FINAL_HOLDOUT_TEST"].append(f"../pagexml/page_{p_id}.xml")
                split_counts["FINAL_HOLDOUT_TEST"] += 1
            else:
                if s not in splits:
                    s = "TRAIN"
                splits[s].append(f"../pagexml/page_{p_id}.xml")
                split_counts[s] += 1
                
        # Write manifests
        for split_name, xml_paths in splits.items():
            if xml_paths:
                with open(manifest_dir / f"{split_name.lower()}.txt", "w", encoding="utf-8") as f:
                    if is_test_export:
                        f.write("# DO_NOT_TRAIN\n")
                    f.write("\n".join(xml_paths))
                    
        # Update metadata
        meta_dict["split_counts"] = split_counts
        with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)
            
        return meta_dict
