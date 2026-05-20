let isChatMode = false;

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
}

function handleFile(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('previewBox').innerHTML = `<img src="${URL.createObjectURL(file)}" style="height:50px; border-radius:8px; margin-bottom:10px; border: 1px solid var(--primary);">`;
    }
}

function toggleMic() {
    const recognition = new (window.webkitSpeechRecognition || window.SpeechRecognition)();
    recognition.onstart = () => document.getElementById('micBtn').style.color = 'red';
    recognition.onresult = (e) => document.getElementById('userInput').value = e.results[0][0].transcript;
    recognition.onend = () => document.getElementById('micBtn').style.color = '#94a3b8';
    recognition.start();
}

async function sendQuery() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    const file = document.getElementById('fileInput').files[0];
    if (!text && !file) return;

    if (!isChatMode) {
        document.body.classList.add('chat-mode');
        document.getElementById('sidebar').classList.remove('active');
        isChatMode = true;
    }

    const chatWindow = document.getElementById('chatWindow');
    chatWindow.innerHTML += `<div class="message user-msg">${text}</div>`;
    input.value = "";
    document.getElementById('previewBox').innerHTML = "";

    // Add Thinking UI
    let aiDiv = document.createElement("div");
    aiDiv.className = "message ai-msg";
    aiDiv.innerHTML = `<div class="thinking-icon"></div><span style="color:var(--primary); font-weight:600; font-size:0.9rem;">NEXUS ANALYZING...</span>`;
    chatWindow.appendChild(aiDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    const formData = new FormData();
    formData.append("message", text);
    if (file) formData.append("image", file);

    try {
        const response = await fetch("http://127.0.0.1:8001/chat", { method: "POST", body: formData });
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        aiDiv.innerHTML = ""; // Remove thinking icon once stream starts

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            aiDiv.innerHTML += decoder.decode(value)
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    } catch (e) {
        aiDiv.innerHTML = "⚠️ Connection to Backend failed. Ensure Port 8001 is running.";
    }
}