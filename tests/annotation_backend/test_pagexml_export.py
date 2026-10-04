import pytest
import os
import json
import xml.etree.ElementTree as ET
from app.services.export_service import ExportService

def test_pagexml_generation(db_conn):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (name, status, is_test_data, archived, training_eligible) VALUES (?, ?, ?, ?, ?)", 
                ("XML DS", "LOCKED", 0, 0, 1))
    ds_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_documents (dataset_id, license_status, source_sha256, license_reference) VALUES (?, ?, ?, ?)",
                (ds_id, "APPROVED", "sha256_mock", "ref"))
    doc_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_pages (document_id, status, human_verified, reading_order_verified, image_path, image_width, image_height) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (doc_id, "LOCKED", 1, 1, "test_img.png", 1000, 1000))
    page_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_regions (page_id) VALUES (?)", (page_id,))
    reg_id = cur.lastrowid
    
    bbox = json.dumps({"x": 10, "y": 20, "width": 100, "height": 30})
    baseline = json.dumps([{"x": 10, "y": 40}, {"x": 110, "y": 40}])
    # Add an RTL string and an ampersand to test escaping and unicode normalization
    rtl_text = "آب & هوا"
    
    cur.execute("""INSERT INTO annotation_lines 
                (page_id, region_id, status, human_verified, bbox_verified, baseline_verified, reading_order_verified, transcription_verified, duplicate_checked, training_eligible, normalized_transcription, transcription, reviewed_by, second_reviewer, bbox_json, baseline_json) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (page_id, reg_id, "LOCKED", 1, 1, 1, 1, 1, 1, 1, rtl_text, rtl_text, "u1", "u2", bbox, baseline))
    
    service = ExportService(db_conn)
    res = service.export_pagexml(ds_id, is_test_export=False, user_id="test_usr")
    
    assert res["dataset_name"] == "XML DS"
    assert res["page_count"] == 1
    assert res["line_count"] == 1
    assert res["training_eligible_count"] == 1
    assert res["excluded_count"] == 0
    
    export_id = res["export_id"]
    xml_path = f"exports/annotation/XML DS/{export_id}/pagexml/page_{page_id}.xml"
    
    assert os.path.exists(xml_path)
    
    # Python ElementTree parse
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # The namespace must be present
    ns = {'pc': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'}
    page = root.find('pc:Page', ns)
    assert page is not None
    assert page.attrib['imageFilename'] == 'test_img.png'
    
    text_equiv = root.find('.//pc:TextEquiv/pc:Unicode', ns)
    assert text_equiv is not None
    # ElementTree handles xml unescaping automatically, so we check original string
    assert text_equiv.text == "آب & هوا"

    # Also check Baseline
    baseline_elem = root.find('.//pc:Baseline', ns)
    assert baseline_elem is not None
    assert baseline_elem.attrib['points'] == '10,40 110,40'

