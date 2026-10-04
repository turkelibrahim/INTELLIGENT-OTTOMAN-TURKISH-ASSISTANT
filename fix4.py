f='run_export_forensic.py'
c=open(f, encoding='utf-8').read()
c = c.replace('service = ExportService(repo, export_dir="exports_test")', 'service = ExportService(conn)')
open(f,'w', encoding='utf-8').write(c)
