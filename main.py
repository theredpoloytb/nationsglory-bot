import discord,aiohttp,asyncio,time,json,os,sys,hmac,hashlib,base64,secrets
from discord import app_commands
from aiohttp import web
from datetime import timedelta,datetime
TOKEN=os.getenv('DISCORD_TOKEN')
NG_KEY=os.getenv('NG_API_KEY')
RENDER_URL=os.getenv('RENDER_EXTERNAL_URL','')
MONGO_URL=os.getenv('MONGO_URL')
CH_RAPPORT=0x14400e533c420056
CH_ALERTE=0x1455d36c2644109a
CH_STORAGE=0x1485ddced2021066
CH_M_RAPPORT=0x14943ec2eb8000e6
CH_M_ALERTE=0x14943ed07902001e
CH_PAYS=0x1455eb96fb40000b
DEFAULT_WL=[]
COUNTRY_WATCHES=[]
cw_msg_id=None
WL=list(DEFAULT_WL)
WL_MOCHA=list(DEFAULT_WL)
wl_msg_id=wl_mocha_msg_id=None

# ── PAYS RÉFÉRENTS ──
REFERENT_WATCHES=[]  # [{'server':str,'country':str,'name':str,'members_snapshot':[],'added_at':str}]

intents=discord.Intents.default()
client=discord.Client(intents=intents)
tree=app_commands.CommandTree(client)
SERVERS={'blue':{'url':'https://blue.nationsglory.fr/standalone/dynmap_world.json','emoji':'🔵'},'coral':{'url':'https://coral.nationsglory.fr/standalone/dynmap_world.json','emoji':'🔴'},'orange':{'url':'https://orange.nationsglory.fr/standalone/dynmap_world.json','emoji':'🟠'},'red':{'url':'https://red.nationsglory.fr/standalone/dynmap_world.json','emoji':'🔴'},'yellow':{'url':'https://yellow.nationsglory.fr/standalone/dynmap_world.json','emoji':'🟡'},'mocha':{'url':'https://mocha.nationsglory.fr/standalone/dynmap_world.json','emoji':'🟤'},'white':{'url':'https://white.nationsglory.fr/standalone/dynmap_world.json','emoji':'⚪'},'jade':{'url':'https://jade.nationsglory.fr/standalone/dynmap_world.json','emoji':'🟢'},'black':{'url':'https://black.nationsglory.fr/standalone/dynmap_world.json','emoji':'⚫'},'cyan':{'url':'https://cyan.nationsglory.fr/standalone/dynmap_world.json','emoji':'🔵'},'lime':{'url':'https://lime.nationsglory.fr/standalone/dynmap_world.json','emoji':'🟢'}}
CACHE_TTL=900
ctry_cache={}
CORS={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type, Authorization'}

# ── JWT AUTH ──

# ── RATE LIMITER / ANTI BRUTEFORCE ──
_fail_attempts={}  # {ip: [timestamps]}
_blocked_ips={}    # {ip: block_until_timestamp}
MAX_ATTEMPTS=5
BLOCK_DURATION=900  # 15 min
ATTEMPT_WINDOW=300  # 5 min

def _get_ip(request):
	return request.headers.get('X-Forwarded-For','').split(',')[0].strip() or request.remote or 'unknown'

def _is_blocked(ip):
	if ip in _blocked_ips:
		if time.time()<_blocked_ips[ip]:return True
		del _blocked_ips[ip]
	return False

def _record_fail(ip):
	now=time.time()
	if ip not in _fail_attempts:_fail_attempts[ip]=[]
	_fail_attempts[ip]=[t for t in _fail_attempts[ip] if now-t<ATTEMPT_WINDOW]
	_fail_attempts[ip].append(now)
	if len(_fail_attempts[ip])>=MAX_ATTEMPTS:
		_blocked_ips[ip]=now+BLOCK_DURATION
		print(f"🚫 IP bloquée {ip} pour {BLOCK_DURATION}s",flush=True)
		return True
	return False

def _clear_attempts(ip):
	_fail_attempts.pop(ip,None)
	_blocked_ips.pop(ip,None)

JWT_SECRET=os.environ.get('JWT_SECRET',secrets.token_hex(32))
def _jwt_sign(payload):
	header=base64.urlsafe_b64encode(json.dumps({'alg':'HS256','typ':'JWT'}).encode()).rstrip(b'=').decode()
	body=base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
	sig=hmac.new(JWT_SECRET.encode(),f"{header}.{body}".encode(),hashlib.sha256).digest()
	return f"{header}.{body}.{base64.urlsafe_b64encode(sig).rstrip(b'=').decode()}"
def _jwt_verify(token):
	try:
		h,b,s=token.split('.')
		expected=hmac.new(JWT_SECRET.encode(),f"{h}.{b}".encode(),hashlib.sha256).digest()
		if not hmac.compare_digest(base64.urlsafe_b64encode(expected).rstrip(b'=').decode(),s):return None
		payload=json.loads(base64.urlsafe_b64decode(b+'=='))
		if payload.get('exp',0)<time.time():return None
		return payload
	except:return None
def _get_token(request):
	auth=request.headers.get('Authorization','')
	if auth.startswith('Bearer '):return auth[7:]
	return None
def require_auth(handler):
	async def wrapper(r,*a,**kw):
		t=_get_token(r)
		if not t or not _jwt_verify(t):return cors({'error':'Non autorisé'},401)
		return await handler(r,*a,**kw)
	return wrapper
def cors(data,status=200):return web.Response(text=json.dumps(data,ensure_ascii=False),status=status,content_type='application/json',headers=CORS)
async def handle_options(r):return web.Response(status=204,headers=CORS)
mongo_ok=False
db=sessions_col=config_col=None
def init_mongo():
	global mongo_ok,db,sessions_col,config_col
	if not MONGO_URL:return
	try:
		from pymongo import MongoClient,ASCENDING
		c=MongoClient(MONGO_URL,serverSelectionTimeoutMS=8000,tls=True,tlsAllowInvalidCertificates=True)
		c.admin.command('ping')
		db=c['mossadglory']
		sessions_col=db['sessions']
		config_col=db['config']
		sessions_col.create_index([('player',ASCENDING),('ts',ASCENDING)])
		db['presence'].create_index([('total',-1)])
		# Index pour les recrutements
		db['recruitments'].create_index([('server',ASCENDING),('country',ASCENDING),('ts',ASCENDING)])
		db['notes'].create_index([('player',ASCENDING)],unique=True)
		mongo_ok=True
		print('✅ MongoDB OK',flush=True)
	except Exception as e:print(f"❌ MongoDB: {e}",flush=True)

def record_connection(player,server):
	if not mongo_ok:return
	try:
		now=datetime.utcnow()+timedelta(hours=1)
		sessions_col.insert_one({'player':player,'server':server,'ts':now,'day':now.weekday(),'hour':now.hour,'minute':now.minute})
		db['presence'].update_one(
			{'player':player},
			{
				'$inc':{'total':1,f'servers.{server}':1},
				'$set':{'last_seen':now,'last_server':server}
			},
			upsert=True
		)
	except:pass

def get_sessions(player,limit=500):
	if not mongo_ok:return[]
	try:from pymongo import ASCENDING;return list(sessions_col.find({'player':player},{'_id':0}).sort('ts',ASCENDING).limit(limit))
	except:return[]
def get_pronostic(player):
	ss=get_sessions(player,200)
	if len(ss)<3:return None
	DAYS=['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'];dc,hbd=[0]*7,[[]for _ in range(7)]
	for s in ss:dc[s['day']]+=1;hbd[s['day']].append(s['hour']+s.get('minute',0)/60)
	total=len(ss);res=[]
	for d in range(7):
		if not dc[d]:continue
		avg=sum(hbd[d])/len(hbd[d]);res.append((d,int(avg),int(avg%1*60),round(dc[d]/total*100)))
	return sorted(res,key=lambda x:-x[3])[:5],DAYS,total
def get_plages(player):
	ss=get_sessions(player,500)
	if not ss:return None
	DAYS=['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];hm=[[0]*24 for _ in range(7)]
	for s in ss:hm[s['day']][s['hour']]+=1
	return hm,DAYS
def cfg_set(key,val):
	if not mongo_ok:return
	try:config_col.update_one({'key':key},{'$set':{'value':val}},upsert=True)
	except:pass
def cfg_get(key):
	if not mongo_ok:return None
	try:doc=config_col.find_one({'key':key});return doc['value']if doc else None
	except:return None
async def _load_wl(global_name,prefix,channel_id):
	global WL,WL_MOCHA,wl_msg_id,wl_mocha_msg_id;ch=client.get_channel(channel_id)
	if not ch:return
	async for msg in ch.history(limit=50):
		if msg.author==client.user and msg.content.startswith(prefix+':'):
			try:
				data=json.loads(msg.content[len(prefix)+1:])
				if global_name=='WL':WL=data['players'];wl_msg_id=msg.id
				else:WL_MOCHA=data['players'];wl_mocha_msg_id=msg.id
				print(f"✅ Watchlist {global_name} chargée",flush=True);return
			except:pass
	await _save_wl(global_name,prefix,channel_id)
async def _save_wl(global_name,prefix,channel_id):
	global wl_msg_id,wl_mocha_msg_id;ch=client.get_channel(channel_id)
	if not ch:return
	players=WL if global_name=='WL'else WL_MOCHA;msg_id=wl_msg_id if global_name=='WL'else wl_mocha_msg_id;content=f"{prefix}:"+json.dumps({'players':players})
	if msg_id:
		try:msg=await ch.fetch_message(msg_id);await msg.edit(content=content);return
		except discord.NotFound:pass
	msg=await ch.send(content)
	if global_name=='WL':wl_msg_id=msg.id
	else:wl_mocha_msg_id=msg.id
async def load_cw():
	global COUNTRY_WATCHES;v=cfg_get('country_watches')
	if v:COUNTRY_WATCHES=v
async def save_cw():cfg_set('country_watches',COUNTRY_WATCHES)

# ── LOAD/SAVE RÉFÉRENTS ──
async def load_referents():
	global REFERENT_WATCHES
	v=cfg_get('referent_watches')
	if v:REFERENT_WATCHES=v;print(f"✅ Référents chargés: {len(REFERENT_WATCHES)}",flush=True)
async def save_referents():cfg_set('referent_watches',REFERENT_WATCHES)

async def load_watchlist():await _load_wl('WL','WATCHLIST',CH_STORAGE)
async def save_watchlist():await _save_wl('WL','WATCHLIST',CH_STORAGE)
async def load_watchlist_mocha():await _load_wl('MOCHA','WATCHLIST_MOCHA',CH_M_RAPPORT)
async def save_watchlist_mocha():await _save_wl('MOCHA','WATCHLIST_MOCHA',CH_M_RAPPORT)
async def get_online(server):
	try:
		async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))as s:
			async with s.get(SERVERS[server]['url'])as r:
				if r.status==200:return[p['name']for p in(await r.json()).get('players',[])]
	except:pass
	return[]
async def get_all_online():results=await asyncio.gather(*[get_online(s)for s in SERVERS],return_exceptions=True);return{s:r if isinstance(r,list)else[]for(s,r)in zip(SERVERS,results)}
# ── FALLBACK STATIQUE (utilisé uniquement si l'API est down ou rate-limitée) ──
_STATIC_COUNTRIES_FALLBACK=sorted(["ArchipelCrozet","Algerie","Angola","IlesAndaman","Autriche","Azerbaidjan","Bahrein","Bangladesh","Belgique","Benin","Bielorussie","Bolivie","Bosnie","BurkinaFaso","Cambodge","CentreAfrique","Chili","Colombie","Congo","RDCongo","CoreeDuSud","CoteDivoire","Egypte","EmiratsArabesUnis","Equateur","Erythree","Ethiopie","Iakoutie","Iamalie","IleBolchevique","IlesBaleares","IleCoats","IleDeLaReunion","IlesFeroe","IlesFidji","IlesGalapagos","IleMaurice","IleVictoria","Gabon","Georgie","Ghana","Groenland","Guatemala","Guyane","Guyana","Hainan","Inde","Indonesie","Irak","Iran","Italie","IlesVancouver","Japon","Java","Kazakhstan","Khabarovsk","Kenya","Kosovo","Krasnoy","Laos","Lettonie","Libye","Lituanie","Macedoine","Malaisie","Malte","Kamtchatka","Mali","Maroc","Mauritanie","Magadan","Mozambique","Namibie","Niger","Nigeria","Norvege","NouvelleGuinee","NouvelleZemble","Ouganda","Ouzbekistan","Palaos","Pakistan","Portugal","Qatar","SaharaOccidental","Serbie","Somalie","Srilanka","StHelena","IlesSandwich","IleBouvet","Suriname","Svalbard","Swaziland","Syrie","Tadjikistan","Tanzanie","Tchoukota","TerreSiple","TerreSpaatz","TerreMill","TerreGrant","TerreVega","TerreThor","TerreLow","TerrePowell","TerreBurke","TerreSigny","TerreBooth","TerreSmith","TerreRoss","TerreLiard","TerreMasson","Thailande","Tibet","Timor","Touva","Tunisie","Turkmenistan","Turquie","TriniteEtTobago","Uruguay","WallisEtFutuna","Yemen","Zambie","Zimbabwe","Montana","Michigan","Nunavut","Sonora","Queensland","Minnesota","Washington","Oregon","Idaho","Utah","NouveauMexique","Colorado","Wyoming","Quinghai","Xinjiang","Yunnam","Sichuan","Guizhou","Guangxi","Guangdong","Chypre","Roumanie","EmpireJordanien","Madagan","Tasmanie","EmpireBissaoguineen","Liberia","EmpireIrkoutsk","IleWrangel","Canada","TerreAdelie","Suede","Djibouti","Paraguay","Nepal","Bhoutan","Sakhaline","RoyaumeUni","IlesSalomon","EtatsUnis","Liban","Bahamas","EmpireOmanais","RepubliqueTcheque","Espagne","Danemark","Jamaique","NouvelleZelande","Bouriatie","Taiwan","Tomsk","Cameroun","Amour","Kirghizistan","Venezuela","IlesKerguelen","Soudan","Sardaigne","Luxembourg","Bresil","Nevada","Moldavie","Malawi","NouvelleCaledonie","AfriqueDuSud","CoreeDuNord","Estonie","Wisconsin","Birmanie","TerreDeFeu","Salvador","Koweit","Baja","Socotra","Botswana","TerreSnow","Allemagne","Pologne","Slovenie","PaysBas","Philippines","Texas","Suisse","Altai","Floride","Quebec","Slovaquie","Madagascar","Montenegro","Mongolie","Nicaragua","Sumatra","France","Bulgarie","Alaska","Argentine","Grece","Australie","Belize","Armenie","Afghanistan","Californie","Russie","Islande","Perou","Arizona","Tchad","Albanie","IlesCanaries","Togo","Chine","Mexique","Ontario","IleGraham","Dakota","Vietnam","Papouasie","Croatie"])

# Délai minimum entre deux appels API /country/list par serveur (anti rate-limit)
_ctry_last_fetch={}   # {server: timestamp du dernier appel réussi ou tenté}
CTRY_FETCH_COOLDOWN=3600  # 1h min entre deux refresh via API

async def get_country_list(server):
	now=time.time()
	# 1. Cache encore valide → on retourne directement
	if server in ctry_cache and now-ctry_cache[server][1]<CACHE_TTL:
		return ctry_cache[server][0]
	# 2. Cooldown anti rate-limit : si on a déjà appelé l'API récemment, retourner le cache (même périmé) ou le fallback
	last_fetch=_ctry_last_fetch.get(server,0)
	if now-last_fetch<CTRY_FETCH_COOLDOWN:
		if server in ctry_cache:
			print(f"[countries] {server} cooldown actif, cache périmé réutilisé ({len(ctry_cache[server][0])} pays)",flush=True)
			return ctry_cache[server][0]
		print(f"[countries] {server} cooldown actif, fallback statique",flush=True)
		return _STATIC_COUNTRIES_FALLBACK
	# 3. Appel API avec retry/backoff exponentiel
	_ctry_last_fetch[server]=now
	headers={'Authorization':f"Bearer {NG_KEY}",'accept':'application/json'}
	delay=30
	for attempt in range(4):
		try:
			async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))as s:
				async with s.get(f"https://publicapi.nationsglory.fr/country/list/{server}",headers=headers)as r:
					if r.status==429:
						retry_after=int(r.headers.get('Retry-After',delay))
						print(f"[countries] {server} 429 rate-limit, attente {retry_after}s (tentative {attempt+1}/4)",flush=True)
						await asyncio.sleep(retry_after)
						delay=min(delay*2,300)
						continue
					if r.status in(200,500):
						data=await r.json()
						raw=data.get('claimed',[])+data.get('availables',[])if isinstance(data,dict)else data
						claimed=sorted([c['name']for c in raw if isinstance(c,dict)and c.get('name','').strip()])
						if claimed:
							print(f"[countries] {server} OK => {len(claimed)} pays",flush=True)
							ctry_cache[server]=claimed,now
							return claimed
					else:
						print(f"[countries] {server} HTTP {r.status}",flush=True)
						break
		except Exception as e:
			print(f"[countries] {server} erreur tentative {attempt+1}: {e}",flush=True)
			await asyncio.sleep(delay)
			delay=min(delay*2,300)
	# 4. Échec total → cache périmé ou fallback statique
	if server in ctry_cache:
		print(f"[countries] {server} fallback sur cache périmé ({len(ctry_cache[server][0])} pays)",flush=True)
		return ctry_cache[server][0]
	print(f"[countries] {server} fallback statique ({len(_STATIC_COUNTRIES_FALLBACK)} pays)",flush=True)
	return _STATIC_COUNTRIES_FALLBACK
async def get_country_members(server,country):
	try:
		headers={'Authorization':f"Bearer {NG_KEY}",'accept':'application/json'}
		async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))as s:
			async with s.get(f"https://publicapi.nationsglory.fr/country/{server}/{country}",headers=headers)as r:
				data=await r.json()
				if data.get('members'):return[m.lstrip('*+-')for m in data['members']],data.get('name',country)
	except:pass
	return None,None

# ══════════════════════════════════════════════
# TRACKING RECRUTEMENTS PAYS RÉFÉRENTS
# ══════════════════════════════════════════════

def record_recruitment(server,country,country_name,player,old_count,new_count):
	"""Enregistre un recrutement détecté dans MongoDB."""
	if not mongo_ok:return
	try:
		now=datetime.utcnow()+timedelta(hours=1)
		db['recruitments'].insert_one({
			'server':server,
			'country':country.lower(),
			'country_name':country_name,
			'player':player,
			'ts':now,
			'members_before':old_count,
			'members_after':new_count,
		})
	except Exception as e:print(f"❌ record_recruitment: {e}",flush=True)

def record_departure(server,country,country_name,player,old_count,new_count):
	"""Enregistre un départ (perte de membre)."""
	if not mongo_ok:return
	try:
		now=datetime.utcnow()+timedelta(hours=1)
		db['recruitments'].insert_one({
			'server':server,
			'country':country.lower(),
			'country_name':country_name,
			'player':player,
			'ts':now,
			'members_before':old_count,
			'members_after':new_count,
			'departure':True,
		})
	except Exception as e:print(f"❌ record_departure: {e}",flush=True)

async def verify_members_by_api(server, members):
	"""Vérifie via l'API /user que chaque joueur appartient vraiment au pays sur ce serveur.
	Retourne uniquement les joueurs ayant un country_rank valide (filtre les faux positifs de l'API membres)."""
	if not members:return[]
	headers={'Authorization':f"Bearer {NG_KEY}",'accept':'application/json'}
	verified=[]
	async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))as s:
		tasks=[s.get(f"https://publicapi.nationsglory.fr/user/{p}",headers=headers)for p in members]
		for(p,task)in zip(members,tasks):
			try:
				async with task as resp:
					if resp.status==200:
						data=await resp.json();rank=data.get('servers',{}).get(server,{}).get('country_rank','')
						if rank:verified.append(p)
					else:verified.append(p)  # En cas d'erreur API on garde le joueur par défaut
			except:verified.append(p)
	return verified

async def verify_members_with_ranks(server, members):
	"""Comme verify_members_by_api mais retourne aussi les ranks.
	Retourne (verified_list, rank_dict) — rank_dict = {player: rank}"""
	if not members:return[],{}
	headers={'Authorization':f"Bearer {NG_KEY}",'accept':'application/json'}
	verified=[];ranks={}
	async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))as s:
		tasks=[s.get(f"https://publicapi.nationsglory.fr/user/{p}",headers=headers)for p in members]
		for(p,task)in zip(members,tasks):
			try:
				async with task as resp:
					if resp.status==200:
						data=await resp.json();rank=data.get('servers',{}).get(server,{}).get('country_rank','')
						if rank:verified.append(p);ranks[p]=rank
					else:verified.append(p)  # En cas d'erreur API on garde le joueur
			except:verified.append(p)
	return verified,ranks

async def check_referent(watch):
	"""Vérifie les recrutements d'un pays référent et met à jour le snapshot."""
	try:
		server=watch['server'];country=watch['country']
		members,name=await get_country_members(server,country)
		if not members:return
		# Vérification double via /user pour filtrer les faux positifs de l'API membres
		members=await verify_members_by_api(server,members)
		if not members:return
		# Mettre à jour le nom réel du pays
		watch['name']=name
		prev_set=set(watch.get('members_snapshot',[]))
		curr_set=set(members)
		old_count=len(prev_set);new_count=len(curr_set)
		# Détection recrutements (nouveaux membres)
		new_recruits=curr_set-prev_set
		for p in new_recruits:
			print(f"🆕 Recrutement détecté : {p} → {name} ({server.upper()})",flush=True)
			record_recruitment(server,country,name,p,old_count,new_count)
		# Détection départs
		departures=prev_set-curr_set
		for p in departures:
			if prev_set:  # Pas au premier scan (snapshot vide)
				print(f"🚪 Départ détecté : {p} ← {name} ({server.upper()})",flush=True)
				record_departure(server,country,name,p,old_count,new_count)
		# Mise à jour snapshot
		watch['members_snapshot']=members
		watch['last_check']=(datetime.utcnow()+timedelta(hours=1)).strftime('%d/%m/%Y %H:%M:%S')
		watch['member_count']=new_count
	except Exception as e:print(f"❌ check_referent {watch}: {e}",flush=True)

async def referent_tracker_loop():
	"""Boucle de tracking des pays référents — toutes les 5 minutes."""
	await client.wait_until_ready()
	await asyncio.sleep(10)  # Laisser le scanner_loop se lancer d'abord
	print("🕵️ Referent tracker démarré",flush=True)
	while True:
		try:
			if REFERENT_WATCHES:
				await asyncio.gather(*[check_referent(w) for w in REFERENT_WATCHES],return_exceptions=True)
				await save_referents()
		except Exception as e:print(f"❌ referent_tracker_loop: {e}",flush=True)
		await asyncio.sleep(1800)  # 30 minutes

# ── API ENDPOINTS RÉFÉRENTS ──

@require_auth
async def api_referent_get(r):
	"""Liste tous les pays référents surveillés."""
	result=[]
	for w in REFERENT_WATCHES:
		result.append({
			'server':w['server'],
			'country':w['country'],
			'name':w.get('name',w['country']),
			'member_count':w.get('member_count',0),
			'last_check':w.get('last_check',None),
			'added_at':w.get('added_at',None),
			'members_snapshot':w.get('members_snapshot',[]),
		})
	return cors({'watches':result})

@require_auth
async def api_referent_add(r):
	"""Ajouter un pays référent à surveiller."""
	try:
		body=await r.json()
		server=body.get('server','').lower()
		country=body.get('country','').strip()
		if not server or not country:return cors({'error':'Données manquantes'},400)
		if server not in SERVERS:return cors({'error':'Serveur invalide'},400)
		exists=any(w['server']==server and w['country'].lower()==country.lower() for w in REFERENT_WATCHES)
		if exists:return cors({'error':'Déjà surveillé'},409)
		# Récupérer le vrai nom + snapshot initial
		members,name=await get_country_members(server,country)
		now=(datetime.utcnow()+timedelta(hours=1)).strftime('%d/%m/%Y %H:%M')
		REFERENT_WATCHES.append({
			'server':server,
			'country':country,
			'name':name or country,
			'members_snapshot':members or [],
			'member_count':len(members) if members else 0,
			'last_check':now,
			'added_at':now,
		})
		await save_referents()
		return cors({'watches':[{'server':w['server'],'country':w['country'],'name':w.get('name',w['country']),'member_count':w.get('member_count',0)} for w in REFERENT_WATCHES]})
	except Exception as e:return cors({'error':str(e)},400)

@require_auth
async def api_referent_remove(r):
	"""Retirer un pays référent."""
	try:
		global REFERENT_WATCHES
		body=await r.json()
		server=body.get('server','').lower()
		country=body.get('country','').strip()
		REFERENT_WATCHES=[w for w in REFERENT_WATCHES if not(w['server']==server and w['country'].lower()==country.lower())]
		await save_referents()
		return cors({'watches':[{'server':w['server'],'country':w['country'],'name':w.get('name',w['country'])} for w in REFERENT_WATCHES]})
	except Exception as e:return cors({'error':str(e)},400)

@require_auth
async def api_referent_stats(r):
	"""Stats globales des recrutements par pays référent (30 derniers jours)."""
	if not mongo_ok:return cors({'error':'MongoDB non connecté'},503)
	try:
		from pymongo import ASCENDING
		server=r.rel_url.query.get('server',None)
		country=r.rel_url.query.get('country',None)
		days=int(r.rel_url.query.get('days',90))
		since=datetime.utcnow()+timedelta(hours=1)-timedelta(days=days)
		query={'ts':{'$gte':since},'departure':{'$exists':False}}
		if server:query['server']=server.lower()
		if country:query['country']=country.lower()
		# Agrégation par pays
		pipeline=[
			{'$match':query},
			{'$group':{
				'_id':{'server':'$server','country':'$country','country_name':'$country_name'},
				'total':{'$sum':1},
				'players':{'$push':'$player'},
				'last_recruit':{'$max':'$ts'},
				'first_recruit':{'$min':'$ts'},
			}},
			{'$sort':{'total':-1}}
		]
		docs=list(db['recruitments'].aggregate(pipeline))
		result=[]
		for d in docs:
			last=d['last_recruit']
			first=d['first_recruit']
			result.append({
				'server':d['_id']['server'],
				'country':d['_id']['country'],
				'country_name':d['_id']['country_name'],
				'total_recruits':d['total'],
				'unique_players':len(set(d['players'])),
				'last_recruit':last.strftime('%d/%m/%Y %H:%M') if hasattr(last,'strftime') else str(last),
				'first_recruit':first.strftime('%d/%m/%Y %H:%M') if hasattr(first,'strftime') else str(first),
			})
		return cors({'stats':result,'days':days})
	except Exception as e:return cors({'error':str(e)},500)

@require_auth
async def api_referent_history(r):
	"""Historique détaillé des recrutements d'un pays référent."""
	if not mongo_ok:return cors({'error':'MongoDB non connecté'},503)
	try:
		from pymongo import DESCENDING
		server=r.rel_url.query.get('server','')
		country=r.rel_url.query.get('country','')
		limit=int(r.rel_url.query.get('limit',200))
		include_departures=r.rel_url.query.get('departures','0')=='1'
		if not server or not country:return cors({'error':'server et country requis'},400)
		query={'server':server.lower(),'country':country.lower()}
		if not include_departures:query['departure']={'$exists':False}
		docs=list(db['recruitments'].find(query,{'_id':0}).sort('ts',DESCENDING).limit(limit))
		for d in docs:
			if 'ts' in d and hasattr(d['ts'],'strftime'):
				d['ts']=d['ts'].strftime('%d/%m/%Y %H:%M:%S')
		# Courbe par jour (30 derniers jours)
		since=datetime.utcnow()+timedelta(hours=1)-timedelta(days=30)
		pipeline=[
			{'$match':{'server':server.lower(),'country':country.lower(),'ts':{'$gte':since},'departure':{'$exists':False}}},
			{'$group':{
				'_id':{'$dateToString':{'format':'%Y-%m-%d','date':{'$subtract':['$ts',timedelta(hours=1)]}}},
				'count':{'$sum':1},
				'players':{'$push':'$player'}
			}},
			{'$sort':{'_id':1}}
		]
		curve=list(db['recruitments'].aggregate(pipeline))
		for c in curve:c['players']=list(set(c['players']))
		return cors({'events':docs,'curve':curve,'total':len(docs)})
	except Exception as e:return cors({'error':str(e)},500)

@require_auth
async def api_referent_timeline(r):
	"""Timeline globale de tous les pays référents — courbe par jour."""
	if not mongo_ok:return cors({'error':'MongoDB non connecté'},503)
	try:
		days=int(r.rel_url.query.get('days',30))
		since=datetime.utcnow()+timedelta(hours=1)-timedelta(days=days)
		pipeline=[
			{'$match':{'ts':{'$gte':since},'departure':{'$exists':False}}},
			{'$group':{
				'_id':{
					'date':{'$dateToString':{'format':'%Y-%m-%d','date':{'$subtract':['$ts',timedelta(hours=1)]}}},
					'server':'$server',
					'country':'$country',
					'country_name':'$country_name',
				},
				'count':{'$sum':1}
			}},
			{'$sort':{'_id.date':1}}
		]
		docs=list(db['recruitments'].aggregate(pipeline))
		return cors({'timeline':docs,'days':days})
	except Exception as e:return cors({'error':str(e)},500)

# ══════════════════════════════════════════════
# NOTES PARTAGÉES
# ══════════════════════════════════════════════

@require_auth
async def api_notes_get(r):
	"""Récupère toutes les notes joueurs."""
	if not mongo_ok:return cors({'notes':{}})
	try:
		docs=list(db['notes'].find({},{'_id':0}))
		notes={d['player']:{'text':d.get('text',''),'tag':d.get('tag',''),'updated':d.get('updated','')} for d in docs}
		return cors({'notes':notes})
	except Exception as e:return cors({'error':str(e)},500)

@require_auth
async def api_notes_save(r):
	"""Sauvegarde ou met à jour une note joueur."""
	try:
		body=await r.json()
		player=body.get('player','').strip()
		text=body.get('text','').strip()
		tag=body.get('tag','')
		if not player:return cors({'error':'Joueur requis'},400)
		now=(datetime.utcnow()+timedelta(hours=1)).strftime('%d/%m/%Y %H:%M')
		if mongo_ok:
			db['notes'].update_one(
				{'player':player},
				{'':{'player':player,'text':text,'tag':tag,'updated':now}},
				upsert=True
			)
		return cors({'ok':True,'updated':now})
	except Exception as e:return cors({'error':str(e)},500)

@require_auth
async def api_notes_delete(r):
	"""Supprime la note d'un joueur."""
	try:
		body=await r.json()
		player=body.get('player','').strip()
		if not player:return cors({'error':'Joueur requis'},400)
		if mongo_ok:db['notes'].delete_one({'player':player})
		return cors({'ok':True})
	except Exception as e:return cors({'error':str(e)},500)

# ══════════════════════════════════════════════
# API EXISTANTS (inchangés)
# ══════════════════════════════════════════════

async def api_health(r):
    return cors({'status':'ok','mongo':mongo_ok,'ng_key_len':len(NG_KEY or ''),'ng_key_start':(NG_KEY or '')[:10]})
@require_auth
async def api_online(r):
	s=r.match_info['server'].lower()
	if s not in SERVERS:return cors({'error':'Serveur invalide'},400)
	pl=await get_online(s);return cors({'server':s,'players':pl,'count':len(pl)})
@require_auth
async def api_online_all(r):return cors(await get_all_online())
@require_auth
async def api_checkall(r):p=r.match_info['player'];all_=await get_all_online();return cors({'player':p,'servers':[s for(s,pl)in all_.items()if p in pl]})
@require_auth
async def api_countries(r):
	s=r.match_info['server'].lower()
	if s not in SERVERS:return cors({'error':'Serveur invalide'},400)
	raw=await get_country_list(s)
	# Renvoie toujours une liste de strings (noms extraits)
	names=[x['name']if isinstance(x,dict)else x for x in raw if(isinstance(x,dict)and x.get('name','').strip())or(isinstance(x,str)and x.strip())]
	return cors({'server':s,'countries':names,'claimed':names})
@require_auth
async def api_check(r):
	s,c=r.match_info['server'].lower(),r.match_info['country']
	if s not in SERVERS:return cors({'error':'Serveur invalide'},400)
	# Normalise le nom du pays (case-insensitive) via la liste cached
	country_list=await get_country_list(s)
	match=next((x for x in country_list if x.lower()==c.lower()),c)
	members,name=await get_country_members(s,match)
	if not members:return cors({'error':'Pays introuvable'},404)
	all_=await get_all_online();found,total={},0
	for(sv,pl)in all_.items():
		f=[m for m in members if m in pl]
		if f:found[sv]=f;total+=len(f)
	return cors({'country':name,'members_total':len(members),'online_total':total,'servers':found})
@require_auth
async def api_wl_get(r):return cors({'players':WL})
@require_auth
async def api_wl_mocha_get(r):return cors({'players':WL_MOCHA})
async def _wl_mutate(r,lst,save_fn):
	try:
		body=await r.json();p=body.get('player','').strip()
		if not p:return cors({'error':'Nom vide'},400)
		action=r.path.split('/')[-1]
		if action=='add'and p not in lst:lst.append(p);await save_fn()
		elif action=='remove'and p in lst:lst.remove(p);await save_fn()
		return cors({'players':lst})
	except Exception as e:return cors({'error':str(e)},400)
@require_auth
async def api_wl_add(r):return await _wl_mutate(r,WL,save_watchlist)
@require_auth
async def api_wl_remove(r):return await _wl_mutate(r,WL,save_watchlist)
@require_auth
async def api_wl_mocha_add(r):return await _wl_mutate(r,WL_MOCHA,save_watchlist_mocha)
@require_auth
async def api_wl_mocha_remove(r):return await _wl_mutate(r,WL_MOCHA,save_watchlist_mocha)
@require_auth
async def api_pronostic(r):
	res=get_pronostic(r.match_info['player'])
	if not res:return cors({'error':'Pas assez de données (min 3)'},404)
	top,DAYS,total=res;return cors({'player':r.match_info['player'],'total':total,'pronostic':[{'day':DAYS[d],'avg_h':h,'avg_m':m,'pct':pct}for(d,h,m,pct)in top]})
@require_auth
async def api_plages(r):
	res=get_plages(r.match_info['player'])
	if not res:return cors({'error':'Aucune donnée'},404)
	hm,DAYS=res;return cors({'player':r.match_info['player'],'days':DAYS,'heatmap':hm})
@require_auth
async def api_cw_get(r):return cors({'watches':COUNTRY_WATCHES})
@require_auth
async def api_cw_add(r):
	try:
		body=await r.json();s=body.get('server','').lower();country=body.get('country','').strip()
		if not s or not country:return cors({'error':'Données manquantes'},400)
		exists=any(w['server']==s and w['country'].lower()==country.lower()for w in COUNTRY_WATCHES)
		if exists:return cors({'error':'Déjà surveillé'},409)
		COUNTRY_WATCHES.append({'server':s,'country':country,'members':[],'last_alert':False});await save_cw();return cors({'watches':COUNTRY_WATCHES})
	except Exception as e:return cors({'error':str(e)},400)
@require_auth
async def api_cw_remove(r):
	try:body=await r.json();s=body.get('server','').lower();country=body.get('country','').strip();global COUNTRY_WATCHES;COUNTRY_WATCHES=[w for w in COUNTRY_WATCHES if not(w['server']==s and w['country'].lower()==country.lower())];await save_cw();return cors({'watches':COUNTRY_WATCHES})
	except Exception as e:return cors({'error':str(e)},400)
@require_auth
async def api_grade(r):
	player=r.match_info['player'];server=r.match_info['server'].lower()
	try:
		headers={'Authorization':f"Bearer {NG_KEY}",'accept':'application/json'}
		async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8))as s:
			async with s.get(f"https://publicapi.nationsglory.fr/user/{player}",headers=headers)as resp:
				if resp.status!=200:return cors({'player':player,'server':server,'rank':None})
				data=await resp.json();rank=data.get('servers',{}).get(server,{}).get('country_rank',None);return cors({'player':player,'server':server,'rank':rank})
	except Exception as e:return cors({'player':player,'server':server,'rank':None,'error':str(e)})
@require_auth
async def api_known_players(r):
	if not mongo_ok:return cors({'players':[]})
	try:pl=sessions_col.distinct('player');pl.sort(key=str.lower);return cors({'players':pl})
	except:return cors({'players':[]})
async def api_auth_check(r):
	try:
		ip=_get_ip(r)
		if _is_blocked(ip):return cors({'ok':False,'error':'Trop de tentatives, réessaie dans 15 minutes'},429)
		data=await r.json();password=os.environ.get('SITE_PASSWORD','')
		if data.get('password')==password:
			_clear_attempts(ip)
			token=_jwt_sign({'sub':'user','exp':int(time.time())+86400*7})
			return cors({'ok':True,'token':token})
		blocked=_record_fail(ip)
		remaining=MAX_ATTEMPTS-len(_fail_attempts.get(ip,[]))
		if blocked:return cors({'ok':False,'error':'Trop de tentatives, réessaie dans 15 minutes'},429)
		return cors({'ok':False,'error':f'Mot de passe incorrect ({remaining} essais restants)'},401)
	except:return cors({'ok':False},400)
@require_auth
async def api_top_players(r):
	if not mongo_ok:return cors({'players':[]})
	try:
		limit=int(r.rel_url.query.get('limit',20))
		docs=list(db['presence'].find({},{'_id':0}).sort('total',-1).limit(limit))
		for d in docs:
			if 'last_seen' in d and hasattr(d['last_seen'],'strftime'):
				d['last_seen']=d['last_seen'].strftime('%d/%m/%Y %H:%M')
		return cors({'players':docs})
	except Exception as e:return cors({'error':str(e)},500)
@require_auth
async def api_top_players_server(r):
	server=r.match_info['server'].lower()
	if server not in SERVERS:return cors({'error':'Serveur invalide'},400)
	if not mongo_ok:return cors({'players':[]})
	try:
		limit=int(r.rel_url.query.get('limit',10))
		docs=list(db['presence'].find(
			{f'servers.{server}':{'$exists':True,'$gt':0}},
			{'_id':0}
		).sort(f'servers.{server}',-1).limit(limit))
		for d in docs:
			if 'last_seen' in d and hasattr(d['last_seen'],'strftime'):
				d['last_seen']=d['last_seen'].strftime('%d/%m/%Y %H:%M')
		return cors({'players':docs})
	except Exception as e:return cors({'error':str(e)},500)

async def srv_ac(i,cur):return[app_commands.Choice(name=s.upper(),value=s)for s in SERVERS if cur.lower()in s][:25]
async def ctry_ac(i,cur):
	s=i.namespace.server
	if not s or s not in SERVERS:return[]
	return[app_commands.Choice(name=c,value=c)for c in await get_country_list(s)if cur.lower()in c.lower()][:25]
@tree.command(name='check',description="Espionner les membres d'un pays")
@app_commands.autocomplete(server=srv_ac,country=ctry_ac)
async def cmd_check(i:discord.Interaction,server:str,country:str):
	await i.response.defer()
	if server not in SERVERS:return await i.followup.send('❌ Serveur invalide')
	members,name=await get_country_members(server,country)
	if not members:return await i.followup.send('❌ Pays introuvable')
	all_=await get_all_online();found,total={},0
	for(s,pl)in all_.items():
		f=[m for m in members if m in pl]
		if f:found[s]=f;total+=len(f)
	e=discord.Embed(title=f"📊 Espionnage {name}",color=discord.Color.red())
	if found:
		for(s,pl)in sorted(found.items(),key=lambda x:(x[0]!=server,x[0])):lbl=f"{SERVERS[s]['emoji']} {s.upper()} ({len(pl)})"+(' ← cible'if s==server else'');e.add_field(name=lbl,value=', '.join(pl),inline=False)
		e.set_footer(text=f"Total : {total} | {len(members)} membres")
	else:e.description=f"✅ Aucun membre de {name} connecté";e.color=discord.Color.green()
	await i.followup.send(embed=e)
@tree.command(name='checkall',description='Localiser un joueur')
async def cmd_checkall(i:discord.Interaction,joueur:str):await i.response.defer();all_=await get_all_online();found=[s for(s,pl)in all_.items()if joueur in pl];e=discord.Embed(title=f"🔍 {joueur}",color=discord.Color.green()if found else discord.Color.red());e.description='\n'.join(f"{SERVERS[s]['emoji']} **{s.upper()}**"for s in found)if found else f"**{joueur}** hors ligne";await i.followup.send(embed=e)
@tree.command(name='online',description='Joueurs en ligne sur un serveur')
@app_commands.autocomplete(server=srv_ac)
async def cmd_online(i:discord.Interaction,server:str):
	await i.response.defer()
	if server not in SERVERS:return await i.followup.send('❌ Serveur invalide')
	pl=await get_online(server);e=discord.Embed(title=f"{SERVERS[server]['emoji']} {server.upper()}",color=discord.Color.blurple())
	if pl:
		for(idx,chunk)in enumerate([pl[j:j+20]for j in range(0,len(pl),20)]):e.add_field(name=f"Joueurs {idx+1}",value='\n'.join(f"• {p}"for p in chunk),inline=True)
		e.set_footer(text=f"{len(pl)} connectés")
	else:e.description='Aucun joueur'
	await i.followup.send(embed=e)
@tree.command(name='pronostic',description='Pronostic de connexion')
async def cmd_pronostic(i:discord.Interaction,joueur:str):
	await i.response.defer()
	if not mongo_ok:return await i.followup.send('❌ MongoDB non connecté',ephemeral=True)
	res=get_pronostic(joueur)
	if not res:return await i.followup.send(f"⚠️ Pas assez de données pour **{joueur}**",ephemeral=True)
	top,DAYS,total=res;e=discord.Embed(title=f"🔮 Pronostic — {joueur}",description=f"Basé sur **{total}** connexions",color=discord.Color.purple())
	for(d,avg_h,avg_m,pct)in top:e.add_field(name=f"{DAYS[d]} — {pct}%",value=f"`{'█'*(pct//10)}{'░'*(10-pct//10)}` **{avg_h}h{str(avg_m).zfill(2)}**",inline=False)
	e.set_footer(text='% = fréquence par jour');await i.followup.send(embed=e)
@tree.command(name='plages',description="Plages horaires d'un joueur")
async def cmd_plages(i:discord.Interaction,joueur:str):
	await i.response.defer()
	if not mongo_ok:return await i.followup.send('❌ MongoDB non connecté',ephemeral=True)
	res=get_plages(joueur)
	if not res:return await i.followup.send(f"⚠️ Aucune donnée pour **{joueur}**",ephemeral=True)
	hm,DAYS=res;e=discord.Embed(title=f"🕐 Plages — {joueur}",color=discord.Color.orange())
	for d in range(7):
		row=hm[d]
		if not sum(row):continue
		hw=[h for h in range(24)if row[h]];plages,start,prev=[],hw[0],hw[0]
		for h in hw[1:]:
			if h-prev>2:plages.append(f"{start}h-{prev+1}h");start=h
			prev=h
		plages.append(f"{start}h-{prev+1}h");e.add_field(name=DAYS[d],value=' • '.join(plages),inline=True)
	e.set_footer(text='Historique complet');await i.followup.send(embed=e)
def _wl_cmd(name,lst,save_fn,label=''):
	suffix=f"_{name}"if name else'';tag=f" {label}"if label else''
	@tree.command(name=f"addwatch{suffix}",description=f"Ajouter à la watchlist{tag}")
	async def _add(i:discord.Interaction,joueur:str):
		if joueur in lst:return await i.response.send_message(f"⚠️ **{joueur}** déjà dans la watchlist{tag}",ephemeral=True)
		lst.append(joueur);await save_fn();await i.response.send_message(f"✅ **{joueur}** ajouté{tag}",ephemeral=True)
	@tree.command(name=f"removewatch{suffix}",description=f"Retirer de la watchlist{tag}")
	async def _remove(i:discord.Interaction,joueur:str):
		if joueur not in lst:return await i.response.send_message(f"❌ **{joueur}** pas dans la watchlist{tag}",ephemeral=True)
		lst.remove(joueur);await save_fn();await i.response.send_message(f"🗑️ **{joueur}** retiré{tag}",ephemeral=True)
	@tree.command(name=f"watchlist{suffix}",description=f"Afficher la watchlist{tag}")
	async def _show(i:discord.Interaction):
		if not lst:return await i.response.send_message(f"📋 Watchlist{tag} vide",ephemeral=True)
		e=discord.Embed(title=f"👁️ Watchlist{tag}",color=discord.Color.blurple());e.description='\n'.join(f"• {p}"for p in lst);e.set_footer(text=f"{len(lst)} joueurs");await i.response.send_message(embed=e,ephemeral=True)
_wl_cmd('',WL,save_watchlist)
_wl_cmd('mocha',WL_MOCHA,save_watchlist_mocha,'MOCHA')
last_states={s:{}for s in SERVERS}
rapport_msg_id=None
_rate_limited=False

async def safe_send(channel,**kwargs):
	global _rate_limited
	while True:
		try:return await channel.send(**kwargs)
		except discord.errors.HTTPException as e:
			if e.status==429:
				retry=e.retry_after if hasattr(e,'retry_after')else 30
				_rate_limited=True;print(f"⚠️ Rate limit, attente {retry}s",flush=True);await asyncio.sleep(retry);_rate_limited=False
			else:raise

async def safe_edit(msg,**kwargs):
	global _rate_limited
	while True:
		try:return await msg.edit(**kwargs)
		except discord.errors.HTTPException as e:
			if e.status==429:
				retry=e.retry_after if hasattr(e,'retry_after')else 30
				_rate_limited=True;print(f"⚠️ Rate limit (edit), attente {retry}s",flush=True);await asyncio.sleep(retry);_rate_limited=False
			else:raise
def _status_text(wl,players):
	on=[p for p in wl if p in players];off=[p for p in wl if p not in players];txt=''
	if on:txt+=f"🟢 **En ligne ({len(on)}) :**\n"+''.join(f"• {p}\n"for p in on)
	if off:txt+=('\n'if txt else'')+f"⚪ **Hors ligne ({len(off)}) :**\n"+''.join(f"• {p}\n"for p in off)
	return txt or'Aucun joueur surveillé en ligne'
def _rapport_embed(title,count,time_str,status_text,color):e=discord.Embed(title=title,color=color,timestamp=discord.utils.utcnow());e.add_field(name='👥 Connectés',value=f"**{count}**",inline=True);e.add_field(name='⏱️ Relevé', value=f"**{time_str}**", inline=True);e.add_field(name='👁️ Surveillance',value=status_text,inline=False);e.set_footer(text=f"Scanner • MongoDB {'✅'if mongo_ok else'❌'}");return e
async def _update_rapport(channel,msg_id_ref,embed,save_fn):
	if not channel:return msg_id_ref
	if msg_id_ref:
		try:msg=await channel.fetch_message(msg_id_ref);await safe_edit(msg,embed=embed);return msg_id_ref
		except discord.NotFound:pass
	msg=await safe_send(channel,embed=embed);await asyncio.get_running_loop().run_in_executor(None,save_fn,msg.id);return msg.id
async def scan_server(server,alerte_ch):
	players=await get_online(server);pset=set(players);prev=last_states[server];mocha_ch=client.get_channel(CH_M_ALERTE);ts=discord.utils.utcnow()
	for p in pset:
		if not prev.get(p):
			record_connection(p,server)
			if p in WL and alerte_ch:e=discord.Embed(title='🟢 CONNEXION',description=f"**{p}** → **{server.upper()}**",color=discord.Color.green(),timestamp=ts);await safe_send(alerte_ch,embed=e)
			if p in WL_MOCHA and server=='mocha'and mocha_ch:e=discord.Embed(title='🟢 CONNEXION — MOCHA',description=f"**{p}** → **MOCHA**",color=discord.Color.orange(),timestamp=ts);await safe_send(mocha_ch,embed=e)
	for(p,was)in prev.items():
		if was and p not in pset:
			if p in WL and alerte_ch:e=discord.Embed(title='🔴 DÉCONNEXION',description=f"**{p}** ← **{server.upper()}**",color=discord.Color.red(),timestamp=ts);await safe_send(alerte_ch,embed=e)
			if p in WL_MOCHA and server=='mocha'and mocha_ch:e=discord.Embed(title='🔴 DÉCONNEXION — MOCHA',description=f"**{p}** ← **MOCHA**",color=discord.Color.red(),timestamp=ts);await safe_send(mocha_ch,embed=e)
	last_states[server]={p:True for p in pset};return players
async def check_country_watch(watch):
	try:
		server=watch['server'];country=watch['country'];members,name=await get_country_members(server,country)
		if not members:return
		# Vérification double via /user pour filtrer les faux positifs de l'API membres
		# On récupère aussi les ranks pour éviter un 2e appel API plus bas
		members,rank_map=await verify_members_with_ranks(server,members)
		if not members:return
		online_players=await get_online(server);online_members=[m for m in members if m in online_players]
		if len(online_members)<2:watch['last_alert']=False;watch['members']=online_members;return
		non_recruits=[(p,rank_map[p])for p in online_members if rank_map.get(p,'')!='recruit']
		watch['members']=online_members;can_assault=len(online_members)>=2 and len(non_recruits)>=1
		if can_assault and not watch.get('last_alert'):
			watch['last_alert']=True;ch=client.get_channel(CH_PAYS)
			if ch:await safe_send(ch,content=f"⚔ **ASSAUT POSSIBLE** — **{name}** sur **{server.upper()}**")
		elif not can_assault and watch.get('last_alert'):
			watch['last_alert']=False;ch=client.get_channel(CH_PAYS)
			if ch:await safe_send(ch,content=f"✅ **PLUS POSSIBLE** — **{name}** sur **{server.upper()}** (moins de 2 membres ou que des recrues)")
	except Exception as e:print(f"❌ CW scan {watch}: {e}",flush=True)
async def scanner_loop():
	global rapport_msg_id;await client.wait_until_ready();await load_watchlist();await load_watchlist_mocha();rapport_msg_id=await asyncio.get_running_loop().run_in_executor(None,cfg_get,'rapport_msg_id');await load_cw();await load_referents();print(f"📋 Country watches: {len(COUNTRY_WATCHES)}",flush=True);print(f"📋 Référents: {len(REFERENT_WATCHES)}",flush=True);print(f"📋 Rapport ID: {rapport_msg_id}",flush=True);ch_rapport=client.get_channel(CH_RAPPORT);ch_alerte=client.get_channel(CH_ALERTE);tick=0
	while True:
		try:
			results=await asyncio.gather(*[scan_server(s,ch_alerte)for s in SERVERS],return_exceptions=True);sp={s:r if isinstance(r,list)else[]for(s,r)in zip(SERVERS,results)}
			if tick%3==0 and COUNTRY_WATCHES:await asyncio.gather(*[check_country_watch(w)for w in COUNTRY_WATCHES],return_exceptions=True);await save_cw()
			if tick%15==0:
				now=discord.utils.utcnow();ts=(now+timedelta(hours=1)).strftime('%H:%M:%S');lp=sp.get('lime',[]);e=_rapport_embed('🟢 RAPPORT TACTIQUE — LIME',len(lp),ts,_status_text(WL,lp),discord.Color.green()if any(p in lp for p in WL)else discord.Color.greyple());rapport_msg_id=await _update_rapport(ch_rapport,rapport_msg_id,e,lambda mid:cfg_set('rapport_msg_id',mid));mp=sp.get('mocha',[]);mocha_e=_rapport_embed('🟤 RAPPORT TACTIQUE — MOCHA',len(mp),ts,_status_text(WL_MOCHA,mp),discord.Color.orange()if any(p in mp for p in WL_MOCHA)else discord.Color.greyple());ch_mr=client.get_channel(CH_M_RAPPORT)
				if ch_mr:
					found=False
					async for old in ch_mr.history(limit=10):
						if old.author==client.user and old.embeds and'RAPPORT TACTIQUE — MOCHA'in(old.embeds[0].title or''):await safe_edit(old,embed=mocha_e);found=True;break
					if not found:await safe_send(ch_mr,embed=mocha_e)
			tick+=1
		except discord.errors.HTTPException as e:
			if e.status==429:retry=e.retry_after if hasattr(e,'retry_after')else 30;print(f"⚠️ Rate limit (loop), attente {retry}s",flush=True);await asyncio.sleep(retry)
			else:print(f"❌ Scanner HTTP: {e}",flush=True)
		except Exception as e:print(f"❌ Scanner: {e}",flush=True)
		await asyncio.sleep(2)
async def start_web():
	app=web.Application()
	routes=[
		('GET','/',api_health),
		('GET','/health',api_health),
		('POST','/api/auth-check',api_auth_check),
		('GET','/api/online/{server}',api_online),
		('GET','/api/online_all',api_online_all),
		('GET','/api/checkall/{player}',api_checkall),
		('GET','/api/countries/{server}',api_countries),
		('GET','/api/check/{server}/{country}',api_check),
		('GET','/api/watchlist',api_wl_get),
		('POST','/api/watchlist/add',api_wl_add),
		('POST','/api/watchlist/remove',api_wl_remove),
		('GET','/api/watchlist_mocha',api_wl_mocha_get),
		('POST','/api/watchlist_mocha/add',api_wl_mocha_add),
		('POST','/api/watchlist_mocha/remove',api_wl_mocha_remove),
		('GET','/api/pronostic/{player}',api_pronostic),
		('GET','/api/plages/{player}',api_plages),
		('GET','/api/known_players',api_known_players),
		('GET','/api/grade/{player}/{server}',api_grade),
		('GET','/api/country_watches',api_cw_get),
		('POST','/api/country_watches/add',api_cw_add),
		('POST','/api/country_watches/remove',api_cw_remove),
		('GET','/api/top_players',api_top_players),
		('GET','/api/top_players/{server}',api_top_players_server),
		# ── NOUVEAUX : Pays Référents ──
		('GET','/api/referents',api_referent_get),
		('POST','/api/referents/add',api_referent_add),
		('POST','/api/referents/remove',api_referent_remove),
		('GET','/api/referents/stats',api_referent_stats),
		('GET','/api/referents/history',api_referent_history),
		('GET','/api/referents/timeline',api_referent_timeline),
		('GET','/api/notes',api_notes_get),
		('POST','/api/notes/save',api_notes_save),
		('POST','/api/notes/delete',api_notes_delete),
	]
	for(method,path,handler)in routes:app.router.add_route(method,path,handler)
	app.router.add_route('OPTIONS','/{path_info:.*}',handle_options);runner=web.AppRunner(app);await runner.setup();port=int(os.getenv('PORT',10000));await web.TCPSite(runner,'0.0.0.0',port).start();print(f"🌐 API démarrée sur {port}",flush=True)
async def self_ping():
	await asyncio.sleep(60);url=(RENDER_URL if RENDER_URL.startswith('http')else f"https://{RENDER_URL}")if RENDER_URL else None
	while True:
		if url:
			try:
				async with aiohttp.ClientSession()as s:await s.get(url,timeout=aiohttp.ClientTimeout(total=10))
			except:pass
		await asyncio.sleep(600)
async def main():
	print('🚀 Démarrage...',flush=True);init_mongo();await asyncio.sleep(5)
	async with client:
		asyncio.create_task(start_web())
		if RENDER_URL:asyncio.create_task(self_ping())
		asyncio.create_task(scanner_loop())
		asyncio.create_task(referent_tracker_loop())  # ← NOUVEAU
		try:await client.start(TOKEN)
		except discord.errors.HTTPException as e:print(f"❌ Rate limit Discord: {e}",flush=True);await asyncio.sleep(60);sys.exit(1)
		except Exception as e:print(f"❌ Erreur: {e}",flush=True);await asyncio.sleep(30);sys.exit(1)
@client.event
async def on_ready():await tree.sync();print(f"✅ {client.user} | {len(SERVERS)} serveurs | MongoDB {'✅'if mongo_ok else'❌'}",flush=True)
if __name__=='__main__':asyncio.run(main())
