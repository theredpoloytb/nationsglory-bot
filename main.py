import discord
from discord import app_commands
import aiohttp
import asyncio
import time
import os
from aiohttp import web

# Configuration des tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NG_API_KEY = os.getenv("NG_API_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")

# Configuration du bot
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Liste des serveurs NationsGlory
SERVERS = {
    "blue": {"url": "https://blue.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🔵"},
    "coral": {"url": "https://coral.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🔴"},
    "orange": {"url": "https://orange.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🟠"},
    "red": {"url": "https://red.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🔴"},
    "yellow": {"url": "https://yellow.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🟡"},
    "mocha": {"url": "https://mocha.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🟤"},
    "white": {"url": "https://white.nationsglory.fr/standalone/dynmap_world.json", "emoji": "⚪"},
    "jade": {"url": "https://jade.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🟢"},
    "black": {"url": "https://black.nationsglory.fr/standalone/dynmap_world.json", "emoji": "⚫"},
    "cyan": {"url": "https://cyan.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🔵"},
    "lime": {"url": "https://lime.nationsglory.fr/standalone/dynmap_world.json", "emoji": "🟢"}
}

# Cache pour les pays avec TTL de 15 minutes
countries_cache = {}
CACHE_TTL = 900

# ==================== SERVEUR WEB POUR KEEP-ALIVE ====================

async def handle_health(request):
    """Endpoint de santé pour Render"""
    return web.Response(text="Bot NationsGlory actif! ✅")

async def start_webserver():
    """Démarre un serveur web pour maintenir le bot éveillé"""
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', 10000))  # Render utilise PORT
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Serveur HTTP démarré sur le port {port}")

# ==================== SELF-PING ====================

async def self_ping():
    """Ping automatique toutes les 10 minutes"""
    await asyncio.sleep(60)  # Attendre 1 minute au démarrage
    
    while True:
        try:
            if RENDER_URL:
                url = RENDER_URL if RENDER_URL.startswith('http') else f"https://{RENDER_URL}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        print(f"🔄 Self-ping: {response.status}")
        except Exception as e:
            print(f"⚠️ Self-ping échoué: {e}")
        
        await asyncio.sleep(600)  # 10 minutes

# ==================== VOS FONCTIONS EXISTANTES ====================

async def get_countries_list(server: str):
    """Récupère la liste de tous les pays d'un serveur avec cache de 15 min"""
    now = time.time()
    
    if server in countries_cache:
        cached_data, cached_time = countries_cache[server]
        if now - cached_time < CACHE_TTL:
            return cached_data
        else:
            print(f"[CACHE] Cache expiré pour {server}, actualisation...")
    
    url = f"https://publicapi.nationsglory.fr/country/list/{server}"
    headers = {
        "Authorization": f"Bearer {NG_API_KEY}",
        "accept": "application/json"
    }
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200 or response.status == 500:
                    data = await response.json()
                    claimed = [c["name"] for c in data.get("claimed", []) if c.get("name")]
                    countries_cache[server] = (claimed, now)
                    print(f"[CACHE] Cache mis à jour pour {server} ({len(claimed)} pays)")
                    return claimed
        except Exception as e:
            print(f"[COUNTRIES] Erreur: {e}")
    
    return []

async def get_country_members(server: str, country: str):
    """Récupère tous les membres d'un pays via l'API"""
    url = f"https://publicapi.nationsglory.fr/country/{server}/{country}"
    headers = {
        "Authorization": f"Bearer {NG_API_KEY}",
        "accept": "application/json",
        "User-Agent": "NationsGlory-Bot/1.0"
    }
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as response:
                try:
                    data = await response.json()
                    
                    if "members" in data and data["members"]:
                        members = [m.lstrip('*+-') for m in data.get("members", [])]
                        return members, data.get("name", country)
                    else:
                        return None, None
                        
                except Exception as json_error:
                    print(f"[API] Erreur parsing JSON: {json_error}")
                    return None, None
                    
        except Exception as e:
            print(f"[API] Erreur: {e}")
            return None, None

async def get_online_players(server: str):
    """Récupère les joueurs connectés sur un serveur via dynmap"""
    url = SERVERS[server]["url"]
    timeout = aiohttp.ClientTimeout(total=5)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    players = [p["name"] for p in data.get("players", [])]
                    return players
                return []
        except Exception:
            return []

# ==================== AUTOCOMPLETIONS ====================

async def server_autocomplete(interaction: discord.Interaction, current: str):
    servers = list(SERVERS.keys())
    return [
        app_commands.Choice(name=srv.upper(), value=srv)
        for srv in servers if current.lower() in srv.lower()
    ][:25]

async def country_autocomplete(interaction: discord.Interaction, current: str):
    server = interaction.namespace.server
    if not server or server not in SERVERS:
        return []
    
    countries = await get_countries_list(server)
    
    return [
        app_commands.Choice(name=country, value=country)
        for country in countries if current.lower() in country.lower()
    ][:25]

# ==================== ÉVÉNEMENTS ====================

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot connecté en tant que {client.user}")
    print(f"📡 Slash commands synchronisées !")
    print(f"🔥 Prêt à espionner les serveurs NationsGlory !")
    print(f"⏱️  Cache des pays: 15 minutes")

# ==================== COMMANDES (vos commandes existantes) ====================

@tree.command(name="check", description="Espionne les membres d'un pays sur d'autres serveurs")
@app_commands.autocomplete(server=server_autocomplete, country=country_autocomplete)
async def check_command(interaction: discord.Interaction, server: str, country: str):
    await interaction.response.defer()
    
    if server not in SERVERS:
        await interaction.followup.send(f"❌ Serveur invalide: {server}")
        return
    
    members, country_name = await get_country_members(server, country)
    
    if not members:
        await interaction.followup.send(f"❌ Impossible de trouver le pays **{country}** sur **{server.upper()}**")
        return
    
    tasks = {srv: get_online_players(srv) for srv in SERVERS.keys()}
    results = await asyncio.gather(*tasks.values())
    
    online_by_server = dict(zip(tasks.keys(), results))
    
    found_players = {}
    total_found = 0
    
    for srv, players in online_by_server.items():
        if srv == server:
            continue
        
        found = [m for m in members if m in players]
        if found:
            found_players[srv] = found
            total_found += len(found)
    
    embed = discord.Embed(
        title=f"📊 Espionnage de {country_name}",
        description=f"Membres connectés ailleurs que **{server.upper()}**",
        color=discord.Color.red()
    )
    
    if found_players:
        for srv, players in sorted(found_players.items()):
            emoji = SERVERS[srv]["emoji"]
            players_list = ", ".join(players)
            embed.add_field(
                name=f"{emoji} {srv.upper()} ({len(players)})",
                value=players_list,
                inline=False
            )
        
        embed.set_footer(text=f"Total: {total_found} joueurs trouvés sur d'autres serveurs")
    else:
        embed.description = f"✅ Tous les membres en ligne sont sur **{server.upper()}** !"
        embed.color = discord.Color.green()
    
    await interaction.followup.send(embed=embed)

# ... (toutes vos autres commandes: online, debug, ping, servers, clearcache) ...

# ==================== LANCEMENT ====================

async def main():
    """Démarre tous les composants du bot"""
    # Démarre le serveur web
    asyncio.create_task(start_webserver())
    
    # Démarre le self-ping
    if RENDER_URL:
        asyncio.create_task(self_ping())
        print(f"🔄 Self-ping activé vers: {RENDER_URL}")
    
    # Démarre le bot Discord
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    print("🚀 Démarrage du bot NationsGlory Spy...")
    print(f"⏱️  TTL du cache: {CACHE_TTL // 60} minutes")
    
    asyncio.run(main())
