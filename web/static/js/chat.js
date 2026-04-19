/**
 * Chat WebSocket client.
 * Gerencia conexão, envio/recebimento de mensagens e UI do chat.
 */

let ws = null;
let currentAgentId = 'gestor';
let isConnected = false;
let reconnectAttempts = 0;
const MAX_RECONNECT = 5;

// Cache de mensagens por agente (para exibição rápida ao trocar)
const messageCache = {};

// ── WebSocket ───────────────────────────────────────────────────

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws/chat`);

    ws.onopen = () => {
        isConnected = true;
        reconnectAttempts = 0;
        console.log('WebSocket conectado');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'message') {
            hideTypingIndicator();
            appendMessage('assistant', data.content, data.agent_id, data.avatar, data.timestamp);

            // Cachear
            if (!messageCache[data.agent_id]) messageCache[data.agent_id] = [];
            messageCache[data.agent_id].push({
                role: 'assistant', content: data.content,
                avatar: data.avatar, timestamp: data.timestamp
            });
        }
        else if (data.type === 'typing') {
            showTypingIndicator(data.agent_id);
        }
        else if (data.type === 'error') {
            hideTypingIndicator();
            showError(data.message);
        }
    };

    ws.onclose = () => {
        isConnected = false;
        console.log('WebSocket desconectado');
        if (reconnectAttempts < MAX_RECONNECT) {
            reconnectAttempts++;
            setTimeout(connectWebSocket, 2000 * reconnectAttempts);
        }
    };

    ws.onerror = (err) => {
        console.error('WebSocket erro:', err);
    };
}

// ── Enviar mensagem ─────────────────────────────────────────────

function sendMessage(event) {
    event.preventDefault();
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message || !isConnected) return;

    // Exibir mensagem do usuário
    const now = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    appendMessage('user', message, null, null, now);

    // Cachear
    if (!messageCache[currentAgentId]) messageCache[currentAgentId] = [];
    messageCache[currentAgentId].push({ role: 'user', content: message, timestamp: now });

    // Enviar via WebSocket
    ws.send(JSON.stringify({
        type: 'message',
        agent_id: currentAgentId,
        content: message,
        condominio: 'parque_colibri',
    }));

    // Limpar input
    input.value = '';
    autoResize(input);

    // Esconder welcome
    const welcome = document.getElementById('welcome-message');
    if (welcome) welcome.style.display = 'none';
}

// ── Selecionar agente ───────────────────────────────────────────

function selectAgent(agentId) {
    currentAgentId = agentId;
    const agent = AGENTS.find(a => a.id === agentId);
    if (!agent) return;

    // Atualizar sidebar
    document.querySelectorAll('.agent-btn').forEach(btn => {
        btn.classList.remove('active-agent', 'bg-blue-600/30');
    });
    const activeBtn = document.querySelector(`.agent-btn[data-agent-id="${agentId}"]`);
    if (activeBtn) activeBtn.classList.add('active-agent');

    // Atualizar header
    document.getElementById('header-avatar').textContent = agent.avatar;
    document.getElementById('header-name').textContent = agent.name;
    document.getElementById('header-role').textContent = agent.role;

    // Limpar mensagens e mostrar welcome ou cache
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';

    if (messageCache[agentId] && messageCache[agentId].length > 0) {
        // Restaurar do cache
        messageCache[agentId].forEach(msg => {
            appendMessage(msg.role, msg.content, agentId, msg.avatar || agent.avatar, msg.timestamp);
        });
    } else {
        // Carregar do servidor
        loadHistory(agentId, agent);
    }

    // Foco no input
    document.getElementById('message-input').focus();
}

// ── Carregar histórico ──────────────────────────────────────────

function loadHistory(agentId, agent) {
    const messagesDiv = document.getElementById('messages');

    fetch(`/api/chat/history/${agentId}`)
        .then(r => r.json())
        .then(data => {
            if (data.messages && data.messages.length > 0) {
                messageCache[agentId] = [];
                data.messages.forEach(msg => {
                    const time = msg.created_at ?
                        new Date(msg.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) :
                        '';
                    appendMessage(msg.role, msg.content, agentId,
                        msg.role === 'assistant' ? agent.avatar : null, time);
                    messageCache[agentId].push({
                        role: msg.role, content: msg.content,
                        avatar: agent.avatar, timestamp: time
                    });
                });
            } else {
                showWelcome(agent);
            }
        })
        .catch(() => {
            showWelcome(agent);
        });
}

function showWelcome(agent) {
    const messagesDiv = document.getElementById('messages');
    const welcomeHTML = `
        <div class="text-center py-12 welcome-fade" id="welcome-message">
            <span class="text-6xl block mb-4">${agent.avatar}</span>
            <h3 class="text-xl font-semibold text-gray-700">${agent.name}</h3>
            <p class="text-gray-500 mt-1">${agent.role}</p>
            <p class="text-gray-400 text-sm mt-4 max-w-md mx-auto">${agent.description}</p>
        </div>
    `;
    messagesDiv.innerHTML = welcomeHTML;
}

// ── Renderizar mensagens ────────────────────────────────────────

function appendMessage(role, content, agentId, avatar, timestamp) {
    const messagesDiv = document.getElementById('messages');
    const container = document.getElementById('messages-container');

    // Esconder welcome se presente
    const welcome = document.getElementById('welcome-message');
    if (welcome) welcome.style.display = 'none';

    const msgDiv = document.createElement('div');
    msgDiv.className = `message-${role} message-enter`;

    // Formatar conteúdo (simples markdown)
    const formattedContent = formatContent(content);

    if (role === 'user') {
        msgDiv.innerHTML = `
            <div>
                <div class="bubble">${formattedContent}</div>
                <div class="message-time text-right">${timestamp || ''}</div>
            </div>
        `;
    } else {
        const ag = agentId ? AGENTS.find(a => a.id === agentId) : null;
        const displayAvatar = avatar || (ag ? ag.avatar : '🤖');
        msgDiv.innerHTML = `
            <span class="avatar">${displayAvatar}</span>
            <div>
                <div class="bubble">${formattedContent}</div>
                <div class="message-time">${timestamp || ''}</div>
            </div>
        `;
    }

    messagesDiv.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function formatContent(text) {
    if (!text) return '';
    // Escape HTML
    let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    // Bold **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic *text*
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Inline code `text`
    html = html.replace(/`(.*?)`/g, '<code class="bg-gray-200 px-1 rounded text-sm">$1</code>');
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    return html;
}

// ── Typing indicator ────────────────────────────────────────────

function showTypingIndicator(agentId) {
    const agent = AGENTS.find(a => a.id === agentId);
    if (!agent) return;

    const indicator = document.getElementById('typing-indicator');
    document.getElementById('typing-avatar').textContent = agent.avatar;
    document.getElementById('typing-name').textContent = agent.name;
    indicator.classList.remove('hidden');

    // Scroll
    const container = document.getElementById('messages-container');
    container.scrollTop = container.scrollHeight;
}

function hideTypingIndicator() {
    document.getElementById('typing-indicator').classList.add('hidden');
}

// ── Error display ───────────────────────────────────────────────

function showError(message) {
    const messagesDiv = document.getElementById('messages');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-center py-2 message-enter';
    errorDiv.innerHTML = `
        <span class="inline-block px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm">
            ⚠️ ${formatContent(message)}
        </span>
    `;
    messagesDiv.appendChild(errorDiv);
}

// ── File upload ─────────────────────────────────────────────────

function uploadFile(input) {
    const file = input.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('condominio', 'parque_colibri');

    // Mostrar indicador
    const now = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    appendMessage('user', `📎 Enviando arquivo: ${file.name}...`, null, null, now);

    fetch('/api/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                // Notificar o agente sobre o upload
                const msg = `Acabei de enviar o arquivo "${file.name}" (salvo como ${data.filename}). O caminho completo é: ${data.path}`;
                if (isConnected) {
                    ws.send(JSON.stringify({
                        type: 'message',
                        agent_id: currentAgentId,
                        content: msg,
                        condominio: 'parque_colibri',
                    }));
                }
            }
        })
        .catch(err => {
            showError('Erro ao enviar arquivo: ' + err.message);
        });

    // Limpar input
    input.value = '';
}

// ── Input helpers ───────────────────────────────────────────────

function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage(event);
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

// ── Init ────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();

    // Carregar histórico do agente inicial (gestor)
    const gestor = AGENTS.find(a => a.id === 'gestor');
    if (gestor) {
        loadHistory('gestor', gestor);
    }

    // Foco no input
    document.getElementById('message-input').focus();
});
