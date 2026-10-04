import os
import hashlib
import sqlite3
import json
import datetime

db_path = 'backend/ottoman_assistant.db'
out_dir = 'evidence/annotation_export_final_gate'
os.makedirs(out_dir, exist_ok=True)

# ----------------- PHASE 6: Production DB After -----------------
st = os.stat(db_path)
with open(db_path, 'rb') as f:
    h = hashlib.sha256(f.read()).hexdigest()

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('PRAGMA integrity_check;')
integrity = cur.fetchall()
cur.execute('PRAGMA foreign_key_check;')
fk = cur.fetchall()

db_after = {
    'file': db_path,
    'sha256': h,
    'size': st.st_size,
    'mtime': st.st_mtime,
    'integrity_check': integrity,
    'foreign_key_check': fk,
    'timestamp': datetime.datetime.now().isoformat()
}

with open(f'{out_dir}/production_db_after.json', 'w') as f:
    json.dump(db_after, f, indent=2)

with open(f'{out_dir}/production_db_before_repair.json', 'r') as f:
    db_before = json.load(f)

db_diff = {
    'sha256_same': db_before['sha256'] == db_after['sha256'],
    'size_same': db_before['size'] == db_after['size'],
    'integrity_check': 'ok' if db_after['integrity_check'] == [('ok',)] else 'failed',
    'foreign_key_check': db_after['foreign_key_check']
}

with open(f'{out_dir}/production_db_diff.json', 'w') as f:
    json.dump(db_diff, f, indent=2)

# ----------------- PHASE 7: Legacy After Hash -----------------
cur.execute('''
    SELECT 
        l.id as line_id,
        p.id as page_id,
        l.transcription as GT_text,
        l.bbox_json as bbox,
        l.baseline_json as baseline,
        l.line_order as reading_order,
        l.human_verified,
        l.status
    FROM annotation_lines l
    JOIN annotation_pages p ON l.page_id = p.id
    JOIN annotation_documents d ON p.document_id = d.id
    WHERE d.dataset_id = 2
    ORDER BY p.id, l.line_order, l.id
''')
rows = cur.fetchall()

legacy_data = {
    'dataset_id': 2,
    'pages_count': len(set([r[1] for r in rows])),
    'lines_count': len(rows),
    'lines': []
}
for r in rows:
    legacy_data['lines'].append({
        'line_id': r[0],
        'page_id': r[1],
        'GT_text': r[2],
        'bbox': r[3],
        'baseline': r[4],
        'reading_order': r[5],
        'human_verified': r[6],
        'status': r[7]
    })

legacy_hash = hashlib.sha256(json.dumps(legacy_data, sort_keys=True).encode('utf-8')).hexdigest()
legacy_data['canonical_hash'] = legacy_hash

with open(f'{out_dir}/legacy_after_hash.json', 'w') as f:
    json.dump(legacy_data, f, indent=2)

with open(f'{out_dir}/legacy_before_hash_repair.json', 'r') as f:
    legacy_before = json.load(f)

legacy_diff = []
if legacy_before['canonical_hash'] != legacy_data['canonical_hash']:
    legacy_diff.append("Hash mismatch")
if legacy_before['pages_count'] != legacy_data['pages_count']:
    legacy_diff.append("Pages count mismatch")
if legacy_before['lines_count'] != legacy_data['lines_count']:
    legacy_diff.append("Lines count mismatch")

with open(f'{out_dir}/legacy_diff.json', 'w') as f:
    json.dump(legacy_diff, f, indent=2)

print('Phase 6 & 7 DONE.')
