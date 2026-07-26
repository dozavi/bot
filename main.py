# Upewnij się, że masz te importy na samej górze:
import os
import threading

# ... (TUTAJ JEST CAŁY TWÓJ KOD FLASKA I BOTA) ...

# Tę funkcję i jej wywołanie umieść NA SAMYM DOLE pliku (BEZ ŻADNEGO if __name__):
def run_bot():
    token = os.getenv("DISCORD_TOKEN")
    if token:
        try:
            bot.run(token)
        except Exception as e:
            print(f"Błąd uruchamiania bota: {e}")

# Odpalenie wątku bezpośrednio w kodzie głównym
t = threading.Thread(target=run_bot, daemon=True)
t.start()

# ==================== STRONA WWW (DASHBOARD FLASK) ====================

app = Flask(__name__)

# Wygląd Twojej strony WWW (HTML + CSS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zavi Bot - Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background-color: #1e293b; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
        h1, h2 { color: #38bdf8; margin-top: 0; }
        .status-online { color: #22c55e; font-weight: bold; }
        .status-offline { color: #ef4444; font-weight: bold; }
        input, button, textarea { width: 100%; padding: 12px; margin-top: 10px; border-radius: 6px; border: 1px solid #334155; background-color: #0f172a; color: #fff; box-sizing: border-box; }
        button { background-color: #2563eb; font-weight: bold; cursor: pointer; border: none; transition: 0.2s; }
        button:hover { background-color: #1d4ed8; }
        .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .stat-box { background-color: #0f172a; padding: 15px; border-radius: 8px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🤖 Zavi Bot - Panel Sterowania</h1>
            <p>Status bota: 
                {% if bot_online %}
                    <span class="status-online">ONLINE 🟢</span>
                {% else %}
                    <span class="status-offline">OFFLINE 🔴</span>
                {% endif %}
            </p>
        </div>

        <div class="card">
            <h2>📊 Statystyki</h2>
            <div class="stat-grid">
                <div class="stat-box">
                    <p>Serwery</p>
                    <h3>{{ guild_count }}</h3>
                </div>
                <div class="stat-box">
                    <p>Ping Bota</p>
                    <h3>{{ latency }} ms</h3>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📢 Wyślij wiadomość jako Bot</h2>
            <form action="/send_message" method="POST">
                <label>ID Kanału na Discordzie:</label>
                <input type="text" name="channel_id" placeholder="np. 123456789012345678" required>
                <label>Treść wiadomości:</label>
                <textarea name="message" rows="4" placeholder="Wpisz treść wiadomości..." required></textarea>
                <button type="submit">🚀 Wyślij Wiadomość</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    bot_online = bot.is_ready()
    guild_count = len(bot.guilds) if bot_online else 0
    latency = round(bot.latency * 1000) if bot_online else 0
    return render_template_string(HTML_TEMPLATE, bot_online=bot_online, guild_count=guild_count, latency=latency)

@app.route('/send_message', methods=['POST'])
def send_message():
    channel_id = request.form.get('channel_id')
    message_text = request.form.get('message')
    
    if channel_id and message_text and bot.is_ready():
        try:
            channel = bot.get_channel(int(channel_id))
            if channel:
                asyncio.run_coroutine_threadsafe(channel.send(message_text), bot.loop)
        except Exception as e:
            print(f"Błąd wysyłania: {e}")
            
    return redirect(url_for('home'))

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ==================== BOT DISCORD ====================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot Zavi jest online jako {bot.user}')

# ==================== START ====================

def run_bot():
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)

# Uruchamiamy bota w tle ZAWSZE przy ładowaniu pliku przez Gunicorna
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
