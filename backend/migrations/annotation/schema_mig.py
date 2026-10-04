
import sqlite3

def upgrade(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    
    # Check if applied
    cur.execute("CREATE TABLE IF NOT EXISTS annotation_schema_version (version INTEGER, applied_at TEXT, migration_name TEXT, checksum TEXT)")
    cur.execute("SELECT * FROM annotation_schema_version WHERE version = 1")
    if cur.fetchone():
        return
        
    cur.execute("BEGIN TRANSACTION")
    try:
        cur.execute('''CREATE TABLE IF NOT EXISTS annotation_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            legacy_dataset_id INTEGER,
            name TEXT,
            description TEXT,
            status TEXT CHECK(status IN ('DRAFT','AUTO_PREANNOTATED','IN_REVIEW','NEEDS_CORRECTION','HUMAN_VERIFIED','SECOND_REVIEW_VERIFIED','LOCKED','REJECTED')),
            is_test_data BOOLEAN,
            archived BOOLEAN,
            training_eligible BOOLEAN,
            target_verified_lines INTEGER,
            double_review_required BOOLEAN,
            created_by TEXT,
            created_at TEXT,
            updated_at TEXT,
            locked_at TEXT
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS annotation_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            source_name TEXT,
            source_path TEXT,
            source_sha256 TEXT,
            license_status TEXT CHECK(license_status IN ('UNKNOWN','MISSING','PENDING','APPROVED','RESTRICTED','REJECTED')),
            license_reference TEXT,
            document_type TEXT,
            script_style TEXT,
            printed_or_handwritten TEXT,
            created_by TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(dataset_id) REFERENCES annotation_datasets(id)
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS annotation_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            page_number INTEGER,
            image_path TEXT,
            image_sha256 TEXT,
            image_width INTEGER,
            image_height INTEGER,
            status TEXT,
            human_verified BOOLEAN,
            reading_order_verified BOOLEAN,
            created_at TEXT,
            updated_at TEXT,
            locked_at TEXT,
            FOREIGN KEY(document_id) REFERENCES annotation_documents(id)
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS annotation_regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER,
            region_type TEXT CHECK(region_type IN ('TEXT','NON_TEXT','IMAGE','TABLE','DECORATION','UNKNOWN')),
            bbox_json TEXT,
            reading_order INTEGER,
            status TEXT,
            created_by TEXT,
            updated_by TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(page_id) REFERENCES annotation_pages(id)
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS annotation_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER,
            region_id INTEGER,
            line_order INTEGER,
            bbox_json TEXT,
            baseline_json TEXT,
            transcription TEXT,
            normalized_transcription TEXT,
            machine_suggestion TEXT,
            machine_confidence REAL,
            status TEXT,
            human_verified BOOLEAN,
            bbox_verified BOOLEAN,
            baseline_verified BOOLEAN,
            reading_order_verified BOOLEAN,
            transcription_verified BOOLEAN,
            duplicate_checked BOOLEAN,
            training_eligible BOOLEAN,
            crop_sha256 TEXT,
            created_by TEXT,
            reviewed_by TEXT,
            second_reviewer TEXT,
            created_at TEXT,
            updated_at TEXT,
            reviewed_at TEXT,
            second_reviewed_at TEXT,
            locked_at TEXT,
            split_name TEXT,
            FOREIGN KEY(page_id) REFERENCES annotation_pages(id),
            FOREIGN KEY(region_id) REFERENCES annotation_regions(id)
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS annotation_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            entity_id INTEGER,
            review_type TEXT,
            reviewer_id TEXT,
            decision TEXT,
            comment TEXT,
            created_at TEXT
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS annotation_audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            entity_id INTEGER,
            action TEXT,
            before_json TEXT,
            after_json TEXT,
            actor_id TEXT,
            success BOOLEAN,
            error_code TEXT,
            created_at TEXT
        )''')
        
        cur.execute('''CREATE TABLE IF NOT EXISTS annotation_exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            export_type TEXT,
            status TEXT,
            output_path TEXT,
            output_sha256 TEXT,
            is_test_export BOOLEAN,
            created_by TEXT,
            created_at TEXT,
            completed_at TEXT,
            error_message TEXT,
            FOREIGN KEY(dataset_id) REFERENCES annotation_datasets(id)
        )''')

        # Indices and constraints
        cur.execute("CREATE INDEX IF NOT EXISTS idx_dataset_id ON annotation_documents(dataset_id)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_doc_source_sha ON annotation_documents(dataset_id, source_sha256)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_page_line_order ON annotation_lines(page_id, line_order)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_page_region_order ON annotation_regions(page_id, reading_order)")
        
        cur.execute("INSERT INTO annotation_schema_version (version, applied_at, migration_name, checksum) VALUES (1, datetime('now'), '001_create_annotation_schema', 'chksum')")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
