
import sys
import subprocess
try:
    import kraken
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "kraken", "lxml"])
    
from kraken.lib.xml import parse_page
try:
    doc = parse_page('/mnt/c/Users/ibrah/OneDrive/Masaüstü/INTELLIGENT OTTOMAN TURKISH ASSISTANT/backend/exports/annotation/Test Dataset/exp_20260808080046_100/pagexml/page_100.xml')
    print('PARSED_LINES:', len(doc["lines"]))
except Exception as e:
    print('ERROR:', e)
