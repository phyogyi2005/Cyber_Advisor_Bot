/**
 * Cyber Advisor AI Engine with Sidebar History, Light/Dark Theme & CORS API Support
 */

document.addEventListener('DOMContentLoaded', () => {
    let currentMode = 'normal';
    let isProcessing = false;
    let chartCounter = 0;
    
    // API Host configuration (from config.js or fallback)
    const BASE_URL = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : '';

    // Conversation State Management
    let conversations = JSON.parse(localStorage.getItem('cyberadvisor_history') || '[]');
    let activeSessionId = localStorage.getItem('cyberadvisor_active_id') || createNewSessionId();

    // Elements
    const chatFeed = document.getElementById('chatFeed');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const modePills = document.querySelectorAll('.mode-pill');

    // Sidebar & History Elements
    const sidebarPanel = document.getElementById('sidebarPanel');
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const newChatBtn = document.getElementById('newChatBtn');
    const historyList = document.getElementById('historyList');
    const clearAllHistoryBtn = document.getElementById('clearAllHistoryBtn');

    // Theme Toggle Setup
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const htmlElement = document.documentElement;

    const savedTheme = localStorage.getItem('cyberadvisor_theme') || 'dark';
    setTheme(savedTheme);

    themeToggleBtn.addEventListener('click', () => {
        const activeTheme = htmlElement.getAttribute('data-theme');
        const nextTheme = activeTheme === 'dark' ? 'light' : 'dark';
        setTheme(nextTheme);
    });

    function setTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);
        localStorage.setItem('cyberadvisor_theme', theme);
        if (theme === 'light') {
            themeIcon.className = 'fa-solid fa-sun';
            themeToggleBtn.title = 'Switch to Dark Theme';
        } else {
            themeIcon.className = 'fa-solid fa-moon';
            themeToggleBtn.title = 'Switch to Light Theme';
        }
    }


    // 1. Sidebar Toggle & History Rendering
    sidebarToggleBtn.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            sidebarPanel.classList.toggle('open');
            sidebarOverlay.classList.toggle('hidden');
        } else {
            sidebarPanel.classList.toggle('collapsed');
        }
    });

    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', () => {
            sidebarPanel.classList.remove('open');
            sidebarOverlay.classList.add('hidden');
        });
    }

    sidebarOverlay.addEventListener('click', () => {
        sidebarPanel.classList.remove('open');
        sidebarOverlay.classList.add('hidden');
    });

    newChatBtn.addEventListener('click', () => {
        startNewChatSession();
    });

    clearAllHistoryBtn.addEventListener('click', () => {
        if (confirm("Are you sure you want to clear all chat history?")) {
            conversations = [];
            saveHistoryToStorage();
            startNewChatSession();
        }
    });

    function createNewSessionId() {
        return 'session_' + Date.now();
    }

    function startNewChatSession() {
        activeSessionId = createNewSessionId();
        localStorage.setItem('cyberadvisor_active_id', activeSessionId);
        
        chatFeed.innerHTML = `
            <div class="chat-row assistant-row">
                <div class="avatar assistant-avatar">
                    <i class="fa-solid fa-user-shield"></i>
                </div>
                <div class="bubble-box">
                    <div class="bubble-meta">Cyber Advisor AI</div>
                    <div class="markdown-body">
                        Hello! 👋 I am Cyber Advisor, your personal AI Security Assistant.
                        
                        Ask me any cybersecurity question, paste code to inspect for vulnerabilities, or click Check URL Safety to scan links for phishing & malware threats!
                    </div>
                </div>
            </div>
        `;
        renderHistoryList();
    }

    function renderHistoryList() {
        historyList.innerHTML = '';
        if (conversations.length === 0) {
            historyList.innerHTML = `<div style="padding: 0.5rem; font-size: 0.78rem; color: var(--text-muted);">No saved history yet.</div>`;
            return;
        }

        conversations.forEach(session => {
            const item = document.createElement('div');
            item.className = `history-item ${session.id === activeSessionId ? 'active' : ''}`;
            item.innerHTML = `
                <span class="history-item-text"><i class="fa-solid fa-message" style="margin-right: 6px; font-size: 0.75rem;"></i> ${escapeHtml(session.title)}</span>
                <button class="history-item-del" title="Delete Session"><i class="fa-solid fa-trash-can"></i></button>
            `;

            item.addEventListener('click', (e) => {
                if (e.target.closest('.history-item-del')) return;
                loadSession(session.id);
            });

            const delBtn = item.querySelector('.history-item-del');
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteSession(session.id);
            });

            historyList.appendChild(item);
        });
    }

    function loadSession(sessionId) {
        const session = conversations.find(s => s.id === sessionId);
        if (!session) return;

        activeSessionId = sessionId;
        localStorage.setItem('cyberadvisor_active_id', activeSessionId);
        chatFeed.innerHTML = '';

        session.messages.forEach(msg => {
            if (msg.type === 'user') {
                appendUserBubble(msg.text, false);
            } else if (msg.type === 'assistant') {
                appendAssistantBubble(msg.text, false);
            } else if (msg.type === 'link_result') {
                renderInlineScanResponse(msg.data, false);
            }
        });

        renderHistoryList();
        scrollToBottom();
    }

    function deleteSession(sessionId) {
        conversations = conversations.filter(s => s.id !== sessionId);
        saveHistoryToStorage();
        if (activeSessionId === sessionId) {
            startNewChatSession();
        } else {
            renderHistoryList();
        }
    }

    function saveMessageToCurrentSession(msgObj) {
        let session = conversations.find(s => s.id === activeSessionId);
        if (!session) {
            session = {
                id: activeSessionId,
                title: msgObj.text ? msgObj.text.substring(0, 28) : 'New Conversation',
                timestamp: Date.now(),
                messages: []
            };
            conversations.unshift(session);
        } else if (session.messages.length === 0 && msgObj.text) {
            session.title = msgObj.text.substring(0, 28);
        }

        session.messages.push(msgObj);
        saveHistoryToStorage();
        renderHistoryList();
    }

    function saveHistoryToStorage() {
        localStorage.setItem('cyberadvisor_history', JSON.stringify(conversations.slice(0, 25)));
    }

    renderHistoryList();


    // 2. Mode Pill Switching
    modePills.forEach(pill => {
        pill.addEventListener('click', () => {
            currentMode = pill.getAttribute('data-mode');
            modePills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            const modeName = currentMode === 'learning' ? 'Cyber Advisor Academy' : 'Normal Cyber Advisor';
            appendAssistantBubble(`Mode switched to ${modeName}.`);
        });
    });


    // 3. Chat Input & Messaging
    sendBtn.addEventListener('click', () => handleUserSend());
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleUserSend();
        }
    });

    function handleUserSend(customText = null) {
        const text = customText || chatInput.value.trim();
        if (!text || isProcessing) return;

        appendUserBubble(text);
        if (!customText) chatInput.value = '';

        if (isUrlString(text)) {
            executeLinkScan(text);
        } else {
            sendAiChatMessage(text);
        }
    }

    function isUrlString(str) {
        return str.startsWith('http://') || str.startsWith('https://') || (str.includes('.') && !str.includes(' ') && str.length > 5);
    }

    // AI Chat API call with configurable BASE_URL
    async function sendAiChatMessage(messageText) {
        isProcessing = true;
        const typingBubble = appendThinkingIndicator();

        try {
            const res = await fetch(`${BASE_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText, mode: currentMode })
            });
            const data = await res.json();
            
            typingBubble.remove();
            if (data.reply) {
                appendAssistantBubble(data.reply);
            } else {
                appendAssistantBubble(`⚠️ Error: ${data.error || 'Failed to generate response.'}`);
            }
        } catch (e) {
            typingBubble.remove();
            appendAssistantBubble(`⚠️ Network Error: Could not connect to backend server at ${BASE_URL || 'local server'}.`);
        } finally {
            isProcessing = false;
        }
    }


    // 4. Link Safety Scanner & Tool Overlay
    const linkToolModal = document.getElementById('linkToolModal');
    const openLinkToolBtn = document.getElementById('openLinkToolBtn');
    const closeToolModal = document.getElementById('closeToolModal');
    const modalUrlInput = document.getElementById('modalUrlInput');
    const modalScanBtn = document.getElementById('modalScanBtn');
    const miniPresetBtns = document.querySelectorAll('.mini-preset-btn');

    openLinkToolBtn.addEventListener('click', () => {
        linkToolModal.classList.remove('hidden');
        modalUrlInput.focus();
    });

    closeToolModal.addEventListener('click', () => {
        linkToolModal.classList.add('hidden');
    });

    miniPresetBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modalUrlInput.value = btn.getAttribute('data-url');
        });
    });

    modalScanBtn.addEventListener('click', () => {
        const targetUrl = modalUrlInput.value.trim();
        if (!targetUrl) return;

        linkToolModal.classList.add('hidden');
        modalUrlInput.value = '';

        appendUserBubble(`🔍 Scan link: ${targetUrl}`);
        executeLinkScan(targetUrl);
    });

    async function executeLinkScan(targetUrl) {
        isProcessing = true;

        const waitingBubble = document.createElement('div');
        waitingBubble.className = 'chat-row assistant-row';
        waitingBubble.innerHTML = `
            <div class="avatar assistant-avatar"><i class="fa-solid fa-user-shield"></i></div>
            <div class="bubble-box">
                <div class="bubble-meta">Cyber Advisor Threat Engine</div>
                <div class="markdown-body">
                    Scanning link security for <code>${escapeHtml(targetUrl)}</code>...
                </div>
                <div class="inline-radar-box">
                    <div class="radar-spinner"></div>
                    <span class="radar-text">Thinking & analyzing link threat vectors...</span>
                </div>
            </div>
        `;
        chatFeed.appendChild(waitingBubble);
        scrollToBottom();

        try {
            const startTime = Date.now();
            const res = await fetch(`${BASE_URL}/api/check_link`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: targetUrl })
            });
            const data = await res.json();

            const elapsed = Date.now() - startTime;
            const remaining = Math.max(0, 1400 - elapsed);

            setTimeout(() => {
                waitingBubble.remove();
                if (data.status === 'success') {
                    renderInlineScanResponse(data);
                } else {
                    appendAssistantBubble(`⚠️ Scan Failed: ${data.error || 'Invalid URL'}`);
                }
                isProcessing = false;
            }, remaining);

        } catch (e) {
            waitingBubble.remove();
            appendAssistantBubble(`⚠️ Network Error: Unable to complete URL scan.`);
            isProcessing = false;
        }
    }

    // Render Threat Analysis & Bar Chart inside Chat
    function renderInlineScanResponse(data, saveToHistory = true) {
        chartCounter++;
        const canvasId = `inlineChart_${chartCounter}`;
        const analysis = data.analysis;
        const score = Math.round(analysis.overall_risk_score);
        
        let ratingClass = 'danger';
        if (score < 30) ratingClass = 'safe';
        else if (score < 60) ratingClass = 'warning';

        const row = document.createElement('div');
        row.className = 'chat-row assistant-row';

        const riskFactorsHtml = analysis.risk_factors.map(f => `
            <div class="inline-finding-item">
                <i class="fa-solid fa-triangle-exclamation danger-icon"></i>
                <span>${escapeHtml(f)}</span>
            </div>
        `).join('');

        row.innerHTML = `
            <div class="avatar assistant-avatar"><i class="fa-solid fa-shield-virus"></i></div>
            <div class="bubble-box" style="width: 100%;">
                <div class="bubble-meta">URL Threat Analysis Report</div>
                <div class="markdown-body">
                    <strong>Target URL:</strong> <code>${escapeHtml(data.url)}</code>
                </div>

                <div class="inline-link-card">
                    <div class="inline-verdict-header">
                        <span class="verdict-tag ${ratingClass}">${analysis.safety_rating.replace('_', ' ')}</span>
                        <span class="score-badge" style="color: ${score > 50 ? '#ef4444' : '#10b981'};">RISK SCORE: ${score}%</span>
                    </div>

                    <div class="markdown-body">
                        <strong>${escapeHtml(analysis.verdict_title)}</strong>
                        <p>${escapeHtml(analysis.summary)}</p>
                    </div>

                    <!-- Bar Chart Canvas -->
                    <div class="inline-chart-container">
                        <canvas id="${canvasId}"></canvas>
                    </div>

                    <div class="inline-findings">
                        <strong>Key Threat Factors:</strong>
                        ${riskFactorsHtml}
                    </div>
                </div>
            </div>
        `;

        chatFeed.appendChild(row);
        scrollToBottom();

        if (saveToHistory) {
            saveMessageToCurrentSession({ type: 'link_result', text: `Scan: ${data.url}`, data: data });
        }

        setTimeout(() => {
            renderInlineThreatChart(canvasId, analysis.chart_data.labels, analysis.chart_data.scores);
        }, 100);
    }


    // 5. Quick Prompts & Helpers
    document.querySelectorAll('.quick-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const prompt = chip.getAttribute('data-prompt');
            handleUserSend(prompt);
        });
    });

    function appendUserBubble(text, saveToHistory = true) {
        const row = document.createElement('div');
        row.className = 'chat-row user-row';
        row.innerHTML = `
            <div class="avatar user-avatar"><i class="fa-solid fa-user-ninja"></i></div>
            <div class="bubble-box">
                <div class="bubble-meta">You</div>
                <div class="markdown-body">${escapeHtml(text)}</div>
            </div>
        `;
        chatFeed.appendChild(row);
        scrollToBottom();

        if (saveToHistory) {
            saveMessageToCurrentSession({ type: 'user', text: text });
        }
    }

    function appendAssistantBubble(text, saveToHistory = true) {
        const row = document.createElement('div');
        row.className = 'chat-row assistant-row';
        row.innerHTML = `
            <div class="avatar assistant-avatar"><i class="fa-solid fa-user-shield"></i></div>
            <div class="bubble-box">
                <div class="bubble-meta">Cyber Advisor AI</div>
                <div class="markdown-body">${marked.parse(text)}</div>
            </div>
        `;
        chatFeed.appendChild(row);
        scrollToBottom();

        if (saveToHistory) {
            saveMessageToCurrentSession({ type: 'assistant', text: text });
        }
    }

    // Animated Thinking Indicator ("Thinking...")
    function appendThinkingIndicator() {
        const row = document.createElement('div');
        row.className = 'chat-row assistant-row';
        row.innerHTML = `
            <div class="avatar assistant-avatar"><i class="fa-solid fa-user-shield"></i></div>
            <div class="bubble-box">
                <div class="markdown-body text-muted thinking-row">
                    <span class="thinking-text">Thinking</span>
                    <span class="thinking-dots">
                        <span>.</span><span>.</span><span>.</span>
                    </span>
                </div>
            </div>
        `;
        chatFeed.appendChild(row);
        scrollToBottom();
        return row;
    }

    function scrollToBottom() {
        chatFeed.scrollTop = chatFeed.scrollHeight;
    }

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
});
