import re

path = r'frontend/src/app/(app)/dashboard/page.tsx'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Emojis/icons get corrupted. Let's replace the common corrupted ones.
content = re.sub(r'<span className="text-amber-500">.*?</span> Son Analiz', '<span className="text-amber-500">📄</span> Son Analiz', content)
content = re.sub(r'<span className="text-xl.*?origin-bottom-left">.*?</span>', '<span className="text-xl group-hover:scale-110 transition-transform origin-bottom-left">📄</span>', content)
content = re.sub(r'<span className="ota-error-icon">.*?</span>', '<span className="ota-error-icon">⚠️</span>', content)
content = re.sub(r'<div className="ota-dropzone-icon" aria-hidden="true">.*?</div>', '<div className="ota-dropzone-icon" aria-hidden="true">📤</div>', content)

# Fixing Turkish characters that might be corrupted as Y, A, etc.
# Actually, since Next.js builds fine, maybe just the emojis were broken.
# But let's check for 'Analiz tamamlanamad'
content = content.replace('Analiz tamamlanamad', 'Analiz tamamlanamadı')
content = content.replace('aYama', 'aşama')
content = content.replace('iYlenirken', 'işlenirken')
content = content.replace('oluYtu', 'oluştu')
content = content.replace('AA', '⚠️')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed dashboard/page.tsx')
