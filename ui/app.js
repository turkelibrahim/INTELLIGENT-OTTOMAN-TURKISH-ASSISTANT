const canvas = document.getElementById('doc-canvas');
const ctx = canvas.getContext('2d');
const editorContainer = document.getElementById('editor-container');
const lineCount = document.getElementById('line-count');

let currentData = null;
let currentImage = new Image();
let activeLineId = null;

// Zoom and Pan state
let scale = 1;
let offsetX = 0;
let offsetY = 0;
let isDragging = false;
let startX, startY;

// Load Data
async function loadData() {
    try {
        const res = await fetch('/api/data');
        currentData = await res.json();
        
        // Load image
        currentImage.src = currentData.imageUrl;
        currentImage.onload = () => {
            resetView();
            renderEditor();
        };
    } catch (e) {
        console.error("Failed to load data:", e);
        // Fallback or show error
        editorContainer.innerHTML = '<div style="color:var(--danger)">Veri yüklenemedi. Backend çalışıyor mu?</div>';
    }
}

// Render Editor
function renderEditor() {
    editorContainer.innerHTML = '';
    lineCount.textContent = `${currentData.lines.length} Satır`;

    currentData.lines.forEach((line, index) => {
        const confClass = line.confidence > 0.8 ? 'conf-high' : (line.confidence > 0.5 ? 'conf-med' : 'conf-low');
        
        const box = document.createElement('div');
        box.className = 'line-box';
        box.id = `box-${line.id}`;
        box.onclick = () => setActiveLine(line.id);

        box.innerHTML = `
            <div class="line-header">
                <div>
                    <span class="conf-indicator ${confClass}" title="Güven: ${Math.round(line.confidence*100)}%"></span>
                    ID: ${line.id}
                </div>
                <div class="line-actions">
                    <button title="Yukarı Taşı" onclick="moveLine(event, ${index}, -1)"><i class="fa-solid fa-arrow-up"></i></button>
                    <button title="Aşağı Taşı" onclick="moveLine(event, ${index}, 1)"><i class="fa-solid fa-arrow-down"></i></button>
                    <button title="Birleştir (Aşağıdaki ile)" onclick="mergeLines(event, ${index})"><i class="fa-solid fa-object-group"></i></button>
                    <button title="Böl" onclick="splitLine(event, ${index})"><i class="fa-solid fa-scissors"></i></button>
                </div>
            </div>
            <textarea class="ocr-input" id="input-${line.id}">${line.text}</textarea>
        `;

        // Update model on input
        const textarea = box.querySelector('textarea');
        textarea.oninput = (e) => {
            line.text = e.target.value;
        };

        editorContainer.appendChild(box);
    });
}

function setActiveLine(id) {
    activeLineId = id;
    
    // Update UI active states
    document.querySelectorAll('.line-box').forEach(b => b.classList.remove('active'));
    const box = document.getElementById(`box-${id}`);
    if (box) box.classList.add('active');
    
    drawCanvas();
    
    // Auto pan to bounding box if possible
    const line = currentData.lines.find(l => l.id === id);
    if (line && line.bbox) {
        // Simple center logic
        const [x1, y1, x2, y2] = line.bbox;
        const cx = (x1 + x2) / 2;
        const cy = (y1 + y2) / 2;
        
        offsetX = (canvas.parentElement.clientWidth / 2) - (cx * scale);
        offsetY = (canvas.parentElement.clientHeight / 2) - (cy * scale);
        drawCanvas();
    }
}

// Canvas Drawing
function drawCanvas() {
    if (!currentImage.src) return;
    
    // Clear and set size based on container
    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;

    // Fill background
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(offsetX, offsetY);
    ctx.scale(scale, scale);

    // Draw Image
    ctx.drawImage(currentImage, 0, 0);

    // Draw bounding boxes
    if (currentData && currentData.lines) {
        currentData.lines.forEach(line => {
            if (!line.bbox) return;
            const [x1, y1, x2, y2] = line.bbox;
            const width = x2 - x1;
            const height = y2 - y1;

            if (line.id === activeLineId) {
                ctx.fillStyle = 'rgba(187, 134, 252, 0.3)';
                ctx.fillRect(x1, y1, width, height);
                ctx.strokeStyle = '#bb86fc';
                ctx.lineWidth = 2 / scale;
            } else {
                ctx.strokeStyle = 'rgba(3, 218, 198, 0.5)';
                ctx.lineWidth = 1 / scale;
            }
            ctx.strokeRect(x1, y1, width, height);
        });
    }

    ctx.restore();
}

function resetView() {
    const container = canvas.parentElement;
    // Fit to width
    scale = container.clientWidth / currentImage.width;
    offsetX = 0;
    offsetY = 0;
    drawCanvas();
}

// --- Interactions ---

// Line Operations
function moveLine(e, index, dir) {
    e.stopPropagation();
    const newIdx = index + dir;
    if (newIdx >= 0 && newIdx < currentData.lines.length) {
        const temp = currentData.lines[index];
        currentData.lines[index] = currentData.lines[newIdx];
        currentData.lines[newIdx] = temp;
        renderEditor();
        if (activeLineId) setActiveLine(activeLineId);
    }
}

function mergeLines(e, index) {
    e.stopPropagation();
    if (index < currentData.lines.length - 1) {
        const curr = currentData.lines[index];
        const next = currentData.lines[index + 1];
        
        curr.text = curr.text + " " + next.text;
        
        // Merge bounding boxes
        if (curr.bbox && next.bbox) {
            curr.bbox = [
                Math.min(curr.bbox[0], next.bbox[0]),
                Math.min(curr.bbox[1], next.bbox[1]),
                Math.max(curr.bbox[2], next.bbox[2]),
                Math.max(curr.bbox[3], next.bbox[3])
            ];
        }
        
        currentData.lines.splice(index + 1, 1);
        renderEditor();
        setActiveLine(curr.id);
    }
}

function splitLine(e, index) {
    e.stopPropagation();
    const curr = currentData.lines[index];
    const newId = `line_${Date.now()}`;
    
    const parts = curr.text.split(' ');
    const half = Math.floor(parts.length / 2);
    
    const t1 = parts.slice(0, half).join(' ');
    const t2 = parts.slice(half).join(' ');
    
    curr.text = t1;
    
    const newLine = {
        id: newId,
        text: t2,
        bbox: curr.bbox, // simple duplicate for now, real UI might let user draw
        confidence: curr.confidence
    };
    
    currentData.lines.splice(index + 1, 0, newLine);
    renderEditor();
}

// Save
document.getElementById('save-btn').onclick = async () => {
    try {
        const res = await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentData)
        });
        if (res.ok) {
            alert('Başarıyla dışa aktarıldı (Fine-Tuning Dataset hazır)!');
        } else {
            alert('Kaydetme hatası!');
        }
    } catch (e) {
        alert('Sunucuya bağlanılamadı.');
    }
};

// Zoom Controls
document.getElementById('zoom-in').onclick = () => { scale *= 1.2; drawCanvas(); };
document.getElementById('zoom-out').onclick = () => { scale /= 1.2; drawCanvas(); };
document.getElementById('zoom-reset').onclick = resetView;

// Pan with Mouse
canvas.onmousedown = (e) => {
    isDragging = true;
    startX = e.clientX - offsetX;
    startY = e.clientY - offsetY;
};
canvas.onmousemove = (e) => {
    if (isDragging) {
        offsetX = e.clientX - startX;
        offsetY = e.clientY - startY;
        drawCanvas();
    }
};
canvas.onmouseup = () => isDragging = false;
canvas.onmouseleave = () => isDragging = false;

window.onresize = drawCanvas;

// Init
loadData();
