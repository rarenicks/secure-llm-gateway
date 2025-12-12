document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const promptInput = document.getElementById('prompt-input');
    const sendBtn = document.getElementById('send-btn');
    const modelSelect = document.getElementById('model-select');
    const logList = document.getElementById('log-list');

    // State
    let currentModel = modelSelect.value;
    let lastLogId = 0;

    // --- Interaction ---

    modelSelect.addEventListener('change', (e) => {
        currentModel = e.target.value;
        addSystemMessage(`Switched to model: ${currentModel}`);
    });

    sendBtn.addEventListener('click', sendMessage);
    promptInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    async function sendMessage() {
        const text = promptInput.value.trim();
        if (!text) return;

        // UI Updates
        promptInput.value = '';
        addMessage('user', text);
        
        // Simulating "Thinking" state could be added here
        
        try {
            const response = await fetch('/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: currentModel,
                    messages: [{ role: 'user', content: text }]
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                const content = data.choices[0].message.content;
                addMessage('assistant', content);
            } else {
                // Handle security blocks or errors
                if (data.error && data.error.message) {
                    addMessage('system', `⚠️ Blocked/Error: ${data.error.message}`);
                } else {
                    addMessage('system', '⚠️ An unknown error occurred.');
                }
            }
        } catch (error) {
            addMessage('system', `⚠️ Connection failed: ${error.message}`);
        }
        
        // Trigger immediate log refresh
        fetchLogs();
    }

    function addMessage(role, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        msgDiv.innerHTML = `<div class="content">${escapeHtml(text)}</div>`;
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function addSystemMessage(text) {
        addMessage('system', text);
    }

    // --- Real-time Logs ---

    async function fetchLogs() {
        try {
            const res = await fetch('/api/logs');
            const logs = await res.json();
            
            if (logs.length > 0) {
                // Clear empty state if exists
                if (logList.querySelector('.empty-state')) {
                    logList.innerHTML = '';
                }
                
                // Only prepend new logs. 
                // Simple implementation: Re-render list if top ID changed to keep it synced.
                // For a robust system, we'd check IDs. keeping it simple: render all recent.
                
                // Optimization: Just replace content if it changed
                renderLogs(logs);
            }
        } catch (e) {
            console.error("Failed to fetch logs", e);
        }
    }

    function renderLogs(logs) {
        // Simple full re-render for this demo (performance is fine for <20 items)
        logList.innerHTML = ''; 
        
        logs.forEach(log => {
            const card = document.createElement('div');
            
            let statusClass = 'passed';
            if (log.verdict !== 'PASSED') statusClass = log.verdict.includes('BLOCKED') ? 'blocked' : 'failed';
            
            card.className = `log-card ${statusClass}`;
            
            const time = new Date(log.timestamp).toLocaleTimeString();
            const latencyMs = (log.latency * 1000).toFixed(0);
            
            card.innerHTML = `
                <div class="log-meta">
                    <span>${time}</span>
                    <span>${latencyMs}ms</span>
                </div>
                <div class="log-verdict">${log.verdict}</div>
                <div class="log-prompt" title="${escapeHtml(log.original_prompt)}">
                    ${escapeHtml(log.original_prompt)}
                </div>
            `;
            logList.appendChild(card);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Polling for logs every 2 seconds
    setInterval(fetchLogs, 2000);
    fetchLogs(); // Initial load
});
