import discord, aiohttp, asyncio, time, json, os, sys
from discord import app_commands
from aiohttp import web
from datetime import timedelta, datetime

# ── CONFIG ──
TOKEN      = os.getenv("DISCORD_TOKEN")
NG_KEY     = os.getenv("NG_API_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")
MONGO_URL  = os.getenv("MONGO_URL")

CH_RAPPORT  = 1459182029924073558
CH_ALERTE   = 1465309715230888090
CH_STORAGE  = 1478831933017428070
CH_M_RAPPORT = 1482879184207347942
CH_M_ALERTE  = 1482879242416029726
CH_PAYS      = 1465336287471861771

DEFAULT_WL = ["Canisi","Darkholess","UFO_Thespoot","Franky753","Blakonne","Farsgame","ClashKiller78","Olmat38","FLOTYR2","Raptor51"]

# ── COUNTRY WATCH ──
COUNTRY_WATCHES = []  # [{server, country, members, last_alert}]
cw_msg_id = None

WL       = list(DEFAULT_WL)
WL_MOCHA = list(DEFAULT_WL)
wl_msg_id = wl_mocha_msg_id = None

intents = discord.Intents.default()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)

SERVERS = {
    "blue":{"url":"https://blue.nationsglory.fr/standalone/dynmap_world.json","emoji":"🔵"},
    "coral":{"url":"https://coral.nationsglory.fr/standalone/dynmap_world.json","emoji":"🔴"},
    "orange":{"url":"https://orange.nationsglory.fr/standalone/dynmap_world.json","emoji":"🟠"},
    "red":{"url":"https://red.nationsglory.fr/standalone/dynmap_world.json","emoji":"🔴"},
    "yellow":{"url":"https://yellow.nationsglory.fr/standalone/dynmap_world.json","emoji":"🟡"},
    "mocha":{"url":"https://mocha.nationsglory.fr/standalone/dynmap_world.json","emoji":"🟤"},
    "white":{"url":"https://white.nationsglory.fr/standalone/dynmap_world.json","emoji":"⚪"},
    "jade":{"url":"https://jade.nationsglory.fr/standalone/dynmap_world.json","emoji":"🟢"},
    "black":{"url":"https://black.nationsglory.fr/standalone/dynmap_world.json","emoji":"⚫"},
    "cyan":{"url":"https://cyan.nationsglory.fr/standalone/dynmap_world.json","emoji":"🔵"},
    "lime":{"url":"https://lime.nationsglory.fr/standalone/dynmap_world.json","emoji":"🟢"},
}
CACHE_TTL = 900
ctry_cache = {}

# ── CORS ──
CORS = {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET, POST, OPTIONS","Access-Control-Allow-Headers":"Content-Type"}

def cors(data, status=200):
    return web.Response(text=json.dumps(data, ensure_ascii=False), status=status, content_type="application/json", headers=CORS)

async def handle_options(r): return web.Response(status=204, headers=CORS)

# ── MONGODB ──
mongo_ok = False
db = sessions_col = config_col = None

def init_mongo():
    global mongo_ok, db, sessions_col, config_col
    if not MONGO_URL: return
    try:
        from pymongo import MongoClient, ASCENDING
        c = MongoClient(MONGO_URL, serverSelectionTimeoutMS=8000, tls=True, tlsAllowInvalidCertificates=True)
        c.admin.command("ping")
        db = c["mossadglory"]
        sessions_col = db["sessions"]
        config_col   = db["config"]
        sessions_col.create_index([("player", ASCENDING), ("ts", ASCENDING)])
        mongo_ok = True
        print("✅ MongoDB OK", flush=True)
    except Exception as e:
        print(f"❌ MongoDB: {e}", flush=True)

def record_connection(player, server):
    if not mongo_ok: return
    try:
        now = datetime.utcnow() + timedelta(hours=1)
        sessions_col.insert_one({"player":player,"server":server,"ts":now,"day":now.weekday(),"hour":now.hour,"minute":now.minute})
    except: pass

def get_sessions(player, limit=500):
    if not mongo_ok: return []
    try:
        from pymongo import ASCENDING
        return list(sessions_col.find({"player":player},{"_id":0}).sort("ts",ASCENDING).limit(limit))
    except: return []

def get_pronostic(player):
    ss = get_sessions(player, 200)
    if len(ss) < 3: return None
    DAYS = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    dc, hbd = [0]*7, [[] for _ in range(7)]
    for s in ss:
        dc[s["day"]] += 1
        hbd[s["day"]].append(s["hour"] + s.get("minute",0)/60)
    total = len(ss)
    res = []
    for d in range(7):
        if not dc[d]: continue
        avg = sum(hbd[d])/len(hbd[d])
        res.append((d, int(avg), int((avg%1)*60), round(dc[d]/total*100)))
    return sorted(res, key=lambda x:-x[3])[:5], DAYS, total

def get_plages(player):
    ss = get_sessions(player, 500)
    if not ss: return None
    DAYS = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]
    hm = [[0]*24 for _ in range(7)]
    for s in ss: hm[s["day"]][s["hour"]] += 1
    return hm, DAYS

def cfg_set(key, val):
    if not mongo_ok: return
    try: config_col.update_one({"key":key},{"$set":{"value":val}},upsert=True)
    except: pass

def cfg_get(key):
    if not mongo_ok: return None
    try:
        doc = config_col.find_one({"key":key})
        return doc["value"] if doc else None
    except: return None

# ── WATCHLIST (générique) ──
async def _load_wl(global_name, prefix, channel_id):
    global WL, WL_MOCHA, wl_msg_id, wl_mocha_msg_id
    ch = client.get_channel(channel_id)
    if not ch: return
    async for msg in ch.history(limit=50):
        if msg.author == client.user and msg.content.startswith(prefix+":"):
            try:
                data = json.loads(msg.content[len(prefix)+1:])
                if global_name == "WL":
                    WL = data["players"]; wl_msg_id = msg.id
                else:
                    WL_MOCHA = data["players"]; wl_mocha_msg_id = msg.id
                print(f"✅ Watchlist {global_name} chargée", flush=True)
                return
            except: pass
    await _save_wl(global_name, prefix, channel_id)

async def _save_wl(global_name, prefix, channel_id):
    global wl_msg_id, wl_mocha_msg_id
    ch = client.get_channel(channel_id)
    if not ch: return
    players = WL if global_name == "WL" else WL_MOCHA
    msg_id  = wl_msg_id if global_name == "WL" else wl_mocha_msg_id
    content = f"{prefix}:" + json.dumps({"players": players})
    if msg_id:
        try:
            msg = await ch.fetch_message(msg_id)
            await msg.edit(content=content)
            return
        except discord.NotFound: pass
    msg = await ch.send(content)
    if global_name == "WL": wl_msg_id = msg.id
    else: wl_mocha_msg_id = msg.id

async def load_cw():
    global COUNTRY_WATCHES
    v = cfg_get("country_watches")
    if v: COUNTRY_WATCHES = v

async def save_cw():
    cfg_set("country_watches", COUNTRY_WATCHES)

async def load_watchlist():       await _load_wl("WL",    "WATCHLIST",       CH_STORAGE)
async def save_watchlist():       await _save_wl("WL",    "WATCHLIST",       CH_STORAGE)
async def load_watchlist_mocha(): await _load_wl("MOCHA", "WATCHLIST_MOCHA", CH_M_RAPPORT)
async def save_watchlist_mocha(): await _save_wl("MOCHA", "WATCHLIST_MOCHA", CH_M_RAPPORT)

# ── FETCH ──
async def get_online(server):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as s:
            async with s.get(SERVERS[server]["url"]) as r:
                if r.status == 200:
                    return [p["name"] for p in (await r.json()).get("players",[])]
    except: pass
    return []

async def get_all_online():
    results = await asyncio.gather(*[get_online(s) for s in SERVERS], return_exceptions=True)
    return {s: (r if isinstance(r,list) else []) for s,r in zip(SERVERS,results)}

async def get_country_list(server):
    now = time.time()
    if server in ctry_cache and now - ctry_cache[server][1] < CACHE_TTL:
        return ctry_cache[server][0]
    try:
        headers = {"Authorization":f"Bearer {NG_KEY}","accept":"application/json"}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            async with s.get(f"https://publicapi.nationsglory.fr/country/list/{server}", headers=headers) as r:
                if r.status in (200,500):
                    data = await r.json()
                    claimed = [c["name"] for c in data.get("claimed",[]) if c.get("name")]
                    ctry_cache[server] = (claimed, now)
                    return claimed
    except: pass
    return []

async def get_country_members(server, country):
    try:
        headers = {"Authorization":f"Bearer {NG_KEY}","accept":"application/json"}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            async with s.get(f"https://publicapi.nationsglory.fr/country/{server}/{country}", headers=headers) as r:
                data = await r.json()
                if data.get("members"):
                    return [m.lstrip("*+-") for m in data["members"]], data.get("name", country)
    except: pass
    return None, None

# ── API ROUTES ──
async def api_health(r):       return cors({"status":"ok","mongo":mongo_ok})
async def api_online(r):
    s = r.match_info["server"].lower()
    if s not in SERVERS: return cors({"error":"Serveur invalide"},400)
    pl = await get_online(s)
    return cors({"server":s,"players":pl,"count":len(pl)})

async def api_online_all(r):   return cors(await get_all_online())

async def api_checkall(r):
    p = r.match_info["player"]
    all_ = await get_all_online()
    return cors({"player":p,"servers":[s for s,pl in all_.items() if p in pl]})

async def api_countries(r):
    s = r.match_info["server"].lower()
    if s not in SERVERS: return cors({"error":"Serveur invalide"},400)
    return cors({"server":s,"countries":await get_country_list(s)})

async def api_check(r):
    s, c = r.match_info["server"].lower(), r.match_info["country"]
    if s not in SERVERS: return cors({"error":"Serveur invalide"},400)
    members, name = await get_country_members(s, c)
    if not members: return cors({"error":"Pays introuvable"},404)
    all_ = await get_all_online()
    found, total = {}, 0
    for sv, pl in all_.items():
        f = [m for m in members if m in pl]
        if f: found[sv] = f; total += len(f)
    return cors({"country":name,"members_total":len(members),"online_total":total,"servers":found})

async def api_wl_get(r):       return cors({"players":WL})
async def api_wl_mocha_get(r): return cors({"players":WL_MOCHA})

async def _wl_mutate(r, lst, save_fn):
    try:
        body = await r.json()
        p = body.get("player","").strip()
        if not p: return cors({"error":"Nom vide"},400)
        action = r.path.split("/")[-1]
        if action == "add" and p not in lst: lst.append(p); await save_fn()
        elif action == "remove" and p in lst: lst.remove(p); await save_fn()
        return cors({"players":lst})
    except Exception as e: return cors({"error":str(e)},400)

async def api_wl_add(r):          return await _wl_mutate(r, WL, save_watchlist)
async def api_wl_remove(r):       return await _wl_mutate(r, WL, save_watchlist)
async def api_wl_mocha_add(r):    return await _wl_mutate(r, WL_MOCHA, save_watchlist_mocha)
async def api_wl_mocha_remove(r): return await _wl_mutate(r, WL_MOCHA, save_watchlist_mocha)

async def api_pronostic(r):
    res = get_pronostic(r.match_info["player"])
    if not res: return cors({"error":"Pas assez de données (min 3)"},404)
    top, DAYS, total = res
    return cors({"player":r.match_info["player"],"total":total,"pronostic":[{"day":DAYS[d],"avg_h":h,"avg_m":m,"pct":pct} for d,h,m,pct in top]})

async def api_plages(r):
    res = get_plages(r.match_info["player"])
    if not res: return cors({"error":"Aucune donnée"},404)
    hm, DAYS = res
    return cors({"player":r.match_info["player"],"days":DAYS,"heatmap":hm})

async def api_cw_get(r):
    return cors({"watches": COUNTRY_WATCHES})

async def api_cw_add(r):
    try:
        body = await r.json()
        s = body.get("server","").lower()
        country = body.get("country","").strip()
        if not s or not country: return cors({"error":"Données manquantes"},400)
        exists = any(w["server"]==s and w["country"].lower()==country.lower() for w in COUNTRY_WATCHES)
        if exists: return cors({"error":"Déjà surveillé"},409)
        COUNTRY_WATCHES.append({"server":s,"country":country,"members":[],"last_alert":False})
        await save_cw()
        return cors({"watches":COUNTRY_WATCHES})
    except Exception as e: return cors({"error":str(e)},400)

async def api_cw_remove(r):
    try:
        body = await r.json()
        s = body.get("server","").lower()
        country = body.get("country","").strip()
        global COUNTRY_WATCHES
        COUNTRY_WATCHES = [w for w in COUNTRY_WATCHES if not (w["server"]==s and w["country"].lower()==country.lower())]
        await save_cw()
        return cors({"watches":COUNTRY_WATCHES})
    except Exception as e: return cors({"error":str(e)},400)

async def api_grade(r):
    player = r.match_info["player"]
    server = r.match_info["server"].lower()
    try:
        headers = {"Authorization": f"Bearer {NG_KEY}", "accept": "application/json"}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as s:
            async with s.get(f"https://publicapi.nationsglory.fr/user/{player}", headers=headers) as resp:
                if resp.status != 200:
                    return cors({"player": player, "server": server, "rank": None})
                data = await resp.json()
                rank = data.get("servers", {}).get(server, {}).get("country_rank", None)
                return cors({"player": player, "server": server, "rank": rank})
    except Exception as e:
        return cors({"player": player, "server": server, "rank": None, "error": str(e)})

async def api_known_players(r):
    if not mongo_ok: return cors({"players":[]})
    try:
        pl = sessions_col.distinct("player")
        pl.sort(key=str.lower)
        return cors({"players":pl})
    except: return cors({"players":[]})

# ── AUTOCOMPLETE ──
async def srv_ac(i, cur): return [app_commands.Choice(name=s.upper(),value=s) for s in SERVERS if cur.lower() in s][:25]
async def ctry_ac(i, cur):
    s = i.namespace.server
    if not s or s not in SERVERS: return []
    return [app_commands.Choice(name=c,value=c) for c in await get_country_list(s) if cur.lower() in c.lower()][:25]

# ── COMMANDES SLASH ──
@tree.command(name="check", description="Espionner les membres d'un pays")
@app_commands.autocomplete(server=srv_ac, country=ctry_ac)
async def cmd_check(i: discord.Interaction, server: str, country: str):
    await i.response.defer()
    if server not in SERVERS: return await i.followup.send("❌ Serveur invalide")
    members, name = await get_country_members(server, country)
    if not members: return await i.followup.send("❌ Pays introuvable")
    all_ = await get_all_online()
    found, total = {}, 0
    for s, pl in all_.items():
        f = [m for m in members if m in pl]
        if f: found[s] = f; total += len(f)
    e = discord.Embed(title=f"📊 Espionnage {name}", color=discord.Color.red())
    if found:
        for s, pl in sorted(found.items(), key=lambda x:(x[0]!=server, x[0])):
            lbl = f"{SERVERS[s]['emoji']} {s.upper()} ({len(pl)})" + (" ← cible" if s==server else "")
            e.add_field(name=lbl, value=", ".join(pl), inline=False)
        e.set_footer(text=f"Total : {total} | {len(members)} membres")
    else:
        e.description = f"✅ Aucun membre de {name} connecté"; e.color = discord.Color.green()
    await i.followup.send(embed=e)

@tree.command(name="checkall", description="Localiser un joueur")
async def cmd_checkall(i: discord.Interaction, joueur: str):
    await i.response.defer()
    all_ = await get_all_online()
    found = [s for s,pl in all_.items() if joueur in pl]
    e = discord.Embed(title=f"🔍 {joueur}", color=discord.Color.green() if found else discord.Color.red())
    e.description = "\n".join(f"{SERVERS[s]['emoji']} **{s.upper()}**" for s in found) if found else f"**{joueur}** hors ligne"
    await i.followup.send(embed=e)

@tree.command(name="online", description="Joueurs en ligne sur un serveur")
@app_commands.autocomplete(server=srv_ac)
async def cmd_online(i: discord.Interaction, server: str):
    await i.response.defer()
    if server not in SERVERS: return await i.followup.send("❌ Serveur invalide")
    pl = await get_online(server)
    e = discord.Embed(title=f"{SERVERS[server]['emoji']} {server.upper()}", color=discord.Color.blurple())
    if pl:
        for idx, chunk in enumerate([pl[j:j+20] for j in range(0,len(pl),20)]):
            e.add_field(name=f"Joueurs {idx+1}", value="\n".join(f"• {p}" for p in chunk), inline=True)
        e.set_footer(text=f"{len(pl)} connectés")
    else: e.description = "Aucun joueur"
    await i.followup.send(embed=e)

@tree.command(name="pronostic", description="Pronostic de connexion")
async def cmd_pronostic(i: discord.Interaction, joueur: str):
    await i.response.defer()
    if not mongo_ok: return await i.followup.send("❌ MongoDB non connecté", ephemeral=True)
    res = get_pronostic(joueur)
    if not res: return await i.followup.send(f"⚠️ Pas assez de données pour **{joueur}**", ephemeral=True)
    top, DAYS, total = res
    e = discord.Embed(title=f"🔮 Pronostic — {joueur}", description=f"Basé sur **{total}** connexions", color=discord.Color.purple())
    for d, avg_h, avg_m, pct in top:
        e.add_field(name=f"{DAYS[d]} — {pct}%", value=f"`{'█'*(pct//10)}{'░'*(10-pct//10)}` **{avg_h}h{str(avg_m).zfill(2)}**", inline=False)
    e.set_footer(text="% = fréquence par jour")
    await i.followup.send(embed=e)

@tree.command(name="plages", description="Plages horaires d'un joueur")
async def cmd_plages(i: discord.Interaction, joueur: str):
    await i.response.defer()
    if not mongo_ok: return await i.followup.send("❌ MongoDB non connecté", ephemeral=True)
    res = get_plages(joueur)
    if not res: return await i.followup.send(f"⚠️ Aucune donnée pour **{joueur}**", ephemeral=True)
    hm, DAYS = res
    e = discord.Embed(title=f"🕐 Plages — {joueur}", color=discord.Color.orange())
    for d in range(7):
        row = hm[d]
        if not sum(row): continue
        hw = [h for h in range(24) if row[h]]
        plages, start, prev = [], hw[0], hw[0]
        for h in hw[1:]:
            if h - prev > 2: plages.append(f"{start}h-{prev+1}h"); start = h
            prev = h
        plages.append(f"{start}h-{prev+1}h")
        e.add_field(name=DAYS[d], value=" • ".join(plages), inline=True)
    e.set_footer(text="Historique complet")
    await i.followup.send(embed=e)

def _wl_cmd(name, lst, save_fn, label=""):
    suffix = f"_{name}" if name else ""
    tag = f" {label}" if label else ""

    @tree.command(name=f"addwatch{suffix}", description=f"Ajouter à la watchlist{tag}")
    async def _add(i: discord.Interaction, joueur: str):
        if joueur in lst: return await i.response.send_message(f"⚠️ **{joueur}** déjà dans la watchlist{tag}", ephemeral=True)
        lst.append(joueur); await save_fn()
        await i.response.send_message(f"✅ **{joueur}** ajouté{tag}", ephemeral=True)

    @tree.command(name=f"removewatch{suffix}", description=f"Retirer de la watchlist{tag}")
    async def _remove(i: discord.Interaction, joueur: str):
        if joueur not in lst: return await i.response.send_message(f"❌ **{joueur}** pas dans la watchlist{tag}", ephemeral=True)
        lst.remove(joueur); await save_fn()
        await i.response.send_message(f"🗑️ **{joueur}** retiré{tag}", ephemeral=True)

    @tree.command(name=f"watchlist{suffix}", description=f"Afficher la watchlist{tag}")
    async def _show(i: discord.Interaction):
        if not lst: return await i.response.send_message(f"📋 Watchlist{tag} vide", ephemeral=True)
        e = discord.Embed(title=f"👁️ Watchlist{tag}", color=discord.Color.blurple())
        e.description = "\n".join(f"• {p}" for p in lst)
        e.set_footer(text=f"{len(lst)} joueurs")
        await i.response.send_message(embed=e, ephemeral=True)

_wl_cmd("",      WL,       save_watchlist)
_wl_cmd("mocha", WL_MOCHA, save_watchlist_mocha, "MOCHA")

# ── SCANNER ──
last_states = {s:{} for s in SERVERS}
rapport_msg_id = None

def _status_text(wl, players):
    on  = [p for p in wl if p in players]
    off = [p for p in wl if p not in players]
    txt = ""
    if on:  txt += f"🟢 **En ligne ({len(on)}) :**\n" + "".join(f"• {p}\n" for p in on)
    if off: txt += ("\n" if txt else "") + f"⚪ **Hors ligne ({len(off)}) :**\n" + "".join(f"• {p}\n" for p in off)
    return txt or "Aucun joueur surveillé en ligne"

def _rapport_embed(title, count, time_str, status_text, color):
    e = discord.Embed(title=title, color=color, timestamp=discord.utils.utcnow())
    e.add_field(name="👥 Connectés", value=f"**{count}**", inline=True)
    e.add_field(name="⏱️ Relevé",    value=f"**{time_str}**", inline=True)
    e.add_field(name="👁️ Surveillance", value=status_text, inline=False)
    e.set_footer(text=f"Scanner • MongoDB {'✅' if mongo_ok else '❌'}")
    return e

async def _update_rapport(channel, msg_id_ref, embed, save_fn):
    if not channel: return msg_id_ref
    if msg_id_ref:
        try:
            msg = await channel.fetch_message(msg_id_ref)
            await msg.edit(embed=embed)
            return msg_id_ref
        except discord.NotFound: pass
    msg = await channel.send(embed=embed)
    await asyncio.get_running_loop().run_in_executor(None, save_fn, msg.id)
    return msg.id

async def scan_server(server, alerte_ch):
    players = await get_online(server)
    pset    = set(players)
    prev    = last_states[server]
    mocha_ch = client.get_channel(CH_M_ALERTE)
    ts = discord.utils.utcnow()

    for p in pset:
        if not prev.get(p):
            record_connection(p, server)
            if p in WL and alerte_ch:
                e = discord.Embed(title="🟢 CONNEXION", description=f"**{p}** → **{server.upper()}**", color=discord.Color.green(), timestamp=ts)
                await alerte_ch.send(embed=e)
            if p in WL_MOCHA and server == "mocha" and mocha_ch:
                e = discord.Embed(title="🟢 CONNEXION — MOCHA", description=f"**{p}** → **MOCHA**", color=discord.Color.orange(), timestamp=ts)
                await mocha_ch.send(embed=e)

    for p, was in prev.items():
        if was and p not in pset:
            if p in WL and alerte_ch:
                e = discord.Embed(title="🔴 DÉCONNEXION", description=f"**{p}** ← **{server.upper()}**", color=discord.Color.red(), timestamp=ts)
                await alerte_ch.send(embed=e)
            if p in WL_MOCHA and server == "mocha" and mocha_ch:
                e = discord.Embed(title="🔴 DÉCONNEXION — MOCHA", description=f"**{p}** ← **MOCHA**", color=discord.Color.red(), timestamp=ts)
                await mocha_ch.send(embed=e)

    last_states[server] = {p: True for p in pset}
    return players

async def check_country_watch(watch):
    """Check if a country has >= 2 non-recruit members online on the target server."""
    try:
        server = watch["server"]
        country = watch["country"]
        members, name = await get_country_members(server, country)
        if not members: return
        online_players = await get_online(server)
        online_members = [m for m in members if m in online_players]
        if len(online_members) < 2:
            watch["last_alert"] = False
            watch["members"] = online_members
            return
        # Check grades — need at least 1 non-recruit
        headers = {"Authorization": f"Bearer {NG_KEY}", "accept": "application/json"}
        non_recruits = []
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            tasks = [s.get(f"https://publicapi.nationsglory.fr/user/{p}", headers=headers) for p in online_members[:8]]
            for p, task in zip(online_members[:8], tasks):
                try:
                    async with task as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            rank = data.get("servers",{}).get(server,{}).get("country_rank","")
                            if rank and rank != "recruit":
                                non_recruits.append((p, rank))
                except: pass
        watch["members"] = online_members
        can_assault = len(online_members) >= 2 and len(non_recruits) >= 1
        if can_assault and not watch.get("last_alert"):
            watch["last_alert"] = True
            ch = client.get_channel(CH_PAYS)
            if ch:
                await ch.send(f"⚔ **ASSAUT POSSIBLE** — **{name}** sur **{server.upper()}**")
        elif not can_assault and watch.get("last_alert"):
            watch["last_alert"] = False
            ch = client.get_channel(CH_PAYS)
            if ch:
                await ch.send(f"✅ **PLUS POSSIBLE** — **{name}** sur **{server.upper()}** (moins de 2 membres ou que des recrues)")
    except Exception as e:
        print(f"❌ CW scan {watch}: {e}", flush=True)

async def scanner_loop():
    global rapport_msg_id
    await client.wait_until_ready()
    await load_watchlist()
    await load_watchlist_mocha()
    rapport_msg_id = await asyncio.get_running_loop().run_in_executor(None, cfg_get, "rapport_msg_id")
    await load_cw()
    print(f"📋 Country watches: {len(COUNTRY_WATCHES)}", flush=True)
    print(f"📋 Rapport ID: {rapport_msg_id}", flush=True)

    ch_rapport = client.get_channel(CH_RAPPORT)
    ch_alerte  = client.get_channel(CH_ALERTE)
    tick = 0

    while True:
        try:
            results = await asyncio.gather(*[scan_server(s, ch_alerte) for s in SERVERS], return_exceptions=True)
            sp = {s: (r if isinstance(r,list) else []) for s,r in zip(SERVERS,results)}

            # Country watch check every 6 ticks (30s)
        if tick % 6 == 0 and COUNTRY_WATCHES:
            await asyncio.gather(*[check_country_watch(w) for w in COUNTRY_WATCHES], return_exceptions=True)
            await save_cw()

        if tick % 5 == 0:
                now = discord.utils.utcnow()
                ts  = (now + timedelta(hours=1)).strftime("%H:%M:%S")

                # LIME rapport
                lp = sp.get("lime",[])
                e  = _rapport_embed("🟢 RAPPORT TACTIQUE — LIME", len(lp), ts, _status_text(WL, lp), discord.Color.green() if any(p in lp for p in WL) else discord.Color.greyple())
                rapport_msg_id = await _update_rapport(ch_rapport, rapport_msg_id, e, lambda mid: cfg_set("rapport_msg_id", mid))

                # MOCHA rapport
                mp       = sp.get("mocha",[])
                mocha_e  = _rapport_embed("🟤 RAPPORT TACTIQUE — MOCHA", len(mp), ts, _status_text(WL_MOCHA, mp), discord.Color.orange() if any(p in mp for p in WL_MOCHA) else discord.Color.greyple())
                ch_mr    = client.get_channel(CH_M_RAPPORT)
                if ch_mr:
                    found = False
                    async for old in ch_mr.history(limit=10):
                        if old.author == client.user and old.embeds and "RAPPORT TACTIQUE — MOCHA" in (old.embeds[0].title or ""):
                            await old.edit(embed=mocha_e); found = True; break
                    if not found: await ch_mr.send(embed=mocha_e)

            tick += 1
        except Exception as e:
            print(f"❌ Scanner: {e}", flush=True)
        await asyncio.sleep(1)

# ── SERVEUR WEB ──
async def start_web():
    app = web.Application()
    routes = [
        ("GET",  "/",                              api_health),
        ("GET",  "/health",                        api_health),
        ("GET",  "/api/online/{server}",           api_online),
        ("GET",  "/api/online_all",                api_online_all),
        ("GET",  "/api/checkall/{player}",         api_checkall),
        ("GET",  "/api/countries/{server}",        api_countries),
        ("GET",  "/api/check/{server}/{country}",  api_check),
        ("GET",  "/api/watchlist",                 api_wl_get),
        ("POST", "/api/watchlist/add",             api_wl_add),
        ("POST", "/api/watchlist/remove",          api_wl_remove),
        ("GET",  "/api/watchlist_mocha",           api_wl_mocha_get),
        ("POST", "/api/watchlist_mocha/add",       api_wl_mocha_add),
        ("POST", "/api/watchlist_mocha/remove",    api_wl_mocha_remove),
        ("GET",  "/api/pronostic/{player}",        api_pronostic),
        ("GET",  "/api/plages/{player}",           api_plages),
        ("GET",  "/api/known_players",             api_known_players),
        ("GET",  "/api/grade/{player}/{server}",   api_grade),
        ("GET",  "/api/country_watches",           api_cw_get),
        ("POST", "/api/country_watches/add",       api_cw_add),
        ("POST", "/api/country_watches/remove",    api_cw_remove),
    ]
    for method, path, handler in routes:
        app.router.add_route(method, path, handler)
    app.router.add_route("OPTIONS", "/{path_info:.*}", handle_options)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"🌐 API démarrée sur {port}", flush=True)

async def self_ping():
    await asyncio.sleep(60)
    url = (RENDER_URL if RENDER_URL.startswith("http") else f"https://{RENDER_URL}") if RENDER_URL else None
    while True:
        if url:
            try:
                async with aiohttp.ClientSession() as s:
                    await s.get(url, timeout=aiohttp.ClientTimeout(total=10))
            except: pass
        await asyncio.sleep(600)

# ── LANCEMENT ──
async def main():
    print("🚀 Démarrage...", flush=True)
    init_mongo()
    await asyncio.sleep(5)
    async with client:
        asyncio.create_task(start_web())
        if RENDER_URL: asyncio.create_task(self_ping())
        asyncio.create_task(scanner_loop())
        try:
            await client.start(TOKEN)
        except discord.errors.HTTPException as e:
            print(f"❌ Rate limit Discord: {e}", flush=True)
            await asyncio.sleep(60); sys.exit(1)
        except Exception as e:
            print(f"❌ Erreur: {e}", flush=True)
            await asyncio.sleep(30); sys.exit(1)

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ {client.user} | {len(SERVERS)} serveurs | MongoDB {'✅' if mongo_ok else '❌'}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
