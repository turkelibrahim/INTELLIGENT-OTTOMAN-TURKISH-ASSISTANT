document.addEventListener("DOMContentLoaded", () => {
    loadDocuments();
    setupUploadArea();
    setupSearch();
});

// Load documents from backend
async function loadDocuments(query = "") {
    const listEl = document.getElementById('doc-list');
    const countEl = document.getElementById('doc-count');
    
    listEl.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-gray-500">Yükleniyor...</td></tr>';
    
    try {
        const res = await fetch(`/api/documents?query=${encodeURIComponent(query)}`);
        const docs = await res.json();
        
        countEl.innerText = `${docs.length} Belge`;
        listEl.innerHTML = '';
        
        if (docs.length === 0) {
            listEl.innerHTML = `<tr><td colspan="4" class="text-center py-8 text-gray-500">Belge bulunamadı.</td></tr>`;
            return;
        }

        docs.forEach(doc => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-panel hover:bg-[#1a1a1a] transition';
            tr.innerHTML = `
                <td class="py-4 px-2 font-medium text-white flex items-center gap-3">
                    <i class="fa-solid fa-file-lines text-gray-400"></i> ${doc.name}
                </td>
                <td class="py-4 px-2 text-gray-400 text-sm">${doc.date} <br><span class="text-xs text-gray-500">${doc.id}</span></td>
                <td class="py-4 px-2">
                    <span class="bg-green-500 bg-opacity-10 text-green-400 border border-green-500 px-2 py-1 rounded text-xs">
                        <i class="fa-solid fa-check mr-1"></i>${doc.status}
                    </span>
                </td>
                <td class="py-4 px-2 text-right">
                    <button title="JSON Olarak Dışa Aktar" onclick="exportData('${doc.id}', 'json')" class="text-gray-400 hover:text-white mx-1"><i class="fa-solid fa-code"></i></button>
                    <button title="Rapor (TXT) Çıkar" onclick="exportData('${doc.id}', 'report')" class="text-gray-400 hover:text-white mx-1"><i class="fa-solid fa-file-alt"></i></button>
                    <a href="chat.html?doc_id=${doc.id}" title="Belgeye Sor" class="text-accent hover:text-white ml-2"><i class="fa-solid fa-comment-dots"></i></a>
                </td>
            `;
            listEl.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
        listEl.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-red-400">Sunucu bağlantı hatası!</td></tr>';
    }
}

// Handle Export logic
function exportData(docId, type) {
    // We simply redirect the browser to download the file directly from backend
    window.open(`/api/export/${docId}/${type}`, '_blank');
}

// Upload Area Simulation
function setupUploadArea() {
    const dropzone = document.getElementById('dropzone');
    const input = document.getElementById('file-input');
    const pContainer = document.getElementById('progress-container');
    const pBar = document.getElementById('progress-bar');
    const pStatus = document.getElementById('upload-status');

    const handleUpload = (file) => {
        if (!file) return;
        
        pContainer.style.display = 'block';
        pStatus.style.display = 'block';
        pStatus.innerText = `Yükleniyor: ${file.name}...`;
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                pStatus.innerText = "Yüklendi ve işleme kuyruğuna alındı!";
                pStatus.classList.replace('text-green-400', 'text-accent');
                
                setTimeout(() => {
                    pContainer.style.display = 'none';
                    pStatus.style.display = 'none';
                    pBar.style.width = '0%';
                    loadDocuments(); // refresh list
                }, 2000);
            }
            pBar.style.width = `${progress}%`;
        }, 200);
    };

    input.onchange = (e) => handleUpload(e.target.files[0]);

    dropzone.ondragover = (e) => { e.preventDefault(); dropzone.classList.add('dragover'); };
    dropzone.ondragleave = () => dropzone.classList.remove('dragover');
    dropzone.ondrop = (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files[0]);
    };
}

// Search form
function setupSearch() {
    document.getElementById('search-form').onsubmit = (e) => {
        e.preventDefault();
        loadDocuments(document.getElementById('search-input').value);
    };
}
