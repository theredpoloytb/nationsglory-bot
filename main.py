Af='❌ MongoDB non connecté'
Ae='❌ Serveur invalide'
Ad='country_rank'
Ac='pronostic'
Ab='WATCHLIST_MOCHA'
Aa='WATCHLIST'
AZ='country_watches'
AY='minute'
AX=isinstance
AD='watches'
AC='Serveur invalide'
AB='MOCHA'
AA='hour'
A2='\n'
A1='servers'
A0='ok'
z='accept'
y='Authorization'
x='name'
s='members'
q='day'
p='application/json'
o='mocha'
n=list
e='last_alert'
d='WL'
c=str
b=range
Y='country'
X=Exception
V='players'
U=False
R='url'
O='error'
N=None
M='emoji'
L=print
J='server'
H='player'
F=''
D=len
A=True
import discord as B,aiohttp as P,asyncio as E,time,json as A3,os as Z,sys
from discord import app_commands as f
from aiohttp import web as g
from datetime import timedelta as AE,datetime as Ag
Ah=Z.getenv('DISCORD_TOKEN')
t=Z.getenv('NG_API_KEY')
h=Z.getenv('RENDER_EXTERNAL_URL',F)
AF=Z.getenv('MONGO_URL')
Ai=0x14400e533c420056
Aj=0x1455d36c2644109a
AG=0x1485ddced2021066
A4=0x14943ec2eb8000e6
Ak=0x14943ed07902001e
AH=0x1455eb96fb40000b
AI=['Canisi','Darkholess','UFO_Thespoot','Franky753','Blakonne','Farsgame','ClashKiller78','Olmat38','FLOTYR2','Raptor51']
K=[]
BJ=N
S=n(AI)
T=n(AI)
i=j=N
Al=B.Intents.default()
I=B.Client(intents=Al)
W=f.CommandTree(I)
G={'blue':{R:'https://blue.nationsglory.fr/standalone/dynmap_world.json',M:'🔵'},'coral':{R:'https://coral.nationsglory.fr/standalone/dynmap_world.json',M:'🔴'},'orange':{R:'https://orange.nationsglory.fr/standalone/dynmap_world.json',M:'🟠'},'red':{R:'https://red.nationsglory.fr/standalone/dynmap_world.json',M:'🔴'},'yellow':{R:'https://yellow.nationsglory.fr/standalone/dynmap_world.json',M:'🟡'},o:{R:'https://mocha.nationsglory.fr/standalone/dynmap_world.json',M:'🟤'},'white':{R:'https://white.nationsglory.fr/standalone/dynmap_world.json',M:'⚪'},'jade':{R:'https://jade.nationsglory.fr/standalone/dynmap_world.json',M:'🟢'},'black':{R:'https://black.nationsglory.fr/standalone/dynmap_world.json',M:'⚫'},'cyan':{R:'https://cyan.nationsglory.fr/standalone/dynmap_world.json',M:'🔵'},'lime':{R:'https://lime.nationsglory.fr/standalone/dynmap_world.json',M:'🟢'}}
Am=900
r={}
AJ={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}
def C(data,status=200):return g.Response(text=A3.dumps(data,ensure_ascii=U),status=status,content_type=p,headers=AJ)
async def An(r):return g.Response(status=204,headers=AJ)
Q=U
u=a=v=N
def Ao():
	global Q,u,a,v
	if not AF:return
	try:from pymongo import MongoClient as D,ASCENDING as B;C=D(AF,serverSelectionTimeoutMS=8000,tls=A,tlsAllowInvalidCertificates=A);C.admin.command('ping');u=C['mossadglory'];a=u['sessions'];v=u['config'];a.create_index([(H,B),('ts',B)]);Q=A;L('✅ MongoDB OK',flush=A)
	except X as E:L(f"❌ MongoDB: {E}",flush=A)
def Ap(player,server):
	if not Q:return
	try:A=Ag.utcnow()+AE(hours=1);a.insert_one({H:player,J:server,'ts':A,q:A.weekday(),AA:A.hour,AY:A.minute})
	except:pass
def AK(player,limit=500):
	if not Q:return[]
	try:from pymongo import ASCENDING as A;return n(a.find({H:player},{'_id':0}).sort('ts',A).limit(limit))
	except:return[]
def AL(player):
	C=AK(player,200)
	if D(C)<3:return
	J=['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'];E,F=[0]*7,[[]for A in b(7)]
	for B in C:E[B[q]]+=1;F[B[q]].append(B[AA]+B.get(AY,0)/60)
	G=D(C);H=[]
	for A in b(7):
		if not E[A]:continue
		I=sum(F[A])/D(F[A]);H.append((A,int(I),int(I%1*60),round(E[A]/G*100)))
	return sorted(H,key=lambda x:-x[3])[:5],J,G
def AM(player):
	A=AK(player,500)
	if not A:return
	D=['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];B=[[0]*24 for A in b(7)]
	for C in A:B[C[q]][C[AA]]+=1
	return B,D
def AN(key,val):
	if not Q:return
	try:v.update_one({'key':key},{'$set':{'value':val}},upsert=A)
	except:pass
def AO(key):
	if not Q:return
	try:A=v.find_one({'key':key});return A['value']if A else N
	except:return
async def AP(global_name,prefix,channel_id):
	F=channel_id;E=prefix;C=global_name;global S,T,i,j;G=I.get_channel(F)
	if not G:return
	async for B in G.history(limit=50):
		if B.author==I.user and B.content.startswith(E+':'):
			try:
				H=A3.loads(B.content[D(E)+1:])
				if C==d:S=H[V];i=B.id
				else:T=H[V];j=B.id
				L(f"✅ Watchlist {C} chargée",flush=A);return
			except:pass
	await A5(C,E,F)
async def A5(global_name,prefix,channel_id):
	C=global_name;global i,j;D=I.get_channel(channel_id)
	if not D:return
	G=S if C==d else T;E=i if C==d else j;F=f"{prefix}:"+A3.dumps({V:G})
	if E:
		try:A=await D.fetch_message(E);await A.edit(content=F);return
		except B.NotFound:pass
	A=await D.send(F)
	if C==d:i=A.id
	else:j=A.id
async def Aq():
	global K;A=AO(AZ)
	if A:K=A
async def A6():AN(AZ,K)
async def Ar():await AP(d,Aa,AG)
async def A7():await A5(d,Aa,AG)
async def As():await AP(AB,Ab,A4)
async def A8():await A5(AB,Ab,A4)
async def k(server):
	try:
		async with P.ClientSession(timeout=P.ClientTimeout(total=5))as B:
			async with B.get(G[server][R])as A:
				if A.status==200:return[A[x]for A in(await A.json()).get(V,[])]
	except:pass
	return[]
async def l():B=await E.gather(*[k(A)for A in G],return_exceptions=A);return{B:A if AX(A,n)else[]for(B,A)in zip(G,B)}
async def AQ(server):
	A=server;B=time.time()
	if A in r and B-r[A][1]<Am:return r[A][0]
	try:
		E={y:f"Bearer {t}",z:p}
		async with P.ClientSession(timeout=P.ClientTimeout(total=10))as F:
			async with F.get(f"https://publicapi.nationsglory.fr/country/list/{A}",headers=E)as C:
				if C.status in(200,500):G=await C.json();D=[A[x]for A in G.get('claimed',[])if A.get(x)];r[A]=D,B;return D
	except:pass
	return[]
async def A9(server,country):
	B=country
	try:
		C={y:f"Bearer {t}",z:p}
		async with P.ClientSession(timeout=P.ClientTimeout(total=10))as D:
			async with D.get(f"https://publicapi.nationsglory.fr/country/{server}/{B}",headers=C)as E:
				A=await E.json()
				if A.get(s):return[A.lstrip('*+-')for A in A[s]],A.get(x,B)
	except:pass
	return N,N
async def AR(r):return C({'status':A0,'mongo':Q})
async def At(r):
	A=r.match_info[J].lower()
	if A not in G:return C({O:AC},400)
	B=await k(A);return C({J:A,V:B,'count':D(B)})
async def Au(r):return C(await l())
async def Av(r):A=r.match_info[H];B=await l();return C({H:A,A1:[B for(B,C)in B.items()if A in C]})
async def Aw(r):
	A=r.match_info[J].lower()
	if A not in G:return C({O:AC},400)
	return C({J:A,'countries':await AQ(A)})
async def Ax(r):
	E,I=r.match_info[J].lower(),r.match_info[Y]
	if E not in G:return C({O:AC},400)
	A,K=await A9(E,I)
	if not A:return C({O:'Pays introuvable'},404)
	L=await l();F,H={},0
	for(M,N)in L.items():
		B=[A for A in A if A in N]
		if B:F[M]=B;H+=D(B)
	return C({Y:K,'members_total':D(A),'online_total':H,A1:F})
async def Ay(r):return C({V:S})
async def Az(r):return C({V:T})
async def w(r,lst,save_fn):
	D=save_fn;A=lst
	try:
		G=await r.json();B=G.get(H,F).strip()
		if not B:return C({O:'Nom vide'},400)
		E=r.path.split('/')[-1]
		if E=='add'and B not in A:A.append(B);await D()
		elif E=='remove'and B in A:A.remove(B);await D()
		return C({V:A})
	except X as I:return C({O:c(I)},400)
async def A_(r):return await w(r,S,A7)
async def B0(r):return await w(r,S,A7)
async def B1(r):return await w(r,T,A8)
async def B2(r):return await w(r,T,A8)
async def B3(r):
	A=AL(r.match_info[H])
	if not A:return C({O:'Pas assez de données (min 3)'},404)
	B,D,E=A;return C({H:r.match_info[H],'total':E,Ac:[{q:D[A],'avg_h':B,'avg_m':C,'pct':E}for(A,B,C,E)in B]})
async def B4(r):
	A=AM(r.match_info[H])
	if not A:return C({O:'Aucune donnée'},404)
	B,D=A;return C({H:r.match_info[H],'days':D,'heatmap':B})
async def B5(r):return C({AD:K})
async def B6(r):
	try:
		D=await r.json();A=D.get(J,F).lower();B=D.get(Y,F).strip()
		if not A or not B:return C({O:'Données manquantes'},400)
		E=any(C[J]==A and C[Y].lower()==B.lower()for C in K)
		if E:return C({O:'Déjà surveillé'},409)
		K.append({J:A,Y:B,s:[],e:U});await A6();return C({AD:K})
	except X as G:return C({O:c(G)},400)
async def B7(r):
	try:A=await r.json();B=A.get(J,F).lower();D=A.get(Y,F).strip();global K;K=[A for A in K if not(A[J]==B and A[Y].lower()==D.lower())];await A6();return C({AD:K})
	except X as E:return C({O:c(E)},400)
async def B8(r):
	D='rank';A=r.match_info[H];B=r.match_info[J].lower()
	try:
		F={y:f"Bearer {t}",z:p}
		async with P.ClientSession(timeout=P.ClientTimeout(total=8))as G:
			async with G.get(f"https://publicapi.nationsglory.fr/user/{A}",headers=F)as E:
				if E.status!=200:return C({H:A,J:B,D:N})
				I=await E.json();K=I.get(A1,{}).get(B,{}).get(Ad,N);return C({H:A,J:B,D:K})
	except X as L:return C({H:A,J:B,D:N,O:c(L)})
async def B9(r):
	if not Q:return C({V:[]})
	try:A=a.distinct(H);A.sort(key=c.lower);return C({V:A})
	except:return C({V:[]})
async def BA(r):
	try:
		B=await r.json();D=Z.environ.get('SITE_PASSWORD',F)
		if B.get('password')==D:return C({A0:A})
		return C({A0:U},401)
	except:return C({A0:U},400)
async def AS(i,cur):return[f.Choice(name=A.upper(),value=A)for A in G if cur.lower()in A][:25]
async def BB(i,cur):
	A=i.namespace.server
	if not A or A not in G:return[]
	return[f.Choice(name=A,value=A)for A in await AQ(A)if cur.lower()in A.lower()][:25]
@W.command(name='check',description="Espionner les membres d'un pays")
@f.autocomplete(server=AS,country=BB)
async def BK(i,server,country):
	E=server;await i.response.defer()
	if E not in G:return await i.followup.send(Ae)
	I,L=await A9(E,country)
	if not I:return await i.followup.send('❌ Pays introuvable')
	O=await l();J,N={},0
	for(A,H)in O.items():
		K=[A for A in I if A in H]
		if K:J[A]=K;N+=D(K)
	C=B.Embed(title=f"📊 Espionnage {L}",color=B.Color.red())
	if J:
		for(A,H)in sorted(J.items(),key=lambda x:(x[0]!=E,x[0])):P=f"{G[A][M]} {A.upper()} ({D(H)})"+(' ← cible'if A==E else F);C.add_field(name=P,value=', '.join(H),inline=U)
		C.set_footer(text=f"Total : {N} | {D(I)} membres")
	else:C.description=f"✅ Aucun membre de {L} connecté";C.color=B.Color.green()
	await i.followup.send(embed=C)
@W.command(name='checkall',description='Localiser un joueur')
async def BL(i,joueur):A=joueur;await i.response.defer();E=await l();C=[B for(B,C)in E.items()if A in C];D=B.Embed(title=f"🔍 {A}",color=B.Color.green()if C else B.Color.red());D.description=A2.join(f"{G[A][M]} **{A.upper()}**"for A in C)if C else f"**{A}** hors ligne";await i.followup.send(embed=D)
@W.command(name='online',description='Joueurs en ligne sur un serveur')
@f.autocomplete(server=AS)
async def BM(i,server):
	C=server;await i.response.defer()
	if C not in G:return await i.followup.send(Ae)
	E=await k(C);F=B.Embed(title=f"{G[C][M]} {C.upper()}",color=B.Color.blurple())
	if E:
		for(H,I)in enumerate([E[A:A+20]for A in b(0,D(E),20)]):F.add_field(name=f"Joueurs {H+1}",value=A2.join(f"• {A}"for A in I),inline=A)
		F.set_footer(text=f"{D(E)} connectés")
	else:F.description='Aucun joueur'
	await i.followup.send(embed=F)
@W.command(name=Ac,description='Pronostic de connexion')
async def BN(i,joueur):
	C=joueur;await i.response.defer()
	if not Q:return await i.followup.send(Af,ephemeral=A)
	F=AL(C)
	if not F:return await i.followup.send(f"⚠️ Pas assez de données pour **{C}**",ephemeral=A)
	G,H,I=F;D=B.Embed(title=f"🔮 Pronostic — {C}",description=f"Basé sur **{I}** connexions",color=B.Color.purple())
	for(J,K,L,E)in G:D.add_field(name=f"{H[J]} — {E}%",value=f"`{"█"*(E//10)}{"░"*(10-E//10)}` **{K}h{c(L).zfill(2)}**",inline=U)
	D.set_footer(text='% = fréquence par jour');await i.followup.send(embed=D)
@W.command(name='plages',description="Plages horaires d'un joueur")
async def BO(i,joueur):
	D=joueur;await i.response.defer()
	if not Q:return await i.followup.send(Af,ephemeral=A)
	J=AM(D)
	if not J:return await i.followup.send(f"⚠️ Aucune donnée pour **{D}**",ephemeral=A)
	M,N=J;E=B.Embed(title=f"🕐 Plages — {D}",color=B.Color.orange())
	for K in b(7):
		L=M[K]
		if not sum(L):continue
		F=[A for A in b(24)if L[A]];G,H,C=[],F[0],F[0]
		for I in F[1:]:
			if I-C>2:G.append(f"{H}h-{C+1}h");H=I
			C=I
		G.append(f"{H}h-{C+1}h");E.add_field(name=N[K],value=' • '.join(G),inline=A)
	E.set_footer(text='Historique complet');await i.followup.send(embed=E)
def AT(name,lst,save_fn,label=F):
	I=label;H=save_fn;E=lst;G=f"_{name}"if name else F;C=f" {I}"if I else F
	@W.command(name=f"addwatch{G}",description=f"Ajouter à la watchlist{C}")
	async def J(i,joueur):
		B=joueur
		if B in E:return await i.response.send_message(f"⚠️ **{B}** déjà dans la watchlist{C}",ephemeral=A)
		E.append(B);await H();await i.response.send_message(f"✅ **{B}** ajouté{C}",ephemeral=A)
	@W.command(name=f"removewatch{G}",description=f"Retirer de la watchlist{C}")
	async def K(i,joueur):
		B=joueur
		if B not in E:return await i.response.send_message(f"❌ **{B}** pas dans la watchlist{C}",ephemeral=A)
		E.remove(B);await H();await i.response.send_message(f"🗑️ **{B}** retiré{C}",ephemeral=A)
	@W.command(name=f"watchlist{G}",description=f"Afficher la watchlist{C}")
	async def L(i):
		if not E:return await i.response.send_message(f"📋 Watchlist{C} vide",ephemeral=A)
		F=B.Embed(title=f"👁️ Watchlist{C}",color=B.Color.blurple());F.description=A2.join(f"• {A}"for A in E);F.set_footer(text=f"{D(E)} joueurs");await i.response.send_message(embed=F,ephemeral=A)
AT(F,S,A7)
AT(o,T,A8,AB)
AU={A:{}for A in G}
m=N
def AV(wl,players):
	E=players;B=[A for A in wl if A in E];C=[A for A in wl if A not in E];A=F
	if B:A+=f"🟢 **En ligne ({D(B)}) :**\n"+F.join(f"• {A}\n"for A in B)
	if C:A+=(A2 if A else F)+f"⚪ **Hors ligne ({D(C)}) :**\n"+F.join(f"• {A}\n"for A in C)
	return A or'Aucun joueur surveillé en ligne'
def AW(title,count,time_str,status_text,color):C=B.Embed(title=title,color=color,timestamp=B.utils.utcnow());C.add_field(name='👥 Connectés',value=f"**{count}**",inline=A);C.add_field(name='⏱️ Relevé',value=f"**{time_str}**",inline=A);C.add_field(name='👁️ Surveillance',value=status_text,inline=U);C.set_footer(text=f"Scanner • MongoDB {"✅"if Q else"❌"}");return C
async def BC(channel,msg_id_ref,embed,save_fn):
	F=embed;D=channel;A=msg_id_ref
	if not D:return A
	if A:
		try:C=await D.fetch_message(A);await C.edit(embed=F);return A
		except B.NotFound:pass
	C=await D.send(embed=F);await E.get_running_loop().run_in_executor(N,save_fn,C.id);return C.id
async def BD(server,alerte_ch):
	G=alerte_ch;D=server;L=await k(D);K=set(L);M=AU[D];H=I.get_channel(Ak);J=B.utils.utcnow()
	for C in K:
		if not M.get(C):
			Ap(C,D)
			if C in S and G:F=B.Embed(title='🟢 CONNEXION',description=f"**{C}** → **{D.upper()}**",color=B.Color.green(),timestamp=J);await G.send(embed=F);await E.sleep(.5)
			if C in T and D==o and H:F=B.Embed(title='🟢 CONNEXION — MOCHA',description=f"**{C}** → **MOCHA**",color=B.Color.orange(),timestamp=J);await H.send(embed=F);await E.sleep(.5)
	for(C,N)in M.items():
		if N and C not in K:
			if C in S and G:F=B.Embed(title='🔴 DÉCONNEXION',description=f"**{C}** ← **{D.upper()}**",color=B.Color.red(),timestamp=J);await G.send(embed=F);await E.sleep(.5)
			if C in T and D==o and H:F=B.Embed(title='🔴 DÉCONNEXION — MOCHA',description=f"**{C}** ← **MOCHA**",color=B.Color.red(),timestamp=J);await H.send(embed=F);await E.sleep(.5)
	AU[D]={B:A for B in K};return L
async def BE(watch):
	B=watch
	try:
		E=B[J];R=B[Y];K,M=await A9(E,R)
		if not K:return
		S=await k(E);C=[A for A in K if A in S]
		if D(C)<2:B[e]=U;B[s]=C;return
		T={y:f"Bearer {t}",z:p};N=[]
		async with P.ClientSession(timeout=P.ClientTimeout(total=10))as V:
			W=[V.get(f"https://publicapi.nationsglory.fr/user/{A}",headers=T)for A in C[:8]]
			for(Z,a)in zip(C[:8],W):
				try:
					async with a as O:
						if O.status==200:
							b=await O.json();H=b.get(A1,{}).get(E,{}).get(Ad,F)
							if H and H!='recruit':N.append((Z,H))
				except:pass
		B[s]=C;Q=D(C)>=2 and D(N)>=1
		if Q and not B.get(e):
			B[e]=A;G=I.get_channel(AH)
			if G:await G.send(f"⚔ **ASSAUT POSSIBLE** — **{M}** sur **{E.upper()}**")
		elif not Q and B.get(e):
			B[e]=U;G=I.get_channel(AH)
			if G:await G.send(f"✅ **PLUS POSSIBLE** — **{M}** sur **{E.upper()}** (moins de 2 membres ou que des recrues)")
	except X as c:L(f"❌ CW scan {B}: {c}",flush=A)
async def BF():
	Z='rapport_msg_id';global m;await I.wait_until_ready();await Ar();await As();m=await E.get_running_loop().run_in_executor(N,AO,Z);await Aq();L(f"📋 Country watches: {D(K)}",flush=A);L(f"📋 Rapport ID: {m}",flush=A);a=I.get_channel(Ai);b=I.get_channel(Aj);J=0
	while A:
		try:
			c=await E.gather(*[BD(A,b)for A in G],return_exceptions=A);Q={B:A if AX(A,n)else[]for(B,A)in zip(G,c)}
			if J%3==0 and K:await E.gather(*[BE(A)for A in K],return_exceptions=A);await A6()
			if J%15==0:
				d=B.utils.utcnow();R=(d+AE(hours=1)).strftime('%H:%M:%S');M=Q.get('lime',[]);C=AW('🟢 RAPPORT TACTIQUE — LIME',D(M),R,AV(S,M),B.Color.green()if any(A in M for A in S)else B.Color.greyple());m=await BC(a,m,C,lambda mid:AN(Z,mid));O=Q.get(o,[]);V=AW('🟤 RAPPORT TACTIQUE — MOCHA',D(O),R,AV(T,O),B.Color.orange()if any(A in O for A in T)else B.Color.greyple());P=I.get_channel(A4)
				if P:
					W=U
					async for H in P.history(limit=10):
						if H.author==I.user and H.embeds and'RAPPORT TACTIQUE — MOCHA'in(H.embeds[0].title or F):await H.edit(embed=V);W=A;break
					if not W:await P.send(embed=V)
			J+=1
		except B.errors.HTTPException as C:
			if C.status==429:Y=C.retry_after if hasattr(C,'retry_after')else 30;L(f"⚠️ Rate limit, attente {Y}s",flush=A);await E.sleep(Y)
			else:L(f"❌ Scanner HTTP: {C}",flush=A)
		except X as C:L(f"❌ Scanner: {C}",flush=A)
		await E.sleep(2)
async def BG():
	C='POST';B='GET';D=g.Application();G=[(B,'/',AR),(B,'/health',AR),(C,'/api/auth-check',BA),(B,'/api/online/{server}',At),(B,'/api/online_all',Au),(B,'/api/checkall/{player}',Av),(B,'/api/countries/{server}',Aw),(B,'/api/check/{server}/{country}',Ax),(B,'/api/watchlist',Ay),(C,'/api/watchlist/add',A_),(C,'/api/watchlist/remove',B0),(B,'/api/watchlist_mocha',Az),(C,'/api/watchlist_mocha/add',B1),(C,'/api/watchlist_mocha/remove',B2),(B,'/api/pronostic/{player}',B3),(B,'/api/plages/{player}',B4),(B,'/api/known_players',B9),(B,'/api/grade/{player}/{server}',B8),(B,'/api/country_watches',B5),(C,'/api/country_watches/add',B6),(C,'/api/country_watches/remove',B7)]
	for(H,I,J)in G:D.router.add_route(H,I,J)
	D.router.add_route('OPTIONS','/{path_info:.*}',An);E=g.AppRunner(D);await E.setup();F=int(Z.getenv('PORT',10000));await g.TCPSite(E,'0.0.0.0',F).start();L(f"🌐 API démarrée sur {F}",flush=A)
async def BH():
	await E.sleep(60);B=(h if h.startswith('http')else f"https://{h}")if h else N
	while A:
		if B:
			try:
				async with P.ClientSession()as C:await C.get(B,timeout=P.ClientTimeout(total=10))
			except:pass
		await E.sleep(600)
async def BI():
	L('🚀 Démarrage...',flush=A);Ao();await E.sleep(5)
	async with I:
		E.create_task(BG())
		if h:E.create_task(BH())
		E.create_task(BF())
		try:await I.start(Ah)
		except B.errors.HTTPException as C:L(f"❌ Rate limit Discord: {C}",flush=A);await E.sleep(60);sys.exit(1)
		except X as C:L(f"❌ Erreur: {C}",flush=A);await E.sleep(30);sys.exit(1)
@I.event
async def BP():await W.sync();L(f"✅ {I.user} | {D(G)} serveurs | MongoDB {"✅"if Q else"❌"}",flush=A)
if __name__=='__main__':E.run(BI())
