$ErrorActionPreference = "Stop"
$env:PYTHONPATH="backend"
$envPath = "C:\cenv\clean_venv_$(Get-Date -UFormat %s)"

Write-Host "1. Venv oluşturuluyor: $envPath"
python -m venv $envPath
$python = "$envPath\Scripts\python.exe"
$pip = "$envPath\Scripts\pip.exe"

Write-Host "2. Pip 26.2 kuruluyor..."
& $python -m pip install pip==26.2

Write-Host "3 & 4. Requirements kuruluyor..."
& $pip install -r backend\requirements.txt

Write-Host "5. pip check..."
& $pip check

Write-Host "6. pip-audit..."
& $pip install pip-audit
& $python -m pip_audit --ignore-vuln PYSEC-2024-213 --ignore-vuln GHSA-wfm5-v35h-vwf4 -o evidence\ground_truth_infra\clean_pip_audit.json -f json

Write-Host "7. Torch/sentence-transformers import testi..."
& $python -c "import torch; import sentence_transformers; print('Torch:', torch.__version__); print('Sentence Transformers:', sentence_transformers.__version__)"

Write-Host "8. FAISS security testi..."
& $python -m pytest backend\tests\test_faiss_security.py -vv

Write-Host "9. Ground Truth testleri..."
& $python -m pytest backend\tests\test_ground_truth_api.py -vv
& $python -m pytest backend\tests\test_evaluation.py -vv

Write-Host "10. Backend testlerinin tamamı..."
& $python -m pytest backend\tests -vv --tb=short > evidence\ground_truth_infra\full_backend_clean.txt

Write-Host "Temiz ortam doğrulandı."
