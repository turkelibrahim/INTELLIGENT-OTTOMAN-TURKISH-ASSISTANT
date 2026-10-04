import glob

def fix_file(f):
    with open(f, 'r') as file:
        content = file.read()
    
    # fix the missing parameter in VALUES
    content = content.replace('INSERT INTO annotation_pages (document_id, status, human_verified, reading_order_verified, image_path) VALUES (?, ?, ?, ?)', 'INSERT INTO annotation_pages (document_id, status, human_verified, reading_order_verified, image_path) VALUES (?, ?, ?, ?, ?)')
    
    # fix the tuple where only 4 values were given
    content = content.replace('(doc_id, "LOCKED", 1, 1)', '(doc_id, "LOCKED", 1, 1, "test.png")')
    content = content.replace('(doc_id, "LOCKED", 1, 1))', '(doc_id, "LOCKED", 1, 1, "test.png"))')
    
    with open(f, 'w') as file:
        file.write(content)

for f in glob.glob('tests/annotation_backend/test_*.py'):
    fix_file(f)
