import re

with open("anklient/engine/api_server.py", "r") as f:
    content = f.read()

# We need to replace the entire _handle_ui function with a much better one.
# Find the start and end of _handle_ui.
match = re.search(r'(    async def _handle_ui.*?)(    # ── Auth)', content, re.DOTALL)
if match:
    old_handle = match.group(1)
    
    NEW_HTML = '''    async def _handle_ui(self, request: web.Request) -> web.Response:
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ankLIENT Cloud</title>
            <!-- Markdown Parser -->
            <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
            <style>
                :root { --bg: #f3f4f6; --chat-bg: #ffffff; --user-msg: #2563eb; --ai-msg: #f3f4f6; --text: #1f2937; }
                body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 0; background-color: var(--bg); color: var(--text); display: flex; flex-direction: column; height: 100vh; }
                header { background: white; padding: 15px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; font-weight: bold; font-size: 1.2rem; }
                #chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; max-width: 800px; margin: 0 auto; width: 100%; box-sizing: border-box; }
                .message { max-width: 85%; padding: 12px 18px; border-radius: 12px; line-height: 1.5; word-wrap: break-word; }
                .message p { margin: 0 0 10px 0; }
                .message p:last-child { margin: 0; }
                .message pre { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 8px; overflow-x: auto; font-size: 0.9em; }
                .message code { font-family: monospace; background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 4px; }
                .message pre code { background: none; padding: 0; }
                .user-message { background-color: var(--user-msg); color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
                .user-message code { background: rgba(255,255,255,0.2); }
                .ai-message { background-color: var(--chat-bg); align-self: flex-start; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #e5e7eb; }
                .input-container { background: white; padding: 15px 20px; border-top: 1px solid #e5e7eb; display: flex; gap: 10px; max-width: 800px; margin: 0 auto; width: 100%; box-sizing: border-box; }
                input[type="text"] { flex: 1; padding: 12px 20px; border: 1px solid #d1d5db; border-radius: 99px; font-size: 16px; outline: none; transition: border-color 0.2s; }
                input[type="text"]:focus { border-color: var(--user-msg); }
                button { background: var(--user-msg); color: white; border: none; padding: 0 24px; border-radius: 99px; font-weight: 600; font-size: 16px; cursor: pointer; transition: opacity 0.2s; }
                button:disabled { opacity: 0.5; cursor: not-allowed; }
                button:hover:not(:disabled) { opacity: 0.9; }
                .typing-indicator { display: inline-flex; gap: 4px; align-items: center; height: 24px; }
                .typing-indicator span { width: 6px; height: 6px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; }
                .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
                .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
                @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
            </style>
        </head>
        <body>
            <header>ankLIENT ✨ Cloud</header>
            <div id="chat-container">
                <div class="message ai-message">
                    <p>Hello! I am connected to your ChatGPT backend. I support <strong>streaming</strong> and <strong>Markdown</strong> formatting now!</p>
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="prompt" placeholder="Message ChatGPT..." autocomplete="off">
                <button id="sendBtn">Send</button>
            </div>

            <script>
                const chatContainer = document.getElementById('chat-container');
                const promptInput = document.getElementById('prompt');
                const sendBtn = document.getElementById('sendBtn');
                
                // Configure marked.js for safe rendering
                marked.setOptions({ breaks: true });

                promptInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') sendMessage();
                });
                sendBtn.addEventListener('click', sendMessage);

                async function sendMessage() {
                    const text = promptInput.value.trim();
                    if (!text) return;

                    // Add user message
                    addMessage(text, 'user');
                    promptInput.value = '';
                    sendBtn.disabled = true;
                    promptInput.disabled = true;

                    // Add empty AI message container for streaming
                    const aiMessageDiv = document.createElement('div');
                    aiMessageDiv.className = 'message ai-message';
                    
                    const typingIndicator = document.createElement('div');
                    typingIndicator.className = 'typing-indicator';
                    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
                    aiMessageDiv.appendChild(typingIndicator);
                    
                    chatContainer.appendChild(aiMessageDiv);
                    chatContainer.scrollTop = chatContainer.scrollHeight;

                    let fullContent = "";

                    try {
                        const response = await fetch('/v1/chat/completions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                model: "auto",
                                messages: [{ role: "user", content: text }],
                                stream: true
                            })
                        });

                        if (!response.ok) throw new Error('API Error');

                        // Remove typing indicator once stream starts
                        aiMessageDiv.innerHTML = '';

                        const reader = response.body.getReader();
                        const decoder = new TextDecoder("utf-8");

                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            
                            const chunk = decoder.decode(value, { stream: true });
                            const lines = chunk.split('\\n');
                            
                            for (const line of lines) {
                                if (line.startsWith('data: ')) {
                                    const dataStr = line.slice(6).trim();
                                    if (dataStr === '[DONE]') break;
                                    
                                    try {
                                        const data = JSON.parse(dataStr);
                                        const delta = data.choices[0].delta;
                                        
                                        if (delta && delta.content) {
                                            fullContent += delta.content;
                                            // Parse markdown in real-time
                                            aiMessageDiv.innerHTML = marked.parse(fullContent);
                                            chatContainer.scrollTop = chatContainer.scrollHeight;
                                        }
                                    } catch (e) {
                                        // Handle incomplete JSON chunks or parse errors silently
                                    }
                                }
                            }
                        }
                    } catch (error) {
                        aiMessageDiv.innerHTML = '<p style="color: red;">Error connecting to API.</p>';
                    } finally {
                        sendBtn.disabled = false;
                        promptInput.disabled = false;
                        promptInput.focus();
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                }

                function addMessage(text, sender) {
                    const div = document.createElement('div');
                    div.className = `message ${sender}-message`;
                    if (sender === 'user') {
                        div.textContent = text; // Prevent XSS for user input
                    } else {
                        div.innerHTML = marked.parse(text);
                    }
                    chatContainer.appendChild(div);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")
'''
    
    content = content.replace(old_handle, NEW_HTML)
    with open("anklient/engine/api_server.py", "w") as f:
        f.write(content)
    print("Patched UI v2 with Streaming and Markdown!")
else:
    print("Could not find _handle_ui")
