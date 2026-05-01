(function(){
  const SESSION_KEY = 'mg_token_v3';
  const MAIN = document.querySelector('.main');
  const HDR  = document.querySelector('.hdr');
  const NAV  = document.querySelector('.nav');

  function lockContent() {
    if(MAIN) MAIN.style.display = 'none';
    if(HDR)  HDR.style.display  = 'none';
    if(NAV)  NAV.style.display  = 'none';
  }

  function unlockContent() {
    const lock = document.getElementById('init-lock');
    if(lock) lock.remove();
    if(MAIN) MAIN.style.display = '';
    if(HDR)  HDR.style.display  = '';
    if(NAV)  NAV.style.display  = '';
  }

  function watchGate() {
    const gate = document.getElementById('pw-gate');
    
    if(!gate && !sessionStorage.getItem(SESSION_KEY)) {
      trollUser();
    }
  }

  function trollUser() {
    lockContent();
    document.body.innerHTML = `
      <div style="
        position:fixed;inset:0;background:#000;
        display:flex;flex-direction:column;
        align-items:center;justify-content:center;
        font-family:monospace;color:#4d9fff;text-align:center;gap:2rem;
        z-index:99999;
      ">
        <div style="font-size:5rem">🕵️</div>
        <div style="font-size:1.6rem;letter-spacing:.2em">INTRUSION DÉTECTÉE</div>
        <div style="font-size:.85rem;color:rgba(26,111,255,.5);letter-spacing:.15em;max-width:420px;line-height:1.8">
          La tentative de contournement a été enregistrée.<br>
          IP transmise à l'unité de surveillance.<br>
          <span style="color:#f04040">Accès définitivement révoqué.</span>
        </div>
        <div style="font-size:.7rem;color:rgba(200,100,100,.4);letter-spacing:.1em" id="fake-ip">
          Identification en cours...
        </div>
        <div style="font-size:.6rem;color:rgba(26,111,255,.2);margin-top:1rem">
          מוסד גלורי — CLASSIFIED
        </div>
      </div>
    `;
    
    setTimeout(() => {
      const fake = `${rand(1,254)}.${rand(0,255)}.${rand(0,255)}.${rand(1,254)}`;
      document.getElementById('fake-ip').textContent =
        `Adresse identifiée : ${fake} — signalement en cours...`;
    }, 1800);
  }

  function rand(a,b){ return Math.floor(Math.random()*(b-a+1))+a; }

  if(sessionStorage.getItem(SESSION_KEY)){
    const gate = document.getElementById('pw-gate');
    if(gate) gate.style.display = 'none';
    unlockContent();
  } else {
    lockContent();
    setTimeout(() => {
      const el = document.getElementById('pw-input-el');
      if(el) el.focus();
    }, 100);
    
    const observer = setInterval(watchGate, 500);
    
    window._stopGateWatch = () => clearInterval(observer);
  }

  window.pwCheck = async function(){
    const inp = document.getElementById('pw-input-el');
    const err = document.getElementById('pw-err');
    const val = inp.value;
    if(!val) return;
    try{
      const r = await fetch('https://nationsglory-spy.onrender.com/api/auth-check', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({password: val})
      });
      const d = await r.json();
      if(d.ok){
        sessionStorage.setItem(SESSION_KEY, d.token);
        if(window._stopGateWatch) window._stopGateWatch();
        requestNotifPerms();
        unlockContent();
        const gate = document.getElementById('pw-gate');
        gate.style.transition = 'opacity .6s';
        gate.style.opacity = '0';
        setTimeout(() => { gate.style.display = 'none'; }, 600);
      } else {
        const msg = d.error || 'MOT DE PASSE INCORRECT';
        err.textContent = msg;
        err.style.opacity = '1';
        inp.value = '';
        inp.style.borderColor = 'rgba(255,24,64,.5)';
        
        if(r.status === 429){
          inp.disabled = true;
          inp.placeholder = 'Bloqué 15 minutes...';
          setTimeout(() => { inp.disabled = false; inp.placeholder = ''; err.style.opacity='0'; inp.style.borderColor='rgba(0,80,216,.2)'; }, 900000);
        } else {
          setTimeout(() => {
            err.style.opacity = '0';
            inp.style.borderColor = 'rgba(0,80,216,.2)';
          }, 3000);
        }
      }
    } catch(e){
      err.textContent = 'ERREUR SERVEUR';
      err.style.opacity = '1';
      setTimeout(() => {
        err.style.opacity = '0';
        err.textContent = 'CODE INVALIDE — ACCÈS REFUSÉ';
      }, 2500);
    }
  };
})();

const API='https://nationsglory-spy.onrender.com';
const SRV=["blue","coral","orange","red","yellow","mocha","white","jade","black","cyan","lime"];
const EMO={blue:"🔵",coral:"🔴",orange:"🟠",red:"🔴",yellow:"🟡",mocha:"🟤",white:"⚪",jade:"🟢",black:"⚫",cyan:"🔵",lime:"🟢"};

const STATIC_COUNTRIES_FALLBACK=["AfriqueDuSud","Afghanistan","Alaska","Albanie","Algerie","Allemagne","Altai","Amour","Angola","ArchipelCrozet","Argentine","Armenie","Arizona","Australie","Autriche","Azerbaidjan","Bahamas","Bahrein","Baja","Bangladesh","Belgique","Belize","Benin","Bhoutan","Bielorussie","Birmanie","Bolivie","Bosnie","Botswana","Bouriatie","Bresil","Bulgarie","BurkinaFaso","Californie","Cambodge","Cameroun","Canada","CentreAfrique","Chili","Chine","Chypre","Colombie","Congo","CoreeDuNord","CoreeDuSud","CoteDivoire","Croatie","Dakota","Danemark","Djibouti","Egypte","EmiratsArabesUnis","EmpireBissaoguineen","EmpireIrkoutsk","EmpireJordanien","EmpireOmanais","Equateur","Erythree","Espagne","Estonie","EtatsUnis","Ethiopie","Floride","France","Gabon","Georgie","Ghana","Grece","Groenland","Guatemala","Guangdong","Guangxi","Guizhou","Guyana","Guyane","Hainan","Iakoutie","Iamalie","Idaho","IleCoats","IleBolchevique","IleDeLaReunion","IleGraham","IleMaurice","IleVictoria","IleWrangel","IlesBaleares","IlesCanaries","IlesFeroe","IlesFidji","IlesGalapagos","IlesKerguelen","IlesSalomon","IlesSandwich","IlesVancouver","IleBouvet","Inde","Indonesie","Irak","Iran","Islande","Italie","Jamaique","Japon","Java","Kazakhstan","Kenya","Khabarovsk","Kirghizistan","Kosovo","Koweit","Krasnoy","Laos","Liban","Liberia","Libye","Lituanie","Lettonie","Luxembourg","Macedoine","Madagan","Madagascar","Magadan","Malaisie","Malawi","Mali","Malte","Maroc","Mauritanie","Mexique","Michigan","Minnesota","Moldavie","Mongolie","Montenegro","Montana","Mozambique","Namibie","Nepal","Nevada","Nicaragua","Niger","Nigeria","Norvege","NouvelleCaledonie","NouvelleGuinee","NouvelleZelande","NouvelleZemble","NouveauMexique","Nunavut","Ontario","Oregon","Ouganda","Ouzbekistan","Pakistan","Palaos","Papouasie","Paraguay","PaysBas","Perou","Philippines","Pologne","Portugal","Qatar","Quebec","Quinghai","RDCongo","RepubliqueTcheque","Roumanie","RoyaumeUni","Russie","SaharaOccidental","Sakhaline","Salvador","Sardaigne","Serbie","Sichuan","Slovaquie","Slovenie","Socotra","Somalie","Sonora","Soudan","Srilanka","StHelena","Suede","Suisse","Sumatra","Suriname","Svalbard","Swaziland","Syrie","Tadjikistan","Taiwan","Tanzanie","Tasmanie","Tchad","Tchoukota","TerreAdelie","TerreBooth","TerreBurke","TerreDeFeu","TerreGrant","TerreLiard","TerreLow","TerreMasson","TerreMill","TerrePowell","TerreRoss","TerreSigny","TerreSiple","TerreSmith","TerreSnow","TerreSpaatz","TerreThor","TerreVega","Texas","Thailande","Tibet","Timor","Togo","Tomsk","Touva","TriniteEtTobago","Tunisie","Turkmenistan","Turquie","Uruguay","Utah","Venezuela","Vietnam","WallisEtFutuna","Washington","Wisconsin","Xinjiang","Yemen","Yunnam","Zambie","Zimbabwe"].sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));

const CC_LS_KEY='mg_cc_v1';const CC_LS_TTL=6*3600*1000;
function _ccLoadLS(){try{const r=JSON.parse(localStorage.getItem(CC_LS_KEY)||'{}');const now=Date.now();Object.entries(r).forEach(([s,v])=>{if(now-v.ts<CC_LS_TTL)cc[s]=v.list;});console.log('[countries] cache localStorage chargé:',Object.keys(cc));}catch{}}
function _ccSaveLS(server,list){try{const r=JSON.parse(localStorage.getItem(CC_LS_KEY)||'{}');r[server]={list,ts:Date.now()};localStorage.setItem(CC_LS_KEY,JSON.stringify(r));}catch{}}
_ccLoadLS();

async function getCountries(server){
  if(cc[server])return cc[server];
  try{
    const d=await fetch(API+'/api/countries/'+server,{headers:{..._authHeader()}});
    if(d.status===429){console.warn('[countries] 429 rate-limit →',server,'fallback statique');cc[server]=[...STATIC_COUNTRIES_FALLBACK];return cc[server];}
    const j=await d.json();
    const raw=j.countries||j.claimed||[];
    const list=raw.map(x=>x.name||x).filter(Boolean).sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));
    if(list.length){cc[server]=list;_ccSaveLS(server,list);}
    else{cc[server]=[...STATIC_COUNTRIES_FALLBACK];}
  }catch{cc[server]=[...STATIC_COUNTRIES_FALLBACK];}
  return cc[server];
}
const BUG=s=>s==='red'||s==='mocha';
const WARN=`<div class="warn">⚠ Dynmap limité — données possiblement incomplètes</div>`;
let WL=[],WLM=[],cwl='lime',snd=localStorage.getItem('mg_sound')!=='off';
let ALR=[],prev={},hist=JSON.parse(localStorage.getItem('mg_h')||'[]'),cc={},oP=[];
const $=id=>document.getElementById(id);
const ld=()=>`<div class="ld">Chargement<span class="ldd"><span>.</span><span>.</span><span>.</span></span></div>`;
const ld2=()=>ld();
const rP=(i,p)=>p.find(x=>x.toLowerCase()===i.toLowerCase())||i;

const sparkData={total:[],wl:[],wc:[]};
function drawSpark(canvasId,data,color='rgba(0,80,216,.55)'){
  const c=$(canvasId);if(!c||!data.length)return;
  const W=c.offsetWidth,H=c.offsetHeight;c.width=W*devicePixelRatio;c.height=H*devicePixelRatio;
  const ctx=c.getContext('2d');ctx.scale(devicePixelRatio,devicePixelRatio);
  if(data.length<2)return;
  const mn=Math.min(...data),mx=Math.max(...data),range=mx-mn||1;
  ctx.beginPath();
  data.forEach((v,i)=>{const x=i/(data.length-1)*W,y=H-(v-mn)/range*H*.8-H*.1;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
  ctx.strokeStyle=color;ctx.lineWidth=1;ctx.stroke();
  const grad=ctx.createLinearGradient(0,0,0,H);grad.addColorStop(0,'rgba(0,80,216,.1)');grad.addColorStop(1,'transparent');
  ctx.lineTo(W,H);ctx.lineTo(0,H);ctx.closePath();ctx.fillStyle=grad;ctx.fill();
}

(()=>{
  const c=$('bg'),ctx=c.getContext('2d');
  const sz=()=>{c.width=innerWidth;c.height=innerHeight};sz();window.addEventListener('resize',sz);
  const pts=Array.from({length:55},()=>({x:Math.random()*innerWidth,y:Math.random()*innerHeight,vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,r:Math.random()*.9+.2,a:Math.random()*.2+.04}));
  let mx=innerWidth/2,my=innerHeight/2,t=0;
  document.addEventListener('mousemove',e=>{mx=e.clientX;my=e.clientY});
  const orbs=[[.14,.1,0,56,184,.055,.44],[.86,.84,26,111,255,.038,.42],[.5,.44,77,159,255,.025,.36]];
  const draw=()=>{
    t+=.003;ctx.clearRect(0,0,c.width,c.height);
    orbs.forEach(([ox,oy,r,g,b,a,s])=>{
      const px=c.width*(ox+Math.sin(t*.6+ox*10)*.038),py=c.height*(oy+Math.cos(t*.42+oy*8)*.028);
      const grd=ctx.createRadialGradient(px,py,0,px,py,c.width*s);
      grd.addColorStop(0,`rgba(${r},${g},${b},${a})`);grd.addColorStop(1,'transparent');
      ctx.fillStyle=grd;ctx.fillRect(0,0,c.width,c.height);
    });
    pts.forEach(p=>{
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0)p.x=c.width;if(p.x>c.width)p.x=0;if(p.y<0)p.y=c.height;if(p.y>c.height)p.y=0;
      const d=Math.hypot(p.x-mx,p.y-my),br=d<90?1-d/90:0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r+br*1.2,0,Math.PI*2);
      ctx.fillStyle=`rgba(26,111,255,${p.a+br*.16})`;ctx.fill();
    });
    for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){
      const d=Math.hypot(pts[i].x-pts[j].x,pts[i].y-pts[j].y);
      if(d<80){ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);ctx.strokeStyle=`rgba(0,80,216,${.028*(1-d/80)})`;ctx.lineWidth=.5;ctx.stroke();}
    }
    requestAnimationFrame(draw);
  };draw();
})();

(()=>{
  
  const tc=document.createElement('canvas');
  tc.id='trl';tc.style.cssText='position:fixed;inset:0;z-index:9998;pointer-events:none';
  document.body.appendChild(tc);
  const ctx=tc.getContext('2d');
  const sync=()=>{tc.width=innerWidth;tc.height=innerHeight};sync();
  window.addEventListener('resize',sync);
  let trail=[],MAX=14;
  document.addEventListener('mousemove',e=>{
    trail.push({x:e.clientX,y:e.clientY,t:Date.now()});
    if(trail.length>MAX)trail.shift();
  });
  const draw=()=>{
    ctx.clearRect(0,0,tc.width,tc.height);
    const now=Date.now();
    trail.forEach((p,i)=>{
      const s=(i+1)/MAX*(1-(now-p.t)/220);
      if(s<=0)return;
      ctx.beginPath();ctx.arc(p.x,p.y,1.4*s,0,Math.PI*2);
      ctx.fillStyle=`rgba(26,111,255,${s*.14})`;ctx.fill();
    });
    requestAnimationFrame(draw);
  };draw();
})();

setInterval(()=>{$('clock').textContent=new Date().toLocaleTimeString('fr-FR');$('hdr-date').textContent=new Date().toLocaleDateString('fr-FR');},1000);

function showToast(msg,duration=3000){
  const wrap=$('toast-wrap'),t=document.createElement('div');
  t.className='toast';t.textContent=msg;wrap.appendChild(t);
  setTimeout(()=>{t.style.animation='toastOut .3s ease forwards';setTimeout(()=>t.remove(),300);},duration);
}

document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT')return;
  const tabs=document.querySelectorAll('.tab');
  const map={'1':0,'2':1,'3':2,'4':3,'5':4,'6':5,'7':6,'8':7,'9':8};
  if(map[e.key]!==undefined&&tabs[map[e.key]]){tabs[map[e.key]].click();showToast(`Onglet ${e.key} — ${tabs[map[e.key]].textContent.trim()}`);return;}
  if(e.key==='/'||e.key==='k'&&(e.ctrlKey||e.metaKey)){e.preventDefault();tabs[2].click();setTimeout(()=>$('ca-input').focus(),300);}
});

let pct=0;
const pctT=setInterval(()=>{pct=Math.min(pct+(Math.random()*8+2),92);if($('l-pct'))$('l-pct').textContent=Math.floor(pct)+'%';},85);
const msgs=['CHARGEMENT DES MODULES...','CONNEXION API SÉCURISÉE...','SYNCHRONISATION SERVEURS...','VÉRIFICATION INTÉGRITÉ...','CHIFFREMENT CANAL...','SYSTÈME PRÊT À DÉMARRER...'];
let mi=0;const msgT=setInterval(()=>{if(mi<msgs.length-1&&$('l-msg'))$('l-msg').textContent=msgs[mi++];},500);

function _loaderReady(){
  clearInterval(pctT);clearInterval(msgT);
  if($('l-pct'))$('l-pct').textContent='100%';
  if($('l-fill'))$('l-fill').style.width='100%';
  setTimeout(()=>{
    const m=$('l-msg');
    if(m){m.textContent='SYSTÈME PRÊT — CLIQUEZ POUR ENTRER';m.classList.remove('blink');m.classList.add('rdy');}
    const b=$('lbtn');if(b)b.style.display='block';
  },300);
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',_loaderReady);
}else{
  
  setTimeout(_loaderReady,200);
}

setTimeout(()=>{
  const b=$('lbtn');
  if(b&&b.style.display==='none'||b&&!b.style.display){_loaderReady();}
},4000);
function enterSite(){
  try{if(!actx)actx=new(window.AudioContext||window.webkitAudioContext)();actx.resume();}catch(e){}
  _au=true;window.scrollTo(0,0);
  $('ldr').classList.add('out');
  setTimeout(()=>{$('ldr').style.display='none';showToast('SYSTÈME OPÉRATIONNEL',2500);},900);
}

let scW=null,scOn=false,scBarT=null;
(()=>{
  const ifr=document.createElement('iframe');ifr.allow='autoplay';
  ifr.style.cssText='position:absolute;width:0;height:0;border:none;opacity:0;pointer-events:none';
  ifr.src='https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/user-164072391-103154989/omer-adam-feat-arisa-tel-aviv&color=%23f0c040&auto_play=false&hide_related=true&show_comments=false&show_user=false&show_reposts=false&show_teaser=false';
  document.body.appendChild(ifr);
  const s=document.createElement('script');s.src='https://w.soundcloud.com/player/api.js';
  s.onload=()=>{
    scW=SC.Widget(ifr);
    scW.bind(SC.Widget.Events.READY,()=>scW.setVolume(70));
    scW.bind(SC.Widget.Events.PLAY,()=>{scOn=true;$('scp-tri').classList.add('p');$('scp-eq').classList.add('on');scStartBar();});
    scW.bind(SC.Widget.Events.PAUSE,()=>{scOn=false;$('scp-tri').classList.remove('p');$('scp-eq').classList.remove('on');scStopBar();});
    scW.bind(SC.Widget.Events.FINISH,()=>{scOn=false;$('scp-tri').classList.remove('p');$('scp-eq').classList.remove('on');$('scp-bf').style.width='0%';});
  };document.head.appendChild(s);
})();
function scToggle(){if(!scW)return;scOn?scW.pause():scW.play();}
function scVol(v){if(scW)scW.setVolume(parseInt(v));}
function scStartBar(){scStopBar();scBarT=setInterval(()=>{if(!scW)return;scW.getPosition(p=>{scW.getDuration(d=>{if(d>0)$('scp-bf').style.width=(p/d*100)+'%';});});},500);}
function scStopBar(){if(scBarT){clearInterval(scBarT);scBarT=null;}}

function _authHeader(){const t=sessionStorage.getItem('mg_token_v3');return t?{'Authorization':'Bearer '+t}:{};}
async function api(p){const r=await fetch(API+p,{headers:{..._authHeader()}});if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}
async function apiP(p,b){const r=await fetch(API+p,{method:'POST',headers:{'Content-Type':'application/json',..._authHeader()},body:JSON.stringify(b)});if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}

async function nav(id,btn){sndNav();pageFlash();document.querySelector('.main').scrollTo({top:0,behavior:'instant'});document.querySelectorAll('.sec').forEach(s=>s.classList.remove('active'));document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));$('s-'+id).classList.add('active');btn.classList.add('active');if(id==='watchlist')await switchWl('lime');if(id==='countrywatch'){cwRender();cwRefreshAll();}if(id==='online'){$('ol-body').innerHTML=ld();loadOnline();}if(id==='checkall')rAT('ca-pl','ppCA');if(id==='stats')rAT('st-pl','ppST');if(id==='referents'){loadReferents();}}

function rAT(id,fn){const e=$(id);if(!e||!oP.length)return;e.innerHTML=oP.map(p=>`<span class="tag" onclick="${fn}('${p.replace(/'/g,"\\'")}')">${p}</span>`).join('');const cnt=$('ca-pl-count');if(cnt&&id==='ca-pl')cnt.textContent=oP.length+' joueurs';}
function fPT(ii,di){const e=$(di);if(!e)return;const v=$(ii).value.trim().toLowerCase(),f=v?oP.filter(p=>p.toLowerCase().includes(v)):oP;if(!f.length){e.innerHTML='';return;}const m={'ca-pl':'ppCA','st-pl':'ppST','wl-pl':'ppWL'};e.innerHTML=f.slice(0,100).map(p=>`<span class="tag" onclick="${m[di]||'qCA'}('${p.replace(/'/g,"\\'")}')">${p}</span>`).join('');}
function ppCA(p){$('ca-input').value=p;$('ca-pl').innerHTML='';$('ca-list').style.display='none';doCA();}
function ppST(p){$('st-input').value=p;$('st-pl').innerHTML='';$('st-list').style.display='none';loadStats();}
function ppWL(p){$('wl-add').value=p;$('wl-pl').innerHTML='';$('wl-acl').style.display='none';}
function acF(ii,li,pool){const v=$(ii).value.trim().toLowerCase(),l=$(li);if(!v||!pool.length){l.style.display='none';return;}const m=pool.filter(p=>p.toLowerCase().includes(v)).slice(0,10);if(!m.length){l.style.display='none';return;}l.innerHTML=m.map(p=>`<div class="aci" onmousedown="acP('${ii}','${li}','${p.replace(/'/g,"\\'")}')">${p}</div>`).join('');l.style.display='block';}
function acFC(){const s=$('ck-srv').value;if(!s)return;const v=$('ck-country').value.trim().toLowerCase(),p=cc[s]||[];$('ck-suggest').innerHTML=(v?p.filter(c=>c.toLowerCase().includes(v)):p).map(c=>`<span class="tag" onclick="selC('${c.replace(/'/g,"\\'")}')">${c}</span>`).join('');acF('ck-country','ck-list',p);}
function acP(i,l,v){$(i).value=v;$(l).style.display='none';}
function acK(e,l,cb){const list=$(l),items=list.querySelectorAll('.aci'),cur=list.querySelector('.sel');if(e.key==='ArrowDown'){e.preventDefault();const n=cur?cur.nextElementSibling:items[0];if(cur)cur.classList.remove('sel');if(n)n.classList.add('sel');}else if(e.key==='ArrowUp'){e.preventDefault();const p=cur?cur.previousElementSibling:items[items.length-1];if(cur)cur.classList.remove('sel');if(p)p.classList.add('sel');}else if(e.key==='Enter'){if(cur){cur.onmousedown();return;}list.style.display='none';cb();}else if(e.key==='Escape')list.style.display='none';}
document.addEventListener('click',e=>{document.querySelectorAll('.acl').forEach(l=>{if(!l.parentElement.contains(e.target))l.style.display='none';});});

async function chkAPI(){try{await api('/health');$('api-led').className='led on';$('api-txt').textContent='API OK';return true;}catch{$('api-led').className='led off';$('api-txt').textContent='DOWN';return false;}}
async function loadWL(){try{const c=new AbortController(),t=setTimeout(()=>c.abort(),6000);const r=await fetch(API+'/api/watchlist',{signal:c.signal,headers:{..._authHeader()}});clearTimeout(t);const d=await r.json();WL=d.players||[];animStat('st-wcount',WL.length);sparkData.wc.push(WL.length);if(sparkData.wc.length>30)sparkData.wc.shift();drawSpark('spark-wc',sparkData.wc);}catch{}}
async function loadWLM(){try{const c=new AbortController(),t=setTimeout(()=>c.abort(),6000);const r=await fetch(API+'/api/watchlist_mocha',{signal:c.signal,headers:{..._authHeader()}});clearTimeout(t);const d=await r.json();WLM=d.players||[];}catch{}}
async function loadKP(){try{const d=await fetch(API+'/api/known_players',{headers:{..._authHeader()}}).then(r=>r.json());oP=[...new Set([...(d.players||[]),...oP])].sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));rAT('ca-pl','ppCA');rAT('st-pl','ppST');rAT('wl-pl','ppWL');}catch{}}

function animStat(id,val){
  const el=$(id);if(!el)return;
  const prev=parseInt(el.textContent)||0;if(prev===val)return;
  el.style.opacity='.12';
  setTimeout(()=>{el.textContent=val;el.style.opacity='1';el.classList.add('bump');setTimeout(()=>el.classList.remove('bump'),350);},120);
}

async function loadDash(){
  if(!$('srv-overview').children.length)$('srv-overview').innerHTML=ld();
  try{
    const all=await api('/api/online_all'),lp=all['lime']||[];
    const pool=new Set(oP);SRV.forEach(s=>(all[s]||[]).forEach(p=>pool.add(p)));
    oP=[...pool].sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));
    WL.forEach(p=>{const lc=p.toLowerCase(),on=(all['lime']||[]).map(x=>x.toLowerCase()).includes(lc),k=p+'@lime';if(on&&!prev[k])pAlert('connect',p,'lime');if(!on&&prev[k])pAlert('disconnect',p,'lime');prev[k]=on;});
    WLM.forEach(p=>{const lc=p.toLowerCase(),on=(all['mocha']||[]).map(x=>x.toLowerCase()).includes(lc),k=p+'@mocha';if(on&&!prev[k])pAlert('connect',p,'mocha');if(!on&&prev[k])pAlert('disconnect',p,'mocha');prev[k]=on;});
    let tot=0;SRV.forEach(s=>tot+=(all[s]||[]).length);
    animStat('st-total',tot);
    sparkData.total.push(tot);if(sparkData.total.length>30)sparkData.total.shift();drawSpark('spark-total',sparkData.total);
    const wonline=WL.filter(p=>lp.map(x=>x.toLowerCase()).includes(p.toLowerCase())).length;
    animStat('st-wonline',wonline);updateWeather(wonline);
    sparkData.wl.push(wonline);if(sparkData.wl.length>30)sparkData.wl.shift();drawSpark('spark-wl',sparkData.wl);
    const mx=Math.max(...SRV.map(s=>(all[s]||[]).length),1);
    const cards=$('srv-overview').querySelectorAll('.sc');
    if(cards.length===SRV.length){SRV.forEach((s,i)=>{const cnt=(all[s]||[]).length,c=cards[i],n=c.querySelector('.sc-n'),b=c.querySelector('.sbar-f');if(n&&parseInt(n.textContent)!==cnt){n.style.opacity='.1';setTimeout(()=>{n.textContent=cnt;n.style.opacity='1';},120);}if(b)b.style.width=Math.round(cnt/mx*100)+'%';});}
    else $('srv-overview').innerHTML=SRV.map(s=>{const cnt=(all[s]||[]).length,bug=BUG(s);return`<div class="sc" onmouseenter="sndH()" onclick="gOL('${s}')" ${bug?'style="border-color:rgba(255,119,0,.22)"':''}><div class="sc-top"><span class="sc-name">${s.toUpperCase()}</span><span class="sc-emo">${EMO[s]}</span></div><div class="sc-n">${cnt}</div>${bug?'<div class="sc-lbl warn">⚠ INSTABLE</div>':'<div class="sc-lbl">EN LIGNE</div>'}<div class="sbar"><div class="sbar-f" style="width:${Math.round(cnt/mx*100)}%"></div></div></div>`;}).join('');
    const mp=await api('/api/online/mocha').then(d=>d.players||[]).catch(()=>[]);
    const mk=(pl,l,c,lb)=>l.length?`<div style="font-family:var(--M);font-size:.46rem;color:${c};letter-spacing:.22em;margin-bottom:.28rem">${lb}</div><div style="display:flex;flex-direction:column;gap:.22rem;margin-bottom:.5rem">${l.map(p=>{const on=pl.map(x=>x.toLowerCase()).includes(p.toLowerCase());const seen=getLastSeenText(p);return`<div class="wi" style="padding:.28rem .5rem;cursor:pointer;opacity:${on?'1':'.55'}" onclick="openPlayerPanel('${p.replace(/'/g,"\\'")}')"><img src="https://skins.nationsglory.fr/face/${encodeURIComponent(p)}/32" style="width:24px;height:24px;border-radius:3px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0" onerror="this.style.display='none'" alt=""><span style="font-family:var(--M);font-size:.6rem;color:${on?'var(--t1)':'var(--t3)'}">${on?'🟢':'⚫'} ${p}</span>${seen?`<span class="wi-seen ${seen.cls}" style="margin-left:auto">${seen.text}</span>`:on?'<span style="font-family:var(--M);font-size:.46rem;color:var(--grn);margin-left:auto">EN LIGNE</span>':''}</div>`;}).join('')}</div>`:'' ;
    $('wl-quick').innerHTML=(mk(lp,WL,'var(--grn)','🟢 LIME')||'')+(mk(mp,WLM,'var(--org)','🟤 MOCHA')||'')||'<div class="empty">Watchlists vides</div>';
    if($('last-update'))$('last-update').textContent=new Date().toLocaleTimeString('fr-FR');
    pushActivity(tot);startCountdown(5);
    _firstCycle=false;
    if(document.getElementById('wl-status')&&document.getElementById('wl-status').innerHTML.trim()!=='')wlRS();
  }catch(e){$('srv-overview').innerHTML=`<div class="empty" style="color:var(--red)">Bot hors ligne<br/><span style="font-size:.52rem;opacity:.6">${e.message}</span></div>`;}
}
const _authed=()=>!!sessionStorage.getItem('mg_token_v3');
let _firstCycle=true;

const CONN_HIST_KEY='mg_conn_hist_v2';
const CONN_HIST_MAX=500;
let connHist=JSON.parse(localStorage.getItem(CONN_HIST_KEY)||'[]');

function saveConnHist(){localStorage.setItem(CONN_HIST_KEY,JSON.stringify(connHist));}

function addConnEvent(type,player,server){
  connHist.unshift({type,player,server,ts:Date.now(),time:new Date().toLocaleTimeString('fr-FR'),date:new Date().toLocaleDateString('fr-FR')});
  if(connHist.length>CONN_HIST_MAX)connHist.pop();
  saveConnHist();
  updateHistPlayerFilter();
  if(document.getElementById('s-historique')?.classList.contains('active')) renderConnHist();
}

function updateHistPlayerFilter(){
  const sel=document.getElementById('hist-filter-player');if(!sel)return;
  const cur=sel.value;
  const players=[...new Set(connHist.map(e=>e.player))].sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));
  sel.innerHTML='<option value="">Tous les joueurs</option>'+players.map(p=>`<option value="${p}" ${p===cur?'selected':''}>${p}</option>`).join('');
}

function renderConnHist(){
  const body=document.getElementById('conn-hist-body');
  const statsEl=document.getElementById('hist-stats');
  const chartEl=document.getElementById('hist-chart-body');
  if(!body)return;
  const fp=document.getElementById('hist-filter-player')?.value||'';
  const ft=document.getElementById('hist-filter-type')?.value||'';
  let filtered=connHist;
  if(fp)filtered=filtered.filter(e=>e.player===fp);
  if(ft)filtered=filtered.filter(e=>e.type===ft);

  if(statsEl){
    const total=connHist.length;
    const connects=connHist.filter(e=>e.type==='connect').length;
    const players=[...new Set(connHist.map(e=>e.player))].length;
    statsEl.innerHTML=[
      {label:'Événements total',val:total,col:'var(--blue-pale)'},
      {label:'Connexions',val:connects,col:'var(--grn)'},
      {label:'Déconnexions',val:total-connects,col:'var(--red)'},
      {label:'Joueurs trackés',val:players,col:'var(--org)'}
    ].map(s=>`<div style="background:var(--bg2);border:1px solid var(--b1);border-radius:var(--r);padding:.6rem 1rem;min-width:120px">
      <div style="font-family:var(--D);font-size:1.6rem;color:${s.col};line-height:1">${s.val}</div>
      <div style="font-family:var(--M);font-size:.5rem;color:var(--t3);letter-spacing:.12em;margin-top:.2rem">${s.label}</div>
    </div>`).join('');
  }

  if(!filtered.length){body.innerHTML='<div class="empty">Aucun événement correspondant aux filtres.</div>';return;}
  body.innerHTML=`<table class="tbl">
    <thead><tr><th>Type</th><th>Joueur</th><th>Serveur</th><th>Date</th><th>Heure</th></tr></thead>
    <tbody>${filtered.slice(0,150).map(e=>`
      <tr onclick="openPlayerPanel('${e.player}')">
        <td><span style="color:${e.type==='connect'?'var(--grn)':'var(--red)'}">
          ${e.type==='connect'?'🟢 Connexion':'🔴 Déco'}
        </span></td>
        <td style="color:var(--t1);font-weight:600">${e.player}</td>
        <td><span class="stag">${(e.server||'').toUpperCase()}</span></td>
        <td style="color:var(--t3)">${e.date||'—'}</td>
        <td style="color:var(--t2)">${e.time}</td>
      </tr>`).join('')}
    </tbody>
  </table>
  ${filtered.length>150?`<div style="font-family:var(--M);font-size:.55rem;color:var(--t3);text-align:center;margin-top:.6rem;letter-spacing:.1em">Affichage limité à 150 / ${filtered.length} événements — utilisez les filtres</div>`:''}`;

  if(chartEl){
    const byPlayer={};
    connHist.forEach(e=>{
      if(!byPlayer[e.player])byPlayer[e.player]={connect:0,disconnect:0};
      byPlayer[e.player][e.type]=(byPlayer[e.player][e.type]||0)+1;
    });
    const sorted=Object.entries(byPlayer).sort((a,b)=>(b[1].connect+b[1].disconnect)-(a[1].connect+a[1].disconnect)).slice(0,10);
    if(!sorted.length){chartEl.innerHTML='<div class="empty">Pas encore de données.</div>';return;}
    const maxVal=Math.max(...sorted.map(([,v])=>v.connect+v.disconnect),1);
    chartEl.innerHTML=sorted.map(([player,v])=>{
      const total=v.connect+v.disconnect;
      const pctC=Math.round(v.connect/maxVal*100);
      const pctD=Math.round(v.disconnect/maxVal*100);
      return`<div style="margin-bottom:.7rem">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.22rem">
          <span style="font-family:var(--M);font-size:.62rem;color:var(--t1);cursor:pointer" onclick="openPlayerPanel('${player}')">${player}</span>
          <span style="font-family:var(--M);font-size:.52rem;color:var(--t3)">${v.connect} co · ${v.disconnect} déco</span>
        </div>
        <div style="display:flex;gap:2px;height:8px;border-radius:4px;overflow:hidden;background:var(--bg2)">
          <div style="width:${pctC}%;background:var(--grn);opacity:.7;transition:width .3s"></div>
          <div style="width:${pctD}%;background:var(--red);opacity:.6;transition:width .3s"></div>
        </div>
      </div>`;
    }).join('');
  }
}

function clearConnHist(){
  if(!confirm('Vider tout l\'historique des connexions ?'))return;
  connHist=[];saveConnHist();
  document.getElementById('hist-filter-player').innerHTML='<option value="">Tous les joueurs</option>';
  renderConnHist();
  showToast('Historique vidé');
}

function pAlert(t,p,s){
  ALR.unshift({type:t,player:p,server:s,time:new Date().toLocaleTimeString('fr-FR')});
  if(ALR.length>60)ALR.pop();
  rAlerts();
  if(!_authed()||_firstCycle)return;
  const inWL=WL.map(x=>x.toLowerCase()).includes(p.toLowerCase())||WLM.map(x=>x.toLowerCase()).includes(p.toLowerCase());
  if(inWL){
    addConnEvent(t,p,s);
    if(t==='connect'){setLastSeen(p,s);startSession(p);sendBrowserNotif('connect',p,s);}
    else{endSession(p);sendBrowserNotif('disconnect',p,s);}
    showPop(t,p,s);
  }
}
function rAlerts(){$('alert-badge').textContent=ALR.length+' évts';$('alert-feed').innerHTML=ALR.length?ALR.map(a=>`<div class="fi"><div class="fi-d ${a.type==='connect'?'g':'r'}"></div><span class="fi-t">${a.time}</span><span class="fi-m">${a.type==='connect'?'🟢':'🔴'} <b style="cursor:pointer" onclick="openPlayerPanel('${a.player}')">${a.player}</b><span class="fi-s">${a.server.toUpperCase()}</span></span></div>`).join(''):'<div class="empty">En attente...</div>';}

function gOL(s){document.querySelectorAll('.tab')[1].click();$('ol-srv').value=s;$('ol-body').innerHTML=ld();loadOLS(s);}
function fOL(s){$('ol-srv').value=s;$('ol-body').innerHTML=ld();loadOLS(s);}
async function loadOLS(srv){const body=$('ol-body'),w=BUG(srv)?WARN:'';try{const d=await api('/api/online/'+srv),pl=d.players||[];body.innerHTML=w+(pl.length?`<div style="font-family:var(--M);font-size:.55rem;color:var(--t3);margin-bottom:.5rem"><span style="color:var(--gb)">${pl.length}</span> joueurs — ${srv.toUpperCase()}</div><div style="display:flex;flex-direction:column;gap:.3rem">${pl.map(p=>`<div class="wi" style="cursor:pointer" onclick="openPlayerPanel('${p.replace(/'/g,"\\'")}')"><img src="https://skins.nationsglory.fr/face/${encodeURIComponent(p)}/32" style="width:28px;height:28px;border-radius:4px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0" onerror="this.style.display='none'" alt=""><span style="font-family:var(--M);font-size:.62rem;color:${WL.map(w=>w.toLowerCase()).includes(p.toLowerCase())?'var(--grn)':'var(--t1)'}">${p}${WL.map(w=>w.toLowerCase()).includes(p.toLowerCase())?'<span style="font-size:.46rem;color:var(--grn);margin-left:.3rem">🎯</span>':''}</span><div class="wis on" style="margin-left:auto"><div class="led on" style="width:5px;height:5px;flex-shrink:0"></div>EN LIGNE</div></div>`).join('')}</div>`:`<div class="empty">${BUG(srv)?'0 joueur (dynmap limité)':'Aucun joueur sur '+srv.toUpperCase()}</div>`);}catch(e){body.innerHTML=w+`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;}}
async function loadOnline(){const srv=$('ol-srv').value,body=$('ol-body');body.innerHTML=ld();try{if(!srv){const all=await api('/api/online_all');let tot=0;SRV.forEach(s=>tot+=(all[s]||[]).length);body.innerHTML=`<div style="font-family:var(--M);font-size:.55rem;color:var(--t3);margin-bottom:.55rem">TOTAL <span style="color:var(--gb)">${tot}</span> joueurs</div><div class="sg">${SRV.map(s=>{const pl=all[s]||[],bug=BUG(s);return`<div class="sc" onmouseenter="sndH()" onclick="fOL('${s}')" ${bug?'style="border-color:rgba(255,119,0,.22)"':''}><div class="sc-top"><span class="sc-name">${s.toUpperCase()}</span><span class="sc-emo">${EMO[s]}</span></div><div class="sc-n">${pl.length}</div>${bug?'<div class="sc-lbl warn">⚠ INSTABLE</div>':'<div class="sc-lbl">CLIQUER</div>'}<div class="tags" style="max-height:110px;overflow-y:auto;padding-right:2px" onclick="event.stopPropagation()">${pl.slice(0,20).map(p=>`<span class="tag ${WL.map(w=>w.toLowerCase()).includes(p.toLowerCase())?'wl':''}" onclick="event.stopPropagation();qCA('${p}')">${p}</span>`).join('')}${pl.length>20?`<span style="font-family:var(--M);font-size:.46rem;color:var(--t3)">+${pl.length-20}</span>`:''}</div><div class="sbar"><div class="sbar-f" style="width:${Math.round(pl.length/Math.max(...SRV.map(ss=>(all[ss]||[]).length),1)*100)}%"></div></div></div>`;}).join('')}</div>`;}else await loadOLS(srv);}catch(e){body.innerHTML=`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;}}

async function doCA(){const raw=$('ca-input').value.trim();if(!raw)return;const p=rP(raw,oP);$('ca-input').value=p;const res=$('ca-result');res.innerHTML=ld();try{const d=await api('/api/checkall/'+encodeURIComponent(p));if(d.servers.length)sndF();const skinUrl=`https://skins.nationsglory.fr/face/${encodeURIComponent(p)}/64`;const countryOnline=d.country&&d.country_server&&d.servers.includes(d.country_server);const countryInfo=countryOnline?`<div style="display:inline-flex;align-items:center;gap:.4rem;font-family:var(--M);font-size:.58rem;color:var(--blue-pale);background:rgba(91,163,255,.07);border:1px solid rgba(91,163,255,.22);border-radius:4px;padding:.2rem .6rem;margin-top:.4rem">🌍 <b>${d.country}</b><span style="color:var(--t4);font-size:.5rem">${d.country_server.toUpperCase()}</span></div>`:'';res.innerHTML=d.servers.length?`<div class="res ok"><div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.5rem"><img src="${skinUrl}" style="width:48px;height:48px;border-radius:6px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0" onerror="this.style.display='none'" alt=""><div><div class="rt" style="margin-bottom:.2rem">Joueur localisé — ${p}</div>${d.servers.map(s=>`<div style="margin:.15rem 0">${EMO[s]} <span style="color:var(--g)">${s.toUpperCase()}</span></div>`).join('')}${countryInfo}</div></div></div>`:`<div class="res err"><div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.3rem"><img src="${skinUrl}" style="width:40px;height:40px;border-radius:5px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0;opacity:.5" onerror="this.style.display='none'" alt=""><div><div class="rt">Résultat</div><span style="color:var(--t3)">${p} n'est connecté nulle part</span>${countryInfo}</div></div></div>`;hist=hist.filter(h=>h.p.toLowerCase()!==p.toLowerCase());hist.unshift({p,servers:d.servers,t:new Date().toLocaleTimeString('fr-FR')});if(hist.length>15)hist.pop();localStorage.setItem('mg_h',JSON.stringify(hist));rHist();}catch(e){res.innerHTML=`<div class="res err">Erreur : ${e.message}</div>`;}}
function qCA(player){openPlayerPanel(player);}
function rHist(){const el=$('ca-history');if(!hist.length){el.innerHTML='<div class="empty">Aucune recherche</div>';return;}el.innerHTML=`<table class="tbl"><thead><tr><th>Joueur</th><th>Serveurs</th><th>Heure</th></tr></thead><tbody>`+hist.slice(0,12).map(h=>`<tr><td style="color:var(--g)" onclick="qCA('${h.p}')">${h.p}</td><td>${h.servers.length?h.servers.map(s=>`<span class="stag">${s.toUpperCase()}</span>`).join(''):'<span style="color:var(--t3)">Hors ligne</span>'}</td><td style="color:var(--t3)">${h.t}</td></tr>`).join('')+'</tbody></table>';}

async function loadCS(){const s=$('ck-srv').value;if(!s)return;await getCountries(s);rCS(s);}
function rCS(s){const el=$('ck-suggest'),p=cc[s]||[];if(!p.length){el.innerHTML='';return;}el.innerHTML=p.map(c=>`<span class="tag" onclick="selC('${c.replace(/'/g,"\\'")}')">${c}</span>`).join('');}
function selC(c){$('ck-country').value=c;$('ck-list').style.display='none';doCheck();}
async function doCheck(){const s=$('ck-srv').value,raw=$('ck-country').value.trim();if(!s||!raw)return;await getCountries(s);const c=rP(raw,cc[s]||[]);$('ck-country').value=c;const res=$('ck-result');res.innerHTML=ld();try{const d=await api(`/api/check/${s}/${encodeURIComponent(c)}`);const note=`<div class="warn" style="margin-top:.34rem">⚠ Dynmap hors service</div>`;const hasDynmap=d.power||d.claims||d.mmr;const powerPct=d.power&&d.maxpower?Math.min(100,Math.round(d.power/d.maxpower*100)):0;const isSP=d.power<d.claims;const powerBar=d.maxpower?`<div style="margin:.3rem 0 .1rem;background:var(--bg2);border-radius:3px;height:4px;overflow:hidden"><div style="height:100%;width:${powerPct}%;background:${isSP?'var(--red)':'var(--grn)'};transition:width .4s"></div></div>`:'';const infoBloc=hasDynmap?`<div style="font-family:var(--M);font-size:.49rem;color:var(--t3);margin:.35rem 0 .05rem;display:flex;gap:.8rem;flex-wrap:wrap;align-items:center">${d.claims?`<span>🏴 <b style="color:var(--t1)">${d.claims}</b> claims</span>`:''}${d.power?`<span>⚡ <b style="color:${isSP?'var(--red)':'var(--grn)'}">${d.power}</b>/<b style="color:var(--t2)">${d.maxpower}</b> power${isSP?` <span style="color:var(--red);font-size:.44rem">▼ SOUS-POWER (${d.claims-d.power})</span>`:''}</span>`:''}${d.mmr?`<span>🏆 <b style="color:var(--t1)">${d.mmr}</b> MMR</span>`:''}${d.leader?`<span style="display:inline-flex;align-items:center;gap:.3rem"><img src="https://skins.nationsglory.fr/face/${d.leader}/32" style="width:20px;height:20px;border-radius:3px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0" onerror="this.style.display='none'">👑 <b style="color:var(--t1)">${d.leader}</b></span>`:''}</div>${powerBar}`:'';if(d.online_total===0){res.innerHTML=`<div class="res ok"><div class="rt">Pays : <a href="https://${s}.nationsglory.fr/" target="_blank" rel="noopener" style="color:var(--blue-pale);text-decoration:none" title="Dynmap ${s}">${d.country} ↗</a> — ${d.members_total} membres</div>${infoBloc}<span style="color:var(--grn)">✓ Aucun membre connecté</span>${BUG(s)?note:''}</div>`;}else{res.innerHTML=`<div class="res err"><div class="rt">Pays : <a href="https://${s}.nationsglory.fr/" target="_blank" rel="noopener" style="color:var(--blue-pale);text-decoration:none" title="Dynmap ${s}">${d.country} ↗</a> — ${d.online_total}/${d.members_total} connectés</div>${infoBloc}`+Object.entries(d.servers).sort((a,b)=>a[0]===s?-1:1).map(([x,pl])=>`<div style="margin:.2rem 0">${EMO[x]} <span style="color:var(--g)">${x.toUpperCase()}</span>${BUG(x)?'<span style="color:var(--org);font-size:.46rem"> ⚠</span>':''}${x===s?'<span style="color:var(--red);font-size:.46rem"> ← CIBLE</span>':''} <span style="color:var(--t3);margin-left:.22rem">${pl.join(', ')}</span></div>`).join('')+(Object.keys(d.servers).some(x=>BUG(x))||BUG(s)?note:'')+'</div>';}}catch(e){res.innerHTML=`<div class="res err"><div class="rt">Erreur</div>${e.message}</div>`;}}

function wlR(){const el=$('wl-manage'),wl=cwl==='mocha'?WLM:WL;if(!wl.length){el.innerHTML='<div class="empty">Watchlist vide</div>';return;}el.innerHTML=wl.map(p=>`<div class="wi"><img src="https://skins.nationsglory.fr/face/${encodeURIComponent(p)}/32" style="width:28px;height:28px;border-radius:4px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0" onerror="this.style.display='none'" alt=""><span style="font-family:var(--M);font-size:.62rem">${p}</span><button class="btn btn-r" style="padding:.07rem .34rem;font-size:.48rem;margin-left:auto" onclick="wlRm('${p}')">✕</button></div>`).join('');}
async function wlAdd(){const raw=$('wl-add').value.trim();if(!raw)return;const name=rP(raw,oP);$('wl-add').value='';try{const d=await apiP(cwl==='mocha'?'/api/watchlist_mocha/add':'/api/watchlist/add',{player:name});if(cwl==='mocha')WLM=d.players;else WL=d.players;wlR();wlRS();showToast(`${name} ajouté à la watchlist`);}catch(e){showToast('Erreur : '+e.message);}}
async function wlRm(name){try{const d=await apiP(cwl==='mocha'?'/api/watchlist_mocha/remove':'/api/watchlist/remove',{player:name});if(cwl==='mocha')WLM=d.players;else WL=d.players;wlR();wlRS();showToast(`${name} retiré`);}catch(e){showToast('Erreur : '+e.message);}}
async function switchWl(s){cwl=s;document.querySelectorAll('.wtb').forEach(e=>e.classList.remove('act'));const a=$('wl-tab-'+s);if(a)a.classList.add('act');if($('wl-pt'))$('wl-pt').textContent='◈ Watchlist — '+s.toUpperCase();if($('wl-st'))$('wl-st').textContent='⚡ Statut live — '+s.toUpperCase();$('wl-manage').innerHTML='';$('wl-status').innerHTML='';if(s==='lime')await loadWL();else await loadWLM();wlR();wlRS();}
async function wlRS(){const el=$('wl-status');if(!el)return;el.innerHTML=ld();const s=cwl==='mocha'?'mocha':'lime',wl=cwl==='mocha'?WLM:WL;if(!wl.length){el.innerHTML='<div class="empty">Watchlist vide</div>';return;}try{const c=new AbortController(),t=setTimeout(()=>c.abort(),8000);const r=await fetch(API+'/api/online/'+s,{signal:c.signal,headers:{..._authHeader()}});clearTimeout(t);const d=await r.json(),lp=d.players||[];const on=wl.filter(p=>lp.map(x=>x.toLowerCase()).includes(p.toLowerCase()));const off=wl.filter(p=>!lp.map(x=>x.toLowerCase()).includes(p.toLowerCase()));on.forEach(p=>{setLastSeen(p,s);loadSessionDurations(p);});el.innerHTML=[...on.map(p=>{const pred=predictDecoTime(p);return`<div class="wi" onclick="openPlayerPanel('${p}')"><img src="https://skins.nationsglory.fr/face/${encodeURIComponent(p)}/32" style="width:28px;height:28px;border-radius:4px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0" onerror="this.style.display='none'" alt=""><span style="font-family:var(--M);font-size:.62rem">${p}</span><div class="wis on"><div class="led on" style="width:5px;height:5px;flex-shrink:0"></div>EN LIGNE</div><span class="session-timer" data-player="${p}">${getSessionTime(p)||''}</span>${pred?`<span class="pred-badge ${pred.cls}">⏳ ${pred.text}</span>`:''}</div>`;}),...off.map(p=>{const seen=getLastSeenText(p);return`<div class="wi" onclick="openPlayerPanel('${p}')"><img src="https://skins.nationsglory.fr/face/${encodeURIComponent(p)}/32" style="width:28px;height:28px;border-radius:4px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0;opacity:${seen?.cls==='fresh'?'.6':'.3'}" onerror="this.style.display='none'" alt=""><span style="font-family:var(--M);font-size:.62rem;opacity:${seen?.cls==='fresh'?'.7':'.38'}">${p}</span><div class="wis off">${seen?`<span class="wi-seen ${seen.cls}">${seen.text}</span>`:'◯ Hors ligne'}</div></div>`;})]
.join('')||'<div class="empty">Aucune donnée</div>';}catch{el.innerHTML=`<div class="empty" style="color:var(--red)">Erreur</div>`;}}

async function loadStats(){
  const raw=$('st-input').value.trim();if(!raw)return;const p=rP(raw,oP);$('st-input').value=p;
  const res=$('st-result');res.innerHTML=`<div class="panel mb"><div class="pacc"></div><div class="ptop"></div><div class="ph"><span class="pt">◐ Analyse — ${p}</span></div><div class="pb">${ld()}</div></div>`;
  const[lR,pR,plR]=await Promise.allSettled([api('/api/checkall/'+encodeURIComponent(p)),api('/api/pronostic/'+encodeURIComponent(p)),api('/api/plages/'+encodeURIComponent(p))]);
  const loc=lR.status==='fulfilled'?lR.value:null,prn=pR.status==='fulfilled'?pR.value:null,plg=plR.status==='fulfilled'?plR.value:null;
  const srvs=loc?loc.servers:[];let h='';
  const skinUrl=`https://skins.nationsglory.fr/face/${encodeURIComponent(p)}/64`;
  const cbs=loc?.countries_by_server||{};
  h+=`<div class="sb"><div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.75rem"><img src="${skinUrl}" style="width:48px;height:48px;border-radius:6px;border:1px solid var(--b2);image-rendering:pixelated;flex-shrink:0" onerror="this.src='https://mc-heads.net/avatar/${encodeURIComponent(p)}/64'" alt=""><div><div class="sbt" style="margin:0 0 .25rem">◉ Localisation</div>${srvs.length?srvs.map(s=>`<span class="stag" style="margin-right:.3rem">${EMO[s]||''} ${s.toUpperCase()}</span>`).join(''):`<span style="font-family:var(--M);font-size:.55rem;color:var(--t3)">Hors ligne</span>`}</div></div>`;
  h+=SRV.map(s=>{
    const country=cbs[s]||'Wilderness';
    const isOnline=srvs.includes(s);
    const countryColor=country==='Wilderness'?'var(--t4)':'var(--blue-pale)';
    const countryIcon=country==='Wilderness'?'🌿':'🌍';
    return`<div class="ir"><span class="ik" style="${isOnline?'color:var(--grn)':''}">${EMO[s]||''} ${s.toUpperCase()}${isOnline?` <span style="font-size:.46rem;color:var(--grn)">● EN LIGNE</span>`:''}</span><span class="iv"><span style="display:inline-flex;align-items:center;gap:.35rem;background:${country==='Wilderness'?'rgba(255,255,255,.04)':'rgba(91,163,255,.1)'};border:1px solid ${country==='Wilderness'?'rgba(255,255,255,.08)':'rgba(91,163,255,.25)'};border-radius:4px;padding:.18rem .6rem;font-family:var(--M);font-size:.6rem;color:${countryColor}">${countryIcon} ${country}</span></span></div>`;
  }).join('');
  h+='</div>';
  h+=`<div class="sb"><div class="sbt">◐ Pronostic de connexion</div>`;
  if(prn?.pronostic?.length){h+=`<div style="font-family:var(--M);font-size:.48rem;color:var(--t3);margin-bottom:.35rem">Basé sur ${prn.total} connexions</div>`;h+=prn.pronostic.map(r=>`<div class="pr"><span class="pd">${r.day}</span><div class="pb3"><div class="pbf" style="width:${r.pct}%"></div></div><span class="pp">${r.pct}%</span><span class="pt3">${r.avg_h}h${String(r.avg_m).padStart(2,'0')}</span></div>`).join('');}
  else h+=`<div class="ir"><span class="ik">Données</span><span class="iv" style="color:var(--t3)">Insuffisantes (min. 3)</span></div>`;
  h+='</div>';
  h+=`<div class="sb"><div class="sbt">🕐 Heatmap horaire</div>`;
  if(plg?.heatmap){const hm=plg.heatmap,days=plg.days,mx=Math.max(...hm.flat(),1);h+=`<div style="overflow-x:auto"><table style="border-collapse:collapse;font-family:var(--M);font-size:.47rem;width:100%"><tr><td style="color:var(--t3);padding-right:.34rem;white-space:nowrap">H→</td>`;for(let i=0;i<24;i++)h+=`<td style="color:var(--t3);text-align:center;padding:0 1px;font-size:.4rem">${i}</td>`;h+='</tr>';days.forEach((day,di)=>{h+=`<tr><td style="color:var(--g);padding-right:.34rem;white-space:nowrap">${day}</td>`;hm[di].forEach(v=>{const intensity=v?(.04+v/mx*.82).toFixed(2):0;const bg=v?`rgba(0,56,184,${intensity})`:'rgba(2,5,12,.9)';const glow=v&&v/mx>.6?`box-shadow:0 0 4px rgba(0,56,184,${(v/mx*.3).toFixed(2)})`:'';h+=`<td style="width:14px;height:13px;background:${bg};border-radius:1px;padding:0;${glow}"></td>`;});h+='</tr>';});h+='</table></div>';}
  else h+=`<div class="ir"><span class="ik">Données</span><span class="iv" style="color:var(--t3)">Aucune donnée</span></div>`;
  h+='</div>';
  h+=`<div class="sb"><div class="sbt">◷ Historique</div>`;
  if(plg?.heatmap){const hm=plg.heatmap,days=plg.days,rows=[];days.forEach((day,di)=>{const tot=hm[di].reduce((a,v)=>a+v,0);if(tot)rows.push({day,total:tot,peakH:hm[di].indexOf(Math.max(...hm[di]))});});rows.sort((a,b)=>b.total-a.total);if(rows.length){h+=`<table class="tbl"><thead><tr><th>Jour</th><th>Connexions</th><th>Pic</th></tr></thead><tbody>`;h+=rows.map(r=>`<tr><td style="color:var(--g)">${r.day}</td><td style="color:var(--gb)">${r.total}</td><td style="color:var(--t3)">${r.peakH}h–${r.peakH+1}h</td></tr>`).join('');h+='</tbody></table>';}else h+=`<div class="ir"><span class="ik">Données</span><span class="iv" style="color:var(--t3)">Aucune connexion</span></div>`;}
  else h+=`<div class="ir"><span class="ik">Données</span><span class="iv" style="color:var(--t3)">Aucune donnée</span></div>`;
  h+='</div>';res.innerHTML=h;
}

let actx=null,_au=false;
function gCtx(){if(!actx)actx=new(window.AudioContext||window.webkitAudioContext)();if(actx.state==='suspended')actx.resume();return actx;}
function unlockAudio(){if(_au)return;_au=true;try{gCtx().resume();}catch(e){}}
document.addEventListener('click',unlockAudio,{once:true});
function toggleSound(){snd=!snd;localStorage.setItem('mg_sound',snd?'on':'off');const b=$('sound-btn');if(b){b.textContent=snd?'🔊 SON':'🔇 SON';b.style.color=snd?'var(--g)':'var(--t3)';}showToast(snd?'Son activé':'Son désactivé');}
function pT(f,t='sine',d=.08,v=.08,dl=0){if(!snd)return;try{const ctx=gCtx(),o=ctx.createOscillator(),g=ctx.createGain();o.connect(g);g.connect(ctx.destination);o.type=t;o.frequency.value=f;const ts=ctx.currentTime+dl;g.gain.setValueAtTime(0,ts);g.gain.linearRampToValueAtTime(v,ts+.01);g.gain.exponentialRampToValueAtTime(.001,ts+d);o.start(ts);o.stop(ts+d);}catch(e){}}
function sndNav(){pT(880,'sine',.06,.055);pT(1100,'sine',.05,.038,.04);}
function sndH(){pT(660,'sine',.04,.018);}
function sndF(){pT(523,'sine',.08,.09);pT(659,'sine',.08,.09,.07);}
function sndA(c){if(c){[0,.14,.28,.42,.56].forEach((dl,i)=>{pT(580+i*85,'square',.11,.28,dl);pT(1160+i*110,'sine',.07,.12,dl+.05);});}else{[0,.17,.34].forEach((dl,i)=>{pT(490-i*95,'sawtooth',.14,.28,dl);pT(245-i*48,'square',.11,.18,dl+.07);});}}
function spk(t){if(!snd)return;try{window.speechSynthesis.cancel();const m=new SpeechSynthesisUtterance(t);m.lang='fr-FR';m.rate=.88;m.pitch=1.25;m.volume=1;const voices=window.speechSynthesis.getVoices();const v=voices.find(v=>v.lang.startsWith('fr')&&v.name.toLowerCase().includes('female'))||voices.find(v=>v.lang.startsWith('fr')&&(v.name.includes('Amélie')||v.name.includes('Audrey')||v.name.includes('Marie')||v.name.includes('Julie')||v.name.includes('Léa')||v.name.includes('Google français')))||voices.find(v=>v.lang.startsWith('fr'));if(v)m.voice=v;window.speechSynthesis.speak(m);}catch(e){}}
if(window.speechSynthesis){window.speechSynthesis.getVoices();window.speechSynthesis.onvoiceschanged=()=>window.speechSynthesis.getVoices();}
function showPop(type,player,server){
  sndA(type==='connect');setTimeout(()=>spk(type==='connect'?`${player} vient de se connecter`:`${player} s'est déconnecté`),400);
  const pop=$('apop'),n=document.createElement('div');
  n.className='an'+(type==='disconnect'?' dc':'');
  n.innerHTML=`<div class="an-type">${type==='connect'?'🟢 Connexion détectée':'🔴 Déconnexion'}</div><div class="an-name">${player}</div><div class="an-meta"><span>${server.toUpperCase()}</span><span style="opacity:.3">·</span><span>${new Date().toLocaleTimeString('fr-FR')}</span></div><span class="an-x" onclick="this.parentElement.remove()">✕</span>`;
  n.onclick=e=>{if(e.target.classList.contains('an-x'))return;qCA(player);};
  pop.appendChild(n);
  setTimeout(()=>{n.style.animation='anOut .28s ease forwards';setTimeout(()=>n.remove(),280);},8000);
}

function pageFlash(){
  const f=document.getElementById('page-flash');
  f.classList.remove('go');void f.offsetWidth;
  f.classList.add('go');
}

const actHistory=[];const actLabels=[];
const MAX_ACT=30;
function pushActivity(total){
  const now=new Date();
  actHistory.push(total);actLabels.push(now.getHours()+':'+String(now.getMinutes()).padStart(2,'0'));
  if(actHistory.length>MAX_ACT){actHistory.shift();actLabels.shift();}
  drawActivityGraph();
}
function drawActivityGraph(){
  const c=document.getElementById('activity-graph');if(!c||actHistory.length<2)return;
  const W=c.parentElement.offsetWidth||400,H=80;
  c.width=W*devicePixelRatio;c.height=H*devicePixelRatio;
  const ctx=c.getContext('2d');ctx.scale(devicePixelRatio,devicePixelRatio);
  const mn=Math.min(...actHistory),mx=Math.max(...actHistory,1),range=mx-mn||1;
  const pad=8,gW=W-pad*2,gH=H-pad*2;
  for(let i=0;i<=4;i++){const y=pad+gH*(1-i/4);ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(W-pad,y);ctx.strokeStyle='rgba(0,56,184,.05)';ctx.lineWidth=1;ctx.stroke();}
  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,'rgba(0,56,184,.22)');grad.addColorStop(1,'rgba(0,56,184,.01)');
  ctx.beginPath();
  actHistory.forEach((v,i)=>{const x=pad+i/(actHistory.length-1)*gW,y=pad+gH*(1-(v-mn)/range);i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);});
  ctx.lineTo(pad+gW,H-pad);ctx.lineTo(pad,H-pad);ctx.closePath();ctx.fillStyle=grad;ctx.fill();
  ctx.beginPath();
  actHistory.forEach((v,i)=>{const x=pad+i/(actHistory.length-1)*gW,y=pad+gH*(1-(v-mn)/range);i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);});
  ctx.strokeStyle='rgba(26,111,255,.7)';ctx.lineWidth=1.5;ctx.lineJoin='round';ctx.stroke();
  const lx=pad+gW,ly=pad+gH*(1-(actHistory[actHistory.length-1]-mn)/range);
  ctx.beginPath();ctx.arc(lx,ly,3,0,Math.PI*2);ctx.fillStyle='#4d9fff';ctx.fill();
  ctx.beginPath();ctx.arc(lx,ly,6,0,Math.PI*2);ctx.fillStyle='rgba(26,111,255,.2)';ctx.fill();
  const lel=document.getElementById('graph-labels');
  if(lel&&actLabels.length>0){
    const step=Math.max(1,Math.floor(actLabels.length/5));
    const shown=actLabels.filter((_,i)=>i%step===0||i===actLabels.length-1);
    lel.textContent='';shown.forEach(l=>{const s=document.createElement('span');s.textContent=l;lel.appendChild(s);});
  }
}

// ── SSE — events temps réel ──────────────────────────────────────
let _sseSource=null,_sseRetry=0;
function _connectSSE(){
  if(_sseSource)_sseSource.close();
  const tok=sessionStorage.getItem('mg_token_v3');
  if(!tok)return;
  const url=`${API}/api/events?token=${encodeURIComponent(tok)}`;
  _sseSource=new EventSource(url);
  _sseSource.onopen=()=>{_sseRetry=0;console.log('[SSE] connecté');};
  _sseSource.onmessage=(e)=>{
    try{
      const d=JSON.parse(e.data);
      if(d.type==='ping')return;
      if(d.type==='connect'||d.type==='disconnect'){
        // Mettre à jour prev pour éviter doublon au prochain poll
        const k=d.player+'@'+d.server;
        prev[k]=d.type==='connect';
        pAlert(d.type,d.player,d.server);
      }
    }catch{}
  };
  _sseSource.onerror=()=>{
    _sseSource.close();_sseSource=null;
    const delay=Math.min(2000*Math.pow(2,_sseRetry++),30000);
    console.warn('[SSE] reconnexion dans',delay,'ms');
    setTimeout(_connectSSE,delay);
  };
}

let cdTotal=5,cdLeft=5;
function startCountdown(total=5){cdTotal=total;cdLeft=total;updateCountdown();}
function updateCountdown(){
  const txt=document.getElementById('cd-txt'),fill=document.getElementById('cd-fill');
  if(txt)txt.textContent=cdLeft+'s';
  if(fill)fill.style.width=(cdLeft/cdTotal*100)+'%';
}
function tickCountdown(){cdLeft=Math.max(0,cdLeft-1);updateCountdown();}

const lastSeen={};
function setLastSeen(player,server){lastSeen[player]={ts:Date.now(),server};}
function getLastSeenText(player){
  const s=lastSeen[player];if(!s)return null;
  const sec=Math.floor((Date.now()-s.ts)/1000);
  if(sec<60)return{text:`vu il y a ${sec}s`,cls:'fresh'};
  if(sec<3600)return{text:`vu il y a ${Math.floor(sec/60)}min`,cls:'recent'};
  return{text:`vu il y a ${Math.floor(sec/3600)}h`,cls:''};
}

let notifGranted=false;
async function requestNotifPerms(){
  if(!('Notification' in window))return;
  if(Notification.permission==='granted'){notifGranted=true;return;}
  if(Notification.permission!=='denied'){const p=await Notification.requestPermission();notifGranted=p==='granted';}
}
function sendBrowserNotif(type,player,server){
  if(!notifGranted||document.visibilityState==='visible')return;
  const icon='https://nationsglory.fr/favicon.ico';
  const title=type==='connect'?`🟢 ${player} connecté`:`🔴 ${player} déconnecté`;
  const body=`Serveur : ${server.toUpperCase()} · ${new Date().toLocaleTimeString('fr-FR')}`;
  try{const n=new Notification(title,{body,icon,silent:false});n.onclick=()=>{window.focus();n.close();};}catch(e){}
}

let ppOpen=false;
async function openPlayerPanel(player){
  const panel=document.getElementById('player-panel');
  const overlay=document.getElementById('pp-overlay');
  const nameEl=document.getElementById('pp-name');
  const body=document.getElementById('pp-body');
  nameEl.textContent=player;
  body.innerHTML=`<div class="pp-loading">◌ Chargement du profil...</div>`;
  panel.classList.add('open');overlay.classList.add('open');
  document.body.style.overflow='hidden';
  ppOpen=true;
  const[caR,prR,plR]=await Promise.allSettled([
    api('/api/checkall/'+encodeURIComponent(player)),
    api('/api/pronostic/'+encodeURIComponent(player)),
    api('/api/plages/'+encodeURIComponent(player))
  ]);
  const ca=caR.status==='fulfilled'?caR.value:null;
  const pr=prR.status==='fulfilled'?prR.value:null;
  const pl=plR.status==='fulfilled'?plR.value:null;
  const seen=getLastSeenText(player);
  const online=ca&&ca.servers.length>0;
  const profileUrl=`https://nationsglory.fr/profile/${encodeURIComponent(player)}`;

  const cbs=ca?.countries_by_server||{};

  let h='';
  h+=`<div class="pp-info-row">
    <div class="pp-avatar"><img src="https://skins.nationsglory.fr/face/${encodeURIComponent(player)}/64" onerror="this.src='https://mc-heads.net/avatar/${encodeURIComponent(player)}/64'" alt=""></div>
    <div class="pp-info-meta">
      <div class="pp-meta-line">${WL.includes(player)?'🎯 Dans la watchlist LIME':''}${WLM.includes(player)?' 🟤 Dans la watchlist MOCHA':''}</div>
      <div class="pp-status ${online?'on':'off'}">
        <div class="led ${online?'on':'off'}" style="width:5px;height:5px;flex-shrink:0"></div>
        ${online?ca.servers.map(s=>{const ctry=cbs[s];const hasCtry=ctry&&ctry!=='Wilderness';return`${EMO[s]} ${s.toUpperCase()}${hasCtry?` <span style="font-size:.5rem;color:var(--blue-pale)">🌍 ${ctry}</span>`:''}`; }).join(' · '):'Hors ligne'}
      </div>
      ${online?(()=>{const pred=predictDecoTime(player);return pred?`<div class="pred-badge ${pred.cls}" style="margin-top:.3rem">⏳ ${pred.text}</div>`:''})():''}
      ${seen?`<div class="pp-meta-line" style="margin-top:.28rem">${seen.text}</div>`:''}
    </div>
  </div>
  <div style="margin:.5rem 0 .6rem;display:flex;flex-direction:column;gap:.2rem">
    ${SRV.map(s=>{
      const country=cbs[s]||'Wilderness';
      const isOnline=online&&ca.servers.includes(s);
      const isWild=country==='Wilderness';
      return`<div style="display:flex;align-items:center;justify-content:space-between;padding:.22rem .5rem;border-radius:4px;background:${isOnline?'rgba(0,232,122,.05)':''};border:1px solid ${isOnline?'rgba(0,232,122,.15)':'transparent'}">
        <span style="font-family:var(--M);font-size:.58rem;color:${isOnline?'var(--grn)':'var(--t3)'}">${EMO[s]||''} ${s.toUpperCase()}${isOnline?' <span style="font-size:.44rem">●</span>':''}</span>
        <span style="font-family:var(--M);font-size:.58rem;color:${isWild?'var(--t4)':'var(--blue-pale)'}${isWild?';opacity:.6':''}">${isWild?'🌿':'🌍'} ${country}</span>
      </div>`;
    }).join('')}
  </div>`;
  h+=`<a class="pp-ng-link" href="${profileUrl}" target="_blank" rel="noopener">↗ Profil NationsGlory</a>`;
  h+=`<div class="pp-section"><div class="pp-sec-title">◐ Pronostic de connexion</div>`;
  if(pr?.pronostic?.length){
    h+=`<div style="font-family:var(--M);font-size:.46rem;color:var(--t3);margin-bottom:.3rem">Basé sur ${pr.total} connexions</div>`;
    h+=pr.pronostic.map(r=>`<div class="pr" style="padding:.28rem 0"><span class="pd">${r.day}</span><div class="pb3"><div class="pbf" style="width:${r.pct}%"></div></div><span class="pp" style="min-width:32px;color:var(--t3);text-align:right;font-size:.52rem">${r.pct}%</span><span style="min-width:44px;color:var(--t1);text-align:right;font-family:var(--M);font-size:.6rem">${r.avg_h}h${String(r.avg_m).padStart(2,'0')}</span></div>`).join('');
  }else h+=`<div style="font-family:var(--M);font-size:.55rem;color:var(--t3)">Pas assez de données</div>`;
  h+='</div>';
  if(pl?.heatmap){
    const hm=pl.heatmap,days=pl.days,mxH=Math.max(...hm.flat(),1);
    h+=`<div class="pp-section"><div class="pp-sec-title">🕐 Heatmap horaire</div><div style="overflow-x:auto"><table class="pp-heatmap" style="border-collapse:collapse;font-family:var(--M);font-size:.44rem"><tr><td style="color:var(--t3);padding-right:.3rem;font-size:.38rem">H→</td>`;
    for(let i=0;i<24;i+=2)h+=`<td colspan="2" style="color:var(--t3);text-align:center;padding:0 1px;font-size:.38rem">${i}</td>`;
    h+='</tr>';
    days.forEach((day,di)=>{h+=`<tr><td style="color:var(--g);padding-right:.3rem;white-space:nowrap;padding-top:2px;font-size:.44rem">${day}</td>`;hm[di].forEach(v=>{const bg=v?`rgba(0,56,184,${(.04+v/mxH*.82).toFixed(2)})`:'rgba(2,5,12,.9)';h+=`<td style="width:13px;height:11px;background:${bg};border-radius:1px;padding:0"></td>`;});h+='</tr>';});
    h+='</table></div></div>';
  }
  body.innerHTML=h;
}
function closePlayerPanel(){
  document.getElementById('player-panel').classList.remove('open');
  document.getElementById('pp-overlay').classList.remove('open');
  document.body.style.overflow='';ppOpen=false;
}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&ppOpen)closePlayerPanel();});

(()=>{
  const c=document.getElementById('matrix-canvas');
  if(!c)return;
  const ctx=c.getContext('2d');
  const resize=()=>{c.width=window.innerWidth;c.height=window.innerHeight;};
  resize();window.addEventListener('resize',resize);
  const chars='アイウエオカキクケコサシスセソタチツテトナニヌネノ0123456789ABCDEF◈⊕◉◎';
  const fs=14;let cols=Math.floor(c.width/fs);
  let drops=Array(cols).fill(1);
  const draw=()=>{
    ctx.fillStyle='rgba(1,4,8,.08)';ctx.fillRect(0,0,c.width,c.height);
    cols=Math.floor(c.width/fs);if(drops.length!==cols)drops=Array(cols).fill(1);
    ctx.font=fs+'px JetBrains Mono,monospace';
    drops.forEach((y,i)=>{
      const ch=chars[Math.floor(Math.random()*chars.length)];
      const bright=Math.random()>.92;
      ctx.fillStyle=bright?'#4d9fff':`rgba(0,80,216,${Math.random()*.6+.15})`;
      ctx.fillText(ch,i*fs,y*fs);
      if(y*fs>c.height&&Math.random()>.975)drops[i]=0;
      drops[i]++;
    });
  };
  const interval=setInterval(draw,45);
  const obs=new MutationObserver(()=>{
    const ldr=document.getElementById('ldr');
    if(ldr&&ldr.style.display==='none'){clearInterval(interval);obs.disconnect();}
  });
  const ldr=document.getElementById('ldr');
  if(ldr)obs.observe(ldr,{attributes:true,attributeFilter:['style']});
})();

function updateWeather(onlineCount){
  const icon=document.getElementById('weather-icon');
  const label=document.getElementById('weather-label');
  if(!icon||!label)return;
  const wl=WL.length+WLM.length;
  const ratio=wl>0?onlineCount/wl:0;
  let ic,lb,cls;
  if(onlineCount===0){ic='🌙';lb='CALME';cls='calm';}
  else if(ratio<.3){ic='🌤';lb='ACTIVITÉ';cls='active';}
  else if(ratio<.6){ic='⚡';lb='AGITÉ';cls='hot';}
  else{ic='🔥';lb='CRITIQUE';cls='critical';}
  if(icon.textContent!==ic){icon.style.transform='scale(1.4)';icon.textContent=ic;setTimeout(()=>icon.style.transform='',300);}
  label.textContent=lb;
  label.className='weather-label '+cls;
}

const sessionStart={};
function startSession(player){if(!sessionStart[player])sessionStart[player]=Date.now();}
function getSessionTime(player){
  if(!sessionStart[player])return null;
  const sec=Math.floor((Date.now()-sessionStart[player])/1000);
  if(sec<60)return sec+'s';
  if(sec<3600)return Math.floor(sec/60)+'min '+String(sec%60).padStart(2,'0')+'s';
  return Math.floor(sec/3600)+'h '+String(Math.floor(sec%3600/60)).padStart(2,'0')+'min';
}
setInterval(()=>{
  document.querySelectorAll('.session-timer[data-player]').forEach(el=>{
    const t=getSessionTime(el.dataset.player);
    if(t)el.textContent=t;
  });
},1000);

function predictDecoTime(player){
  const s=sessionStart[player];
  if(!s)return null;
  const elapsed=Math.floor((Date.now()-s)/1000/60);
  const durs=sessionDurations[player]||[];
  if(durs.length<2)return null;
  const avg=durs.reduce((a,b)=>a+b,0)/durs.length;
  const remaining=Math.round(avg-elapsed);
  if(remaining<=0)return{text:'déco imminente',cls:'verysoon'};
  if(remaining<=10)return{text:`~${remaining}min restantes`,cls:'verysoon'};
  if(remaining<=30)return{text:`~${remaining}min restantes`,cls:'soon'};
  return{text:`~${remaining}min restantes`,cls:''};
}

const sessionDurations={};
function endSession(player){
  if(sessionStart[player]){
    const dur=Math.floor((Date.now()-sessionStart[player])/1000/60);
    if(dur>1){
      if(!sessionDurations[player])sessionDurations[player]=[];
      sessionDurations[player].push(dur);
      if(sessionDurations[player].length>10)sessionDurations[player].shift();
    }
  }
  delete sessionStart[player];
}

async function loadSessionDurations(player){
  try{
    const d=await api('/api/plages/'+encodeURIComponent(player));
    if(!d||!d.heatmap)return;
    const hm=d.heatmap;
    let totalSessions=0,totalDur=0;
    hm.forEach(dayRow=>{
      let streak=0,maxStreak=0;
      dayRow.forEach(v=>{if(v>0){streak++;maxStreak=Math.max(maxStreak,streak);}else{streak=0;}});
      if(maxStreak>0){totalSessions++;totalDur+=maxStreak*60;}
    });
    if(totalSessions>0&&!sessionDurations[player]?.length){
      const avgMin=Math.round(totalDur/totalSessions);
      sessionDurations[player]=[avgMin,avgMin];
    }
  }catch(e){}
}

let cwWatches=[];
let cwCountries={};

async function cwSave(){localStorage.setItem('mg_cw',JSON.stringify(cwWatches));}

async function cwLoadCountries(){
  const s=$('cw-srv').value;if(!s)return;
  $('cw-suggest').innerHTML=`<span style="font-family:var(--M);font-size:.5rem;color:var(--t3)">Chargement...</span>`;
  try{
    cwCountries[s]=await getCountries(s);
    cwFilterCountries();
  }catch{$('cw-suggest').innerHTML='';}
}

function cwFilterCountries(){
  const s=$('cw-srv').value,v=$('cw-country').value.trim().toLowerCase();
  const p=cwCountries[s]||[];
  const f=v?p.filter(x=>x.toLowerCase().includes(v)):p;
  $('cw-suggest').innerHTML=f.slice(0,60).map(x=>`<span class="tag" onclick="$('cw-country').value='${x.replace(/'/g,"\'")}';$('cw-acl').style.display='none';cwFilterCountries()">${x}</span>`).join('');
  const acl=$('cw-acl');
  if(v&&f.length){
    acl.innerHTML=f.slice(0,8).map(x=>`<div class="aci" onmousedown="$('cw-country').value='${x.replace(/'/g,"\'")}';acl.style.display='none'">${x}</div>`).join('');
    acl.style.display='block';
  }else acl.style.display='none';
}

function cwAdd(){
  const s=$('cw-srv').value,country=$('cw-country').value.trim();
  if(!s||!country)return showToast('Sélectionne un serveur et un pays');
  const exists=cwWatches.find(w=>w.server===s&&w.country.toLowerCase()===country.toLowerCase());
  if(exists)return showToast('Déjà surveillé !');
  cwWatches.push({server:s,country,threshold:2,online:0,members:[],alertFired:false});
  cwSave();cwRender();cwRefreshAll();
  $('cw-country').value='';
  showToast(`${country} (${s.toUpperCase()}) ajouté`);
}

async function cwRemove(idx){
  const w=cwWatches[idx];if(!w)return;
  try{await apiP('/api/country_watches/remove',{server:w.server,country:w.country});}catch(e){}
  cwWatches.splice(idx,1);cwSave();cwRender();
  showToast('Surveillance supprimée');
}

async function cwRefreshOne(idx){
  const w=cwWatches[idx];if(!w)return;
  try{
    const d=await api(`/api/check/${w.server}/${encodeURIComponent(w.country)}`);
    const members=d.servers?.[w.server]||[];
    const online=members.length;
    const wasAlert=w.alertFired;
    w.online=online;w.members=members;w.hasNonRecruit=false;w.alertFired=false;w.leader=d.leader||'';
    if(online>=2){const _nr=await hasNonRecruit(members,w.server);w.hasNonRecruit=_nr;w.alertFired=_nr;}
    if(w.alertFired&&!wasAlert){
      showPop('connect',`⚔ ${w.country}`,`${online} membres · assaut possible · ${w.server.toUpperCase()}`);
      sendBrowserNotif('connect',`🚨 Assaut possible sur ${w.country} — ${online} membres connectés`,w.server);
      sndA(true);
      showToast(`🚨 ASSAUT POSSIBLE — ${w.country} · ${online} membres sur ${w.server.toUpperCase()}`);
    }
    cwSave();
  }catch(e){w.online=-1;}
  cwRender();
}

async function cwRefreshAll(){await Promise.all(cwWatches.map((_,i)=>cwRefreshOne(i)));}

function cwRender(){
  const el=$('cw-list');if(!el)return;
  if(!cwWatches.length){el.innerHTML='<div class="cw-empty">Aucun pays surveillé — ajoutez-en un ci-dessus</div>';return;}
  el.innerHTML=cwWatches.map((w,i)=>{
    const alert=w.alertFired;const recruitOnly=w.online>=2&&!w.hasNonRecruit&&!alert;
    const cnt=w.online<0?'?':w.online;
    return`<div class="cw-item ${alert?'alert':recruitOnly?'recruit-only':''}" style="margin-bottom:.5rem">
      <div class="cw-count ${alert?'danger':''}">${cnt}</div>
      <div class="cw-info">
        <div class="cw-name">${w.country}</div>${w.leader?`<div style="display:flex;align-items:center;gap:.4rem;margin-top:.2rem;font-family:var(--M);font-size:.52rem;color:var(--t3)"><img src="https://skins.nationsglory.fr/face/${w.leader}/16" style="width:16px;height:16px;border-radius:2px;image-rendering:pixelated" onerror="this.style.display='none'"> 👑 ${w.leader}</div>`:''}
        <div class="cw-meta">${EMO[w.server]||''} ${w.server.toUpperCase()} · assaut possible si ≥ 2 connectés</div>
        ${w.members.length?`<div class="cw-members">${w.members.slice(0,8).map(p=>{const k=p+'@'+w.server;const g=gradeCache[k]?.rank||'?';const col=g&&g!=='recruit'&&g!=='?'?'var(--grn)':g==='recruit'?'var(--red)':'var(--t3)';return`<span style="color:${col}">${p} <span style="font-size:.4rem;opacity:.7">[${g}]</span></span>`;}).join(', ')}${w.members.length>8?` <span style="color:var(--t3)">+${w.members.length-8}</span>`:''}</div>`:''}
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:.35rem">
        <span class="cw-status ${alert?'':'ok'}">${alert?'🚨 ASSAUT POSSIBLE':'◯ PAS ASSEZ'}</span>
        <button class="btn btn-r" style="padding:.08rem .35rem;font-size:.46rem" onclick="cwRemove(${i})">✕</button>
      </div>
    </div>`;
  }).join('');
}

setInterval(cwRefreshAll, 30000);

const gradeCache={};
async function getPlayerGrade(player,server){
  const key=player+'@'+server;
  if(gradeCache[key]&&Date.now()-gradeCache[key].ts<120000)return gradeCache[key].rank;
  try{
    const r=await fetch(`${API}/api/grade/${encodeURIComponent(player)}/${server}`,{headers:{..._authHeader()}});
    if(!r.ok)return null;
    const d=await r.json();
    gradeCache[key]={rank:d.rank,ts:Date.now()};
    return d.rank;
  }catch{return null;}
}
async function hasNonRecruit(members,server){
  const results=await Promise.allSettled(members.slice(0,12).map(p=>getPlayerGrade(p,server)));
  return results.some(r=>r.status==='fulfilled'&&r.value&&r.value!==''&&r.value!=='recruit');
}

async function init(){
  const b=$('sound-btn');if(b&&!snd){b.textContent='🔇 SON';b.style.color='var(--t3)';}
  if(_authed()) requestNotifPerms();
  api('/api/country_watches').then(d=>{cwWatches=d.watches||[];const stored=JSON.parse(localStorage.getItem('mg_cw')||'[]');stored.forEach(w=>{if(!cwWatches.find(x=>x.server===w.server&&x.country===w.country))cwWatches.push(w);});cwRender();}).catch(()=>{cwWatches=JSON.parse(localStorage.getItem('mg_cw')||'[]');cwRender();});
  rHist();const ok=await chkAPI();$('scan-led').className=ok?'led on':'led off';
  if(ok){
    await loadWL();await loadWLM();loadKP();await loadDash();
    startCountdown(5);
    setInterval(tickCountdown,1000);
    setInterval(async()=>{await loadWL();await loadDash();},5000);
    _connectSSE();
  }
}
init();

function rmCalc() {
  const power   = parseFloat(document.getElementById('rm-power')?.value)   || 0;
  let   warzone = parseFloat(document.getElementById('rm-warzone')?.value)  || 0;
  const claims  = parseFloat(document.getElementById('rm-claims')?.value)   || 0;

  if (power <= 0) {
    showToast('⚠ Entre un power total valide');
    return;
  }

  if (warzone > power) warzone = power;

  const factor      = Math.pow(0.96, 18);
  const soumis      = power - warzone;
  const powerAfter  = Math.round(soumis * factor);
  const powerLost   = power - powerAfter;          
  const claimsAfter = Math.max(0, claims - 8);

  const results = document.getElementById('rm-results');
  if (results) results.style.display = 'block';

  const elLost   = document.getElementById('rm-lost');
  const elRemain = document.getElementById('rm-remain');
  const elClaims = document.getElementById('rm-claims-out');
  const elAlert  = document.getElementById('rm-alert');

  if (elLost)   { elLost.textContent   = powerLost.toLocaleString('fr-FR');   elLost.style.animation='none'; setTimeout(()=>{elLost.style.animation='bump .35s cubic-bezier(.34,1.56,.64,1)';},10); }
  if (elRemain) { elRemain.textContent = powerAfter.toLocaleString('fr-FR');  elRemain.style.animation='none'; setTimeout(()=>{elRemain.style.animation='bump .35s cubic-bezier(.34,1.56,.64,1)';},10); }
  if (elClaims) { elClaims.textContent = claimsAfter.toLocaleString('fr-FR'); elClaims.style.animation='none'; setTimeout(()=>{elClaims.style.animation='bump .35s cubic-bezier(.34,1.56,.64,1)';},10); }

  if (elAlert) {
    elAlert.style.display = 'block';
    const diff = powerAfter - claimsAfter;
    const isSafe = powerAfter >= claimsAfter;

    if (isSafe) {
      elAlert.style.background = 'rgba(0,240,122,.06)';
      elAlert.style.border     = '1px solid rgba(0,240,122,.25)';
      elAlert.style.color      = '#00f07a';
      elAlert.innerHTML = `
        ✅ &nbsp;<strong>SAFE</strong> — Le pays survit au Red Matter<br>
        <span style="opacity:.7">Power restant : <strong>${powerAfter.toLocaleString('fr-FR')}</strong> · Claims restants : <strong>${claimsAfter.toLocaleString('fr-FR')}</strong> · Avance : <strong>+${diff.toLocaleString('fr-FR')}</strong> power</span>
      `;
    } else {
      elAlert.style.background = 'rgba(255,24,64,.06)';
      elAlert.style.border     = '1px solid rgba(255,24,64,.25)';
      elAlert.style.color      = '#ff1840';
      const manquant = Math.abs(diff);
      elAlert.innerHTML = `
        ☢ &nbsp;<strong>SOUS-POWER</strong> — Le pays sera en sous-power !<br>
        <span style="opacity:.7">Power restant : <strong>${powerAfter.toLocaleString('fr-FR')}</strong> · Claims restants : <strong>${claimsAfter.toLocaleString('fr-FR')}</strong> · Il manque : <strong>${manquant.toLocaleString('fr-FR')}</strong> power</span>
      `;
    }
  }

  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.frequency.setValueAtTime(80, ctx.currentTime);
    o.frequency.exponentialRampToValueAtTime(40, ctx.currentTime + 0.3);
    g.gain.setValueAtTime(0.3, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
    o.start(ctx.currentTime); o.stop(ctx.currentTime + 0.4);
  } catch(e) {}
}

let playerNotes={};
let noteSelectedTag='';

async function notesLoadFromAPI(){
  try{const d=await api('/api/notes');playerNotes=d.notes||{};}catch{}
}
function noteSaveStore(){}

function noteSelectTag(btn){
  document.querySelectorAll('.note-tag-btn').forEach(b=>b.style.outline='none');
  if(noteSelectedTag===btn.dataset.tag){noteSelectedTag='';return;}
  noteSelectedTag=btn.dataset.tag;
  btn.style.outline='2px solid currentColor';
}

function noteLoadExisting(){
  const p=document.getElementById('note-player')?.value.trim();
  if(!p||!playerNotes[p]){
    document.getElementById('note-text').value='';
    noteSelectedTag='';
    document.querySelectorAll('.note-tag-btn').forEach(b=>b.style.outline='none');
    return;
  }
  const n=playerNotes[p];
  document.getElementById('note-text').value=n.text||'';
  noteSelectedTag=n.tag||'';
  document.querySelectorAll('.note-tag-btn').forEach(b=>{
    b.style.outline=b.dataset.tag===noteSelectedTag?'2px solid currentColor':'none';
  });
}

async function noteSave(){
  const p=document.getElementById('note-player')?.value.trim();
  const txt=document.getElementById('note-text')?.value.trim();
  if(!p)return showToast('⚠ Entre un pseudo');
  if(!txt&&!noteSelectedTag)return showToast('⚠ Ajoute une note ou une étiquette');
  try{
    await apiP('/api/notes/save',{player:p,text:txt,tag:noteSelectedTag});
    playerNotes[p]={text:txt,tag:noteSelectedTag,updated:new Date().toLocaleString('fr-FR')};
    renderNotes();
    const fb=document.getElementById('note-feedback');
    if(fb){fb.textContent='✓ Note sauvegardée';fb.style.opacity='1';setTimeout(()=>fb.style.opacity='0',2000);}
    showToast(`Note sauvegardée — ${p}`);
  }catch(e){showToast('❌ Erreur sauvegarde');}
}

async function noteDelete(){
  const p=document.getElementById('note-player')?.value.trim();
  if(!p||!playerNotes[p])return showToast('Aucune note pour ce joueur');
  try{
    await apiP('/api/notes/delete',{player:p});
    delete playerNotes[p];
    document.getElementById('note-text').value='';
    noteSelectedTag='';
    document.querySelectorAll('.note-tag-btn').forEach(b=>b.style.outline='none');
    renderNotes();
    showToast(`Note supprimée — ${p}`);
  }catch(e){showToast('❌ Erreur suppression');}
}

const NOTE_TAG_STYLES={
  'ennemi':{color:'var(--red)',bg:'rgba(255,51,85,.12)',label:'⚔ Ennemi'},
  'allié':{color:'var(--grn)',bg:'rgba(0,232,122,.1)',label:'🤝 Allié'},
  'neutre':{color:'var(--blue-pale)',bg:'rgba(91,163,255,.1)',label:'◯ Neutre'},
  'espion':{color:'var(--org)',bg:'rgba(255,153,0,.1)',label:'🕵 Espion'},
  'vip':{color:'#ffd700',bg:'rgba(255,215,0,.08)',label:'⭐ VIP'},
};

function getNoteTagHtml(tag){
  const s=NOTE_TAG_STYLES[tag];if(!s)return'';
  return`<span style="font-family:var(--M);font-size:.5rem;padding:.12rem .45rem;border-radius:3px;background:${s.bg};color:${s.color};letter-spacing:.08em">${s.label}</span>`;
}

function renderNotes(){
  const el=document.getElementById('notes-list');if(!el)return;
  const search=document.getElementById('note-search')?.value.trim().toLowerCase()||'';
  let entries=Object.entries(playerNotes);
  if(search)entries=entries.filter(([p,n])=>p.toLowerCase().includes(search)||(n.text||'').toLowerCase().includes(search));
  if(!entries.length){el.innerHTML='<div class="empty">Aucune note trouvée</div>';return;}
  entries.sort((a,b)=>a[0].toLowerCase().localeCompare(b[0].toLowerCase()));
  el.innerHTML=entries.map(([player,n])=>{
    const s=n.tag?NOTE_TAG_STYLES[n.tag]:null;
    return`<div style="padding:.65rem .85rem;border-bottom:1px solid var(--b1);display:flex;align-items:flex-start;gap:.7rem;cursor:pointer;transition:background .1s" onmouseenter="this.style.background='var(--bg2)'" onmouseleave="this.style.background=''" onclick="noteEditPlayer('${player}')">
      <img src="https://mc-heads.net/avatar/${encodeURIComponent(player)}/28" style="width:28px;height:28px;border-radius:3px;flex-shrink:0" onerror="this.style.display='none'" alt="">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.2rem;flex-wrap:wrap">
          <span style="font-family:var(--M);font-size:.65rem;color:var(--t1)">${player}</span>
          ${n.tag?getNoteTagHtml(n.tag):''}
        </div>
        ${n.text?`<div style="font-family:var(--M);font-size:.58rem;color:var(--t3);line-height:1.5;white-space:pre-wrap">${n.text.substring(0,120)}${n.text.length>120?'…':''}</div>`:''}
        <div style="font-family:var(--M);font-size:.46rem;color:var(--t4);margin-top:.2rem">${n.updated||''}</div>
      </div>
      <button class="btn btn-r" style="padding:.07rem .3rem;font-size:.46rem;flex-shrink:0" onclick="event.stopPropagation();noteDeleteDirect('${player}')">✕</button>
    </div>`;
  }).join('');
}

function noteEditPlayer(player){
  document.getElementById('note-player').value=player;
  noteLoadExisting();
  document.getElementById('note-player').scrollIntoView({behavior:'smooth',block:'center'});
}

async function noteDeleteDirect(player){
  try{
    await apiP('/api/notes/delete',{player});
    delete playerNotes[player];renderNotes();showToast(`Note supprimée — ${player}`);
  }catch{showToast('❌ Erreur suppression');}
}

const _origOpenPP=openPlayerPanel;
window.openPlayerPanel=async function(player){
  await _origOpenPP(player);
  
  const body=document.getElementById('pp-body');
  if(!body)return;
  const n=playerNotes[player];
  const noteSection=document.createElement('div');
  noteSection.className='pp-section';
  noteSection.id='pp-note-section';
  const s=n?.tag?NOTE_TAG_STYLES[n.tag]:null;
  noteSection.innerHTML=`<div class="pp-sec-title">📝 Note personnelle</div>
    <div style="background:var(--bg2);border:1px solid var(--b1);border-radius:var(--r);padding:.7rem .9rem;margin-top:.4rem">
      ${n?.tag?`<div style="margin-bottom:.4rem">${getNoteTagHtml(n.tag)}</div>`:''}
      ${n?.text?`<div style="font-family:var(--M);font-size:.6rem;color:var(--t2);line-height:1.6;white-space:pre-wrap">${n.text}</div>`:'<div style="font-family:var(--M);font-size:.58rem;color:var(--t4)">Aucune note — <span style="color:var(--blue-pale);cursor:pointer" onclick="closePlayerPanel();setTimeout(()=>{nav(\'notes\',document.querySelector(\'.tab:nth-child(10)\'));document.getElementById(\'note-player\').value=\''+player+'\';noteLoadExisting();},200)">Ajouter une note ↗</span></div>'}
      ${n?.updated?`<div style="font-family:var(--M);font-size:.44rem;color:var(--t4);margin-top:.35rem">Modifié : ${n.updated}</div>`:''}
    </div>`;
  body.appendChild(noteSection);
};

let carteData={};

async function loadCarte(){
  const grid=document.getElementById('carte-grid');
  const ranking=document.getElementById('carte-ranking');
  if(grid)grid.innerHTML='<div class="ld" style="grid-column:1/-1">Chargement<span class="ldd"><span>.</span><span>.</span><span>.</span></span></div>';
  try{
    const all=await api('/api/online_all');
    carteData=all;
    renderCarte(all);
  }catch(e){
    if(grid)grid.innerHTML=`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;
  }
}

function getCarteColor(cnt,max){
  if(cnt===0)return{bg:'rgba(1,10,26,.8)',border:'rgba(0,56,184,.12)',text:'var(--t4)',glow:''};
  const r=max>0?cnt/max:0;
  if(r<.2)return{bg:'rgba(0,40,120,.25)',border:'rgba(0,80,216,.3)',text:'var(--blue-pale)',glow:'0 0 8px rgba(0,80,216,.15)'};
  if(r<.45)return{bg:'rgba(0,60,160,.35)',border:'rgba(26,111,255,.5)',text:'#7ec8ff',glow:'0 0 12px rgba(26,111,255,.2)'};
  if(r<.7)return{bg:'rgba(255,120,0,.12)',border:'rgba(255,120,0,.4)',text:'var(--org)',glow:'0 0 14px rgba(255,120,0,.2)'};
  return{bg:'rgba(255,30,60,.12)',border:'rgba(255,30,60,.5)',text:'var(--red)',glow:'0 0 18px rgba(255,30,60,.25)'};
}

function renderCarte(all){
  const grid=document.getElementById('carte-grid');
  const ranking=document.getElementById('carte-ranking');
  const totalEl=document.getElementById('carte-total-txt');
  if(!grid)return;
  const counts=SRV.map(s=>({s,cnt:(all[s]||[]).length,bug:BUG(s)}));
  const max=Math.max(...counts.map(x=>x.cnt),1);
  let total=counts.reduce((a,x)=>a+x.cnt,0);
  if(totalEl)totalEl.textContent=`${total} joueurs connectés en tout`;

  grid.innerHTML=counts.map(({s,cnt,bug})=>{
    const c=getCarteColor(cnt,max);
    const wlOn=(WL.concat(WLM)).filter(p=>(all[s]||[]).map(x=>x.toLowerCase()).includes(p.toLowerCase()));
    const pct=max>0?Math.round(cnt/max*100):0;
    return`<div onclick="gOL('${s}')" style="background:${c.bg};border:1px solid ${c.border};border-radius:var(--r);padding:1rem 1.1rem;cursor:pointer;transition:all .2s;position:relative;overflow:hidden;box-shadow:${c.glow}" onmouseenter="this.style.transform='translateY(-2px)'" onmouseleave="this.style.transform=''">
      <div style="position:absolute;bottom:0;left:0;width:${pct}%;height:3px;background:${c.border};transition:width .4s;opacity:.7"></div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem">
        <span style="font-family:var(--D);font-size:1.1rem;letter-spacing:.2em;color:${c.text}">${s.toUpperCase()}</span>
        <span style="font-size:.9rem">${EMO[s]}</span>
      </div>
      <div style="font-family:var(--D);font-size:2.4rem;color:${c.text};line-height:1;text-shadow:${c.glow}">${cnt}</div>
      <div style="font-family:var(--M);font-size:.5rem;color:var(--t4);letter-spacing:.12em;margin-top:.25rem">${bug?'⚠ INSTABLE':'EN LIGNE'}</div>
      ${wlOn.length?`<div style="margin-top:.4rem;font-family:var(--M);font-size:.48rem;color:var(--grn);letter-spacing:.06em">🎯 ${wlOn.join(', ')}</div>`:''}
    </div>`;
  }).join('');

  const sorted=[...counts].sort((a,b)=>b.cnt-a.cnt);
  if(ranking){
    ranking.innerHTML=`<table class="tbl"><thead><tr><th>#</th><th>Serveur</th><th>Joueurs</th><th>Part</th><th>Cibles</th></tr></thead><tbody>${
      sorted.map((x,i)=>{
        const c=getCarteColor(x.cnt,max);
        const pct2=total>0?Math.round(x.cnt/total*100):0;
        const wl2=(WL.concat(WLM)).filter(p=>(all[x.s]||[]).map(v=>v.toLowerCase()).includes(p.toLowerCase()));
        const medal=i===0?'🥇':i===1?'🥈':i===2?'🥉':'';
        return`<tr onclick="gOL('${x.s}')">
          <td style="color:var(--t3)">${medal||'#'+(i+1)}</td>
          <td><span style="color:${c.text};font-family:var(--D);letter-spacing:.15em">${x.s.toUpperCase()}</span>${x.bug?'<span style="color:var(--org);font-size:.46rem"> ⚠</span>':''}</td>
          <td style="color:var(--t1);font-family:var(--D);font-size:1.1rem">${x.cnt}</td>
          <td><div style="display:flex;align-items:center;gap:.4rem"><div style="width:60px;height:4px;background:var(--bg3);border-radius:2px;overflow:hidden"><div style="width:${pct2}%;height:100%;background:${c.border}"></div></div><span style="color:var(--t3);font-size:.55rem">${pct2}%</span></div></td>
          <td>${wl2.length?`<span style="color:var(--grn);font-size:.58rem">🎯 ${wl2.join(', ')}</span>`:'<span style="color:var(--t4)">—</span>'}</td>
        </tr>`;
      }).join('')
    }</tbody></table>`;
  }
}

const presenceCount={};  

function trackPresence(all){
  SRV.forEach(s=>{
    (all[s]||[]).forEach(p=>{
      if(!presenceCount[p])presenceCount[p]={total:0,servers:{}};
      presenceCount[p].total++;
      presenceCount[p].servers[s]=(presenceCount[p].servers[s]||0)+1;
    });
  });
}

let top5AllData={};
let top5ServerData=[];

async function loadTop5(){
  const interEl=document.getElementById('top5-inter');
  if(interEl)interEl.innerHTML='<div class="ld">Chargement<span class="ldd"><span>.</span><span>.</span><span>.</span></span></div>';
  try{
    
    const [all, topData] = await Promise.all([
      api('/api/online_all'),
      api('/api/top_players?limit=20')
    ]);
    top5AllData=all;
    trackPresence(all);
    renderTop5Inter(topData.players||[], all);
    await renderTop5BySrv();
  }catch(e){
    if(interEl)interEl.innerHTML=`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;
  }
}

function renderTop5Inter(players, allOnline){
  const el=document.getElementById('top5-inter');if(!el)return;
  if(!players.length){el.innerHTML='<div class="empty">Pas encore de données — le classement se construit automatiquement au fil du temps.</div>';return;}

  const nowOnline={};
  SRV.forEach(s=>(allOnline[s]||[]).forEach(p=>{if(!nowOnline[p])nowOnline[p]=[];nowOnline[p].push(s);}));

  const top=players.slice(0,5);
  const maxScore=top[0]?.total||1;
  const medals=['🥇','🥈','🥉','④','⑤'];
  el.innerHTML=top.map((x,i)=>{
    const inWL=WL.concat(WLM).map(w=>w.toLowerCase()).includes(x.player.toLowerCase());
    const currentSrvs=nowOnline[x.player]||[];
    const isOnline=currentSrvs.length>0;
    
    const topSrv=x.servers?Object.entries(x.servers).sort((a,b)=>b[1]-a[1])[0]:null;
    return`<div style="display:flex;align-items:center;gap:1rem;padding:.8rem .9rem;border-bottom:1px solid var(--b1);cursor:pointer;transition:background .1s" onmouseenter="this.style.background='var(--bg2)'" onmouseleave="this.style.background=''" onclick="openPlayerPanel('${x.player}')">
      <div style="font-family:var(--D);font-size:1.6rem;width:28px;text-align:center;flex-shrink:0">${medals[i]}</div>
      <img src="https://skins.nationsglory.fr/face/${encodeURIComponent(x.player)}/36" style="width:36px;height:36px;border-radius:4px;flex-shrink:0;image-rendering:pixelated;border:1px solid var(--b2)" onerror="this.src='https://mc-heads.net/avatar/${encodeURIComponent(x.player)}/36'" alt="">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.25rem;flex-wrap:wrap">
          <span style="font-family:var(--M);font-size:.7rem;color:var(--t1)">${x.player}</span>
          ${inWL?'<span style="font-family:var(--M);font-size:.46rem;color:var(--grn);background:rgba(0,232,122,.1);padding:.1rem .35rem;border-radius:3px">🎯 WATCHLIST</span>':''}
          ${isOnline?`<span style="font-family:var(--M);font-size:.46rem;color:var(--grn)">● EN LIGNE</span>`:'<span style="font-family:var(--M);font-size:.46rem;color:var(--t4)">○ hors ligne</span>'}
        </div>
        <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap">
          <div style="width:120px;height:4px;background:var(--bg3);border-radius:2px;overflow:hidden"><div style="width:${Math.round(x.total/maxScore*100)}%;height:100%;background:var(--blue-lt);transition:width .4s"></div></div>
          <span style="font-family:var(--M);font-size:.52rem;color:var(--t3)">${x.total} connexions</span>
          ${topSrv?`<span style="font-family:var(--M);font-size:.52rem;color:var(--t3)">· Fav : <span style="color:var(--blue-pale)">${topSrv[0].toUpperCase()}</span></span>`:''}
        </div>
        ${isOnline?`<div style="margin-top:.2rem">${currentSrvs.map(s=>`<span class="stag">${s.toUpperCase()}</span>`).join(' ')}</div>`:''}
        ${x.last_seen?`<div style="font-family:var(--M);font-size:.44rem;color:var(--t4);margin-top:.15rem">Dernière co : ${x.last_seen}</div>`:''}
      </div>
    </div>`;
  }).join('');
}

async function renderTop5BySrv(){
  const el=document.getElementById('top5-srv');if(!el)return;
  const srv=document.getElementById('top5-srv-sel')?.value||'lime';
  el.innerHTML='<div class="ld">Chargement<span class="ldd"><span>.</span><span>.</span><span>.</span></span></div>';
  try{
    const [srvData, onlineNow] = await Promise.all([
      api(`/api/top_players/${srv}?limit=10`),
      api(`/api/online/${srv}`)
    ]);
    const players=srvData.players||[];
    const onlineList=(onlineNow.players||[]).map(p=>p.toLowerCase());
    if(!players.length){el.innerHTML=`<div class="empty">Pas encore de données pour ${srv.toUpperCase()}</div>`;return;}
    const maxS=players[0]?.servers?.[srv]||1;
    const medals=['🥇','🥈','🥉','④','⑤'];
    el.innerHTML=players.slice(0,5).map((x,i)=>{
      const score=x.servers?.[srv]||0;
      const inWL=WL.concat(WLM).map(w=>w.toLowerCase()).includes(x.player.toLowerCase());
      const isOnline=onlineList.includes(x.player.toLowerCase());
      return`<div style="display:flex;align-items:center;gap:1rem;padding:.8rem .9rem;border-bottom:1px solid var(--b1);cursor:pointer;transition:background .1s" onmouseenter="this.style.background='var(--bg2)'" onmouseleave="this.style.background=''" onclick="openPlayerPanel('${x.player}')">
        <div style="font-family:var(--D);font-size:1.6rem;width:28px;text-align:center;flex-shrink:0">${medals[i]||'#'+(i+1)}</div>
        <img src="https://skins.nationsglory.fr/face/${encodeURIComponent(x.player)}/36" style="width:36px;height:36px;border-radius:4px;flex-shrink:0;image-rendering:pixelated;border:1px solid var(--b2)" onerror="this.src='https://mc-heads.net/avatar/${encodeURIComponent(x.player)}/36'" alt="">
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.2rem;flex-wrap:wrap">
            <span style="font-family:var(--M);font-size:.7rem;color:var(--t1)">${x.player}</span>
            ${inWL?'<span style="font-family:var(--M);font-size:.46rem;color:var(--grn);background:rgba(0,232,122,.1);padding:.1rem .35rem;border-radius:3px">🎯 WATCHLIST</span>':''}
            ${isOnline?`<span style="font-family:var(--M);font-size:.46rem;color:var(--grn)">● EN LIGNE</span>`:'<span style="font-family:var(--M);font-size:.46rem;color:var(--t4)">○ hors ligne</span>'}
          </div>
          <div style="display:flex;align-items:center;gap:.5rem">
            <div style="width:100px;height:4px;background:var(--bg3);border-radius:2px;overflow:hidden"><div style="width:${Math.round(score/maxS*100)}%;height:100%;background:var(--blue-lt)"></div></div>
            <span style="font-family:var(--M);font-size:.5rem;color:var(--t3)">${score} connexions</span>
          </div>
          ${x.last_seen?`<div style="font-family:var(--M);font-size:.44rem;color:var(--t4);margin-top:.15rem">Dernière co : ${x.last_seen}</div>`:''}
        </div>
      </div>`;
    }).join('');
  }catch(e){
    el.innerHTML=`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;
  }
}

setInterval(()=>{
  const active=document.querySelector('.sec.active');
  if(!active)return;
},30000);

const _origLoadDash=loadDash;
window.loadDash=async function(){
  await _origLoadDash();
  try{
    const all=await api('/api/online_all');
    trackPresence(all);
    if(Object.keys(top5AllData).length===0)top5AllData=all;
  }catch(e){}
};

let refAllReferents=[],refAllStats=[],refCurSrv=null,refCurCtry=null,refCmpPeriod=90;
const refCountryCache={};

async function refLoadCountries(){
  const s=$('ref-add-srv').value;
  if(!s){$('ref-suggest').innerHTML='';return;}
  $('ref-suggest').innerHTML=`<span style="font-family:var(--M);font-size:.5rem;color:var(--t3)">Chargement...</span>`;
  try{
    refCountryCache[s]=await getCountries(s);
    refFilterCountries();
  }catch(e){$('ref-suggest').innerHTML='';}
}

function refFilterCountries(){
  const s=$('ref-add-srv').value,v=$('ref-add-country').value.trim().toLowerCase();
  const p=refCountryCache[s]||[];
  const f=v?p.filter(x=>x.toLowerCase().includes(v)):p;
  $('ref-suggest').innerHTML=f.slice(0,60).map(x=>`<span class="tag" onclick="refSelectTag('${x.replace(/'/g,"\\'")}')">${x}</span>`).join('');
  const acl=$('ref-add-acl');
  if(v&&f.length){acl.innerHTML=f.slice(0,8).map(x=>`<div class="aci" onmousedown="refSelectTag('${x.replace(/'/g,"\\'")}')">${x}</div>`).join('');acl.style.display='block';}
  else acl.style.display='none';
}

function refSelectTag(name){$('ref-add-country').value=name;$('ref-add-acl').style.display='none';refFilterCountries();}

async function loadReferents(){
  const grid=$('ref-grid');
  grid.innerHTML=`<div class="ld">Chargement<span class="ldd"><span>.</span><span>.</span><span>.</span></span></div>`;
  try{
    const[rRefs,rStats7,rStats30,rStats90]=await Promise.all([
      fetch(API+'/api/referents',{headers:{..._authHeader()}}).then(r=>r.json()),
      fetch(API+'/api/referents/stats?days=7',{headers:{..._authHeader()}}).then(r=>r.json()),
      fetch(API+'/api/referents/stats?days=30',{headers:{..._authHeader()}}).then(r=>r.json()),
      fetch(API+'/api/referents/stats?days=90',{headers:{..._authHeader()}}).then(r=>r.json()),
    ]);
    refAllReferents=rRefs.watches||[];
    refAllStats=rStats90.stats||[];
    $('ref-gs-total').textContent=refAllReferents.length;
    $('ref-gs-week').textContent=(rStats7.stats||[]).reduce((a,x)=>a+x.total_recruits,0);
    $('ref-gs-month').textContent=(rStats30.stats||[]).reduce((a,x)=>a+x.total_recruits,0);
    const leader=(rStats90.stats||[])[0];
    if(leader){$('ref-gs-leader').textContent=leader.country_name;$('ref-gs-leader-sub').textContent=leader.total_recruits+' recrues — '+leader.server.toUpperCase();}
    renderRefGrid();
    loadRefCmp();
  }catch(e){grid.innerHTML=`<div class="empty" style="color:var(--red)">Erreur chargement</div>`;}
}

function renderRefGrid(){
  const el=$('ref-grid');
  if(!refAllReferents.length){el.innerHTML='<div class="empty">Aucun pays référent surveillé — ajoutez-en un ci-dessus</div>';return;}
  el.innerHTML=`<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem">${refAllReferents.map(w=>{
    const stat=refAllStats.find(s=>s.server===w.server&&s.country.toLowerCase()===w.country.toLowerCase());
    const recruits=stat?.total_recruits||0;
    const isSel=refCurSrv===w.server&&refCurCtry===w.country;
    return`<div onclick="openRefMembers('${w.server}','${w.country.replace(/'/g,"\\'")}')"
      style="background:var(--bg2);border:1px solid ${isSel?'var(--blue-lt)':'var(--b1)'};border-radius:var(--r);overflow:hidden;cursor:pointer;transition:all .15s;${isSel?'box-shadow:0 0 0 1px var(--blue-mid)':''}"
      onmouseenter="this.style.borderColor='var(--b3)'" onmouseleave="this.style.borderColor='${isSel?'var(--blue-lt)':'var(--b1)'}'">
      <div style="padding:.7rem 1rem;border-bottom:1px solid var(--b1);display:flex;align-items:center;justify-content:space-between">
        <span style="font-family:var(--D);font-size:1.3rem;letter-spacing:.2em;color:var(--t1)">${w.name||w.country}</span>
        <span style="font-family:var(--M);font-size:.55rem;color:var(--t3);background:var(--bg3);padding:.12rem .4rem;border-radius:3px">${w.server.toUpperCase()}</span>
      </div>
      <div style="padding:.65rem 1rem">
        <div style="display:flex;justify-content:space-between;margin-bottom:.28rem">
          <span style="font-family:var(--M);font-size:.58rem;color:var(--t3)">MEMBRES</span>
          <span style="font-family:var(--D);font-size:1rem;color:var(--t1)">${w.member_count||'—'}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:.45rem">
          <span style="font-family:var(--M);font-size:.58rem;color:var(--t3)">RECRUES 30J</span>
          <span style="font-family:var(--D);font-size:1rem;color:${recruits>0?'var(--grn)':'var(--t4)'}">${recruits}</span>
        </div>
        <div style="height:3px;background:var(--bg3);border-radius:2px;overflow:hidden">
          <div style="width:${Math.min(recruits*5,100)}%;height:100%;background:linear-gradient(90deg,var(--blue-mid),var(--blue-lt));border-radius:2px"></div>
        </div>
      </div>
      <div style="padding:.38rem 1rem;border-top:1px solid var(--b1);background:rgba(0,0,0,.18);display:flex;justify-content:space-between;align-items:center">
        <span style="font-family:var(--M);font-size:.48rem;color:var(--t4)">Click pour voir les membres</span>
        <span style="font-family:var(--M);font-size:.52rem;color:${recruits>0?'var(--grn)':'var(--t4)'}">${recruits>0?'▲ '+recruits+' recrues':'—'}</span>
      </div>
    </div>`;
  }).join('')}</div>`;
}

async function openRefMembers(server,country){
  refCurSrv=server;refCurCtry=country;
  const ref=refAllReferents.find(w=>w.server===server&&w.country.toLowerCase()===country.toLowerCase());
  $('ref-mp-title').textContent=(ref?.name||country).toUpperCase();
  $('ref-mp-sub').textContent=server.toUpperCase()+' · '+(ref?.member_count||'?')+' membres';
  $('ref-members-panel').style.display='block';
  $('ref-members-panel').scrollIntoView({behavior:'smooth',block:'start'});
  renderRefGrid();
  await refRefreshMembers();
}

async function refRefreshMembers(){
  if(!refCurSrv||!refCurCtry)return;
  const body=$('ref-members-body');
  body.innerHTML=`<div class="ld">Chargement<span class="ldd"><span>.</span><span>.</span><span>.</span></span></div>`;
  try{
    
    const[checkData,onlineData]=await Promise.all([
      fetch(`${API}/api/check/${refCurSrv}/${encodeURIComponent(refCurCtry)}`,{headers:{..._authHeader()}}).then(r=>r.json()),
      fetch(`${API}/api/online/${refCurSrv}`,{headers:{..._authHeader()}}).then(r=>r.json()),
    ]);
    if(checkData.error){body.innerHTML=`<div class="empty" style="color:var(--red)">❌ ${checkData.error}</div>`;return;}
    const allMembers=checkData.members_total||0;
    const onlineList=(onlineData.players||[]).map(p=>p.toLowerCase());
    
    const onlineOnSrv=(checkData.servers?.[refCurSrv]||[]);
    
    const onlineElsewhere=Object.entries(checkData.servers||{})
      .filter(([s])=>s!==refCurSrv)
      .flatMap(([s,pl])=>pl.map(p=>({player:p,server:s})));

    const knownOnline=new Set([...onlineOnSrv,...onlineElsewhere.map(x=>x.player)].map(p=>p.toLowerCase()));
    const snapshot=refAllReferents.find(w=>w.server===refCurSrv&&w.country.toLowerCase()===refCurCtry.toLowerCase())?.members_snapshot||[];

    const onlineCount=checkData.online_total||0;
    body.innerHTML=`
      <div style="display:flex;align-items:center;gap:1.5rem;margin-bottom:1rem;flex-wrap:wrap">
        <div style="font-family:var(--M);font-size:.65rem;color:var(--t3)">
          <span style="font-family:var(--D);font-size:1.8rem;color:var(--grn);margin-right:.3rem">${onlineCount}</span>en ligne
        </div>
        <div style="font-family:var(--M);font-size:.65rem;color:var(--t3)">
          <span style="font-family:var(--D);font-size:1.8rem;color:var(--t2);margin-right:.3rem">${allMembers}</span>membres total
        </div>
        <div style="font-family:var(--M);font-size:.65rem;color:var(--t3)">
          <span style="font-family:var(--D);font-size:1.8rem;color:var(--blue-pale);margin-right:.3rem">${snapshot.length||allMembers}</span>dans snapshot
        </div>
      </div>
      ${onlineOnSrv.length?`
        <div style="font-family:var(--M);font-size:.6rem;letter-spacing:.18em;color:var(--grn);margin-bottom:.5rem">🟢 EN LIGNE — ${refCurSrv.toUpperCase()} (${onlineOnSrv.length})</div>
        <div class="tags" style="margin-bottom:1rem">
          ${onlineOnSrv.map(p=>`<span class="tag on" onclick="openPlayerPanel('${p.replace(/'/g,"\\'")}') " style="cursor:pointer">🟢 ${p}</span>`).join('')}
        </div>`:''}
      ${onlineElsewhere.length?`
        <div style="font-family:var(--M);font-size:.6rem;letter-spacing:.18em;color:var(--org);margin-bottom:.5rem">🟡 EN LIGNE AILLEURS (${onlineElsewhere.length})</div>
        <div class="tags" style="margin-bottom:1rem">
          ${onlineElsewhere.map(({player:p,server:s})=>`<span class="tag" onclick="openPlayerPanel('${p.replace(/'/g,"\\'")}') " style="cursor:pointer;border-color:rgba(255,153,0,.35);color:var(--org)">🟡 ${p} <span style="font-size:.42rem;opacity:.7">${s.toUpperCase()}</span></span>`).join('')}
        </div>`:''}
      ${snapshot.length?`
        <div style="font-family:var(--M);font-size:.6rem;letter-spacing:.18em;color:var(--t3);margin-bottom:.5rem">⚫ HORS LIGNE (${snapshot.filter(p=>!knownOnline.has(p.toLowerCase())).length})</div>
        <div class="tags">
          ${snapshot.filter(p=>!knownOnline.has(p.toLowerCase())).map(p=>`<span class="tag" onclick="openPlayerPanel('${p.replace(/'/g,"\\'")}') " style="cursor:pointer">⚫ ${p}</span>`).join('')}
        </div>`
      :(!onlineOnSrv.length&&!onlineElsewhere.length?'<div class="empty">Aucun membre connu hors ligne — le snapshot se remplira au prochain scan (5 min)</div>':'')}
    `;
  }catch(e){body.innerHTML=`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;}
}

async function loadRefHistory(){
  if(!refCurSrv||!refCurCtry)return;
  const body=$('ref-hist-body');
  if(!body)return;
  body.innerHTML=`<div class="ld">Chargement<span class="ldd"><span>.</span><span>.</span><span>.</span></span></div>`;
  try{
    const d=await fetch(`${API}/api/referents/history?server=${refCurSrv}&country=${encodeURIComponent(refCurCtry)}&limit=200&departures=1`,{headers:{..._authHeader()}}).then(r=>r.json());
    const events=d.events||[];
    if(!events.length){body.innerHTML='<div class="empty">Aucun événement enregistré — le tracking démarre au prochain scan (30 min)</div>';return;}
    const recruits=events.filter(e=>!e.departure);
    const departs=events.filter(e=>e.departure);
    body.innerHTML=`
      <div style="display:flex;gap:2rem;margin-bottom:1rem;flex-wrap:wrap">
        <div style="font-family:var(--M);font-size:.6rem;color:var(--t3)"><span style="font-family:var(--D);font-size:1.6rem;color:var(--grn)">${recruits.length}</span> recrutements</div>
        <div style="font-family:var(--M);font-size:.6rem;color:var(--t3)"><span style="font-family:var(--D);font-size:1.6rem;color:var(--red)">${departs.length}</span> départs</div>
      </div>
      <div style="display:flex;gap:.5rem;margin-bottom:.8rem">
        <button class="btn" id="ref-hist-tab-all" onclick="refHistFilter('all')" style="font-size:.5rem;padding:.2rem .6rem">Tous (${events.length})</button>
        <button class="btn" id="ref-hist-tab-recruit" onclick="refHistFilter('recruit')" style="font-size:.5rem;padding:.2rem .6rem">Recrutements</button>
        <button class="btn" id="ref-hist-tab-depart" onclick="refHistFilter('depart')" style="font-size:.5rem;padding:.2rem .6rem">Départs</button>
      </div>
      <div id="ref-hist-list">
        ${renderHistEvents(events)}
      </div>
    `;
    body._allEvents=events;
  }catch(e){body.innerHTML=`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;}
}

function renderHistEvents(events){
  if(!events.length)return'<div class="empty">Aucun événement</div>';
  return events.map(e=>{
    const isDepart=!!e.departure;
    const color=isDepart?'var(--red)':'var(--grn)';
    const icon=isDepart?'🚪':'🆕';
    const label=isDepart?'DÉPART':'RECRUTEMENT';
    return`<div style="display:flex;align-items:center;gap:.7rem;padding:.5rem .2rem;border-bottom:1px solid var(--b1)">
      <img src="https://mc-heads.net/avatar/${encodeURIComponent(e.player)}/24" style="width:24px;height:24px;border-radius:3px;flex-shrink:0" onerror="this.style.display='none'" alt="">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap">
          <span style="font-family:var(--M);font-size:.62rem;color:var(--t1);cursor:pointer" onclick="openPlayerPanel('${e.player.replace(/'/g,"\'")}')">${e.player}</span>
          <span style="font-family:var(--M);font-size:.46rem;padding:.08rem .35rem;border-radius:3px;background:${isDepart?'rgba(255,51,85,.12)':'rgba(0,232,122,.1)'};color:${color}">${icon} ${label}</span>
        </div>
        <div style="font-family:var(--M);font-size:.5rem;color:var(--t4);margin-top:.15rem">${e.ts} · ${e.members_before}→${e.members_after} membres</div>
      </div>
    </div>`;
  }).join('');
}

function refHistFilter(type){
  const body=$('ref-hist-body');
  if(!body||!body._allEvents)return;
  let evts=body._allEvents;
  if(type==='recruit')evts=evts.filter(e=>!e.departure);
  else if(type==='depart')evts=evts.filter(e=>e.departure);
  const list=$('ref-hist-list');
  if(list)list.innerHTML=renderHistEvents(evts);
  document.querySelectorAll('[id^="ref-hist-tab-"]').forEach(b=>b.style.borderColor='');
  const active=$('ref-hist-tab-'+type);
  if(active)active.style.borderColor='var(--blue)';
}

function refShowTab(tab){
  ['members','history'].forEach(t=>{
    const panel=$('ref-tab-'+t);
    const btn=$('ref-tabn-'+t);
    if(panel)panel.style.display=t===tab?'block':'none';
    if(btn){btn.style.color=t===tab?'var(--blue)':'var(--t3)';btn.style.borderBottom=t===tab?'1px solid var(--blue)':'1px solid transparent';}
  });
  if(tab==='history')loadRefHistory();
}

function closeRefMembers(){
  $('ref-members-panel').style.display='none';
  refCurSrv=null;refCurCtry=null;
  renderRefGrid();
}

async function loadRefCmp(){
  const el=$('ref-cmp');
  el.innerHTML=`<div class="ld">Chargement<span class="ldd"><span>.</span><span>.</span><span>.</span></span></div>`;
  try{
    const d=await fetch(API+'/api/referents/stats?days='+refCmpPeriod,{headers:{..._authHeader()}}).then(r=>r.json());
    const stats=d.stats||[];
    if(!stats.length){el.innerHTML='<div class="empty">Pas encore de données — le tracking démarre au prochain scan (30 min)</div>';return;}
    const max=stats[0]?.total_recruits||1;
    const colors=['#1a6fff','#0050d8','#0038b8','#5ba3ff','#344d72'];
    el.innerHTML=stats.map((x,i)=>`<div onclick="openRefMembers('${x.server}','${x.country.replace(/'/g,"\\'")}')" style="display:flex;align-items:center;gap:.8rem;padding:.55rem 0;border-bottom:1px solid var(--b1);cursor:pointer;transition:background .1s" onmouseenter="this.style.background='var(--bg2)'" onmouseleave="this.style.background=''">
      <span style="font-family:var(--D);font-size:1.1rem;letter-spacing:.15em;min-width:130px;color:var(--t1)">${x.country_name}</span>
      <span style="font-family:var(--M);font-size:.52rem;color:var(--t3);min-width:55px">${x.server.toUpperCase()}</span>
      <div style="flex:1;height:7px;background:var(--bg3);border-radius:4px;overflow:hidden">
        <div style="width:${Math.round(x.total_recruits/max*100)}%;height:100%;background:${colors[i%colors.length]};border-radius:4px;transition:width .6s"></div>
      </div>
      <span style="font-family:var(--D);font-size:1.1rem;min-width:35px;text-align:right;color:var(--t1)">${x.total_recruits}</span>
      <span style="font-family:var(--M);font-size:.5rem;color:var(--t4);min-width:65px;text-align:right">${x.unique_players} joueurs</span>
    </div>`).join('');
  }catch(e){el.innerHTML='<div class="empty" style="color:var(--red)">Erreur chargement</div>';}
}

function setCmpRefPeriod(days,btn){
  refCmpPeriod=days;
  btn.closest('.ph').querySelectorAll('.btn').forEach(b=>{b.style.background='';b.style.borderColor='';b.style.color='';});
  btn.style.background='rgba(0,56,184,.2)';btn.style.borderColor='rgba(26,111,255,.4)';btn.style.color='var(--blue-pale)';
  loadRefCmp();
}

async function addReferentEntry(){
  const server=$('ref-add-srv').value,country=$('ref-add-country').value.trim();
  if(!server||!country)return showToast('⚠ Sélectionne un serveur et un pays');
  try{
    const d=await fetch(API+'/api/referents/add',{method:'POST',headers:{'Content-Type':'application/json',..._authHeader()},body:JSON.stringify({server,country})}).then(r=>r.json());
    if(d.error)return showToast('❌ '+d.error);
    $('ref-add-country').value='';
    showToast('✅ '+country+' ('+server.toUpperCase()+') ajouté');
    await loadReferents();
  }catch(e){showToast('❌ Erreur réseau');}
}

async function removeReferentEntry(server,country){
  if(!confirm('Retirer '+country+' ('+server.toUpperCase()+') de la surveillance ?'))return;
  try{
    const d=await fetch(API+'/api/referents/remove',{method:'POST',headers:{'Content-Type':'application/json',..._authHeader()},body:JSON.stringify({server,country})}).then(r=>r.json());
    if(d.error)return showToast('❌ '+d.error);
    showToast('🗑 '+country+' retiré');
    closeRefMembers();
    await loadReferents();
  }catch(e){showToast('❌ Erreur réseau');}
}

setInterval(()=>{
  const active=document.querySelector('.sec.active');
  if(active&&active.id==='s-referents'){
    loadReferents();
    if(refCurSrv)refRefreshMembers();
  }
},300000);

// ── SOUS-POWER ──────────────────────────────────────────────────────

// Calcule l'aire d'un polygone (Shoelace) pour déduire les claims réels dans une dimension
function _polyArea(xs,zs){
  let area=0;const n=xs.length;
  for(let i=0;i<n;i++){const j=(i+1)%n;area+=xs[i]*zs[j]-xs[j]*zs[i];}
  return Math.abs(area)/2;
}

// Fetches dimension marker JSON and returns a map: countryName (lowercase) → {claims, x, z}
// Claims dans une dim = aire du polygone / 256 (chaque chunk = 16x16 blocs)
// Passe par le backend pour éviter le CORS
async function _fetchDimClaims(server,dim){
  try{
    const dimUrl=`${API}/api/dim_markers/${server}/${encodeURIComponent(dim)}`;
    const r=await fetch(dimUrl,{headers:{..._authHeader()}});
    if(!r.ok){console.warn('[dimClaims] HTTP',r.status,dimUrl);return{};}
    const areas=await r.json();
    // Si le backend retourne une erreur JSON, areas sera {error:...}
    if(!areas||typeof areas!=='object'||areas.error)return{};
    const map={};
    for(const[k,v]of Object.entries(areas)){
      const label=v.label||'';
      if(!label)continue;
      const name=label.toLowerCase();
      const xs=v.x||[];const zs=v.z||[];
      if(xs.length<3)continue;
      const claims=Math.round(_polyArea(xs,zs)/256);
      if(claims===0)continue;
      const cx=xs.reduce((a,b)=>a+b,0)/xs.length;
      const cz=zs.reduce((a,b)=>a+b,0)/zs.length;
      if(map[name]){
        map[name].claims+=claims;
      } else {
        map[name]={claims,x:Math.round(cx),z:Math.round(cz)};
      }
    }
    return map;
  }catch(e){console.error('[dimClaims] erreur fetch',dimUrl,e);return{};}
}

async function loadSouspower(){
  const s=$('sp-srv').value;
  if(!s){alert('Choisis un serveur');return;}
  const res=$('sp-result'),ts=$('sp-ts');
  res.innerHTML=ld();ts.textContent='';
  try{
    // Fetch main souspower data + all 3 dimension markers in parallel
    const [d, dimLune, dimMars, dimEdora] = await Promise.all([
      api(`/api/souspower/${s}`),
      _fetchDimClaims(s,'DIM-28'),
      _fetchDimClaims(s,'DIM-29'),
      _fetchDimClaims(s,'DIM-31'),
    ]);
    const pays=d.countries||[];
    if(!pays.length){res.innerHTML='<div class="empty">Aucun pays trouvé</div>';return;}
    const sp=pays.filter(p=>p.marge<0);
    const proche=pays.filter(p=>p.marge>=0&&p.marge<200);
    const safe=pays.filter(p=>p.marge>=200);

    // Helper to build a dim claims chip
    const dimChip=(dimData, dimWorldname, dimLabel, dimColor)=>{
      const key=dimData; // already the entry {claims,x,z} or null
      if(!key){
        return`<span style="font-family:var(--M);font-size:.5rem;color:var(--t4);border:1px solid var(--b1);border-radius:3px;padding:.1rem .4rem;white-space:nowrap">${dimLabel} <span style="opacity:.5">aucun claim</span></span>`;
      }
      const url=`https://${s}.nationsglory.fr/?worldname=${dimWorldname}&mapname=flat&zoom=4&x=${key.x}&y=64&z=${key.z}`;
      return`<a href="${url}" target="_blank" rel="noopener"
          title="Voir ${dimLabel} sur la Dynmap"
          style="display:inline-flex;align-items:center;gap:.3rem;font-family:var(--M);font-size:.5rem;
            color:${dimColor};text-decoration:none;border:1px solid ${dimColor}33;
            border-radius:3px;padding:.1rem .45rem;background:${dimColor}11;
            transition:all .15s;white-space:nowrap"
          onmouseover="this.style.background='${dimColor}22';this.style.borderColor='${dimColor}66'"
          onmouseout="this.style.background='${dimColor}11';this.style.borderColor='${dimColor}33'">
          ${dimLabel} <b>${key.claims}</b> <span style="opacity:.6">↗</span>
        </a>`;
    };

    const row=(p,cat)=>{
      const pct=p.maxpower?Math.min(100,Math.round(p.power/p.maxpower*100)):0;
      const col=cat==='sp'?'var(--red)':cat==='proche'?'var(--org)':'var(--grn)';
      const badge=cat==='sp'?`<span style="background:rgba(255,60,60,.15);color:var(--red);border:1px solid rgba(255,60,60,.3);border-radius:4px;padding:.2rem .5rem;font-size:.55rem;margin-left:.6rem;font-weight:700">⛔ −${Math.abs(p.marge)}</span>`:
        cat==='proche'?`<span style="background:rgba(255,160,0,.12);color:var(--org);border:1px solid rgba(255,160,0,.25);border-radius:4px;padding:.2rem .5rem;font-size:.55rem;margin-left:.6rem">⚠ +${p.marge}</span>`:
        `<span style="color:var(--t3);font-size:.55rem;margin-left:.6rem">+${p.marge}</span>`;
      const hasCoord=(p.x||p.z);
      const dynmapUrl=`https://${s}.nationsglory.fr/?worldname=world&mapname=flat&zoom=4&x=${Math.round(p.x)}&y=64&z=${Math.round(p.z)}`;
      const coordBlock=hasCoord?`<a href="${dynmapUrl}" target="_blank" rel="noopener"
          title="Ouvrir sur la Dynmap"
          style="display:inline-flex;align-items:center;gap:.35rem;font-family:var(--M);font-size:.58rem;
            color:var(--blue-pale);text-decoration:none;border:1px solid rgba(91,163,255,.25);
            border-radius:4px;padding:.15rem .55rem;background:rgba(91,163,255,.07);
            transition:all .15s;white-space:nowrap"
          onmouseover="this.style.background='rgba(91,163,255,.18)';this.style.borderColor='rgba(91,163,255,.5)'"
          onmouseout="this.style.background='rgba(91,163,255,.07)';this.style.borderColor='rgba(91,163,255,.25)'">
          📍 ${Math.round(p.x)}, ${Math.round(p.z)} <span style="font-size:.5rem;opacity:.7">↗</span>
        </a>`:'';
      const leaderSkin=p.leader?`<img src="https://skins.nationsglory.fr/face/${p.leader}/32"
          alt="${p.leader}" title="${p.leader}"
          style="width:22px;height:22px;border-radius:3px;border:1px solid var(--b2);
            image-rendering:pixelated;flex-shrink:0;vertical-align:middle"
          onerror="this.style.display='none'">`:'';

      // Dimension claims lookup
      const nk=p.name.toLowerCase();
      const luneData=dimLune[nk]||null;
      const marsData=dimMars[nk]||null;
      const edoraData=dimEdora[nk]||null;
      const dimRow=`<div style="display:flex;align-items:center;gap:.5rem;margin-top:.45rem;flex-wrap:wrap">
          <span style="font-family:var(--M);font-size:.48rem;color:var(--t4);letter-spacing:.08em;white-space:nowrap">DIMS :</span>
          ${dimChip(luneData,'DIM-28','🌙 Lune','#c8aaff')}
          ${dimChip(marsData,'DIM-29','🔴 Mars','#ff7755')}
          ${dimChip(edoraData,'DIM-31','🟢 Edora','#44dd88')}
        </div>`;

      return`<div style="display:flex;align-items:center;gap:1rem;padding:.75rem 1rem;border-bottom:1px solid var(--b1);flex-wrap:wrap">
        <div style="min-width:160px;font-family:var(--D);font-size:1.05rem;color:var(--t1);display:flex;align-items:center">${p.name}${badge}</div>
        <div style="flex:1;min-width:200px">
          <div style="display:flex;gap:1.2rem;font-family:var(--M);font-size:.6rem;color:var(--t3);margin-bottom:.3rem;flex-wrap:wrap;align-items:center">
            <span>⚡ <b style="color:${col};font-size:.65rem">${p.power}</b><span style="color:var(--t3)">/${p.maxpower}</span></span>
            <span>🏴 <b style="color:var(--t1)">${p.claims}</b> claims</span>
            ${p.mmr?`<span>🏆 <b style="color:var(--t1)">${p.mmr}</b> MMR</span>`:''}
            <span>👥 <b style="color:var(--t1)">${p.members}</b> membres</span>
            ${p.leader?`<span style="display:inline-flex;align-items:center;gap:.3rem">${leaderSkin}👑 <b style="color:var(--t2)">${p.leader}</b></span>`:''}
          </div>
          <div style="background:var(--bg2);border-radius:4px;height:6px;overflow:hidden">
            <div style="height:100%;width:${pct}%;background:${col};transition:width .4s"></div>
          </div>
          ${hasCoord?`<div style="margin-top:.4rem">${coordBlock}</div>`:''}
          ${dimRow}
        </div>
      </div>`;
    };
    const section=(title,list,cat,color)=>list.length?`
      <div style="font-family:var(--M);font-size:.6rem;color:${color};letter-spacing:.1em;padding:.7rem 1rem;border-bottom:1px solid var(--b1);background:rgba(0,0,0,.2);font-weight:700">${title} — ${list.length} pays</div>
      ${list.map(p=>row(p,cat)).join('')}
    `:'';
    res.innerHTML=`<div style="border:1px solid var(--b1);border-radius:var(--r);overflow:hidden">
      ${section('⛔ EN SOUS-POWER',sp,'sp','var(--red)')}
      ${section('⚠ PROCHES DU SOUS-POWER (marge < 200)',proche,'proche','var(--org)')}
      ${section('✅ SAFE',safe,'safe','var(--grn)')}
    </div>`;
    ts.textContent=`${pays.length} pays analysés — ${new Date().toLocaleTimeString('fr-FR')}`;
  }catch(e){res.innerHTML=`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;}
}
