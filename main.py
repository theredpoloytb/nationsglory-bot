import discord
from discord import app_commands
import aiohttp
import asyncio
import time
import os
from aiohttp import web
import logging

# ==================== CONFIGURATION ====================

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validation des variables d'environnement
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NG_API_KEY = os.getenv("NG_API_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")

if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN manquant dans les variables d'environnement")
if not NG_API_KEY:
    raise ValueError("❌ NG_API_KEY manquant dans les variables d'environnement")

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
surveillance_lock = asyncio.Lock()
ASSAUT_CHANNEL_ID = int(os.getenv("ASSAUT_CHANNEL_ID", "1465336287471861771"))
MAX_SURVEILLANCES = 20

# Configuration de la surveillance automatique
AUTO_SURVEILLANCE_SERVER = "lime"
AUTO_SURVEILLANCE_COUNTRY = "tasmanie"
AUTO_UPDATE_INTERVAL = 5

# Intervalles de rafraîchissement
MEMBER_REFRESH_INTERVAL = 60  # FIX: Actualiser les membres toutes les 60 secondes
ONLINE_CHECK_INTERVAL = 2      # Vérifier qui est en ligne toutes les 2 secondes

current_enemies = set()
last_notification = {}  # {country: timestamp} - Cooldown pour éviter le spam

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
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 500):
                    data = await resp.json()
                    claimed = [c["name"] for c in data.get("claimed", []) if c.get("name")]
                    countries_cache[server] = (claimed, now)
                    return claimed
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f"Erreur get_countries_list({server}): {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue get_countries_list({server}): {e}")
    
    return []

async def get_country_members(server: str, country: str):
    """FIX: Correction de la structure try/except défectueuse"""
    url = f"https://publicapi.nationsglory.fr/country/{server}/{country}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 500):  # L'API peut renvoyer 500 même quand ça marche
                    data = await resp.json()
                    if "members" in data and data["members"]:
                        members = [m.lstrip("*+-") for m in data.get("members", [])]
                        return members, data.get("name", country)
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f"Erreur get_country_members({server}, {country}): {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue get_country_members({server}, {country}): {e}")
    
    return None, None

async def get_country_info(server: str, country: str):
    """Récupère toutes les infos d'un pays incluant les ennemis"""
    url = f"https://publicapi.nationsglory.fr/country/{server}/{country}"
    headers = {"Authorization": f"Bearer {NG_API_KEY}", "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status in (200, 500):
                    return await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f"Erreur get_country_info({server}, {country}): {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue get_country_info({server}, {country}): {e}")
    
    return None

async def get_online_players(server: str):
    url = SERVERS[server]["url"]
    timeout = aiohttp.ClientTimeout(total=5)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [p["name"] for p in data.get("players", [])]
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning(f"Erreur get_online_players({server}): {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue get_online_players({server}): {e}")
    
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
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rank = data.get("servers", {}).get(server, {}).get("country_rank")
                    user_rank_cache[key] = (rank, now)
                    return rank
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning(f"Erreur get_user_rank({username}, {server}): {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue get_user_rank({username}, {server}): {e}")
    
    return None

def can_send_notification(country: str, cooldown: int = 300) -> bool:
    """Empêche le spam de notifications @everyone"""
    now = time.time()
    if country in last_notification:
        if now - last_notification[country] < cooldown:
            return False
    last_notification[country] = now
    return True

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
    """
    FIX MAJEUR: Actualise périodiquement la liste des membres du pays
    pour détecter les nouveaux arrivants et les départs
    """
    channel = client.get_channel(ASSAUT_CHANNEL_ID)
    
    if not channel:
        logger.error(f"Canal {ASSAUT_CHANNEL_ID} introuvable!")
        return

    # Variables pour la gestion des membres
    members = []
    country_name = country
    last_member_refresh = 0
    
    # Initialiser la surveillance avec le verrou
    async with surveillance_lock:
        if server not in surveillance:
            surveillance[server] = {}
        surveillance[server][country] = {
            "task": asyncio.current_task(),
            "assaut_possible": False
        }

    logger.info(f"✅ Surveillance démarrée pour {country} sur {server.upper()}")

    try:
        error_count = 0
        
        while True:
            try:
                now = time.time()
                
                # FIX: Rafraîchir les membres périodiquement
                if now - last_member_refresh >= MEMBER_REFRESH_INTERVAL or not members:
                    new_members, new_name = await get_country_members(server, country)
                    
                    if new_members:
                        # Détecter les changements significatifs
                        if members and len(new_members) != len(members):
                            diff = len(new_members) - len(members)
                            if diff > 0:
                                logger.info(f"📈 {country_name}: +{diff} membre(s)")
                                if diff >= 3 and channel:
                                    await channel.send(
                                        f"⚠️ **{country_name}** ({server.upper()}) a recruté "
                                        f"**{diff} nouveaux membres** !"
                                    )
                            else:
                                logger.info(f"📉 {country_name}: {diff} membre(s)")
                                if abs(diff) >= 3 and channel:
                                    await channel.send(
                                        f"ℹ️ **{country_name}** ({server.upper()}) a perdu "
                                        f"**{abs(diff)} membres**"
                                    )
                        
                        members = new_members
                        country_name = new_name
                        last_member_refresh = now
                        
                        if not error_count:  # Ne log que si pas en mode recovery
                            logger.debug(f"🔄 Membres actualisés pour {country_name}: {len(members)} membres")
                    else:
                        # Le pays a disparu ou est vide
                        logger.warning(f"⚠️ Pays {country} introuvable ou vide, arrêt surveillance")
                        if channel:
                            await channel.send(
                                f"⚠️ Pays **{country_name}** ({server.upper()}) introuvable - "
                                f"Surveillance arrêtée"
                            )
                        break
                
                # Si on n'a pas encore de membres, attendre le prochain refresh
                if not members:
                    await asyncio.sleep(5)
                    continue
                
                # Vérifier qui est en ligne
                online = await get_online_players(server)
                connected = [m for m in members if m in online]
                
                # FIX: Logique d'assaut clarifiée
                possible = False
                if len(connected) >= 2:
                    ranks = {p: await get_user_rank(p, server) for p in connected}
                    valids = [p for p, r in ranks.items() if r in ("member", "officer", "leader")]
                    
                    # Assaut possible si au moins 2 joueurs ET au moins 1 non-recruit
                    if len(connected) >= 2 and len(valids) >= 1:
                        possible = True
                
                async with surveillance_lock:
                    if server not in surveillance or country not in surveillance[server]:
                        logger.warning(f"Surveillance retirée pour {country_name}, arrêt de la boucle")
                        break
                    
                    prev = surveillance[server][country]["assaut_possible"]
                    
                    if possible and not prev:
                        # Cooldown pour éviter le spam
                        if can_send_notification(country):
                            await channel.send(
                                f"⚔️ @everyone **ASSAUT POSSIBLE** sur **{country_name}** ({server.upper()})\n"
                                f"👥 Connectés ({len(connected)}): {', '.join(connected)}"
                            )
                        surveillance[server][country]["assaut_possible"] = True
                    elif not possible and prev:
                        await channel.send(
                            f"🛡️ Assaut plus possible sur **{country_name}** ({server.upper()})"
                        )
                        surveillance[server][country]["assaut_possible"] = False
                
                error_count = 0  # Reset du compteur d'erreurs
                await asyncio.sleep(ONLINE_CHECK_INTERVAL)
                
            except Exception as e:
                error_count += 1
                logger.error(f"Erreur dans assaut_loop ({error_count}/5): {e}")
                if error_count >= 5:
                    logger.error(f"Trop d'erreurs pour {country_name}, arrêt de la surveillance")
                    if channel:
                        await channel.send(
                            f"❌ Surveillance de **{country_name}** ({server.upper()}) arrêtée "
                            f"suite à des erreurs répétées"
                        )
                    break
                await asyncio.sleep(5)  # Backoff en cas d'erreur
                
    except asyncio.CancelledError:
        logger.info(f"🛑 Surveillance annulée pour {country_name} sur {server}")
    finally:
        # Nettoyage sécurisé
        async with surveillance_lock:
            if server in surveillance and country in surveillance[server]:
                del surveillance[server][country]
                if not surveillance[server]:
                    del surveillance[server]
                logger.info(f"Nettoyage effectué pour {country_name}")

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
        # Vérifier la limite de surveillances
        total_surveillances = sum(len(countries) for countries in surveillance.values())
        if total_surveillances >= MAX_SURVEILLANCES:
            return await interaction.followup.send(
                f"⚠️ Limite atteinte ({MAX_SURVEILLANCES} surveillances max)"
            )
        
        async with surveillance_lock:
            if surveillance.get(server, {}).get(country):
                return await interaction.followup.send(
                    f"⚠️ Surveillance déjà active pour {country} sur {server.upper()}"
                )

        task = asyncio.create_task(assaut_loop(server, country))
        await interaction.followup.send(f"🔍 Surveillance activée pour {country} sur {server.upper()}")
    else:
        async with surveillance_lock:
            if surveillance.get(server, {}).get(country):
                surveillance[server][country]["task"].cancel()
                await interaction.followup.send(f"🛑 Surveillance arrêtée pour {country} sur {server.upper()}")
            else:
                await interaction.followup.send("❌ Cette surveillance n'existe pas")

@tree.command(name="assaut_list", description="Affiche toutes les surveillances actives")
async def assaut_list_command(interaction: discord.Interaction):
    await interaction.response.defer()

    async with surveillance_lock:
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

# ==================== SURVEILLANCE AUTO ====================

async def update_enemies_surveillance():
    """Mise à jour automatique des surveillances en fonction des ennemis"""
    channel = client.get_channel(ASSAUT_CHANNEL_ID)
    await asyncio.sleep(10)

    while True:
        try:
            country_info = await get_country_info(AUTO_SURVEILLANCE_SERVER, AUTO_SURVEILLANCE_COUNTRY)

            if country_info:
                new_enemies = set(country_info.get("enemies", []))

                # Nouveaux ennemis à ajouter
                to_add = new_enemies - current_enemies
                for enemy in to_add:
                    members, country_name = await get_country_members(AUTO_SURVEILLANCE_SERVER, enemy)
                    if members:
                        async with surveillance_lock:
                            if not surveillance.get(AUTO_SURVEILLANCE_SERVER, {}).get(enemy):
                                asyncio.create_task(assaut_loop(AUTO_SURVEILLANCE_SERVER, enemy))
                                logger.info(f"➕ Nouveau pays surveillé: {country_name}")
                                if channel:
                                    await channel.send(
                                        f"➕ **Nouvelle guerre détectée !** Surveillance activée pour **{country_name}**"
                                    )

                # Ennemis à retirer (paix signée)
                to_remove = current_enemies - new_enemies
                for enemy in to_remove:
                    async with surveillance_lock:
                        if surveillance.get(AUTO_SURVEILLANCE_SERVER, {}).get(enemy):
                            surveillance[AUTO_SURVEILLANCE_SERVER][enemy]["task"].cancel()
                            logger.info(f"➖ Pays retiré: {enemy} (paix signée)")
                            if channel:
                                await channel.send(f"🕊️ Paix signée avec **{enemy}** - Surveillance arrêtée")

                current_enemies.clear()
                current_enemies.update(new_enemies)

        except Exception as e:
            logger.error(f"Erreur update_enemies_surveillance: {e}")

        await asyncio.sleep(AUTO_UPDATE_INTERVAL)

# ==================== SERVEUR WEB / SELF-PING ====================

async def handle_health(request):
    total_surveillances = sum(len(countries) for countries in surveillance.values())
    return web.Response(
        text=f"Bot actif! ✅\nSurveillances: {total_surveillances}/{MAX_SURVEILLANCES}"
    )

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/health', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Serveur HTTP démarré sur le port {port}")

async def self_ping():
    await asyncio.sleep(60)
    while True:
        try:
            if RENDER_URL:
                url = RENDER_URL if RENDER_URL.startswith("http") else f"https://{RENDER_URL}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)):
                        pass
        except Exception as e:
            logger.warning(f"Erreur self-ping: {e}")
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
    logger.info(f"✅ Bot connecté en tant que {client.user}")

    channel = client.get_channel(ASSAUT_CHANNEL_ID)
    if not channel:
        logger.error(f"❌ Canal {ASSAUT_CHANNEL_ID} introuvable!")
        return

    logger.info(f"🔍 Récupération des ennemis de {AUTO_SURVEILLANCE_COUNTRY} sur {AUTO_SURVEILLANCE_SERVER.upper()}...")
    country_info = await get_country_info(AUTO_SURVEILLANCE_SERVER, AUTO_SURVEILLANCE_COUNTRY)

    if not country_info:
        logger.error(f"Impossible de récupérer les infos de {AUTO_SURVEILLANCE_COUNTRY}")
        if channel:
            await channel.send(f"❌ Impossible de récupérer les infos de {AUTO_SURVEILLANCE_COUNTRY}")
        return

    enemies = country_info.get("enemies", [])
    current_enemies = set(enemies)

    if not enemies:
        logger.info(f"ℹ️ Aucun ennemi trouvé pour {AUTO_SURVEILLANCE_COUNTRY}")
        if channel:
            await channel.send(
                f"🤖 Bot démarré - Aucun pays en guerre avec {country_info.get('name', AUTO_SURVEILLANCE_COUNTRY)}"
            )
    else:
        logger.info(f"⚔️ Ennemis trouvés: {', '.join(enemies)}")

        started = []
        failed = []
        for enemy in enemies:
            members, country_name = await get_country_members(AUTO_SURVEILLANCE_SERVER, enemy)
            if members:
                asyncio.create_task(assaut_loop(AUTO_SURVEILLANCE_SERVER, enemy))
                await asyncio.sleep(1)
                started.append(country_name or enemy)
                logger.info(f"✅ Surveillance démarrée: {country_name} ({len(members)} membres)")
            else:
                failed.append(enemy)
                logger.warning(f"⚠️ Pays {enemy} introuvable ou sans membres")

        if channel:
            msg = f"🤖 Bot démarré - {len(started)}/{len(enemies)} surveillance(s) activée(s)\n"
            if started:
                msg += f"📍 Pays surveillés: {', '.join(started)}"
            if failed:
                msg += f"\n⚠️ Pays ignorés: {', '.join(failed)}"
            await channel.send(msg)

    asyncio.create_task(update_enemies_surveillance())
    logger.info(f"🔄 Mise à jour automatique activée (toutes les {AUTO_UPDATE_INTERVAL}s)")

if __name__ == "__main__":
    asyncio.run(main())
