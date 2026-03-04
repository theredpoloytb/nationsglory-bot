import discord
from discord import app_commands
import aiohttp
import asyncio
import time
import json
import os
from aiohttp import web
from datetime import timedelta

# ==================== CONFIGURATION ====================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NG_API_KEY = os.getenv("NG_API_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")

RAPPORT_CHANNEL_ID = 1459182029924073558
ALERTE_CHANNEL_ID  = 1465309715230888090
STORAGE_CHANNEL_ID = 1478831933017428070

WATCH_LIST_DEFAULT = [
    "Canisi", "Darkholess", "UFO_Thespoot", "Franky753",
    "Blakonne", "Farsgame", "ClashKiller78", "Olmat38",
    "FLOTYR2", "Raptor51"
]

WATCH_LIST = list(WATCH_LIST_DEFAULT)
watchlist_message_id = None

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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

LIME_URL = "https://lime.nationsglory.fr/standalone/dynmap_world.json"

countries_cache = {}
CACHE_TTL = 900

# ==================== WATCHLIST STOCKAGE DISCORD ====================

async def load_watchlist():
    global WATCH_LIST, watchlist_message_id
    channel = client.get_channel(STORAGE_CHANNEL_ID)
    if not channel:
        print("⚠️ Channel storage introuvable")
        return
    async for msg in channel.history(limit=10):
        if msg.author == client.user and msg.content.startswith("WATCHLIST:"):
            try:
                data = json.loads(msg.content[len("WATCHLIST:"):])
                WATCH_LIST = data["players"]
                watchlist_message_id = msg.id
                print(f"✅ Watchlist chargée depuis Discord : {WATCH_LIST}")
                return
            except:
                pass
    # Aucun message trouvé, on crée
    await save_watchlist()

async def save_watchlist():
    global watchlist_message_id
    channel = client.get_channel(STORAGE_CHANNEL_ID)
    if not channel:
        return
    content = "WATCHLIST:" + json.dumps({"players": WATCH_LIST})
    if watchlist_message_id:
        try:
            msg = await channel.fetch_message(watchlist_message_id)
            await msg.edit(content=content)
            return
        except discord.NotFound:
            pass
    msg = await channel.send(content)
    watchlist_message_id = msg.id

# ==================== FONCTIONS COMMUNES ====================

async def get_countries_list(server: str):
    now = time.time()
    if server in countries_cache:
        cached_data, cached_time = countries_cache[server]
        if now - cached_time < CACHE_TTL:
            return cached_data
    url = f"https://publicapi.nationsglory.fr/country/list/{server}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 500):
                    data = await resp.json()
                    claimed = [c["name"] for c in data.get("claimed", []) if c.get("name")]
                    countries_cache[server] = (claimed, now)
                    return claimed
        except:
            pass
    return []

async def get_country_members(server: str, country: str):
    url = f"https://publicapi.nationsglory.fr/country/{server}/{country}"
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
    url = SERVERS[server]["url"]
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

    tasks = {s: get_online_players(s) for s in SERVERS}
    results = await asyncio.gather(*tasks.values())
    online_by_server = dict(zip(tasks.keys(), results))

    found = {}
    total = 0
    for s, players in online_by_server.items():
        f = [m for m in members if m in players]
        if f:
            found[s] = f
            total += len(f)

    embed = discord.Embed(title=f"📊 Espionnage {country_name}", color=discord.Color.red())
    if found:
        sorted_servers = sorted(found.items(), key=lambda x: (x[0] != server, x[0]))
        for s, pl in sorted_servers:
            label = f"{SERVERS[s]['emoji']} {s.upper()} ({len(pl)})"
            if s == server:
                label += " ← serveur cible"
            embed.add_field(name=label, value=", ".join(pl), inline=False)
        embed.set_footer(text=f"Total connectés : {total} joueurs | {len(members)} membres au total")
    else:
        embed.description = f"✅ Aucun membre de {country_name} n'est connecté en ce moment"
        embed.color = discord.Color.green()

    await interaction.followup.send(embed=embed)

# ==================== COMMANDE ONLINE ====================

@tree.command(name="online", description="Voir tous les joueurs connectés sur un serveur")
@app_commands.autocomplete(server=server_autocomplete)
async def online_command(interaction: discord.Interaction, server: str):
    await interaction.response.defer()
    if server not in SERVERS:
        return await interaction.followup.send("❌ Serveur invalide")
    players = await get_online_players(server)
    embed = discord.Embed(
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

# ==================== COMMANDE STATS ====================

@tree.command(name="stats", description="Voir les stats d'un joueur sur NationsGlory")
@app_commands.autocomplete(server=server_autocomplete)
async def stats_command(interaction: discord.Interaction, joueur: str, server: str):
    await interaction.response.defer()
    url = f"https://publicapi.nationsglory.fr/user/{joueur}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(f"❌ Joueur **{joueur}** introuvable")
                data = await resp.json()
        except:
            return await interaction.followup.send("❌ Erreur lors de la récupération des stats")
    server_data = data.get("servers", {}).get(server, {})
    embed = discord.Embed(
        title=f"📊 Stats de {joueur} — {server.upper()}",
        color=discord.Color.gold()
    )
    if server_data:
        embed.add_field(name="🏅 Rang", value=server_data.get("country_rank", "N/A"), inline=True)
        embed.add_field(name="💰 Argent", value=f"{server_data.get('money', 'N/A')} $", inline=True)
        embed.add_field(name="⚔️ Kills", value=server_data.get("kills", "N/A"), inline=True)
        embed.add_field(name="💀 Morts", value=server_data.get("deaths", "N/A"), inline=True)
        kd = round(server_data.get("kills", 0) / max(server_data.get("deaths", 1), 1), 2)
        embed.add_field(name="📈 K/D", value=kd, inline=True)
        embed.add_field(name="🏳️ Pays", value=server_data.get("country", "Sans pays"), inline=True)
    else:
        embed.description = f"Aucune donnée pour **{joueur}** sur **{server.upper()}**"
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

# ==================== SCANNER LIME ====================

last_known_state = {}
rapport_message_id = None

async def fetch_lime_players():
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(LIME_URL) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [p["name"] for p in data.get("players", [])], data.get("currentcount", 0), data.get("servertime", 0)
        except:
            pass
    return [], 0, 0

async def scanner_loop():
    global last_known_state, rapport_message_id

    await client.wait_until_ready()
    await load_watchlist()

    rapport_channel = client.get_channel(RAPPORT_CHANNEL_ID)
    alerte_channel  = client.get_channel(ALERTE_CHANNEL_ID)

    while True:
        try:
            online_players, total_online, servertime = await fetch_lime_players()

            watched_online  = []
            watched_offline = []

            for player in WATCH_LIST:
                is_online = player in online_players
                prev = last_known_state.get(player)

                if prev is not None and is_online != prev:
                    if alerte_channel:
                        if is_online:
                            alert_embed = discord.Embed(
                                title="🟢 CONNEXION DÉTECTÉE",
                                description=f"**{player}** vient de se connecter sur **LIME**",
                                color=discord.Color.green(),
                                timestamp=discord.utils.utcnow()
                            )
                        else:
                            alert_embed = discord.Embed(
                                title="🔴 DÉCONNEXION",
                                description=f"**{player}** vient de se déconnecter de **LIME**",
                                color=discord.Color.red(),
                                timestamp=discord.utils.utcnow()
                            )
                        await alerte_channel.send(embed=alert_embed)

                last_known_state[player] = is_online
                (watched_online if is_online else watched_offline).append(player)

            # Heure IG
            hours   = (servertime // 1000) % 24
            minutes = int((servertime % 1000) / 1000 * 60)
            time_ig = f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}"

            now      = discord.utils.utcnow()
            time_str = (now + timedelta(hours=1)).strftime("%H:%M:%S")

            # Rapport
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
            rapport_embed.add_field(name="👥 Connectés Total", value=f"**{total_online}**", inline=True)
            rapport_embed.add_field(name="🕐 Heure IG",        value=f"**{time_ig}**",      inline=True)
            rapport_embed.add_field(name="⏱️ Dernier relevé",  value=f"**{time_str}**",     inline=True)
            rapport_embed.add_field(name="👁️ Surveillance", value=status_text or "Aucun joueur surveillé en ligne", inline=False)
            rapport_embed.set_footer(text="Scanner en temps réel • Actualisation 1s")

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
    await client.start(DISCORD_TOKEN)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot connecté en tant que {client.user}")
    print(f"👁️ Scanner Lime actif — watchlist chargée depuis Discord")

if __name__ == "__main__":
    asyncio.run(main())
