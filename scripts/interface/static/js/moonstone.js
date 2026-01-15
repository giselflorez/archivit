/**
 * MOONSTONE - AI Brain Interface for ARCHIV-IT
 *
 * Embeddable AI chat component for troubleshooting and assistance.
 * Uses Claude API via backend proxy for secure communication.
 *
 * Usage:
 *   <div id="moonstone-container"></div>
 *   <script src="/static/js/moonstone.js"></script>
 *   <script>
 *     Moonstone.init({
 *       container: '#moonstone-container',
 *       context: 'NFT-8 Minting',
 *       apiEndpoint: '/api/ai/chat'
 *     });
 *   </script>
 */

const Moonstone = (function() {
    'use strict';

    // Configuration
    let config = {
        container: null,
        context: 'ARCHIV-IT',
        apiEndpoint: '/api/ai/chat',
        maxHistory: 10,
        placeholder: 'Describe your issue or ask a question...',
        systemPrompt: null
    };

    // State
    let chatHistory = [];
    let isLoading = false;
    let isMinimized = false;

    // DOM Elements
    let elements = {};

    /**
     * Initialize Moonstone
     */
    function init(options = {}) {
        config = { ...config, ...options };

        if (typeof config.container === 'string') {
            config.container = document.querySelector(config.container);
        }

        if (!config.container) {
            console.error('Moonstone: Container not found');
            return;
        }

        render();
        attachEventListeners();
        loadHistory();

        console.log('Moonstone AI Brain initialized for:', config.context);
    }

    /**
     * Render the chat interface
     */
    function render() {
        const html = `
            <div class="moonstone-wrapper ${isMinimized ? 'minimized' : ''}">
                <div class="moonstone-header" onclick="Moonstone.toggle()">
                    <div class="moonstone-title">
                        <span class="moonstone-icon">◈</span>
                        <span>MOONSTONE</span>
                        <span class="moonstone-context">${config.context}</span>
                    </div>
                    <div class="moonstone-controls">
                        <button class="moonstone-btn-clear" onclick="Moonstone.clear(event)" title="Clear history">⟳</button>
                        <button class="moonstone-btn-toggle">${isMinimized ? '▲' : '▼'}</button>
                    </div>
                </div>

                <div class="moonstone-body">
                    <div class="moonstone-messages" id="moonstone-messages">
                        ${renderMessages()}
                        ${chatHistory.length === 0 ? renderWelcome() : ''}
                    </div>

                    <div class="moonstone-input-area">
                        <textarea
                            id="moonstone-input"
                            class="moonstone-input"
                            placeholder="${config.placeholder}"
                            rows="3"
                        ></textarea>
                        <div class="moonstone-actions">
                            <span class="moonstone-hint">Shift+Enter for new line</span>
                            <button class="moonstone-send" onclick="Moonstone.send()" ${isLoading ? 'disabled' : ''}>
                                ${isLoading ? '◌ Thinking...' : '◈ Send'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        config.container.innerHTML = html;

        // Cache elements
        elements.wrapper = config.container.querySelector('.moonstone-wrapper');
        elements.messages = config.container.querySelector('#moonstone-messages');
        elements.input = config.container.querySelector('#moonstone-input');

        // Inject styles if not present
        if (!document.getElementById('moonstone-styles')) {
            injectStyles();
        }
    }

    /**
     * Render welcome message
     */
    function renderWelcome() {
        return `
            <div class="moonstone-welcome">
                <div class="moonstone-welcome-icon">◈</div>
                <div class="moonstone-welcome-title">AI Brain Ready</div>
                <div class="moonstone-welcome-text">
                    I'm here to help you troubleshoot, understand features,
                    and solve problems. Ask me anything about ${config.context}.
                </div>
                <div class="moonstone-suggestions">
                    <button onclick="Moonstone.suggest('How do I upload to IPFS?')">How do I upload to IPFS?</button>
                    <button onclick="Moonstone.suggest('Scan my wallet for NFTs')">Scan my wallet</button>
                    <button onclick="Moonstone.suggest('Explain the minting process')">Explain minting</button>
                </div>
            </div>
        `;
    }

    /**
     * Render chat messages
     */
    function renderMessages() {
        return chatHistory.map(msg => `
            <div class="moonstone-message ${msg.role}">
                <div class="moonstone-message-header">
                    <span class="moonstone-role">${msg.role === 'user' ? 'You' : 'Moonstone'}</span>
                    <span class="moonstone-time">${formatTime(msg.timestamp)}</span>
                </div>
                <div class="moonstone-message-content">${formatContent(msg.content)}</div>
                ${msg.role === 'assistant' ? `
                    <div class="moonstone-message-actions">
                        <button onclick="Moonstone.copy('${escapeQuotes(msg.content)}')">Copy</button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    /**
     * Attach event listeners
     */
    function attachEventListeners() {
        const input = elements.input;
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    send();
                }
            });
        }
    }

    /**
     * Send message to AI
     */
    async function send() {
        const input = elements.input;
        const message = input?.value?.trim();

        if (!message || isLoading) return;

        // Add user message
        chatHistory.push({
            role: 'user',
            content: message,
            timestamp: Date.now()
        });

        input.value = '';
        isLoading = true;
        render();
        scrollToBottom();

        try {
            const response = await fetch(config.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    context: config.context,
                    history: chatHistory.slice(-config.maxHistory),
                    systemPrompt: config.systemPrompt
                })
            });

            const data = await response.json();

            if (data.success) {
                chatHistory.push({
                    role: 'assistant',
                    content: data.response,
                    timestamp: Date.now()
                });
            } else {
                chatHistory.push({
                    role: 'assistant',
                    content: `Error: ${data.error || 'Failed to get response'}`,
                    timestamp: Date.now()
                });
            }
        } catch (error) {
            chatHistory.push({
                role: 'assistant',
                content: `Connection error: ${error.message}. The AI endpoint may not be configured yet.`,
                timestamp: Date.now()
            });
        }

        isLoading = false;
        saveHistory();
        render();
        scrollToBottom();
    }

    /**
     * Suggest a message
     */
    function suggest(text) {
        const input = elements.input;
        if (input) {
            input.value = text;
            input.focus();
        }
    }

    /**
     * Toggle minimize/expand
     */
    function toggle() {
        isMinimized = !isMinimized;
        render();
    }

    /**
     * Clear chat history
     */
    function clear(event) {
        if (event) event.stopPropagation();
        chatHistory = [];
        saveHistory();
        render();
    }

    /**
     * Copy text to clipboard
     */
    function copy(text) {
        navigator.clipboard.writeText(text.replace(/\\n/g, '\n'));
    }

    /**
     * Save history to localStorage
     */
    function saveHistory() {
        try {
            const key = `moonstone_history_${config.context.replace(/\s+/g, '_')}`;
            localStorage.setItem(key, JSON.stringify(chatHistory.slice(-20)));
        } catch (e) {
            console.warn('Could not save Moonstone history:', e);
        }
    }

    /**
     * Load history from localStorage
     */
    function loadHistory() {
        try {
            const key = `moonstone_history_${config.context.replace(/\s+/g, '_')}`;
            const saved = localStorage.getItem(key);
            if (saved) {
                chatHistory = JSON.parse(saved);
                render();
            }
        } catch (e) {
            console.warn('Could not load Moonstone history:', e);
        }
    }

    /**
     * Scroll messages to bottom
     */
    function scrollToBottom() {
        if (elements.messages) {
            elements.messages.scrollTop = elements.messages.scrollHeight;
        }
    }

    /**
     * Format timestamp
     */
    function formatTime(ts) {
        const date = new Date(ts);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Format message content (basic markdown)
     */
    function formatContent(content) {
        return content
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank">$1</a>');
    }

    /**
     * Escape quotes for onclick
     */
    function escapeQuotes(str) {
        return str.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
    }

    /**
     * Inject CSS styles
     */
    function injectStyles() {
        const style = document.createElement('style');
        style.id = 'moonstone-styles';
        style.textContent = `
            .moonstone-wrapper {
                font-family: 'Inter', -apple-system, sans-serif;
                background: #0a0a12;
                border: 1px solid rgba(140, 160, 200, 0.2);
                border-radius: 12px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                max-height: 600px;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
            }

            .moonstone-wrapper.minimized .moonstone-body {
                display: none;
            }

            .moonstone-header {
                background: linear-gradient(135deg, rgba(90, 168, 185, 0.15), rgba(120, 101, 186, 0.15));
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
                border-bottom: 1px solid rgba(140, 160, 200, 0.1);
            }

            .moonstone-title {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #f0ece7;
                font-size: 0.85rem;
                font-weight: 300;
                letter-spacing: 0.1em;
            }

            .moonstone-icon {
                color: #5aa8b9;
                font-size: 1.2rem;
            }

            .moonstone-context {
                color: #7865ba;
                font-size: 0.7rem;
                padding: 2px 8px;
                background: rgba(120, 101, 186, 0.2);
                border-radius: 4px;
            }

            .moonstone-controls {
                display: flex;
                gap: 8px;
            }

            .moonstone-controls button {
                background: transparent;
                border: none;
                color: #9a9690;
                cursor: pointer;
                padding: 4px 8px;
                border-radius: 4px;
                transition: all 0.2s;
            }

            .moonstone-controls button:hover {
                background: rgba(90, 168, 185, 0.2);
                color: #5aa8b9;
            }

            .moonstone-body {
                display: flex;
                flex-direction: column;
                flex: 1;
                min-height: 300px;
            }

            .moonstone-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .moonstone-messages::-webkit-scrollbar {
                width: 4px;
            }

            .moonstone-messages::-webkit-scrollbar-thumb {
                background: #7865ba;
                border-radius: 2px;
            }

            .moonstone-welcome {
                text-align: center;
                padding: 40px 20px;
                color: #9a9690;
            }

            .moonstone-welcome-icon {
                font-size: 3rem;
                color: #5aa8b9;
                margin-bottom: 16px;
            }

            .moonstone-welcome-title {
                font-size: 1.2rem;
                color: #f0ece7;
                margin-bottom: 8px;
                letter-spacing: 0.1em;
            }

            .moonstone-welcome-text {
                font-size: 0.85rem;
                line-height: 1.6;
                max-width: 400px;
                margin: 0 auto 20px;
            }

            .moonstone-suggestions {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                justify-content: center;
            }

            .moonstone-suggestions button {
                background: rgba(90, 168, 185, 0.1);
                border: 1px solid rgba(90, 168, 185, 0.3);
                color: #5aa8b9;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.75rem;
                cursor: pointer;
                transition: all 0.2s;
            }

            .moonstone-suggestions button:hover {
                background: rgba(90, 168, 185, 0.2);
                border-color: #5aa8b9;
            }

            .moonstone-message {
                background: rgba(255, 255, 255, 0.02);
                border-radius: 8px;
                padding: 12px;
                border-left: 2px solid transparent;
            }

            .moonstone-message.user {
                border-left-color: #5aa8b9;
                background: rgba(90, 168, 185, 0.05);
            }

            .moonstone-message.assistant {
                border-left-color: #7865ba;
                background: rgba(120, 101, 186, 0.05);
            }

            .moonstone-message-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 0.7rem;
            }

            .moonstone-role {
                color: #d4a574;
                font-weight: 500;
                letter-spacing: 0.05em;
            }

            .moonstone-time {
                color: #5a5854;
            }

            .moonstone-message-content {
                font-size: 0.85rem;
                line-height: 1.6;
                color: #f0ece7;
            }

            .moonstone-message-content code {
                background: rgba(0, 0, 0, 0.3);
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 0.8rem;
                color: #5aa8b9;
            }

            .moonstone-message-actions {
                margin-top: 8px;
                display: flex;
                gap: 8px;
            }

            .moonstone-message-actions button {
                background: transparent;
                border: 1px solid rgba(140, 160, 200, 0.2);
                color: #9a9690;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 0.65rem;
                cursor: pointer;
                transition: all 0.2s;
            }

            .moonstone-message-actions button:hover {
                border-color: #5aa8b9;
                color: #5aa8b9;
            }

            .moonstone-input-area {
                padding: 16px;
                border-top: 1px solid rgba(140, 160, 200, 0.1);
                background: rgba(0, 0, 0, 0.2);
            }

            .moonstone-input {
                width: 100%;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(140, 160, 200, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: #f0ece7;
                font-size: 0.9rem;
                font-family: inherit;
                resize: none;
                outline: none;
                transition: border-color 0.2s;
            }

            .moonstone-input:focus {
                border-color: #5aa8b9;
            }

            .moonstone-input::placeholder {
                color: #5a5854;
            }

            .moonstone-actions {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 12px;
            }

            .moonstone-hint {
                font-size: 0.65rem;
                color: #5a5854;
            }

            .moonstone-send {
                background: linear-gradient(135deg, #5aa8b9, #7865ba);
                border: none;
                color: #f0ece7;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 0.8rem;
                font-weight: 500;
                letter-spacing: 0.1em;
                cursor: pointer;
                transition: all 0.2s;
            }

            .moonstone-send:hover:not(:disabled) {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(90, 168, 185, 0.3);
            }

            .moonstone-send:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
        `;
        document.head.appendChild(style);
    }

    // Public API
    return {
        init,
        send,
        suggest,
        toggle,
        clear,
        copy
    };
})();

// Auto-init if container exists
document.addEventListener('DOMContentLoaded', () => {
    const autoContainer = document.querySelector('[data-moonstone]');
    if (autoContainer) {
        Moonstone.init({
            container: autoContainer,
            context: autoContainer.dataset.moonstoneContext || 'ARCHIV-IT'
        });
    }
});
