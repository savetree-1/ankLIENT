import re

with open("anklient/engine/api_server.py", "r") as f:
    content = f.read()

# Add the route
content = content.replace(
    'self.app.router.add_get("/", self._handle_health)',
    'self.app.router.add_get("/", self._handle_health)\n        self.app.router.add_get("/chat", self._handle_ui)'
)

# Define the HTML template
HTML = '''    async def _handle_ui(self, request: web.Request) -> web.Response:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>ankLIENT Chat</title>
            <style>
                body { font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f0f2f5; }
                #chat { height: 60vh; background: white; border-radius: 10px; padding: 15px; overflow-y: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; display: flex; flex-direction: column; gap: 10px;}
                .msg { padding: 10px 15px; border-radius: 20px; max-width: 80%; line-height: 1.4; word-wrap: break-word;}
                .user { background: #007aff; color: white; align-self: flex-end; border-bottom-right-radius: 5px;}
                .ai { background: #e9ecef; color: black; align-self: flex-start; border-bottom-left-radius: 5px;}
                .input-area { display: flex; gap: 10px; }
                input { flex: 1; padding: 15px; border: 1px solid #ddd; border-radius: 25px; outline: none; font-size: 16px;}
                button { padding: 15px 25px; background: #007aff; color: white; border: none; border-radius: 25px; cursor: pointer; font-weight: bold;}
                button:disabled { background: #ccc; }
            </style>
        </head>
        <body>
            <h2 style="text-align: center; color: #333;">ankLIENT Web</h2>
            <div id="chat">
                <div class="msg ai">Hello! I am running on ankLIENT in the cloud. How can I help you?</div>
            </div>
            <div class="input-area">
                <input type="text" id="prompt" placeholder="Type a message..." onkeypress="if(event.key === 'Enter') send()">
                <button id="sendBtn" onclick="send()">Send</button>
            </div>
            <script>
                async function send() {
                    let input = document.getElementById('prompt');
                    let text = input.value.trim();
                    if(!text) return;
                    
                    let chat = document.getElementById('chat');
                    chat.innerHTML += `<div class="msg user">${text}</div>`;
                    input.value = '';
                    let btn = document.getElementById('sendBtn');
                    btn.disabled = true;
                    btn.innerText = '...';
                    chat.scrollTop = chat.scrollHeight;

                    try {
                        let res = await fetch('/v1/chat/completions', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                model: "gpt-4o",
                                messages: [{role: "user", content: text}],
                                stream: false
                            })
                        });
                        let data = await res.json();
                        let reply = data.choices[0].message.content;
                        chat.innerHTML += `<div class="msg ai">${reply.replace(/\\n/g, '<br>')}</div>`;
                    } catch(e) {
                        chat.innerHTML += `<div class="msg ai" style="background:#ffdddd;color:red;">Error connecting to API.</div>`;
                    }
                    btn.disabled = false;
                    btn.innerText = 'Send';
                    chat.scrollTop = chat.scrollHeight;
                }
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

    # ── Auth'''

# Insert after _handle_health definition
content = content.replace('    # ── Auth', HTML)

with open("anklient/engine/api_server.py", "w") as f:
    f.write(content)
print("Patched!")
