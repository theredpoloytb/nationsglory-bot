import discord
from discord import app_commands
import aiohttp
import asyncio
import time
import json
import os
import sys
from aiohttp import web
from datetime import timedelta, datetime

# ==================== CONFIGURATION ====================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NG_API_KEY    = os.getenv("NG_API_KEY")
RENDER_URL    = os.getenv("RENDER_EXTERNAL_URL", "")
MONGO_URL     = os.getenv("MONGO_URL")

RAPPORT_CHANNEL_ID = 1459182029924073558
ALERTE_CHANNEL_ID  = 1465309715230888090
STORAGE_CHANNEL_ID = 1478831933017428070

WATCH_LIST_DEFAULT = [
    "Canisi", "Darkholess", "UFO_Thespoot", "Franky753",
    "Blakonne", "Farsgame", "ClashKiller78", "Olmat38",
    "FLOTYR2", "Raptor51"
]

WATCH_LIST       = list(WATCH_LIST_DEFAULT)
watchlist_msg_id = None

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

CACHE_TTL       = 900
countries_cache = {}

# ==================== CORS ====================

CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

def cors(data, status=200):
    return web.Response(
        text=json.dumps(data, ensure_ascii=False),
        status=status,
        content_type="application/json",
        headers=CORS_HEADERS
    )

async def handle_options(request):
    return web.Response(status=204, headers=CORS_HEADERS)

# ==================== MONGODB ====================

mongo_client = None
db           = None
sessions_col = None
config_col   = None
mongo_ok     = False

def init_mongo():
    global mongo_client, db, sessions_col, config_col, mongo_ok
    print("🔌 Connexion MongoDB...", flush=True)
    if not MONGO_URL:
        print("❌ MONGO_URL non défini !", flush=True)
        return
    try:
        from pymongo import MongoClient, ASCENDING
        mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=8000, tls=True, tlsAllowInvalidCertificates=True)
        mongo_client.admin.command('ping')
        db           = mongo_client["mossadglory"]
        sessions_col = db["sessions"]
        config_col   = db["config"]
        sessions_col.create_index([("player", ASCENDING), ("ts", ASCENDING)])
        mongo_ok = True
        print("✅ MongoDB connecté !", flush=True)
    except Exception as e:
        print(f"❌ MongoDB erreur: {e}", flush=True)

def record_connection(player: str, server: str):
    if not mongo_ok or sessions_col is None:
        return
    try:
        now = datetime.utcnow() + timedelta(hours=1)
        sessions_col.insert_one({
            "player":  player,
            "server":  server,
            "ts":      now,
            "day":     now.weekday(),
            "hour":    now.hour,
            "minute":  now.minute
        })
    except Exception as e:
        print(f"❌ record_connection erreur: {e}", flush=True)

def get_sessions(player: str, limit: int = 500):
    if not mongo_ok or sessions_col is None:
        return []
    try:
        from pymongo import ASCENDING
        return list(sessions_col.find(
            {"player": player},
            {"_id": 0}
        ).sort("ts", ASCENDING).limit(limit))
    except:
        return []

def get_pronostic(player: str):
    sessions = get_sessions(player, limit=200)
    if len(sessions) < 3:
        return None
    DAYS        = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    day_counts  = [0] * 7
    hour_by_day = [[] for _ in range(7)]
    for s in sessions:
        d = s["day"]
        day_counts[d] += 1
        hour_by_day[d].append(s["hour"] + s.get("minute", 0) / 60)
    total  = len(sessions)
    result = []
    for d in range(7):
        if day_counts[d] == 0:
            continue
        avg   = sum(hour_by_day[d]) / len(hour_by_day[d])
        avg_h = int(avg)
        avg_m = int((avg - avg_h) * 60)
        pct   = round(day_counts[d] / total * 100)
        result.append((d, avg_h, avg_m, pct))
    result.sort(key=lambda x: -x[3])
    return result[:5], DAYS, total

def get_plages(player: str):
    sessions = get_sessions(player, limit=500)
    if not sessions:
        return None
    DAYS    = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    heatmap = [[0]*24 for _ in range(7)]
    for s in sessions:
        heatmap[s["day"]][s["hour"]] += 1
    return heatmap, DAYS

def save_rapport_id(msg_id: int):
    if not mongo_ok or config_col is None:
        return
    try:
        config_col.update_one(
            {"key": "rapport_msg_id"},
            {"$set": {"value": msg_id}},
            upsert=True
        )
    except:
        pass

def load_rapport_id():
    if not mongo_ok or config_col is None:
        return None
    try:
        doc = config_col.find_one({"key": "rapport_msg_id"})
        return doc["value"] if doc else None
    except:
        return None

# ==================== WATCHLIST ====================

async def load_watchlist():
    global WATCH_LIST, watchlist_msg_id
    channel = client.get_channel(STORAGE_CHANNEL_ID)
    if not channel:
        return
    async for msg in channel.history(limit=50):
        if msg.author == client.user and msg.content.startswith("WATCHLIST:"):
            try:
                data             = json.loads(msg.content[len("WATCHLIST:"):])
                WATCH_LIST       = data["players"]
                watchlist_msg_id = msg.id
                print(f"✅ Watchlist chargée : {WATCH_LIST}", flush=True)
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

# ==================== API ROUTES ====================

async def api_health(request):
    return cors({"status": "ok", "mongo": mongo_ok})

async def api_online(request):
    server = request.match_info["server"].lower()
    if server not in SERVERS:
        return cors({"error": "Serveur invalide"}, 400)
    players = await get_online_players(server)
    return cors({"server": server, "players": players, "count": len(players)})

async def api_online_all(request):
    tasks   = {s: get_online_players(s) for s in SERVERS}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    data    = {s: (r if isinstance(r, list) else []) for s, r in zip(tasks.keys(), results)}
    return cors(data)

async def api_checkall(request):
    player  = request.match_info["player"]
    tasks   = {s: get_online_players(s) for s in SERVERS}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    found   = [s for s, r in zip(tasks.keys(), results) if isinstance(r, list) and player in r]
    return cors({"player": player, "servers": found})

async def api_countries(request):
    server = request.match_info["server"].lower()
    if server not in SERVERS:
        return cors({"error": "Serveur invalide"}, 400)
    countries = await get_countries_list(server)
    return cors({"server": server, "countries": countries})

async def api_check(request):
    server  = request.match_info["server"].lower()
    country = request.match_info["country"]
    if server not in SERVERS:
        return cors({"error": "Serveur invalide"}, 400)
    members, name = await get_country_members(server, country)
    if not members:
        return cors({"error": "Pays introuvable"}, 404)
    tasks   = {s: get_online_players(s) for s in SERVERS}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    found   = {}
    total   = 0
    for s, r in zip(tasks.keys(), results):
        if not isinstance(r, list):
            continue
        f = [m for m in members if m in r]
        if f:
            found[s] = f
            total   += len(f)
    return cors({"country": name, "members_total": len(members), "online_total": total, "servers": found})

async def api_watchlist_get(request):
    return cors({"players": WATCH_LIST})

async def api_watchlist_add(request):
    try:
        body   = await request.json()
        player = body.get("player", "").strip()
        if not player:
            return cors({"error": "Nom vide"}, 400)
        if player not in WATCH_LIST:
            WATCH_LIST.append(player)
            await save_watchlist()
        return cors({"players": WATCH_LIST})
    except Exception as e:
        return cors({"error": str(e)}, 400)

async def api_watchlist_remove(request):
    try:
        body   = await request.json()
        player = body.get("player", "").strip()
        if player in WATCH_LIST:
            WATCH_LIST.remove(player)
            await save_watchlist()
        return cors({"players": WATCH_LIST})
    except Exception as e:
        return cors({"error": str(e)}, 400)

async def api_pronostic(request):
    player = request.match_info["player"]
    result = get_pronostic(player)
    if not result:
        return cors({"error": "Pas assez de données (min 3 connexions)"}, 404)
    top, DAYS, total = result
    return cors({
        "player": player, "total": total,
        "pronostic": [{"day": DAYS[d], "avg_h": h, "avg_m": m, "pct": pct} for d, h, m, pct in top]
    })

async def api_plages(request):
    player = request.match_info["player"]
    result = get_plages(player)
    if not result:
        return cors({"error": "Aucune donnée"}, 404)
    heatmap, DAYS = result
    return cors({"player": player, "days": DAYS, "heatmap": heatmap})

# ==================== AUTOCOMPLETIONS ====================

async def server_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=s.upper(), value=s) for s in SERVERS if current.lower() in s.lower()][:25]

async def country_autocomplete(interaction: discord.Interaction, current: str):
    server = interaction.namespace.server
    if not server or server not in SERVERS:
        return []
    countries = await get_countries_list(server)
    return [app_commands.Choice(name=c, value=c) for c in countries if current.lower() in c.lower()][:25]

# ==================== COMMANDES ====================

@tree.command(name="check", description="Espionne les membres d'un pays sur tous les serveurs")
@app_commands.autocomplete(server=server_autocomplete, country=country_autocomplete)
async def check_command(interaction: discord.Interaction, server: str, country: str):
    await interaction.response.defer()
    if server not in SERVERS:
        return await interaction.followup.send("❌ Serveur invalide")
    members, country_name = await get_country_members(server, country)
    if not members:
        return await interaction.followup.send("❌ Pays introuvable")
    tasks            = {s: get_online_players(s) for s in SERVERS}
    results          = await asyncio.gather(*tasks.values())
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

@tree.command(name="checkall", description="Voir sur quel serveur un joueur est connecté")
async def checkall_command(interaction: discord.Interaction, joueur: str):
    await interaction.response.defer()
    tasks            = {s: get_online_players(s) for s in SERVERS}
    results          = await asyncio.gather(*tasks.values())
    online_by_server = dict(zip(tasks.keys(), results))
    found = [s for s, players in online_by_server.items() if joueur in players]
    embed = discord.Embed(title=f"🔍 Localisation de {joueur}", color=discord.Color.red())
    if found:
        embed.color       = discord.Color.green()
        embed.description = "\n".join([f"{SERVERS[s]['emoji']} **{s.upper()}**" for s in found])
    else:
        embed.description = f"**{joueur}** n'est connecté sur aucun serveur"
    await interaction.followup.send(embed=embed)

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

@tree.command(name="pronostic", description="Pronostic de connexion d'un joueur")
async def pronostic_command(interaction: discord.Interaction, joueur: str):
    await interaction.response.defer()
    if not mongo_ok:
        return await interaction.followup.send("❌ MongoDB non connecté", ephemeral=True)
    result = get_pronostic(joueur)
    if not result:
        return await interaction.followup.send(
            f"⚠️ Pas assez de données pour **{joueur}** (minimum 3 connexions)", ephemeral=True
        )
    top, DAYS, total = result
    embed = discord.Embed(
        title=f"🔮 Pronostic — {joueur}",
        description=f"Basé sur **{total}** connexions enregistrées",
        color=discord.Color.purple()
    )
    for d, avg_h, avg_m, pct in top:
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        embed.add_field(
            name=f"{DAYS[d]} — {pct}%",
            value=f"`{bar}` Heure moyenne : **{avg_h}h{str(avg_m).zfill(2)}**",
            inline=False
        )
    embed.set_footer(text="% = fréquence de connexion par jour de la semaine")
    await interaction.followup.send(embed=embed)

@tree.command(name="plages", description="Voir les plages horaires de connexion d'un joueur")
async def plages_command(interaction: discord.Interaction, joueur: str):
    await interaction.response.defer()
    if not mongo_ok:
        return await interaction.followup.send("❌ MongoDB non connecté", ephemeral=True)
    result = get_plages(joueur)
    if not result:
        return await interaction.followup.send(f"⚠️ Aucune donnée pour **{joueur}**", ephemeral=True)
    heatmap, DAYS = result
    embed = discord.Embed(title=f"🕐 Plages horaires — {joueur}", color=discord.Color.orange())
    for d in range(7):
        row = heatmap[d]
        if sum(row) == 0:
            continue
        hours_with_data = [h for h in range(24) if row[h] > 0]
        plages = []
        start  = hours_with_data[0]
        prev   = hours_with_data[0]
        for h in hours_with_data[1:]:
            if h - prev > 2:
                plages.append(f"{start}h-{prev+1}h")
                start = h
            prev = h
        plages.append(f"{start}h-{prev+1}h")
        embed.add_field(name=DAYS[d], value=" • ".join(plages), inline=True)
    embed.set_footer(text="Basé sur l'historique complet des connexions")
    await interaction.followup.send(embed=embed)

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

# ==================== SCANNER ====================

last_states        = {s: {} for s in SERVERS}
rapport_message_id = None

async def scan_server(server: str, alerte_channel):
    players    = await get_online_players(server)
    player_set = set(players)
    prev       = last_states[server]
    for player in player_set:
        if not prev.get(player, False):
            record_connection(player, server)
            if player in WATCH_LIST and alerte_channel:
                embed = discord.Embed(
                    title="🟢 CONNEXION DÉTECTÉE",
                    description=f"**{player}** vient de se connecter sur **{server.upper()}**",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                await alerte_channel.send(embed=embed)
    for player, was_online in prev.items():
        if was_online and player not in player_set:
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

async def scanner_loop():
    global rapport_message_id
    await client.wait_until_ready()
    await load_watchlist()
    rapport_message_id = await asyncio.get_event_loop().run_in_executor(None, load_rapport_id)
    print(f"📋 Rapport message ID: {rapport_message_id}", flush=True)
    rapport_channel = client.get_channel(RAPPORT_CHANNEL_ID)
    alerte_channel  = client.get_channel(ALERTE_CHANNEL_ID)
    scan_tick = 0
    while True:
        try:
            tasks          = {s: scan_server(s, alerte_channel) for s in SERVERS}
            results        = await asyncio.gather(*tasks.values(), return_exceptions=True)
            server_players = dict(zip(tasks.keys(), results))
            if scan_tick % 5 == 0:
                lime_players    = server_players.get("lime", [])
                if isinstance(lime_players, Exception):
                    lime_players = []
                watched_online  = [p for p in WATCH_LIST if p in lime_players]
                watched_offline = [p for p in WATCH_LIST if p not in lime_players]
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
                rapport_embed.add_field(name="👥 Connectés Total", value=f"**{len(lime_players)}**", inline=True)
                rapport_embed.add_field(name="⏱️ Dernier relevé",  value=f"**{time_str}**",          inline=True)
                rapport_embed.add_field(name="👁️ Surveillance", value=status_text or "Aucun joueur surveillé en ligne", inline=False)
                rapport_embed.set_footer(text=f"Scanner interserveur • MongoDB {'✅' if mongo_ok else '❌'}")
                if rapport_channel:
                    if rapport_message_id:
                        try:
                            msg = await rapport_channel.fetch_message(rapport_message_id)
                            await msg.edit(embed=rapport_embed)
                        except discord.NotFound:
                            msg                = await rapport_channel.send(embed=rapport_embed)
                            rapport_message_id = msg.id
                            await asyncio.get_event_loop().run_in_executor(None, save_rapport_id, rapport_message_id)
                    else:
                        msg                = await rapport_channel.send(embed=rapport_embed)
                        rapport_message_id = msg.id
                        await asyncio.get_event_loop().run_in_executor(None, save_rapport_id, rapport_message_id)
            scan_tick += 1
        except Exception as e:
            print(f"❌ Erreur scanner: {e}", flush=True)
        await asyncio.sleep(1)

# ==================== SERVEUR WEB ====================

async def start_webserver():
    app = web.Application()
    app.router.add_get('/',       api_health)
    app.router.add_get('/health', api_health)
    app.router.add_get('/api/online/{server}',          api_online)
    app.router.add_get('/api/online_all',               api_online_all)
    app.router.add_get('/api/checkall/{player}',        api_checkall)
    app.router.add_get('/api/countries/{server}',       api_countries)
    app.router.add_get('/api/check/{server}/{country}', api_check)
    app.router.add_get('/api/watchlist',                api_watchlist_get)
    app.router.add_post('/api/watchlist/add',           api_watchlist_add)
    app.router.add_post('/api/watchlist/remove',        api_watchlist_remove)
    app.router.add_get('/api/pronostic/{player}',       api_pronostic)
    app.router.add_get('/api/plages/{player}',          api_plages)
    app.router.add_route('OPTIONS', '/{path_info:.*}',  handle_options)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Serveur HTTP + API démarré sur port {port}", flush=True)

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
    print("🚀 Démarrage du bot...", flush=True)
    init_mongo()
    await asyncio.sleep(5)
    async with client:
        asyncio.create_task(start_webserver())
        if RENDER_URL:
            asyncio.create_task(self_ping())
        asyncio.create_task(scanner_loop())
        try:
            await client.start(DISCORD_TOKEN)
        except discord.errors.HTTPException as e:
            print(f"❌ Erreur connexion Discord (rate limit?) : {e}", flush=True)
            await asyncio.sleep(60)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}", flush=True)
            await asyncio.sleep(30)
            sys.exit(1)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot connecté : {client.user}", flush=True)
    print(f"🌍 Scanner interserveur actif — {len(SERVERS)} serveurs", flush=True)
    print(f"🗄️ MongoDB : {'✅ OK' if mongo_ok else '❌ NON CONNECTÉ'}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
