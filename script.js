// ═══════════════════════════════════════════════════════════
// PASSWORD GATE — protection renforcée
// ═══════════════════════════════════════════════════════════
(function(){
  const SESSION_KEY = 'mg_auth_v2';
  const MAIN = document.querySelector('.main');
  const HDR  = document.querySelector('.hdr');
  const NAV  = document.querySelector('.nav');

  // Cache le contenu réel dès le départ
  function lockContent() {
    if(MAIN) MAIN.style.display = 'none';
    if(HDR)  HDR.style.display  = 'none';
    if(NAV)  NAV.style.display  = 'none';
  }

  // Révèle le contenu seulement après auth validée
  function unlockContent() {
    const lock = document.getElementById('init-lock');
    if(lock) lock.remove();
    if(MAIN) MAIN.style.display = '';
    if(HDR)  HDR.style.display  = '';
    if(NAV)  NAV.style.display  = '';
  }

  // Vérifie en permanence que le gate est toujours là (anti-inspecteur)
  function watchGate() {
    const gate = document.getElementById('pw-gate');
    // Si quelqu'un supprime le gate sans être authentifié → troll
    if(!gate && sessionStorage.getItem(SESSION_KEY) !== 'ok') {
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
    // Fausse IP pour faire peur
    setTimeout(() => {
      const fake = `${rand(1,254)}.${rand(0,255)}.${rand(0,255)}.${rand(1,254)}`;
      document.getElementById('fake-ip').textContent =
        `Adresse identifiée : ${fake} — signalement en cours...`;
    }, 1800);
  }

  function rand(a,b){ return Math.floor(Math.random()*(b-a+1))+a; }

  // Auth déjà validée en session → débloquer directement
  if(sessionStorage.getItem(SESSION_KEY) === 'ok'){
    const gate = document.getElementById('pw-gate');
    if(gate) gate.style.display = 'none';
    unlockContent();
  } else {
    lockContent();
    setTimeout(() => {
      const el = document.getElementById('pw-input-el');
      if(el) el.focus();
    }, 100);
    // Surveille toutes les 500ms si le gate est supprimé
    const observer = setInterval(watchGate, 500);
    // On arrête de surveiller une fois authentifié
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
        sessionStorage.setItem(SESSION_KEY, 'ok');
        if(window._stopGateWatch) window._stopGateWatch();
        requestNotifPerms();
        _authDone=true;
        unlockContent();
        const gate = document.getElementById('pw-gate');
        gate.style.transition = 'opacity .6s';
        gate.style.opacity = '0';
        setTimeout(() => { gate.style.display = 'none'; }, 600);
      } else {
        err.style.opacity = '1';
        inp.value = '';
        inp.style.borderColor = 'rgba(255,24,64,.5)';
        setTimeout(() => {
          err.style.opacity = '0';
          inp.style.borderColor = 'rgba(0,80,216,.2)';
        }, 2500);
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


// ═══════════════════════════════════════════════════════════
// MAIN APPLICATION
// ═══════════════════════════════════════════════════════════
const API='https://nationsglory-spy.onrender.com';
const SRV=["blue","coral","orange","red","yellow","mocha","white","jade","black","cyan","lime"];
const EMO={blue:"🔵",coral:"🔴",orange:"🟠",red:"🔴",yellow:"🟡",mocha:"🟤",white:"⚪",jade:"🟢",black:"⚫",cyan:"🔵",lime:"🟢"};
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
  const cur=$('cur'),dot=$('cd');
  const tc=$('trl'),tc2=tc.getContext('2d');
  const sync=()=>{tc.width=innerWidth;tc.height=innerHeight};sync();window.addEventListener('resize',sync);
  let trail=[],MAX=16;
  document.addEventListener('mousemove',e=>{
    dot.style.left=e.clientX+'px';dot.style.top=e.clientY+'px';
    trail.push({x:e.clientX,y:e.clientY,t:Date.now()});if(trail.length>MAX)trail.shift();
  });
  document.addEventListener('mousedown',()=>cur.classList.add('c'));
  document.addEventListener('mouseup',()=>cur.classList.remove('c'));
  const draw=()=>{
    tc2.clearRect(0,0,tc.width,tc.height);
    const now=Date.now();
    trail.forEach((p,i)=>{const s=(i+1)/MAX*(1-(now-p.t)/200);if(s<=0)return;tc2.beginPath();tc2.arc(p.x,p.y,1.2*s,0,Math.PI*2);tc2.fillStyle=`rgba(26,111,255,${s*.16})`;tc2.fill();});
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
window.addEventListener('load',()=>{
  clearInterval(pctT);clearInterval(msgT);if($('l-pct'))$('l-pct').textContent='100%';
  setTimeout(()=>{const m=$('l-msg');if(m){m.textContent='SYSTÈME PRÊT — CLIQUEZ POUR ENTRER';m.classList.remove('blink');m.classList.add('rdy');}const b=$('lbtn');if(b)b.style.display='block';},300);
});
function enterSite(){
  try{if(!actx)actx=new(window.AudioContext||window.webkitAudioContext)();actx.resume();}catch(e){}
  requestNotifPerms();
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

async function api(p){const r=await fetch(API+p);if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}
async function apiP(p,b){const r=await fetch(API+p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}

async function nav(id,btn){sndNav();pageFlash();document.querySelectorAll('.sec').forEach(s=>s.classList.remove('active'));document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));$('s-'+id).classList.add('active');btn.classList.add('active');if(id==='watchlist')await switchWl('lime');if(id==='countrywatch'){cwRender();cwRefreshAll();}if(id==='online'){$('ol-body').innerHTML=ld();loadOnline();}if(id==='checkall')rAT('ca-pl','ppCA');if(id==='stats')rAT('st-pl','ppST');}

function rAT(id,fn){const e=$(id);if(!e||!oP.length)return;e.innerHTML=oP.map(p=>`<span class="tag" onclick="${fn}('${p.replace(/'/g,"\\'")}')">${p}</span>`).join('');}
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
async function loadWL(){try{const c=new AbortController(),t=setTimeout(()=>c.abort(),6000);const r=await fetch(API+'/api/watchlist',{signal:c.signal});clearTimeout(t);const d=await r.json();WL=d.players||[];animStat('st-wcount',WL.length);sparkData.wc.push(WL.length);if(sparkData.wc.length>30)sparkData.wc.shift();drawSpark('spark-wc',sparkData.wc);}catch{}}
async function loadWLM(){try{const c=new AbortController(),t=setTimeout(()=>c.abort(),6000);const r=await fetch(API+'/api/watchlist_mocha',{signal:c.signal});clearTimeout(t);const d=await r.json();WLM=d.players||[];}catch{}}
async function loadKP(){try{const d=await fetch(API+'/api/known_players').then(r=>r.json());oP=[...new Set([...(d.players||[]),...oP])].sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));rAT('ca-pl','ppCA');rAT('st-pl','ppST');rAT('wl-pl','ppWL');}catch{}}

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
    const mk=(pl,l,c,lb)=>l.length?`<div style="font-family:var(--M);font-size:.66rem;color:${c};letter-spacing:.22em;margin-bottom:.18rem">${lb}</div><div class="tags" style="margin-bottom:.35rem">${l.map(p=>{const on=pl.map(x=>x.toLowerCase()).includes(p.toLowerCase());const seen=getLastSeenText(p);return`<span class="tag ${on?'on':''}" onclick="openPlayerPanel('${p}')" title="Voir profil">${on?'🟢':'⚫'} ${p}${seen?` <span class="wi-seen ${seen.cls}">${seen.text}</span>`:''}</span>`;}).join('')}</div>`:'';
    $('wl-quick').innerHTML=(mk(lp,WL,'var(--grn)','🟢 LIME')||'')+(mk(mp,WLM,'var(--org)','🟤 MOCHA')||'')||'<div class="empty">Watchlists vides</div>';
    if($('last-update'))$('last-update').textContent=new Date().toLocaleTimeString('fr-FR');
    pushActivity(tot);startCountdown(5);
    if(document.getElementById('wl-status')&&document.getElementById('wl-status').innerHTML.trim()!=='')wlRS();
  }catch(e){$('srv-overview').innerHTML=`<div class="empty" style="color:var(--red)">Bot hors ligne<br/><span style="font-size:.74rem;opacity:.6">${e.message}</span></div>`;}
}
function pAlert(t,p,s){ALR.unshift({type:t,player:p,server:s,time:new Date().toLocaleTimeString('fr-FR')});if(ALR.length>60)ALR.pop();rAlerts();const inWL=WL.map(x=>x.toLowerCase()).includes(p.toLowerCase())||WLM.map(x=>x.toLowerCase()).includes(p.toLowerCase());if(inWL){if(t==='connect'){setLastSeen(p,s);startSession(p);sendBrowserNotif('connect',p,s);}else{endSession(p);sendBrowserNotif('disconnect',p,s);}showPop(t,p,s);}}
function rAlerts(){$('alert-badge').textContent=ALR.length+' évts';$('alert-feed').innerHTML=ALR.length?ALR.map(a=>`<div class="fi"><div class="fi-d ${a.type==='connect'?'g':'r'}"></div><span class="fi-t">${a.time}</span><span class="fi-m">${a.type==='connect'?'🟢':'🔴'} <b style="cursor:pointer" onclick="openPlayerPanel('${a.player}')">${a.player}</b><span class="fi-s">${a.server.toUpperCase()}</span></span></div>`).join(''):'<div class="empty">En attente...</div>';}

function gOL(s){document.querySelectorAll('.tab')[1].click();$('ol-srv').value=s;$('ol-body').innerHTML=ld();loadOLS(s);}
function fOL(s){$('ol-srv').value=s;$('ol-body').innerHTML=ld();loadOLS(s);}
async function loadOLS(srv){const body=$('ol-body'),w=BUG(srv)?WARN:'';try{const d=await api('/api/online/'+srv),pl=d.players||[];body.innerHTML=w+(pl.length?`<div style="font-family:var(--M);font-size:.76rem;color:var(--t3);margin-bottom:.35rem"><span style="color:var(--gb)">${pl.length}</span> joueurs — ${srv.toUpperCase()}</div><div class="tags">${pl.map(p=>`<span class="tag ${WL.map(w=>w.toLowerCase()).includes(p.toLowerCase())?'on':''}" onclick="openPlayerPanel('${p}')">${p}</span>`).join('')}</div>`:`<div class="empty">${BUG(srv)?'0 joueur (dynmap limité)':'Aucun joueur sur '+srv.toUpperCase()}</div>`);}catch(e){body.innerHTML=w+`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;}}
async function loadOnline(){const srv=$('ol-srv').value,body=$('ol-body');body.innerHTML=ld();try{if(!srv){const all=await api('/api/online_all');let tot=0;SRV.forEach(s=>tot+=(all[s]||[]).length);body.innerHTML=`<div style="font-family:var(--M);font-size:.76rem;color:var(--t3);margin-bottom:.55rem">TOTAL <span style="color:var(--gb)">${tot}</span> joueurs</div><div class="sg">${SRV.map(s=>{const pl=all[s]||[],bug=BUG(s);return`<div class="sc" onmouseenter="sndH()" onclick="fOL('${s}')" ${bug?'style="border-color:rgba(255,119,0,.22)"':''}><div class="sc-top"><span class="sc-name">${s.toUpperCase()}</span><span class="sc-emo">${EMO[s]}</span></div><div class="sc-n">${pl.length}</div>${bug?'<div class="sc-lbl warn">⚠ INSTABLE</div>':'<div class="sc-lbl">CLIQUER</div>'}<div class="tags" style="max-height:64px;overflow-y:auto" onclick="event.stopPropagation()">${pl.slice(0,16).map(p=>`<span class="tag ${WL.map(w=>w.toLowerCase()).includes(p.toLowerCase())?'wl':''}" onclick="event.stopPropagation();qCA('${p}')">${p}</span>`).join('')}${pl.length>16?`<span style="font-family:var(--M);font-size:.66rem;color:var(--t3)">+${pl.length-16}</span>`:''}</div><div class="sbar"><div class="sbar-f" style="width:${Math.round(pl.length/Math.max(...SRV.map(ss=>(all[ss]||[]).length),1)*100)}%"></div></div></div>`;}).join('')}</div>`;}else await loadOLS(srv);}catch(e){body.innerHTML=`<div class="empty" style="color:var(--red)">Erreur : ${e.message}</div>`;}}

async function doCA(){const raw=$('ca-input').value.trim();if(!raw)return;const p=rP(raw,oP);$('ca-input').value=p;const res=$('ca-result');res.innerHTML=ld();try{const d=await api('/api/checkall/'+encodeURIComponent(p));if(d.servers.length)sndF();res.innerHTML=d.servers.length?`<div class="res ok"><div class="rt">Joueur localisé — ${p}</div>${d.servers.map(s=>`<div style="margin:.2rem 0">${EMO[s]} <span style="color:var(--g)">${s.toUpperCase()}</span></div>`).join('')}</div>`:`<div class="res err"><div class="rt">Résultat</div><span style="color:var(--t3)">${p} n'est connecté nulle part</span></div>`;hist=hist.filter(h=>h.p.toLowerCase()!==p.toLowerCase());hist.unshift({p,servers:d.servers,t:new Date().toLocaleTimeString('fr-FR')});if(hist.length>15)hist.pop();localStorage.setItem('mg_h',JSON.stringify(hist));rHist();}catch(e){res.innerHTML=`<div class="res err">Erreur : ${e.message}</div>`;}}
function qCA(player){openPlayerPanel(player);}
function rHist(){const el=$('ca-history');if(!hist.length){el.innerHTML='<div class="empty">Aucune recherche</div>';return;}el.innerHTML=`<table class="tbl"><thead><tr><th>Joueur</th><th>Serveurs</th><th>Heure</th></tr></thead><tbody>`+hist.slice(0,12).map(h=>`<tr><td style="color:var(--g)" onclick="qCA('${h.p}')">${h.p}</td><td>${h.servers.length?h.servers.map(s=>`<span class="stag">${s.toUpperCase()}</span>`).join(''):'<span style="color:var(--t3)">Hors ligne</span>'}</td><td style="color:var(--t3)">${h.t}</td></tr>`).join('')+'</tbody></table>';}

async function loadCS(){const s=$('ck-srv').value;if(!s)return;$('ck-suggest').innerHTML=`<span style="font-family:var(--M);font-size:.72rem;color:var(--t3)">Chargement...</span>`;try{if(!cc[s]){const d=await api('/api/countries/'+s);cc[s]=(d.countries||[]).sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));}rCS(s);}catch{cc[s]=[];$('ck-suggest').innerHTML='';}}
function rCS(s){const el=$('ck-suggest'),p=cc[s]||[];if(!p.length){el.innerHTML='';return;}el.innerHTML=p.map(c=>`<span class="tag" onclick="selC('${c.replace(/'/g,"\\'")}')">${c}</span>`).join('');}
function selC(c){$('ck-country').value=c;$('ck-list').style.display='none';doCheck();}
async function doCheck(){const s=$('ck-srv').value,raw=$('ck-country').value.trim();if(!s||!raw)return;const c=rP(raw,cc[s]||[]);$('ck-country').value=c;const res=$('ck-result');res.innerHTML=ld();try{const d=await api(`/api/check/${s}/${encodeURIComponent(c)}`);const note=`<div class="warn" style="margin-top:.34rem">⚠ Dynmap hors service</div>`;if(d.online_total===0){res.innerHTML=`<div class="res ok"><div class="rt">Pays : ${d.country} — ${d.members_total} membres</div><span style="color:var(--grn)">✓ Aucun membre connecté</span>${BUG(s)?note:''}</div>`;}else{res.innerHTML=`<div class="res err"><div class="rt">Pays : ${d.country} — ${d.online_total}/${d.members_total} connectés</div>`+Object.entries(d.servers).sort((a,b)=>a[0]===s?-1:1).map(([x,pl])=>`<div style="margin:.2rem 0">${EMO[x]} <span style="color:var(--g)">${x.toUpperCase()}</span>${BUG(x)?'<span style="color:var(--org);font-size:.66rem"> ⚠</span>':''}${x===s?'<span style="color:var(--red);font-size:.66rem"> ← CIBLE</span>':''} <span style="color:var(--t3);margin-left:.22rem">${pl.join(', ')}</span></div>`).join('')+(Object.keys(d.servers).some(x=>BUG(x))||BUG(s)?note:'')+'</div>';}}catch(e){res.innerHTML=`<div class="res err"><div class="rt">Erreur</div>${e.message}</div>`;}}

function wlR(){const el=$('wl-manage'),wl=cwl==='mocha'?WLM:WL;if(!wl.length){el.innerHTML='<div class="empty">Watchlist vide</div>';return;}el.innerHTML=wl.map(p=>`<div class="wi"><span style="font-family:var(--M);font-size:.62rem">${p}</span><button class="btn btn-r" style="padding:.07rem .34rem;font-size:.68rem" onclick="wlRm('${p}')">✕</button></div>`).join('');}
async function wlAdd(){const raw=$('wl-add').value.trim();if(!raw)return;const name=rP(raw,oP);$('wl-add').value='';try{const d=await apiP(cwl==='mocha'?'/api/watchlist_mocha/add':'/api/watchlist/add',{player:name});if(cwl==='mocha')WLM=d.players;else WL=d.players;wlR();wlRS();showToast(`${name} ajouté à la watchlist`);}catch(e){showToast('Erreur : '+e.message);}}
async function wlRm(name){try{const d=await apiP(cwl==='mocha'?'/api/watchlist_mocha/remove':'/api/watchlist/remove',{player:name});if(cwl==='mocha')WLM=d.players;else WL=d.players;wlR();wlRS();showToast(`${name} retiré`);}catch(e){showToast('Erreur : '+e.message);}}
async function switchWl(s){cwl=s;document.querySelectorAll('.wtb').forEach(e=>e.classList.remove('act'));const a=$('wl-tab-'+s);if(a)a.classList.add('act');if($('wl-pt'))$('wl-pt').textContent='◈ Watchlist — '+s.toUpperCase();if($('wl-st'))$('wl-st').textContent='⚡ Statut live — '+s.toUpperCase();$('wl-manage').innerHTML='';$('wl-status').innerHTML='';if(s==='lime')await loadWL();else await loadWLM();wlR();wlRS();}
async function wlRS(){const el=$('wl-status');if(!el)return;el.innerHTML=ld();const s=cwl==='mocha'?'mocha':'lime',wl=cwl==='mocha'?WLM:WL;if(!wl.length){el.innerHTML='<div class="empty">Watchlist vide</div>';return;}try{const c=new AbortController(),t=setTimeout(()=>c.abort(),8000);const r=await fetch(API+'/api/online/'+s,{signal:c.signal});clearTimeout(t);const d=await r.json(),lp=d.players||[];const on=wl.filter(p=>lp.map(x=>x.toLowerCase()).includes(p.toLowerCase()));const off=wl.filter(p=>!lp.map(x=>x.toLowerCase()).includes(p.toLowerCase()));on.forEach(p=>{setLastSeen(p,s);loadSessionDurations(p);});el.innerHTML=[...on.map(p=>{const pred=predictDecoTime(p);return`<div class="wi" onclick="openPlayerPanel('${p}')"><span style="font-family:var(--M);font-size:.62rem">${p}</span><div class="wis on"><div class="led on" style="width:5px;height:5px;flex-shrink:0"></div>EN LIGNE</div><span class="session-timer" data-player="${p}">${getSessionTime(p)||''}</span>${pred?`<span class="pred-badge ${pred.cls}">⏳ ${pred.text}</span>`:''}</div>`;}),...off.map(p=>{const seen=getLastSeenText(p);return`<div class="wi" onclick="openPlayerPanel('${p}')"><span style="font-family:var(--M);font-size:.62rem;opacity:${seen?.cls==='fresh'?'.7':'.38'}">${p}</span><div class="wis off">${seen?`<span class="wi-seen ${seen.cls}">${seen.text}</span>`:'◯ Hors ligne'}</div></div>`;})]
.join('')||'<div class="empty">Aucune donnée</div>';}catch{el.innerHTML=`<div class="empty" style="color:var(--red)">Erreur</div>`;}}

async function loadStats(){
  const raw=$('st-input').value.trim();if(!raw)return;const p=rP(raw,oP);$('st-input').value=p;
  const res=$('st-result');res.innerHTML=`<div class="panel mb"><div class="pacc"></div><div class="ptop"></div><div class="ph"><span class="pt">◐ Analyse — ${p}</span></div><div class="pb">${ld()}</div></div>`;
  const[lR,pR,plR]=await Promise.allSettled([api('/api/checkall/'+encodeURIComponent(p)),api('/api/pronostic/'+encodeURIComponent(p)),api('/api/plages/'+encodeURIComponent(p))]);
  const loc=lR.status==='fulfilled'?lR.value:null,prn=pR.status==='fulfilled'?pR.value:null,plg=plR.status==='fulfilled'?plR.value:null;
  const srvs=loc?loc.servers:[];let h='';
  h+=`<div class="sb"><div class="sbt">◉ Localisation</div>`;
  h+=srvs.length?srvs.map(s=>`<div class="ir"><span class="ik">${EMO[s]} Serveur</span><span class="iv ok">${s.toUpperCase()}</span></div>`).join(''):`<div class="ir"><span class="ik">Statut</span><span class="iv" style="color:var(--t3)">Hors ligne</span></div>`;
  h+='</div>';
  h+=`<div class="sb"><div class="sbt">◐ Pronostic de connexion</div>`;
  if(prn?.pronostic?.length){h+=`<div style="font-family:var(--M);font-size:.68rem;color:var(--t3);margin-bottom:.35rem">Basé sur ${prn.total} connexions</div>`;h+=prn.pronostic.map(r=>`<div class="pr"><span class="pd">${r.day}</span><div class="pb3"><div class="pbf" style="width:${r.pct}%"></div></div><span class="pp">${r.pct}%</span><span class="pt3">${r.avg_h}h${String(r.avg_m).padStart(2,'0')}</span></div>`).join('');}
  else h+=`<div class="ir"><span class="ik">Données</span><span class="iv" style="color:var(--t3)">Insuffisantes (min. 3)</span></div>`;
  h+='</div>';
  h+=`<div class="sb"><div class="sbt">🕐 Heatmap horaire</div>`;
  if(plg?.heatmap){const hm=plg.heatmap,days=plg.days,mx=Math.max(...hm.flat(),1);h+=`<div style="overflow-x:auto"><table style="border-collapse:collapse;font-family:var(--M);font-size:.68rem;width:100%"><tr><td style="color:var(--t3);padding-right:.34rem;white-space:nowrap">H→</td>`;for(let i=0;i<24;i++)h+=`<td style="color:var(--t3);text-align:center;padding:0 1px;font-size:.6rem">${i}</td>`;h+='</tr>';days.forEach((day,di)=>{h+=`<tr><td style="color:var(--g);padding-right:.34rem;white-space:nowrap">${day}</td>`;hm[di].forEach(v=>{const intensity=v?(.04+v/mx*.82).toFixed(2):0;const bg=v?`rgba(0,56,184,${intensity})`:'rgba(2,5,12,.9)';const glow=v&&v/mx>.6?`box-shadow:0 0 4px rgba(0,56,184,${(v/mx*.3).toFixed(2)})`:'';h+=`<td style="width:14px;height:13px;background:${bg};border-radius:1px;padding:0;${glow}"></td>`;});h+='</tr>';});h+='</table></div>';}
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
  if(!_authDone)return;
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
  ctx.beginPath();ctx.arc(lx,ly,3,0,Math.PI*2);ctx.fillStyle='var(--il-blue-lt)';ctx.fill();
  ctx.beginPath();ctx.arc(lx,ly,6,0,Math.PI*2);ctx.fillStyle='rgba(26,111,255,.2)';ctx.fill();
  const lel=document.getElementById('graph-labels');
  if(lel&&actLabels.length>0){
    const step=Math.max(1,Math.floor(actLabels.length/5));
    const shown=actLabels.filter((_,i)=>i%step===0||i===actLabels.length-1);
    lel.textContent='';shown.forEach(l=>{const s=document.createElement('span');s.textContent=l;lel.appendChild(s);});
  }
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
let _authDone=false;
async function requestNotifPerms(){
  if(!('Notification' in window))return;
  if(Notification.permission==='granted'){notifGranted=true;return;}
  if(Notification.permission!=='denied'){const p=await Notification.requestPermission();notifGranted=p==='granted';}
}
function sendBrowserNotif(type,player,server){
  if(!_authDone||!notifGranted||document.visibilityState==='visible')return;
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
  let h='';
  h+=`<div class="pp-info-row">
    <div class="pp-avatar"><img src="https://mc-heads.net/avatar/${encodeURIComponent(player)}/64" onerror="this.style.display='none'" alt=""></div>
    <div class="pp-info-meta">
      <div class="pp-meta-line">${WL.includes(player)?'🎯 Dans la watchlist LIME':''}${WLM.includes(player)?' 🟤 Dans la watchlist MOCHA':''}</div>
      <div class="pp-status ${online?'on':'off'}">
        <div class="led ${online?'on':'off'}" style="width:5px;height:5px;flex-shrink:0"></div>
        ${online?ca.servers.map(s=>`${EMO[s]} ${s.toUpperCase()}`).join(' · '):'Hors ligne'}
      </div>
      ${online?(()=>{const pred=predictDecoTime(player);return pred?`<div class="pred-badge ${pred.cls}" style="margin-top:.3rem">⏳ ${pred.text}</div>`:''})():''}
      ${seen?`<div class="pp-meta-line" style="margin-top:.28rem">${seen.text}</div>`:''}
    </div>
  </div>`;
  h+=`<a class="pp-ng-link" href="${profileUrl}" target="_blank" rel="noopener">↗ Profil NationsGlory</a>`;
  h+=`<div class="pp-section"><div class="pp-sec-title">◐ Pronostic de connexion</div>`;
  if(pr?.pronostic?.length){
    h+=`<div style="font-family:var(--M);font-size:.66rem;color:var(--t3);margin-bottom:.3rem">Basé sur ${pr.total} connexions</div>`;
    h+=pr.pronostic.map(r=>`<div class="pr" style="padding:.28rem 0"><span class="pd">${r.day}</span><div class="pb3"><div class="pbf" style="width:${r.pct}%"></div></div><span class="pp" style="min-width:32px;color:var(--t3);text-align:right;font-size:.74rem">${r.pct}%</span><span style="min-width:44px;color:var(--t1);text-align:right;font-family:var(--M);font-size:.6rem">${r.avg_h}h${String(r.avg_m).padStart(2,'0')}</span></div>`).join('');
  }else h+=`<div style="font-family:var(--M);font-size:.76rem;color:var(--t3)">Pas assez de données</div>`;
  h+='</div>';
  if(pl?.heatmap){
    const hm=pl.heatmap,days=pl.days,mxH=Math.max(...hm.flat(),1);
    h+=`<div class="pp-section"><div class="pp-sec-title">🕐 Heatmap horaire</div><div style="overflow-x:auto"><table class="pp-heatmap" style="border-collapse:collapse;font-family:var(--M);font-size:.64rem"><tr><td style="color:var(--t3);padding-right:.3rem;font-size:.58rem">H→</td>`;
    for(let i=0;i<24;i+=2)h+=`<td colspan="2" style="color:var(--t3);text-align:center;padding:0 1px;font-size:.58rem">${i}</td>`;
    h+='</tr>';
    days.forEach((day,di)=>{h+=`<tr><td style="color:var(--g);padding-right:.3rem;white-space:nowrap;padding-top:2px;font-size:.64rem">${day}</td>`;hm[di].forEach(v=>{const bg=v?`rgba(0,56,184,${(.04+v/mxH*.82).toFixed(2)})`:'rgba(2,5,12,.9)';h+=`<td style="width:13px;height:11px;background:${bg};border-radius:1px;padding:0"></td>`;});h+='</tr>';});
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
  $('cw-suggest').innerHTML=`<span style="font-family:var(--M);font-size:.72rem;color:var(--t3)">Chargement...</span>`;
  try{
    if(!cwCountries[s]){const d=await api('/api/countries/'+s);cwCountries[s]=(d.countries||[]).sort((a,b)=>a.localeCompare(b));}
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
    w.online=online;w.members=members;w.hasNonRecruit=false;w.alertFired=false;
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
        <div class="cw-name">${w.country}</div>
        <div class="cw-meta">${EMO[w.server]||''} ${w.server.toUpperCase()} · assaut possible si ≥ 2 connectés</div>
        ${w.members.length?`<div class="cw-members">${w.members.slice(0,8).map(p=>{const k=p+'@'+w.server;const g=gradeCache[k]?.rank||'?';const col=g&&g!=='recruit'&&g!=='?'?'var(--grn)':g==='recruit'?'var(--red)':'var(--t3)';return`<span style="color:${col}">${p} <span style="font-size:.6rem;opacity:.7">[${g}]</span></span>`;}).join(', ')}${w.members.length>8?` <span style="color:var(--t3)">+${w.members.length-8}</span>`:''}</div>`:''}
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:.35rem">
        <span class="cw-status ${alert?'':'ok'}">${alert?'🚨 ASSAUT POSSIBLE':'◯ PAS ASSEZ'}</span>
        <button class="btn btn-r" style="padding:.08rem .35rem;font-size:.66rem" onclick="cwRemove(${i})">✕</button>
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
    const r=await fetch(`${API}/api/grade/${encodeURIComponent(player)}/${server}`);
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
  _authDone=true;
  const b=$('sound-btn');if(b&&!snd){b.textContent='🔇 SON';b.style.color='var(--t3)';}
  requestNotifPerms();
  api('/api/country_watches').then(d=>{cwWatches=d.watches||[];const stored=JSON.parse(localStorage.getItem('mg_cw')||'[]');stored.forEach(w=>{if(!cwWatches.find(x=>x.server===w.server&&x.country===w.country))cwWatches.push(w);});cwRender();}).catch(()=>{cwWatches=JSON.parse(localStorage.getItem('mg_cw')||'[]');cwRender();});
  rHist();const ok=await chkAPI();$('scan-led').className=ok?'led on':'led off';
  if(ok){
    await loadWL();await loadWLM();loadKP();await loadDash();
    startCountdown(5);
    setInterval(tickCountdown,1000);
    setInterval(async()=>{await loadWL();await loadDash();},5000);
  }
}
init();

// ═══════════════════════════════════════════════════════════
// RED MATTER SIMULATOR — FONCTION MANQUANTE AJOUTÉE EN V2
// ═══════════════════════════════════════════════════════════
function rmCalc() {
  const power   = parseFloat(document.getElementById('rm-power')?.value)   || 0;
  const warzone = parseFloat(document.getElementById('rm-warzone')?.value)  || 0;
  const claims  = parseFloat(document.getElementById('rm-claims')?.value)   || 0;

  if (power <= 0) {
    showToast('⚠ Entre un power total valide');
    return;
  }

  // Formule officielle Red Matter : 0.96^18 × (power − warzone)
  const factor     = Math.pow(0.96, 18);          // ≈ 0.4796
  const effectivePow = power - warzone;
  const powerAfter   = Math.round(effectivePow * factor);
  const powerLost    = Math.round(power - warzone - powerAfter);
  const claimsAfter  = Math.max(0, claims - 8);

  // Affichage résultats
  const results = document.getElementById('rm-results');
  if (results) results.style.display = 'block';

  const elLost   = document.getElementById('rm-lost');
  const elRemain = document.getElementById('rm-remain');
  const elClaims = document.getElementById('rm-claims-out');
  const elAlert  = document.getElementById('rm-alert');

  if (elLost)   { elLost.textContent   = powerLost.toLocaleString('fr-FR');   elLost.style.animation='none'; setTimeout(()=>{elLost.style.animation='bump .35s cubic-bezier(.34,1.56,.64,1)';},10); }
  if (elRemain) { elRemain.textContent = powerAfter.toLocaleString('fr-FR');  elRemain.style.animation='none'; setTimeout(()=>{elRemain.style.animation='bump .35s cubic-bezier(.34,1.56,.64,1)';},10); }
  if (elClaims) { elClaims.textContent = claimsAfter.toLocaleString('fr-FR'); elClaims.style.animation='none'; setTimeout(()=>{elClaims.style.animation='bump .35s cubic-bezier(.34,1.56,.64,1)';},10); }

  // Verdict sous-power ou safe
  if (elAlert) {
    // Règle NationsGlory : sous-power si claims > power / 10
    const needed    = Math.ceil(claimsAfter * 10);
    const isSafe    = powerAfter >= needed;
    const ratio     = powerAfter > 0 ? Math.round((powerAfter / Math.max(needed,1)) * 100) : 0;

    elAlert.style.display = 'block';
    if (isSafe) {
      elAlert.style.background    = 'rgba(0,240,122,.06)';
      elAlert.style.border        = '1px solid rgba(0,240,122,.25)';
      elAlert.style.color         = '#00f07a';
      elAlert.innerHTML = `
        ✅ &nbsp;<strong>SAFE</strong> — Le pays survit au Red Matter<br>
        <span style="opacity:.7">Power restant : <strong>${powerAfter.toLocaleString('fr-FR')}</strong> · Requis pour ${claimsAfter} claims : <strong>${needed.toLocaleString('fr-FR')}</strong> · Ratio : <strong>${ratio}%</strong></span>
      `;
    } else {
      elAlert.style.background    = 'rgba(255,24,64,.06)';
      elAlert.style.border        = '1px solid rgba(255,24,64,.25)';
      elAlert.style.color         = '#ff1840';
      const deficit = needed - powerAfter;
      elAlert.innerHTML = `
        ☢ &nbsp;<strong>SOUS-POWER</strong> — Le pays sera en sous-power !<br>
        <span style="opacity:.7">Déficit : <strong>${deficit.toLocaleString('fr-FR')}</strong> power · Requis : <strong>${needed.toLocaleString('fr-FR')}</strong> · Actuel après impact : <strong>${powerAfter.toLocaleString('fr-FR')}</strong></span>
      `;
    }
  }

  // Son impact
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
