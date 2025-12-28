document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const promptInput = document.getElementById('prompt-input');
    const sendBtn = document.getElementById('send-btn');
    const modelSelect = document.getElementById('model-select');
    const profileSelect = document.getElementById('profile-select');
    const logList = document.getElementById('log-list');

    // Modals & Buttons
    const infoBtn = document.getElementById('info-btn');
    const createBtn = document.getElementById('create-btn');
    const infoModal = document.getElementById('infoModal');
    const createModal = document.getElementById('createModal');
    const saveProfileBtn = document.getElementById('save-profile-btn');
    const closeBtns = document.querySelectorAll('.close-btn');

    // State
    let currentModel = modelSelect.value;
    let lastProcessedLogId = 0; // Track processed logs for notifications
    let allProfiles = []; // Store full profile metadata

    // --- Profile Management ---

    async function fetchProfiles() {
        try {
            const res = await fetch('/api/profiles');
            const data = await res.json();
            allProfiles = data.profiles; // Store for info modal

            // Populate Select
            profileSelect.innerHTML = '';

            // Add groups: Base vs Custom
            const baseGroup = document.createElement('optgroup');
            baseGroup.label = "Standard Profiles";
            const customGroup = document.createElement('optgroup');
            customGroup.label = "Custom Profiles";

            data.profiles.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.path; // Use path as value
                opt.textContent = p.name;
                opt.selected = p.name === data.active_profile;

                if (p.path.includes('custom/')) {
                    customGroup.appendChild(opt);
                } else {
                    baseGroup.appendChild(opt);
                }
            });

            if (baseGroup.children.length > 0) profileSelect.appendChild(baseGroup);
            if (customGroup.children.length > 0) profileSelect.appendChild(customGroup);

        } catch (e) {
            console.error("Failed to fetch profiles", e);
            showToast("Failed to load profiles", "error");
        }
    }

    profileSelect.addEventListener('change', async (e) => {
        const path = e.target.value;
        try {
            const res = await fetch('/api/profiles/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_path: path })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast(`Switched to ${data.active_profile}`);
                addSystemMessage(`Security Profile switched to: ${data.active_profile}`);
            }
        } catch (e) {
            showToast("Failed to switch profile", "error");
        }
    });

    // --- Modal Interaction ---

    // Open Info Modal
    infoBtn.addEventListener('click', () => {
        const activePath = profileSelect.value;
        const profile = allProfiles.find(p => p.path === activePath);

        if (profile) {
            const contentDiv = document.getElementById('infoContent');
            const features = profile.features && profile.features.length > 0
                ? profile.features.map(f => `<span class="feature-tag">${f}</span>`).join('')
                : '<span>Standard protections</span>';

            contentDiv.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h3>${profile.name}</h3>
                    <p style="margin-top: 8px; color: var(--text-primary);">${profile.description}</p>
                </div>
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 8px; font-size: 0.9rem; color: var(--text-secondary);">Active Features</h4>
                    <div>${features}</div>
                </div>
                <div>
                    <h4 style="margin-bottom: 8px; font-size: 0.9rem; color: var(--text-secondary);">Configuration (Snippet)</h4>
                    <pre style="background: var(--bg-input); padding: 12px; border-radius: 8px; overflow-x: auto; font-family: var(--font-mono); font-size: 0.85rem;">${JSON.stringify(profile.raw_config, null, 2).slice(0, 500)}...</pre>
                </div>
            `;
            infoModal.classList.add('show');
        }
    });

    // Open Create Modal
    createBtn.addEventListener('click', () => {
        // Pre-fill with template
        document.getElementById('new-profile-yaml').value = `profile_name: "custom_v1"
description: "My custom experiment"
detectors:
  pii:
    enabled: true
    patterns: 
      - "PHONE"
  injection:
    enabled: true
    keywords:
      - "ignore previous instructions"
  topics:
    enabled: true
    banned_topics:
      - "politics"
      - "competitors"
`;
        createModal.classList.add('show');
    });

    // Close Modals
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            infoModal.classList.remove('show');
            createModal.classList.remove('show');
        });
    });

    // Close on click outside
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('show');
        }
    });

    // Save New Profile
    saveProfileBtn.addEventListener('click', async () => {
        const name = document.getElementById('new-profile-name').value.trim();
        const yamlContent = document.getElementById('new-profile-yaml').value.trim();

        if (!name || !yamlContent) {
            showToast("Please provide name and config", "error");
            return;
        }

        try {
            saveProfileBtn.textContent = "Saving...";
            const res = await fetch('/api/profiles/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: name, content: yamlContent })
            });
            const data = await res.json();

            if (res.ok) {
                showToast("Profile Created Successfully!");
                createModal.classList.remove('show');
                // Refresh list and switch
                await fetchProfiles();
                // Find new profile option
                const newOption = Array.from(profileSelect.options).find(o => o.text.includes(name) || o.value.includes(name));
                if (newOption) {
                    profileSelect.value = newOption.value;
                    profileSelect.dispatchEvent(new Event('change')); // Trigger switch
                }
            } else {
                showToast(data.detail || "Failed to create", "error");
            }
        } catch (e) {
            showToast("Error creating profile", "error");
        } finally {
            saveProfileBtn.textContent = "Save & Switch";
        }
    });

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

    // --- Toast Notification ---
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return; // Safety check

        const toast = document.createElement('div');

        let icon = '✅';
        let className = 'toast'; // Start invisible

        if (type === 'pii-redacted') {
            icon = '🛡️';
            className += ' pii-redacted';
        }

        toast.className = className;
        toast.innerHTML = `<span class="toast-icon">${icon}</span> ${escapeHtml(message)}`;

        container.appendChild(toast);

        // Trigger reflow/animation
        requestAnimationFrame(() => {
            toast.classList.add('visible');
        });

        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }

    // --- Real-time Logs ---

    async function fetchLogs() {
        try {
            const res = await fetch('/api/logs');
            const logs = await res.json();

            if (logs.length > 0) {
                if (logList.querySelector('.empty-state')) {
                    logList.innerHTML = '';
                }

                // Render Logs
                renderLogs(logs);

                // Check for new logs and PII redaction
                // We only check logs newer than what we've seen to avoid spamming on reload
                const newLogs = logs.filter(l => l.id > lastProcessedLogId);


                newLogs.forEach(log => {
                    // Check if PII was redacted
                    const isRedacted = log.original_prompt !== log.sanitized_prompt;

                    console.log(`[DEBUG] Log ${log.id}:`);
                    console.log(`Original: "${log.original_prompt}"`);
                    console.log(`Sanitized: "${log.sanitized_prompt}"`);
                    console.log(`Is Redacted: ${isRedacted}`);
                    console.log(`Verdict: ${log.verdict}`);

                    if (isRedacted && log.verdict === "PASSED") {
                        showToast("PII Redacted & Secured!", "pii-redacted");
                    }
                });

                if (newLogs.length > 0) {
                    lastProcessedLogId = Math.max(...newLogs.map(l => l.id));
                }
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
    fetchProfiles(); // Load metadata
});
