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

surveillance = {}
ASSAUT_CHANNEL_ID = 1465336287471861771

AUTO_SURVEILLANCE_SERVER = "lime"
AUTO_SURVEILLANCE_COUNTRY = "tasmanie"
AUTO_UPDATE_INTERVAL = 5
MEMBER_UPDATE_INTERVAL = 10

current_enemies = set()

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
        except Exception as e:
            print(f"❌ Erreur get_countries_list: {e}")
    return []

async def get_country_members(server: str, country: str):
    url = f"https://publicapi.nationsglory.fr/country/{server}/{country}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 500):
                    data = await resp.json()
                    if "members" in data and data["members"]:
                        members = [m.lstrip("*+-") for m in data.get("members", [])]
                        return members, data.get("name", country)
        except Exception as e:
            print(f"❌ Erreur get_country_members({server}, {country}): {e}")
    return None, None

async def get_country_info(server: str, country: str):
    url = f"https://publicapi.nationsglory.fr/country/{server}/{country}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 500):
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
        except Exception as e:
            print(f"⚠️ Erreur get_online_players({server}): {e}")
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
    
    if not channel:
        print(f"❌ Channel introuvable pour {country}")
        return
    
    if not members:
        print(f"⚠️ Pas de membres pour {country}, réessai au prochain cycle...")
        members = []
        country_name = country
    
    if server not in surveillance:
        surveillance[server] = {}
    surveillance[server][country] = {"task": asyncio.current_task(), "assaut_possible": False}
    
    print(f"✅ Surveillance: {country_name} ({len(members)} membres)")
    
    last_member_update = time.time()
    
    try:
        while True:
            current_time = time.time()
            if current_time - last_member_update >= MEMBER_UPDATE_INTERVAL:
                new_members, new_country_name = await get_country_members(server, country)
                if new_members:
                    added = set(new_members) - set(members)
                    removed = set(members) - set(new_members)
                    
                    if added:
                        print(f"➕ {country_name}: {', '.join(added)}")
                    if removed:
                        print(f"➖ {country_name}: {', '.join(removed)}")
                    
                    members = new_members
                    country_name = new_country_name or country_name
                    print(f"🔄 {country_name}: {len(members)} membres")
                
                last_member_update = current_time
            
            if members:
                online = await get_online_players(server)
                connected = [m for m in members if m in online]
                
                verified_connected = []
                if len(connected) >= 2:
                    fresh_members, _ = await get_country_members(server, country)
                    if fresh_members:
                        verified_connected = [p for p in connected if p in fresh_members]
                        if len(connected) != len(verified_connected):
                            print(f"🔍 {country_name}: {len(connected)} online → {len(verified_connected)} vérifiés")
                    else:
                        verified_connected = []
                        print(f"⚠️ {country_name}: Impossible vérif, pas d'alerte")
                
                possible = False
                if len(verified_connected) >= 2:
                    ranks = {p: await get_user_rank(p, server) for p in verified_connected}
                    recruits = [p for p, r in ranks.items() if r == "recruit"]
                    valids = [p for p, r in ranks.items() if r in ("member", "officer", "leader")]
                    if (not recruits) or valids:
                        possible = True
                
                prev = surveillance[server][country]["assaut_possible"]
                if possible and not prev:
                    await channel.send(f"⚔️ @everyone ASSAUT POSSIBLE sur {country_name} ({server.upper()})\n👥 Connectés : {', '.join(verified_connected)}")
                    surveillance[server][country]["assaut_possible"] = True
                elif not possible and prev:
                    await channel.send(f"ℹ️ Assaut plus possible sur {country_name} ({server.upper()})")
                    surveillance[server][country]["assaut_possible"] = False
            
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        print(f"🛑 Surveillance annulée: {country_name}")
    except Exception as e:
        print(f"❌ Erreur assaut_loop {country}: {e}")
    finally:
        if server in surveillance and country in surveillance[server]:
            del surveillance[server][country]
            if not surveillance[server]:
                del surveillance[server]

@tree.command(name="assaut", description="Gérer la surveillance des assauts")
@app_commands.autocomplete(server=server_autocomplete, country=country_autocomplete, action=action_autocomplete)
async def assaut_command(interaction: discord.Interaction, server: str, country: str, action: str):
    await interaction.response.defer()
    if action.lower() not in ("start", "stop"):
        return await interaction.followup.send("❌ Action: start ou stop")
    
    if action.lower() == "start":
        if surveillance.get(server, {}).get(country):
            return await interaction.followup.send(f"⚠️ Déjà actif pour {country}")
        asyncio.create_task(assaut_loop(server, country))
        await interaction.followup.send(f"🔍 Surveillance activée: {country} ({server.upper()})")
    else:
        if surveillance.get(server, {}).get(country):
            surveillance[server][country]["task"].cancel()
            del surveillance[server][country]
            if not surveillance[server]:
                del surveillance[server]
            await interaction.followup.send(f"🛑 Surveillance arrêtée: {country}")
        else:
            await interaction.followup.send("❌ Surveillance inexistante")

@tree.command(name="assaut_list", description="Surveillances actives")
async def assaut_list_command(interaction: discord.Interaction):
    await interaction.response.defer()
    if not surveillance or all(not c for c in surveillance.values()):
        return await interaction.followup.send("ℹ️ Aucune surveillance")
    
    embed = discord.Embed(title="🔍 Surveillances", color=discord.Color.blue())
    total = 0
    for server, countries in surveillance.items():
        if countries:
            country_list = []
            for country, data in countries.items():
                status = "⚔️ POSSIBLE" if data["assaut_possible"] else "🛡️ Pas d'assaut"
                country_list.append(f"• {country} - {status}")
                total += 1
            embed.add_field(name=f"{SERVERS[server]['emoji']} {server.upper()}", value="\n".join(country_list), inline=False)
    embed.set_footer(text=f"Total: {total}")
    await interaction.followup.send(embed=embed)

@tree.command(name="debug_members", description="[DEBUG] Membres d'un pays")
@app_commands.autocomplete(server=server_autocomplete, country=country_autocomplete)
async def debug_members(interaction: discord.Interaction, server: str, country: str):
    await interaction.response.defer()
    if server not in SERVERS:
        return await interaction.followup.send("❌ Serveur invalide")
    members, country_name = await get_country_members(server, country)
    if not members:
        return await interaction.followup.send(f"❌ Pays introuvable")
    
    embed = discord.Embed(title=f"👥 {country_name}", description=f"{SERVERS[server]['emoji']} {server.upper()}", color=discord.Color.blue())
    chunks = [members[i:i+20] for i in range(0, len(members), 20)]
    for i, chunk in enumerate(chunks):
        name = f"Membres ({i*20+1}-{i*20+len(chunk)})" if len(chunks) > 1 else "Membres"
        embed.add_field(name=name, value=", ".join(chunk), inline=False)
    embed.set_footer(text=f"Total: {len(members)}")
    await interaction.followup.send(embed=embed)

@tree.command(name="debug_online", description="[DEBUG] Joueurs en ligne")
@app_commands.autocomplete(server=server_autocomplete)
async def debug_online(interaction: discord.Interaction, server: str):
    await interaction.response.defer()
    if server not in SERVERS:
        return await interaction.followup.send("❌ Serveur invalide")
    online = await get_online_players(server)
    if not online:
        return await interaction.followup.send(f"ℹ️ Personne en ligne sur {server.upper()}")
    
    embed = discord.Embed(title=f"🟢 {server.upper()}", color=discord.Color.green())
    chunks = [online[i:i+30] for i in range(0, len(online), 30)]
    for i, chunk in enumerate(chunks):
        name = f"Joueurs ({i*30+1}-{i*30+len(chunk)})" if len(chunks) > 1 else "Joueurs"
        embed.add_field(name=name, value=", ".join(chunk), inline=False)
    embed.set_footer(text=f"Total: {len(online)}")
    await interaction.followup.send(embed=embed)

@tree.command(name="debug_state", description="[DEBUG] État surveillance")
@app_commands.autocomplete(server=server_autocomplete, country=country_autocomplete)
async def debug_state(interaction: discord.Interaction, server: str, country: str):
    await interaction.response.defer()
    if server not in SERVERS:
        return await interaction.followup.send("❌ Serveur invalide")
    if not surveillance.get(server, {}).get(country):
        return await interaction.followup.send(f"❌ Pas de surveillance pour {country}")
    
    members, country_name = await get_country_members(server, country)
    online = await get_online_players(server)
    if not members:
        return await interaction.followup.send("❌ Erreur récup données")
    
    connected = [m for m in members if m in online]
    verified_connected = []
    if len(connected) >= 2:
        fresh_members, _ = await get_country_members(server, country)
        if fresh_members:
            verified_connected = [p for p in connected if p in fresh_members]
    
    embed = discord.Embed(title=f"🔍 {country_name}", description=f"{SERVERS[server]['emoji']} {server.upper()}", color=discord.Color.orange())
    status = "⚔️ POSSIBLE" if surveillance[server][country]["assaut_possible"] else "🛡️ Pas d'assaut"
    embed.add_field(name="📍 Statut", value=status, inline=False)
    
    members_preview = ", ".join(members[:10])
    if len(members) > 10:
        members_preview += f"... (+{len(members)-10})"
    embed.add_field(name=f"👥 Membres ({len(members)})", value=members_preview, inline=False)
    embed.add_field(name=f"🟢 En ligne", value=f"{len(online)} joueurs", inline=True)
    
    if connected:
        embed.add_field(name=f"🎮 Connectés ({len(connected)})", value=", ".join(connected), inline=False)
    else:
        embed.add_field(name="🎮 Connectés", value="Aucun", inline=False)
    
    if len(connected) >= 2:
        if verified_connected:
            embed.add_field(name=f"✅ Vérifiés ({len(verified_connected)})", value=", ".join(verified_connected), inline=False)
        else:
            embed.add_field(name="✅ Vérifiés", value="⚠️ Aucun", inline=False)
    
    await interaction.followup.send(embed=embed)

# ==================== SERVEUR WEB ====================

async def update_enemies_surveillance():
    global current_enemies
    channel = client.get_channel(ASSAUT_CHANNEL_ID)
    await asyncio.sleep(10)
    
    while True:
        try:
            country_info = await get_country_info(AUTO_SURVEILLANCE_SERVER, AUTO_SURVEILLANCE_COUNTRY)
            if country_info:
                new_enemies = set(country_info.get("enemies", []))
                to_add = new_enemies - current_enemies
                for enemy in to_add:
                    members, country_name = await get_country_members(AUTO_SURVEILLANCE_SERVER, enemy)
                    if members:
                        if not surveillance.get(AUTO_SURVEILLANCE_SERVER, {}).get(enemy):
                            asyncio.create_task(assaut_loop(AUTO_SURVEILLANCE_SERVER, enemy))
                            print(f"➕ Nouveau: {country_name}")
                            if channel:
                                await channel.send(f"➕ Guerre détectée ! Surveillance: **{country_name}**")
                
                to_remove = current_enemies - new_enemies
                for enemy in to_remove:
                    if surveillance.get(AUTO_SURVEILLANCE_SERVER, {}).get(enemy):
                        surveillance[AUTO_SURVEILLANCE_SERVER][enemy]["task"].cancel()
                        del surveillance[AUTO_SURVEILLANCE_SERVER][enemy]
                        if not surveillance[AUTO_SURVEILLANCE_SERVER]:
                            del surveillance[AUTO_SURVEILLANCE_SERVER]
                        print(f"➖ Paix: {enemy}")
                        if channel:
                            await channel.send(f"🕊️ Paix avec **{enemy}**")
                current_enemies = new_enemies
        except Exception as e:
            print(f"❌ Erreur update enemies: {e}")
        await asyncio.sleep(AUTO_UPDATE_INTERVAL)

async def handle_health(request):
    return web.Response(text="✅")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 HTTP: {port}")

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
    print(f"✅ Connecté: {client.user}")
    
    try:
        await tree.sync()
        print("✅ Commandes sync")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return
    
    channel = client.get_channel(ASSAUT_CHANNEL_ID)
    print(f"🔍 Récup ennemis {AUTO_SURVEILLANCE_COUNTRY}...")
    
    country_info = await get_country_info(AUTO_SURVEILLANCE_SERVER, AUTO_SURVEILLANCE_COUNTRY)
    if not country_info:
        print(f"❌ Infos {AUTO_SURVEILLANCE_COUNTRY} impossible")
        if channel:
            await channel.send(f"❌ Erreur démarrage")
        return
    
    enemies = country_info.get("enemies", [])
    current_enemies = set(enemies)
    
    if not enemies:
        print(f"ℹ️ Pas d'ennemis")
        if channel:
            await channel.send(f"🤖 Démarré - Aucune guerre")
    else:
        print(f"⚔️ Ennemis: {', '.join(enemies)}")
        started = []
        for enemy in enemies:
            members, country_name = None, None
            for _ in range(3):
                members, country_name = await get_country_members(AUTO_SURVEILLANCE_SERVER, enemy)
                if members:
                    break
                await asyncio.sleep(1)
            
            asyncio.create_task(assaut_loop(AUTO_SURVEILLANCE_SERVER, enemy))
            await asyncio.sleep(0.3)
            started.append(country_name or enemy)
            if members:
                print(f"✅ {country_name} ({len(members)} membres)")
            else:
                print(f"⚠️ {enemy} (récup plus tard)")
        
        if channel:
            await channel.send(f"🤖 Démarré - {len(started)} surveillance(s)\n📍 {', '.join(started)}")
    
    asyncio.create_task(update_enemies_surveillance())
    print(f"🔄 Auto-update: {AUTO_UPDATE_INTERVAL}s")

if __name__ == "__main__":
    asyncio.run(main())
