import discord
from discord import app_commands
import aiohttp
import asyncio
import time
import json
import os
from aiohttp import web
from datetime import timedelta, datetime

# ==================== CONFIGURATION ====================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NG_API_KEY    = os.getenv("NG_API_KEY")
RENDER_URL    = os.getenv("RENDER_EXTERNAL_URL", "")

RAPPORT_CHANNEL_ID = 1459182029924073558
ALERTE_CHANNEL_ID  = 1465309715230888090
STORAGE_CHANNEL_ID = 1478831933017428070

WATCH_LIST_DEFAULT = [
    "Canisi", "Darkholess", "UFO_Thespoot", "Franky753",
    "Blakonne", "Farsgame", "ClashKiller78", "Olmat38",
    "FLOTYR2", "Raptor51"
]

WATCH_LIST         = list(WATCH_LIST_DEFAULT)
watchlist_msg_id   = None

# Historique global : {pseudo: [{day, hour, server, ts}]}
global_history     = {}
history_chunks_ids = []  # liste d'IDs de messages HISTORY_X

intents = discord.Intents.default()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)

SERVERS = {
    "blue":   {"url": "https://blue.nationsglory.fr/standalone/dynmap_world.json",   "emoji": "🔵"},
    "coral":  {"url": "https://coral.nationsglory.fr/standalone/dynmap_world.json",  "emoji": "🔴"},
    "orange": {"url": "https://orange.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🟠"},
    "red":    {"url": "https://red.nationsglory.fr/standalone/dynmap_world.json",    "emoji": "🔴"},
    "yellow": {"url": "https://yellow.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🟡"},
    "mocha":  {"url": "https://mocha.nationsglory.fr/standalone/dynmap_world.json",  "emoji": "🟤"},
    "white":  {"url": "https://white.nationsglory.fr/standalone/dynmap_world.json",  "emoji": "⚪"},
    "jade":   {"url": "https://jade.nationsglory.fr/standalone/dynmap_world.json",   "emoji": "🟢"},
    "black":  {"url": "https://black.nationsglory.fr/standalone/dynmap_world.json",  "emoji": "⚫"},
    "cyan":   {"url": "https://cyan.nationsglory.fr/standalone/dynmap_world.json",   "emoji": "🔵"},
    "lime":   {"url": "https://lime.nationsglory.fr/standalone/dynmap_world.json",   "emoji": "🟢"}
}

LIME_URL  = "https://lime.nationsglory.fr/standalone/dynmap_world.json"
CACHE_TTL = 900
countries_cache = {}

# ==================== UTILS ====================

def now_paris():
    return datetime.utcnow() + timedelta(hours=1)

# ==================== WATCHLIST ====================

async def load_watchlist():
    global WATCH_LIST, watchlist_msg_id
    channel = client.get_channel(STORAGE_CHANNEL_ID)
    if not channel:
        return
    async for msg in channel.history(limit=50):
        if msg.author == client.user and msg.content.startswith("WATCHLIST:"):
            try:
                data = json.loads(msg.content[len("WATCHLIST:"):])
                WATCH_LIST      = data["players"]
                watchlist_msg_id = msg.id
                print(f"✅ Watchlist chargée : {WATCH_LIST}")
                return
            except:
                pass
    await save_watchlist()

async def save_watchlist():
    global watchlist_msg_id
    channel = client.get_channel(STORAGE_CHANNEL_ID)
    if not channel:
        return
    content = "WATCHLIST:" + json.dumps({"players": WATCH_LIST})
    if watchlist_msg_id:
        try:
            msg = await channel.fetch_message(watchlist_msg_id)
            await msg.edit(content=content)
            return
        except discord.NotFound:
            pass
    msg = await channel.send(content)
    watchlist_msg_id = msg.id

# ==================== HISTORIQUE ====================

MAX_SESSIONS_PER_PLAYER = 30
CHUNK_SIZE = 1800  # chars max par message Discord

async def load_history():
    global global_history, history_chunks_ids
    channel = client.get_channel(STORAGE_CHANNEL_ID)
    if not channel:
        return
    chunks = {}
    async for msg in channel.history(limit=100):
        if msg.author == client.user and msg.content.startswith("HISTORY_"):
            try:
                idx   = int(msg.content.split(":")[0].replace("HISTORY_", ""))
                data  = json.loads(msg.content[msg.content.index(":")+1:])
                chunks[idx] = (msg.id, data)
            except:
                pass
    if chunks:
        history_chunks_ids = []
        for idx in sorted(chunks.keys()):
            msg_id, data = chunks[idx]
            history_chunks_ids.append(msg_id)
            global_history.update(data)
        print(f"✅ Historique chargé : {len(global_history)} joueurs")
    else:
        await save_history()

async def save_history():
    global history_chunks_ids
    channel = client.get_channel(STORAGE_CHANNEL_ID)
    if not channel:
        return

    # Sérialiser et splitter en chunks de CHUNK_SIZE
    full_json = json.dumps(global_history)
    # Split par joueur pour ne pas couper au milieu
    chunks    = []
    current   = {}
    current_len = 0
    for player, sessions in global_history.items():
        entry     = json.dumps({player: sessions})
        entry_len = len(entry)
        if current_len + entry_len > CHUNK_SIZE and current:
            chunks.append(current)
            current     = {}
            current_len = 0
        current[player]  = sessions
        current_len     += entry_len
    if current:
        chunks.append(current)

    # Mettre à jour ou créer les messages
    new_ids = []
    for i, chunk in enumerate(chunks):
        content = f"HISTORY_{i}:" + json.dumps(chunk)
        if i < len(history_chunks_ids):
            try:
                msg = await channel.fetch_message(history_chunks_ids[i])
                await msg.edit(content=content)
                new_ids.append(msg.id)
                continue
            except discord.NotFound:
                pass
        msg = await channel.send(content)
        new_ids.append(msg.id)

    # Supprimer les anciens messages en trop
    for old_id in history_chunks_ids[len(chunks):]:
        try:
            msg = await channel.fetch_message(old_id)
            await msg.delete()
        except:
            pass

    history_chunks_ids = new_ids

def record_connection(player: str, server: str):
    n = now_paris()
    if player not in global_history:
        global_history[player] = []
    global_history[player].append({
        "day":    n.weekday(),
        "hour":   n.hour,
        "server": server,
        "ts":     int(n.timestamp())
    })
    # Garder seulement les N dernières sessions
    if len(global_history[player]) > MAX_SESSIONS_PER_PLAYER:
        global_history[player] = global_history[player][-MAX_SESSIONS_PER_PLAYER:]

def get_pronostic(player: str):
    sessions = global_history.get(player, [])
    if len(sessions) < 3:
        return None
    DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    day_counts  = [0] * 7
    hour_by_day = [[] for _ in range(7)]
    for s in sessions:
        d = s["day"]
        day_counts[d] += 1
        hour_by_day[d].append(s["hour"])
    total  = len(sessions)
    result = []
    for d in range(7):
        if day_counts[d] == 0:
            continue
        avg_hour = round(sum(hour_by_day[d]) / len(hour_by_day[d]))
        pct      = round(day_counts[d] / total * 100)
        result.append((d, avg_hour, pct))
    result.sort(key=lambda x: -x[2])
    return result[:4], DAYS, total

# ==================== FONCTIONS API ====================

async def get_countries_list(server: str):
    now = time.time()
    if server in countries_cache:
        cached_data, cached_time = countries_cache[server]
        if now - cached_time < CACHE_TTL:
            return cached_data
    url     = f"https://publicapi.nationsglory.fr/country/list/{server}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 500):
                    data    = await resp.json()
                    claimed = [c["name"] for c in data.get("claimed", []) if c.get("name")]
                    countries_cache[server] = (claimed, now)
                    return claimed
        except:
            pass
    return []

async def get_country_members(server: str, country: str):
    url     = f"https://publicapi.nationsglory.fr/country/{server}/{country}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                if "members" in data and data["members"]:
                    members = [m.lstrip("*+-") for m in data.get("members", [])]
                    return members, data.get("name", country)
        except:
            pass
    return None, None

async def get_online_players(server: str):
    url     = SERVERS[server]["url"]
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [p["name"] for p in data.get("players", [])]
        except:
            pass
    return []

# ==================== AUTOCOMPLETIONS ====================

async def server_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=s.upper(), value=s) for s in SERVERS if current.lower() in s.lower()][:25]

async def country_autocomplete(interaction: discord.Interaction, current: str):
    server = interaction.namespace.server
    if not server or server not in SERVERS:
        return []
    countries = await get_countries_list(server)
    return [app_commands.Choice(name=c, value=c) for c in countries if current.lower() in c.lower()][:25]

# ==================== COMMANDE CHECK ====================

@tree.command(name="check", description="Espionne les membres d'un pays sur tous les serveurs")
@app_commands.autocomplete(server=server_autocomplete, country=country_autocomplete)
async def check_command(interaction: discord.Interaction, server: str, country: str):
    await interaction.response.defer()
    if server not in SERVERS:
        return await interaction.followup.send("❌ Serveur invalide")
    members, country_name = await get_country_members(server, country)
    if not members:
        return await interaction.followup.send("❌ Pays introuvable")
    tasks          = {s: get_online_players(s) for s in SERVERS}
    results        = await asyncio.gather(*tasks.values())
    online_by_server = dict(zip(tasks.keys(), results))
    found = {}
    total = 0
    for s, players in online_by_server.items():
        f = [m for m in members if m in players]
        if f:
            found[s] = f
            total   += len(f)
    embed = discord.Embed(title=f"📊 Espionnage {country_name}", color=discord.Color.red())
    if found:
        for s, pl in sorted(found.items(), key=lambda x: (x[0] != server, x[0])):
            label = f"{SERVERS[s]['emoji']} {s.upper()} ({len(pl)})"
            if s == server:
                label += " ← serveur cible"
            embed.add_field(name=label, value=", ".join(pl), inline=False)
        embed.set_footer(text=f"Total connectés : {total} | {len(members)} membres au total")
    else:
        embed.description = f"✅ Aucun membre de {country_name} n'est connecté"
        embed.color       = discord.Color.green()
    await interaction.followup.send(embed=embed)

# ==================== COMMANDE CHECKALL ====================

@tree.command(name="checkall", description="Voir sur quel serveur un joueur est connecté")
async def checkall_command(interaction: discord.Interaction, joueur: str):
    await interaction.response.defer()
    tasks          = {s: get_online_players(s) for s in SERVERS}
    results        = await asyncio.gather(*tasks.values())
    online_by_server = dict(zip(tasks.keys(), results))
    found = [s for s, players in online_by_server.items() if joueur in players]
    embed = discord.Embed(title=f"🔍 Localisation de {joueur}", color=discord.Color.red())
    if found:
        embed.color       = discord.Color.green()
        embed.description = "\n".join([f"{SERVERS[s]['emoji']} **{s.upper()}**" for s in found])
    else:
        embed.description = f"**{joueur}** n'est connecté sur aucun serveur"
    await interaction.followup.send(embed=embed)

# ==================== COMMANDE ONLINE ====================

@tree.command(name="online", description="Voir tous les joueurs connectés sur un serveur")
@app_commands.autocomplete(server=server_autocomplete)
async def online_command(interaction: discord.Interaction, server: str):
    await interaction.response.defer()
    if server not in SERVERS:
        return await interaction.followup.send("❌ Serveur invalide")
    players = await get_online_players(server)
    embed   = discord.Embed(
        title=f"{SERVERS[server]['emoji']} Joueurs en ligne — {server.upper()}",
        color=discord.Color.blurple()
    )
    if players:
        chunks = [players[i:i+20] for i in range(0, len(players), 20)]
        for i, chunk in enumerate(chunks):
            embed.add_field(name=f"Joueurs {i+1}", value="\n".join([f"• {p}" for p in chunk]), inline=True)
        embed.set_footer(text=f"{len(players)} joueurs connectés")
    else:
        embed.description = "Aucun joueur connecté"
    await interaction.followup.send(embed=embed)

# ==================== COMMANDE PRONOSTIC ====================

@tree.command(name="pronostic", description="Pronostic de connexion d'un joueur")
async def pronostic_command(interaction: discord.Interaction, joueur: str):
    await interaction.response.defer()
    result = get_pronostic(joueur)
    if not result:
        return await interaction.followup.send(f"⚠️ Pas assez de données pour **{joueur}** (minimum 3 connexions)", ephemeral=True)
    top, DAYS, total = result
    embed = discord.Embed(
        title=f"🔮 Pronostic — {joueur}",
        description=f"Basé sur **{total}** connexions enregistrées",
        color=discord.Color.purple()
    )
    for d, avg_hour, pct in top:
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        embed.add_field(
            name=f"{DAYS[d]} — {pct}%",
            value=f"`{bar}` Heure moyenne : **{avg_hour}h**",
            inline=False
        )
    embed.set_footer(text="% = fréquence de connexion par jour de la semaine")
    await interaction.followup.send(embed=embed)

# ==================== COMMANDES WATCHLIST ====================

@tree.command(name="addwatch", description="Ajouter un joueur à la surveillance")
async def addwatch_command(interaction: discord.Interaction, joueur: str):
    if joueur in WATCH_LIST:
        return await interaction.response.send_message(f"⚠️ **{joueur}** est déjà dans la watchlist", ephemeral=True)
    WATCH_LIST.append(joueur)
    await save_watchlist()
    await interaction.response.send_message(f"✅ **{joueur}** ajouté à la surveillance", ephemeral=True)

@tree.command(name="removewatch", description="Retirer un joueur de la surveillance")
async def removewatch_command(interaction: discord.Interaction, joueur: str):
    if joueur not in WATCH_LIST:
        return await interaction.response.send_message(f"❌ **{joueur}** n'est pas dans la watchlist", ephemeral=True)
    WATCH_LIST.remove(joueur)
    await save_watchlist()
    await interaction.response.send_message(f"🗑️ **{joueur}** retiré de la surveillance", ephemeral=True)

@tree.command(name="watchlist", description="Afficher la liste de surveillance")
async def watchlist_command(interaction: discord.Interaction):
    if not WATCH_LIST:
        return await interaction.response.send_message("📋 La watchlist est vide", ephemeral=True)
    embed = discord.Embed(title="👁️ Watchlist — LIME", color=discord.Color.blurple())
    embed.description = "\n".join([f"• {p}" for p in WATCH_LIST])
    embed.set_footer(text=f"{len(WATCH_LIST)} joueurs surveillés")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== SCANNER INTERSERVEUR ====================

# {server: {player: bool}}
last_states = {s: {} for s in SERVERS}

async def scan_server(server: str, alerte_channel):
    players = await get_online_players(server)
    player_set = set(players)
    prev = last_states[server]

    for player in player_set:
        if not prev.get(player, False):
            # Connexion détectée
            record_connection(player, server)
            # Alerte watchlist
            if player in WATCH_LIST and alerte_channel:
                embed = discord.Embed(
                    title="🟢 CONNEXION DÉTECTÉE",
                    description=f"**{player}** vient de se connecter sur **{server.upper()}**",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                await alerte_channel.send(embed=embed)

    for player in list(prev.keys()):
        if prev[player] and player not in player_set:
            # Déconnexion watchlist
            if player in WATCH_LIST and alerte_channel:
                embed = discord.Embed(
                    title="🔴 DÉCONNEXION",
                    description=f"**{player}** vient de se déconnecter de **{server.upper()}**",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await alerte_channel.send(embed=embed)

    last_states[server] = {p: True for p in player_set}
    return players

# ==================== SCANNER LIME (RAPPORT) ====================

rapport_message_id = None

async def scanner_loop():
    global rapport_message_id

    await client.wait_until_ready()
    await load_watchlist()
    await load_history()

    rapport_channel = client.get_channel(RAPPORT_CHANNEL_ID)
    alerte_channel  = client.get_channel(ALERTE_CHANNEL_ID)

    while True:
        try:
            # Scanner tous les serveurs en parallèle
            tasks   = {s: scan_server(s, alerte_channel) for s in SERVERS}
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            server_players = dict(zip(tasks.keys(), results))

            # Rapport Lime
            lime_players = server_players.get("lime", [])
            if isinstance(lime_players, Exception):
                lime_players = []

            total_lime = len(lime_players)

            watched_online  = []
            watched_offline = []
            for player in WATCH_LIST:
                (watched_online if player in lime_players else watched_offline).append(player)

            now      = discord.utils.utcnow()
            time_str = (now + timedelta(hours=1)).strftime("%H:%M:%S")

            status_text = ""
            if watched_online:
                status_text += f"🟢 **En ligne ({len(watched_online)}) :**\n"
                for p in watched_online:
                    status_text += f"• {p}\n"
            if watched_offline:
                if status_text:
                    status_text += "\n"
                status_text += f"⚪ **Hors ligne ({len(watched_offline)}) :**\n"
                for p in watched_offline:
                    status_text += f"• {p}\n"

            rapport_embed = discord.Embed(
                title="🟢 RAPPORT TACTIQUE — LIME",
                color=discord.Color.green() if watched_online else discord.Color.greyple(),
                timestamp=now
            )
            rapport_embed.add_field(name="👥 Connectés Total", value=f"**{total_lime}**", inline=True)
            rapport_embed.add_field(name="⏱️ Dernier relevé",  value=f"**{time_str}**",   inline=True)
            rapport_embed.add_field(name="👁️ Surveillance", value=status_text or "Aucun joueur surveillé en ligne", inline=False)
            rapport_embed.set_footer(text="Scanner interserveur • Actualisation 1s")

            if rapport_channel:
                if rapport_message_id:
                    try:
                        msg = await rapport_channel.fetch_message(rapport_message_id)
                        await msg.edit(embed=rapport_embed)
                    except discord.NotFound:
                        msg = await rapport_channel.send(embed=rapport_embed)
                        rapport_message_id = msg.id
                else:
                    msg = await rapport_channel.send(embed=rapport_embed)
                    rapport_message_id = msg.id

        except Exception as e:
            print(f"❌ Erreur scanner: {e}")

        await asyncio.sleep(1)

async def history_saver():
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(300)
        await save_history()
        print(f"💾 Historique sauvegardé — {len(global_history)} joueurs")

# ==================== SERVEUR WEB / SELF-PING ====================

async def handle_health(request):
    return web.Response(text="Bot actif! ✅")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Serveur HTTP démarré sur {port}")

async def self_ping():
    await asyncio.sleep(60)
    while True:
        try:
            if RENDER_URL:
                url = RENDER_URL if RENDER_URL.startswith("http") else f"https://{RENDER_URL}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)):
                        pass
        except:
            pass
        await asyncio.sleep(600)

# ==================== LANCEMENT ====================

async def main():
    asyncio.create_task(start_webserver())
    if RENDER_URL:
        asyncio.create_task(self_ping())
    asyncio.create_task(scanner_loop())
    asyncio.create_task(history_saver())
    await client.start(DISCORD_TOKEN)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot connecté : {client.user}")
    print(f"🌍 Scanner interserveur actif — {len(SERVERS)} serveurs")

if __name__ == "__main__":
    asyncio.run(main())
