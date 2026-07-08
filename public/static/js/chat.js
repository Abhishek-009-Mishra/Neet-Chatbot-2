(function () {
    "use strict";

    const chatMessages = document.getElementById('chatMessages');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const typingIndicator = document.getElementById('typingIndicator');
    const clearBtn = document.getElementById('clearBtn');

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeWelcome() {
        if (welcomeScreen && welcomeScreen.parentNode) {
            welcomeScreen.remove();
        }
    }

    function appendMessage(role, text, sources) {
        const msg = document.createElement('div');
        msg.className = `msg ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';
        bubble.textContent = text;
        msg.appendChild(bubble);

        if (role === 'bot') {
            const wrap = document.createElement('div');
            const sourcesEl = document.createElement('div');
            sourcesEl.className = 'sources';

            if (sources && sources.length > 0) {
                sources.forEach(s => {
                    const tab = document.createElement('span');
                    tab.className = 'source-tab';
                    tab.textContent = `${s.book} · pg ${s.page}`;
                    sourcesEl.appendChild(tab);
                });
            } else {
                const tab = document.createElement('span');
                tab.className = 'source-tab none';
                tab.textContent = 'Not found in your book';
                sourcesEl.appendChild(tab);
            }
            wrap.appendChild(bubble);
            wrap.appendChild(sourcesEl);
            msg.innerHTML = '';
            msg.appendChild(wrap);
        }

        chatMessages.appendChild(msg);
        scrollToBottom();
    }

    async function sendMessage(text) {
        if (!text.trim()) return;

        removeWelcome();
        appendMessage('user', text);
        userInput.value = '';
        sendBtn.disabled = true;
        typingIndicator.classList.add('active');
        scrollToBottom();

        try {
            const formData = new FormData();
            formData.append('text', text);

            const res = await fetch('/chat', { method: 'POST', body: formData });
            const data = await res.json();

            typingIndicator.classList.remove('active');
            sendBtn.disabled = false;

            if (data.error) {
                appendMessage('bot', `Error: ${data.error}`, []);
                return;
            }
            appendMessage('bot', data.text, data.sources || []);
        } catch (err) {
            typingIndicator.classList.remove('active');
            sendBtn.disabled = false;
            appendMessage('bot', 'Something went wrong reaching the server. Please try again.', []);
            console.error(err);
        }
    }

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        sendMessage(userInput.value);
    });

    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => sendMessage(chip.dataset.q));
    });

    clearBtn.addEventListener('click', async function () {
        try {
            await fetch('/chat/clear', { method: 'POST' });
        } catch (err) {
            console.error(err);
        }
        chatMessages.innerHTML = '';
        location.reload();
    });

    userInput.focus();
})();
