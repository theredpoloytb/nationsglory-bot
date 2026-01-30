import discord
from discord import app_commands
import aiohttp
import asyncio
import time
import os
from aiohttp import web

# ==================== CONFIGURATION ====================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NG_API_KEY = os.getenv("NG_API_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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

countries_cache = {}
CACHE_TTL = 900

user_rank_cache = {}
USER_RANK_TTL = 60

# ==================== SURVEILLANCE DES ASSAUTS ====================

surveillance = {}  # {server: {country: {"task": asyncio.Task, "assaut_possible": bool}}}
ASSAUT_CHANNEL_ID = 1465336287471861771

# Configuration de la surveillance automatique
AUTO_SURVEILLANCE_SERVER = "lime"
AUTO_SURVEILLANCE_COUNTRY = "tasmanie"  # Le pays dont on surveille les ennemis
AUTO_UPDATE_INTERVAL = 5  # Mise à jour des ennemis toutes les 5 secondes
MEMBER_UPDATE_INTERVAL = 10  # Mise à jour des membres toutes les 10 secondes

current_enemies = set()  # Pour tracker les ennemis actuels

# ==================== FONCTIONS ====================

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
                if resp.status in (200, 500):  # L'API peut renvoyer 500 même quand ça marche
                    data = await resp.json()
                    if "members" in data and data["members"]:
                        members = [m.lstrip("*+-") for m in data.get("members", [])]
                        return members, data.get("name", country)
        except Exception as e:
            print(f"❌ Erreur get_country_members({server}, {country}): {e}")
    return None, None

async def get_country_info(server: str, country: str):
    """Récupère toutes les infos d'un pays incluant les ennemis"""
    url = f"https://publicapi.nationsglory.fr/country/{server}/{country}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 500):  # L'API peut renvoyer 500 même quand ça marche
                    return await resp.json()
        except Exception as e:
            print(f"❌ Erreur get_country_info({server}, {country}): {e}")
    return None

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

async def get_user_rank(username: str, server: str):
    now = time.time()
    key = f"{username}:{server}"
    if key in user_rank_cache:
        rank, ts = user_rank_cache[key]
        if now - ts < USER_RANK_TTL:
            return rank
    url = f"https://publicapi.nationsglory.fr/user/{username}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rank = data.get("servers", {}).get(server, {}).get("country_rank")
                    user_rank_cache[key] = (rank, now)
                    return rank
        except:
            pass
    return None

# ==================== AUTOCOMPLETIONS ====================

async def server_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=s.upper(), value=s) for s in SERVERS if current.lower() in s.lower()][:25]

async def country_autocomplete(interaction: discord.Interaction, current: str):
    server = interaction.namespace.server
    if not server or server not in SERVERS:
        return []
    countries = await get_countries_list(server)
    return [app_commands.Choice(name=c, value=c) for c in countries if current.lower() in c.lower()][:25]

async def action_autocomplete(interaction: discord.Interaction, current: str):
    actions = ["start", "stop"]
    return [app_commands.Choice(name=a.capitalize(), value=a) for a in actions if current.lower() in a.lower()]

# ==================== COMMANDES ====================

@tree.command(name="check", description="Espionne les membres d'un pays sur d'autres serveurs")
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
        if s == server:
            continue
        f = [m for m in members if m in players]
        if f:
            found[s] = f
            total += len(f)
    embed = discord.Embed(title=f"📊 Espionnage {country_name}", color=discord.Color.red())
    if found:
        for s, pl in sorted(found.items()):
            embed.add_field(name=f"{SERVERS[s]['emoji']} {s.upper()} ({len(pl)})", value=", ".join(pl), inline=False)
        embed.set_footer(text=f"Total: {total} joueurs")
    else:
        embed.description = f"✅ Tous les membres sont sur {server.upper()}"
        embed.color = discord.Color.green()
    await interaction.followup.send(embed=embed)

# ==================== ASSAUT START/STOP ====================

async def assaut_loop(server: str, country: str):
    members, country_name = await get_country_members(server, country)
    channel = client.get_channel(ASSAUT_CHANNEL_ID)
    
    # Vérifier le channel
    if not channel:
        print(f"❌ Impossible de démarrer surveillance pour {country} sur {server}: channel introuvable")
        return
    
    # Si pas de membres au départ, on initialise quand même la surveillance
    # Les membres seront récupérés au prochain cycle
    if not members:
        print(f"⚠️ Pas de membres trouvés pour {country} sur {server}, réessai au prochain cycle...")
        members = []
        country_name = country
    
    # Initialiser la surveillance
    if server not in surveillance:
        surveillance[server] = {}
    surveillance[server][country] = {"task": asyncio.current_task(), "assaut_possible": False}
    
    print(f"✅ Surveillance démarrée pour {country_name} ({len(members)} membres)")
    
    last_member_update = time.time()
    
    try:
        while True:
            # Mettre à jour la liste des membres périodiquement
            current_time = time.time()
            if current_time - last_member_update >= MEMBER_UPDATE_INTERVAL:
                new_members, new_country_name = await get_country_members(server, country)
                if new_members:
                    # Détecter les changements (UNIQUEMENT EN PRINT, PAS SUR DISCORD)
                    added = set(new_members) - set(members)
                    removed = set(members) - set(new_members)
                    
                    if added:
                        print(f"➕ {country_name}: Nouveaux membres détectés: {', '.join(added)}")
                    
                    if removed:
                        print(f"➖ {country_name}: Membres partis: {', '.join(removed)}")
                    
                    members = new_members
                    country_name = new_country_name or country_name
                    print(f"🔄 Liste des membres mise à jour pour {country_name} ({len(members)} membres)")
                else:
                    print(f"⚠️ Impossible de mettre à jour les membres de {country_name}")
                
                last_member_update = current_time
            
            # Vérifier l'état d'assaut seulement si on a des membres
            if members:
                online = await get_online_players(server)
                # IMPORTANT: Ne garder que les joueurs connectés QUI SONT TOUJOURS MEMBRES
                connected = [m for m in members if m in online]
                
                possible = False
                if len(connected) >= 2:
                    ranks = {p: await get_user_rank(p, server) for p in connected}
                    recruits = [p for p, r in ranks.items() if r == "recruit"]
                    valids = [p for p, r in ranks.items() if r in ("member", "officer", "leader")]
                    # Assaut possible si: pas que des recruits OU au moins un membre valide
                    if (not recruits) or valids:
                        possible = True
                
                prev = surveillance[server][country]["assaut_possible"]
                if possible and not prev:
                    await channel.send(f"⚔️ @everyone ASSAUT POSSIBLE sur {country_name} ({server.upper()})\n👥 Connectés : {', '.join(connected)}")
                    surveillance[server][country]["assaut_possible"] = True
                elif not possible and prev:
                    await channel.send(f"ℹ️ Assaut plus possible sur {country_name} ({server.upper()})")
                    surveillance[server][country]["assaut_possible"] = False
            
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        # La tâche a été annulée (surveillance arrêtée)
        print(f"🛑 Surveillance annulée pour {country_name} sur {server}")
    except Exception as e:
        print(f"❌ Erreur dans assaut_loop pour {country} sur {server}: {e}")
    finally:
        # Nettoyer la surveillance si la tâche se termine
        if server in surveillance and country in surveillance[server]:
            del surveillance[server][country]
            if not surveillance[server]:
                del surveillance[server]

@tree.command(name="assaut", description="Gérer la surveillance des assauts")
@app_commands.autocomplete(
    server=server_autocomplete, 
    country=country_autocomplete,
    action=action_autocomplete
)
async def assaut_command(interaction: discord.Interaction, server: str, country: str, action: str):
    await interaction.response.defer()
    if action.lower() not in ("start", "stop"):
        return await interaction.followup.send("❌ Action invalide: start ou stop")
    
    if action.lower() == "start":
        # Vérifier si déjà actif
        if surveillance.get(server, {}).get(country):
            return await interaction.followup.send(f"⚠️ Surveillance déjà active pour {country} sur {server.upper()}")
        
        task = asyncio.create_task(assaut_loop(server, country))
        await interaction.followup.send(f"🔍 Surveillance activée pour {country} sur {server.upper()}")
    else:
        if surveillance.get(server, {}).get(country):
            surveillance[server][country]["task"].cancel()
            del surveillance[server][country]
            if not surveillance[server]:
                del surveillance[server]
            
            await interaction.followup.send(f"🛑 Surveillance arrêtée pour {country} sur {server.upper()}")
        else:
            await interaction.followup.send("❌ Cette surveillance n'existe pas")

@tree.command(name="assaut_list", description="Affiche toutes les surveillances actives")
async def assaut_list_command(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if not surveillance or all(not countries for countries in surveillance.values()):
        return await interaction.followup.send("ℹ️ Aucune surveillance active")
    
    embed = discord.Embed(
        title="🔍 Surveillances actives",
        color=discord.Color.blue()
    )
    
    total = 0
    for server, countries in surveillance.items():
        if countries:
            country_list = []
            for country, data in countries.items():
                status = "⚔️ ASSAUT POSSIBLE" if data["assaut_possible"] else "🛡️ Pas d'assaut"
                country_list.append(f"• {country} - {status}")
                total += 1
            
            embed.add_field(
                name=f"{SERVERS[server]['emoji']} {server.upper()} ({len(countries)})",
                value="\n".join(country_list),
                inline=False
            )
    
    embed.set_footer(text=f"Total: {total} surveillance(s)")
    await interaction.followup.send(embed=embed)

# ==================== SERVEUR WEB / SELF-PING ====================

async def update_enemies_surveillance():
    """Met à jour automatiquement les surveillances en fonction des ennemis"""
    global current_enemies
    channel = client.get_channel(ASSAUT_CHANNEL_ID)
    
    await asyncio.sleep(10)  # Attendre que le bot soit bien démarré
    
    while True:
        try:
            # Récupérer les ennemis actuels
            country_info = await get_country_info(AUTO_SURVEILLANCE_SERVER, AUTO_SURVEILLANCE_COUNTRY)
            
            if country_info:
                new_enemies = set(country_info.get("enemies", []))
                
                # Nouveaux ennemis à ajouter
                to_add = new_enemies - current_enemies
                for enemy in to_add:
                    # Vérifier que le pays existe
                    members, country_name = await get_country_members(AUTO_SURVEILLANCE_SERVER, enemy)
                    if members:
                        # Vérifier qu'on ne surveille pas déjà ce pays
                        if not surveillance.get(AUTO_SURVEILLANCE_SERVER, {}).get(enemy):
                            asyncio.create_task(assaut_loop(AUTO_SURVEILLANCE_SERVER, enemy))
                            print(f"➕ Nouveau pays surveillé: {country_name}")
                            if channel:
                                await channel.send(f"➕ Nouvelle guerre détectée ! Surveillance activée pour **{country_name}**")
                
                # Ennemis à retirer (paix signée)
                to_remove = current_enemies - new_enemies
                for enemy in to_remove:
                    if surveillance.get(AUTO_SURVEILLANCE_SERVER, {}).get(enemy):
                        surveillance[AUTO_SURVEILLANCE_SERVER][enemy]["task"].cancel()
                        del surveillance[AUTO_SURVEILLANCE_SERVER][enemy]
                        if not surveillance[AUTO_SURVEILLANCE_SERVER]:
                            del surveillance[AUTO_SURVEILLANCE_SERVER]
                        print(f"➖ Pays retiré: {enemy} (paix signée)")
                        if channel:
                            await channel.send(f"🕊️ Paix signée avec **{enemy}** - Surveillance arrêtée")
                
                current_enemies = new_enemies
                
        except Exception as e:
            print(f"❌ Erreur update enemies: {e}")
        
        await asyncio.sleep(AUTO_UPDATE_INTERVAL)

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
    await client.start(DISCORD_TOKEN)

@client.event
async def on_ready():
    global current_enemies
    await tree.sync()
    print(f"✅ Bot connecté en tant que {client.user}")
    
    # Récupérer les ennemis de la Tasmanie et les surveiller
    channel = client.get_channel(ASSAUT_CHANNEL_ID)
    
    print(f"🔍 Récupération des ennemis de {AUTO_SURVEILLANCE_COUNTRY} sur {AUTO_SURVEILLANCE_SERVER.upper()}...")
    country_info = await get_country_info(AUTO_SURVEILLANCE_SERVER, AUTO_SURVEILLANCE_COUNTRY)
    
    if not country_info:
        print(f"❌ Impossible de récupérer les infos de {AUTO_SURVEILLANCE_COUNTRY}")
        if channel:
            await channel.send(f"❌ Impossible de récupérer les infos de {AUTO_SURVEILLANCE_COUNTRY}")
        return
    
    enemies = country_info.get("enemies", [])
    current_enemies = set(enemies)  # Initialiser la liste des ennemis actuels
    
    if not enemies:
        print(f"ℹ️ Aucun ennemi trouvé pour {AUTO_SURVEILLANCE_COUNTRY}")
        if channel:
            await channel.send(f"🤖 Bot démarré - Aucun pays en guerre avec {country_info.get('name', AUTO_SURVEILLANCE_COUNTRY)}")
    else:
        print(f"⚔️ Ennemis trouvés: {', '.join(enemies)}")
        
        started = []
        failed = []
        for enemy in enemies:
            # Essayer plusieurs fois de récupérer les membres (au cas où l'API est lente)
            members, country_name = None, None
            for attempt in range(3):
                members, country_name = await get_country_members(AUTO_SURVEILLANCE_SERVER, enemy)
                if members:
                    break
                await asyncio.sleep(1)  # Attendre 1 seconde entre chaque tentative
            
            if members:
                # Créer la tâche et attendre un peu pour s'assurer qu'elle démarre
                asyncio.create_task(assaut_loop(AUTO_SURVEILLANCE_SERVER, enemy))
                await asyncio.sleep(0.5)  # Petit délai pour laisser la tâche s'initialiser
                started.append(country_name or enemy)
                print(f"✅ Surveillance démarrée: {country_name} ({len(members)} membres)")
            else:
                # Démarrer quand même la surveillance, elle récupérera les membres plus tard
                asyncio.create_task(assaut_loop(AUTO_SURVEILLANCE_SERVER, enemy))
                await asyncio.sleep(0.5)
                started.append(enemy)
                print(f"⚠️ Surveillance démarrée pour {enemy} (membres seront récupérés au prochain cycle)")
                failed.append(enemy)
        
        if channel:
            msg = f"🤖 Bot démarré - {len(started)}/{len(enemies)} surveillance(s) activée(s)\n"
            if started:
                msg += f"📍 Pays surveillés: {', '.join(started)}"
            if failed:
                msg += f"\n⚠️ Pays ignorés: {', '.join(failed)}"
            await channel.send(msg)
    
    # Lancer la tâche de mise à jour automatique
    asyncio.create_task(update_enemies_surveillance())
    print(f"🔄 Mise à jour automatique activée (toutes les {AUTO_UPDATE_INTERVAL}s)")

if __name__ == "__main__":
    asyncio.run(main())
