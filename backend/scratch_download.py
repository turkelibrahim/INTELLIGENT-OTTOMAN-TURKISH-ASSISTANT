import sys
import easyocr

sys.stdout.reconfigure(encoding='utf-8')

print("Downloading EasyOCR Arabic/English model...")
reader1 = easyocr.Reader(['en', 'ar'])
print("Downloading EasyOCR Turkish/English model...")
reader2 = easyocr.Reader(['en', 'tr'])
print("Models downloaded successfully!")
