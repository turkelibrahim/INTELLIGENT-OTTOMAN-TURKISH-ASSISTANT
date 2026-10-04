import os
import re

replacements = {
    'Y': 'ş',
    'z': 'Ş',
    'A': 'ç',
    'A': 'ü',
    'A ': 'ö',
    '': 'ı',
    'GiriY': 'Giriş',
    'Giriş yapılıyor': 'Giriş yapılıyor',
    'Giriş Yap': 'Giriş Yap',
    'Giriş yaplamadı': 'Giriş yapılamadı',
    'aYama': 'aşama',
    'iYlenirken': 'işlenirken',
    'oluYtu': 'oluştu',
    'kullanm': 'kullanım',
    'arYiv': 'arşiv',
    'baYar': 'başar',
    'sifre': 'şifre',
    'Sifre': 'Şifre',
    'TArk': 'Türk',
    'A': 'ü',
    'A§': 'ç',
    'A¶': 'ö',
    'A±': 'ı',
    'A°': 'İ',
    'AŸ': 'ğ',
    'Až': 'Ş',
    'A?': 'ş',
}

def fix_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    orig = content
    # Common words fixes
    content = content.replace('GiriY Yap', 'Giriş Yap')
    content = content.replace('GiriY yaplyor', 'Giriş yapılıyor')
    content = content.replace('GiriY yaplamad', 'Giriş yapılamadı')
    content = content.replace('zifre', 'Şifre')
    content = content.replace('Yifre', 'şifre')
    content = content.replace('hesabnza', 'hesabınıza')
    content = content.replace('eriYmek', 'erişmek')
    content = content.replace('iA in', 'için')
    content = content.replace('hatal', 'hatalı')
    content = content.replace('baYlanlamad', 'bağlanılamadı')
    content = content.replace('A alYtYn', 'çalıştığını')
    content = content.replace('oluYtu', 'oluştu')
    content = content.replace('LAtfen', 'Lütfen')
    content = content.replace('hatrla', 'hatırla')
    content = content.replace('gA ster', 'göster')
    content = content.replace('GAvenli', 'Güvenli')
    content = content.replace('Kullanm', 'Kullanım')
    content = content.replace('sakldr', 'saklıdır')
    content = content.replace('Osmanlca', 'Osmanlıca')
    content = content.replace('Asistan', 'Asistanı')
    content = content.replace('TArkA esi', 'Türkçesi')
    content = content.replace('modernleYtirme', 'modernleştirme')
    content = content.replace('arYiv', 'arşiv')
    content = content.replace('zekA', 'zekâ')
    content = content.replace('doYrulama', 'doğrulama')
    content = content.replace('Kayt Ol', 'Kayıt Ol')
    
    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {path}")

for root, _, files in os.walk('frontend/src'):
    for file in files:
        if file.endswith(('.tsx', '.ts', '.css')):
            fix_file(os.path.join(root, file))

