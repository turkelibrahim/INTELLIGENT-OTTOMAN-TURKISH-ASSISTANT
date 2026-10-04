import glob

def fix_file(f):
    with open(f, 'r') as file:
        content = file.read()
    
    # fix the NoneType in bbox_json by setting it to a mock json object
    content = content.replace('(p1, r1, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test1", "u1", "u2", "TRAIN"))', '(p1, r1, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test1", "u1", "u2", "TRAIN", \'{"x":0, "y":0, "width":10, "height":10}\'))')
    content = content.replace('(p2, r2, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test2", "u1", "u2", "FINAL_HOLDOUT_TEST"))', '(p2, r2, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test2", "u1", "u2", "FINAL_HOLDOUT_TEST", \'{"x":0, "y":0, "width":10, "height":10}\'))')
    
    content = content.replace('second_reviewer, split_name)', 'second_reviewer, split_name, bbox_json)')
    
    with open(f, 'w') as file:
        file.write(content)

for f in glob.glob('tests/annotation_backend/test_kraken_export.py') + glob.glob('tests/annotation_backend/test_export_split_leakage.py') + glob.glob('tests/annotation_backend/test_export_eligibility.py'):
    fix_file(f)
