document.addEventListener("DOMContentLoaded", () => {
    loadDocumentDetails();
    setupChat();
});

async function loadDocumentDetails() {
    try {
        const res = await fetch('/api/doc_details');
        const data = await res.json();
        
        document.getElementById('doc-ottoman').innerText = data.ottoman;
        document.getElementById('doc-academic').innerText = data.academic;
        document.getElementById('doc-modern').innerText = data.modern;
        
        const entitiesContainer = document.getElementById('doc-entities');
        entitiesContainer.innerHTML = ''; // clear loading
        
        // Render entities
        const renderEntity = (list, colorClass, icon) => {
            list.forEach(item => {
                const span = document.createElement('span');
                span.className = `text-xs px-2 py-1 rounded border ${colorClass} bg-opacity-10`;
                span.innerHTML = `<i class="${icon} mr-1"></i> ${item}`;
                entitiesContainer.appendChild(span);
            });
        };
        
        renderEntity(data.entities.PERSON, 'border-blue-500 text-blue-400 bg-blue-500', 'fa-solid fa-user');
        renderEntity(data.entities.LOCATION, 'border-green-500 text-green-400 bg-green-500', 'fa-solid fa-location-dot');
        renderEntity(data.entities.DATE, 'border-yellow-500 text-yellow-400 bg-yellow-500', 'fa-solid fa-calendar');
        renderEntity(data.entities.ORGANIZATION, 'border-purple-500 text-purple-400 bg-purple-500', 'fa-solid fa-building');
        
        if (entitiesContainer.innerHTML === '') {
            entitiesContainer.innerHTML = '<span class="text-gray-500 italic">Hiç varlık tespit edilemedi.</span>';
        }
    } catch (e) {
        console.error("Belge detayları yüklenemedi", e);
    }
}

function setupChat() {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');

    const appendMessage = (text, isUser) => {
        const div = document.createElement('div');
        div.className = `chat-bubble ${isUser ? 'chat-user text-white' : 'chat-bot text-gray-200'}`;
        div.innerText = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    };

    form.onsubmit = async (e) => {
        e.preventDefault();
        const msg = input.value.trim();
        if (!msg) return;
        
        // Show User Message
        appendMessage(msg, true);
        input.value = '';
        input.disabled = true;

        // Show thinking indicator
        const typingId = Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.id = `typing-${typingId}`;
        typingDiv.className = 'text-gray-500 text-sm ml-4 mb-4 italic';
        typingDiv.innerText = 'RAG Asistan düşünüyor...';
        messages.appendChild(typingDiv);
        messages.scrollTop = messages.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg, doc_id: "doc_mock_001" })
            });
            const data = await res.json();
            
            // Remove typing
            document.getElementById(`typing-${typingId}`).remove();
            
            // Show Bot Message
            appendMessage(data.reply, false);
        } catch (e) {
            document.getElementById(`typing-${typingId}`).remove();
            appendMessage("Üzgünüm, sunucuya bağlanırken bir hata oluştu.", false);
        } finally {
            input.disabled = false;
            input.focus();
        }
    };
}
