import os
import threading
import random
import datetime
import asyncio
from flask import Flask, render_template_string, request, redirect, url_for
import discord
from discord.ext import commands

# ==================== KONFIGURACJA BAZY DANYCH / EKONOMII ====================
# Prosty słownik w pamięci (lub możesz podpiąć plik JSON)
# Tutaj dla uproszczenia trzymamy dane użytkowników
economy_data = {}

def get_user_data(user_id):
    if user_id not in economy_data:
        economy_data[user_id] = {
            "wallet": 500,
            "bank": 1000,
            "last_rob": None
        }
    return economy_data[user_id]

def parse_amount(amount_str, max_val):
    amount_str = amount_str.lower()
    if amount_str == "all":
        return max_val
    elif amount_str == "half":
        return max_val // 2
    elif amount_str == "quarter":
        return max_val // 4
    try:
        val = int(amount_str)
        return val
    except ValueError:
        return 0


# ==================== STRONA WWW (DASHBOARD FLASK) ====================

app = Flask(__name__)

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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


# ==================== BOT DISCORD ====================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot Zavi jest online jako {bot.user}')
    try:
        # Synchronizacja globalna komend Slash (dzięki temu Discord od razu je widzi)
        synced = await bot.tree.sync()
        print(f'✅ Zasynchronizowano pomyślnie {len(synced)} komend slash!')
    except Exception as e:
        print(f'❌ Błąd synchronizacji komend: {e}')


# ==================== KOMENDY EKONOMICZNE I HAZARD ====================

@bot.tree.command(name="portfel", description="Sprawdź stan swojego konta i portfela")
async def slash_portfel(interaction: discord.Interaction):
    data = get_user_data(interaction.user.id)
    embed = discord.Embed(title=f"💰 Portfel użytkownika {interaction.user.display_name}", color=discord.Color.gold())
    embed.add_field(name="Portfel (gotówka)", value=f"{data['wallet']} PLN", inline=True)
    embed.add_field(name="Bank", value=f"{data['bank']} PLN", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="slots", description="Zagraj na automatach (stawka: liczba, all, half, quarter)")
async def slash_slots(interaction: discord.Interaction, stawka: str):
    data = get_user_data(interaction.user.id)
    real_stawka = parse_amount(stawka, data["wallet"])
    
    if real_stawka <= 0 or data["wallet"] < real_stawka:
        return await interaction.response.send_message("❌ Niepoprawna stawka lub za mało gotówki w portfelu!", ephemeral=True)
        
    data["wallet"] -= real_stawka
    
    emotki = ["🍒", "🍋", "🍉", "🔔", "💎"]
    waga = [40, 30, 20, 15, 5]
    
    wynik = random.choices(emotki, weights=waga, k=3)
    
    mnoznik = 0
    if wynik[0] == wynik[1] == wynik[2]:
        if wynik[0] == "💎":
            mnoznik = 10
        elif wynik[0] == "🔔":
            mnoznik = 5
        else:
            mnoznik = 3
    elif wynik[0] == wynik[1] or wynik[1] == wynik[2] or wynik[0] == wynik[2]:
        mnoznik = 1.5

    embed = discord.Embed(title="🎰 Jednoręki Bandyta", color=discord.Color.dark_magenta())
    embed.add_field(name="Wynik losowania", value=f"**[ {wynik[0]} | {wynik[1]} | {wynik[2]} ]**", inline=False)

    if mnoznik > 0:
        wygrana = int(real_stawka * mnoznik)
        data["wallet"] += wygrana
        embed.description = f"🎉 Wygrywasz! Zgarniasz **{wygrana} PLN**!"
        embed.color = discord.Color.green()
    else:
        embed.description = f"💸 Przegrywasz. Tracisz **{real_stawka} PLN**."
        embed.color = discord.Color.red()

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rob", description="Spróbuj okraść innego gracza (Ryzyko wpadki!)")
async def slash_rob(interaction: discord.Interaction, ofiara: discord.Member):
    if ofiara.id == interaction.user.id:
        return await interaction.response.send_message("❌ Nie możesz okraść samego siebie!", ephemeral=True)
        
    data_zlodziej = get_user_data(interaction.user.id)
    data_ofiara = get_user_data(ofiara.id)
    
    now_ts = datetime.datetime.now().timestamp()
    
    if data_zlodziej["last_rob"] and (now_ts - data_zlodziej["last_rob"]) < 1800:
        pozostalo = int((1800 - (now_ts - data_zlodziej["last_rob"])) / 60)
        return await interaction.response.send_message(f"⏳ Policja Cię szuka! Ukrywaj się jeszcze przez **{pozostalo} min**.", ephemeral=True)
        
    if data_ofiara["wallet"] < 100:
        return await interaction.response.send_message("❌ Ten gracz jest zbyt biedny, żeby go okradać (wymagane min. 100 PLN w portfelu).", ephemeral=True)
        
    data_zlodziej["last_rob"] = now_ts
    
    if random.random() < 0.40:
        procent = random.uniform(0.1, 0.4)
        lup = int(data_ofiara["wallet"] * procent)
        
        data_ofiara["wallet"] -= lup
        data_zlodziej["wallet"] += lup
        await interaction.response.send_message(f"🥷 **Skok udany!** Ukradłeś **{lup} PLN** z portfela gracza {ofiara.mention}!")
    else:
        kara = random.randint(200, 1000)
        data_zlodziej["wallet"] = max(0, data_zlodziej["wallet"] - kara)
        await interaction.response.send_message(f"🚨 **Wpadka!** Zostałeś złapany na próbie kradzieży gracza {ofiara.mention}. Płacisz **{kara} PLN** grzywny!")


# ==================== KOMENDY 4FUN ====================

@bot.tree.command(name="hug", description="Przytul innego użytkownika")
async def slash_hug(interaction: discord.Interaction, osoba: discord.Member):
    embed = discord.Embed(
        description=f"🤗 **{interaction.user.display_name}** przytula **{osoba.display_name}**!", 
        color=discord.Color.purple()
    )
    gify = [
        "https://media.giphy.com/media/3M4NpbLCTxBqU/giphy.gif",
        "https://media.giphy.com/media/od5H3PmEG5EVq/giphy.gif",
        "https://media.giphy.com/media/lrr9VkGv0CQdq/giphy.gif"
    ]
    embed.set_image(url=random.choice(gify))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="slap", description="Uderz kogoś (wirtualnie!)")
async def slash_slap(interaction: discord.Interaction, osoba: discord.Member):
    embed = discord.Embed(
        description=f"🖐️ **{interaction.user.display_name}** daje plaskacza **{osoba.display_name}**!", 
        color=discord.Color.red()
    )
    gify = [
        "https://media.giphy.com/media/jLeyZWgtwgr2U/giphy.gif",
        "https://media.giphy.com/media/Zau0yrl17uzdK/giphy.gif"
    ]
    embed.set_image(url=random.choice(gify))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ship", description="Sprawdź poziom miłości między dwiema osobami")
async def slash_ship(interaction: discord.Interaction, osoba1: discord.Member, osoba2: discord.Member = None):
    if not osoba2:
        osoba2 = osoba1
        osoba1 = interaction.user

    random.seed(osoba1.id + osoba2.id)
    procent = random.randint(0, 100)
    random.seed()

    paski = int(procent / 10)
    pasek_progress = "🟥" * paski + "⬛" * (10 - paski)

    if procent > 80:
        komentarz = "💖 Prawdziwa miłość!"
    elif procent > 50:
        komentarz = "💕 Jest potencjał, idźcie na randkę!"
    elif procent > 20:
        komentarz = "friendzone..."
    else:
        komentarz = "💔 Oj, z tego nic nie będzie."

    embed = discord.Embed(title="💘 Kalkulator Miłości 💘", color=discord.Color.pink())
    embed.add_field(name=f"**{osoba1.display_name}**  +  **{osoba2.display_name}**", value=f"**Wskaźnik:** {procent}%\n{pasek_progress}\n\n*{komentarz}*", inline=False)
    
    await interaction.response.send_message(embed=embed)


# ==================== START APLIKACI ====================

if __name__ == "__main__":
    # Uruchomienie serwera Flask w tle
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Pobranie tokenu i uruchomienie bota
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ Brak tokena DISCORD_TOKEN w zmiennych środowiskowych!")
