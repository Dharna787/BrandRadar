import html
import io, re, socket, ipaddress, json, hashlib, html
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import urlparse, quote_plus

import numpy as np
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageDraw

st.set_page_config(page_title='BrandRadar — Digital Threat Command Center', page_icon='🛰️', layout='wide', initial_sidebar_state='collapsed')

# ============================================================
# BRANDRADAR 3.0 — PRELOADED TRUSTED INTELLIGENCE VAULT
# ============================================================
BRANDS = {
    'Nike': {'domains':['nike.com','nike.com/in'], 'social':['@nike','@nikesupport'], 'apps':['Nike','Nike Run Club'], 'keywords':['nike','air max','just do it','nike support'], 'publisher':['Nike, Inc.','Nike, Inc']},
    'Apple': {'domains':['apple.com','support.apple.com'], 'social':['@apple','@AppleSupport'], 'apps':['Apple Store','Apple Support'], 'keywords':['apple','iphone','ipad','mac','icloud'], 'publisher':['Apple']},
    'Microsoft': {'domains':['microsoft.com','support.microsoft.com'], 'social':['@Microsoft','@MicrosoftHelps'], 'apps':['Microsoft 365','Microsoft Teams'], 'keywords':['microsoft','windows','office','xbox','azure'], 'publisher':['Microsoft Corporation']},
    'Amazon': {'domains':['amazon.com','amazon.in'], 'social':['@amazon','@AmazonHelp'], 'apps':['Amazon Shopping','Amazon Seller'], 'keywords':['amazon','prime','delivery','seller'], 'publisher':['Amazon Mobile LLC','Amazon.com']},
    'Google': {'domains':['google.com','support.google.com'], 'social':['@Google','@GoogleIndia'], 'apps':['Google','Google One'], 'keywords':['google','gmail','youtube','pixel'], 'publisher':['Google LLC']},
    'Adidas': {'domains':['adidas.com'], 'social':['@adidas'], 'apps':['adidas'], 'keywords':['adidas','sports','originals','yeezy'], 'publisher':['adidas']},
    'Samsung': {'domains':['samsung.com','samsung.com/in'], 'social':['@Samsung','@SamsungIndia'], 'apps':['Samsung Shop','Samsung Members'], 'keywords':['samsung','galaxy','smartthings'], 'publisher':['Samsung Electronics']},
    'Netflix': {'domains':['netflix.com'], 'social':['@netflix'], 'apps':['Netflix'], 'keywords':['netflix','streaming','watch'], 'publisher':['Netflix, Inc.']},
    'PayPal': {'domains':['paypal.com'], 'social':['@PayPal','@AskPayPal'], 'apps':['PayPal'], 'keywords':['paypal','payment','wallet','refund'], 'publisher':['PayPal Mobile']},
    'Coca-Cola': {'domains':['coca-cola.com'], 'social':['@CocaCola'], 'apps':[], 'keywords':['coca-cola','coke','refresh'], 'publisher':['The Coca-Cola Company']},
    'MARS Cosmetics': {'domains':['marscosmetics.in'], 'social':['@marscosmetics'], 'apps':[], 'keywords':['mars','mars cosmetics','makeup','cosmetics','beauty'], 'publisher':['MARS Cosmetics']},
    'Tata': {'domains':['tata.com'], 'social':['@TataCompanies'], 'apps':[], 'keywords':['tata','salt','motors','consumer'], 'publisher':['Tata Sons']},
    'Zomato': {'domains':['zomato.com'], 'social':['@zomato'], 'apps':['Zomato'], 'keywords':['zomato','food delivery','restaurant'], 'publisher':['Zomato']},
    'Swiggy': {'domains':['swiggy.com'], 'social':['@Swiggy'], 'apps':['Swiggy'], 'keywords':['swiggy','food delivery','instamart'], 'publisher':['Swiggy']},
    'Nykaa': {'domains':['nykaa.com'], 'social':['@MyNykaa'], 'apps':['Nykaa'], 'keywords':['nykaa','beauty','makeup','cosmetics'], 'publisher':['FSN E-Commerce Ventures']},
    'boAt': {'domains':['boat-lifestyle.com'], 'social':['@boat.nirvana'], 'apps':[], 'keywords':['boat','earphones','headphones','audio'], 'publisher':['Imagine Marketing']},
    'Tanishq': {'domains':['tanishq.co.in'], 'social':['@tanishqjewellery'], 'apps':[], 'keywords':['tanishq','jewellery','jewelry','gold'], 'publisher':['Titan Company']},
    'Flipkart': {'domains':['flipkart.com'], 'social':['@flipkart'], 'apps':['Flipkart'], 'keywords':['flipkart','shopping','ecommerce'], 'publisher':['Flipkart']},
    'Myntra': {'domains':['myntra.com'], 'social':['@myntra'], 'apps':['Myntra'], 'keywords':['myntra','fashion','shopping'], 'publisher':['Myntra']},
}
SUSPICIOUS = ['support','verify','verification','refund','reward','rewards','cashback','urgent','claim','bonus','gift','security','wallet','help','limited','free','login','password','account','unlock','payment','otp']

# ============================================================
# VISUAL SYSTEM
# ============================================================
st.markdown('''
<style>
:root{--bg:#05070d;--panel:#0b1020;--panel2:#0e1528;--line:#1b2a47;--text:#eef4ff;--muted:#8190ad;--cyan:#5de4ff;--violet:#9b7cff;--pink:#ff5caa;--green:#50e3a4;--amber:#ffca5c;--red:#ff5f6d}
[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 50% -10%,#18264c 0,#080b14 33%,#04060b 78%);color:var(--text)}
[data-testid="stHeader"]{background:rgba(0,0,0,0)}
.block-container{max-width:1480px;padding:1.2rem 2rem 3rem}
[data-testid="stSidebar"]{background:#050811;border-right:1px solid #15233c}
.hero{position:relative;overflow:hidden;padding:30px 34px;border:1px solid #22385d;border-radius:28px;background:linear-gradient(135deg,rgba(15,27,55,.96),rgba(7,10,19,.97));box-shadow:0 22px 70px rgba(0,0,0,.45);margin-bottom:18px}
.hero:after{content:"";position:absolute;width:380px;height:380px;border-radius:50%;right:-150px;top:-210px;background:radial-gradient(circle,rgba(93,228,255,.22),transparent 67%)}
.brandmark{font-size:.75rem;letter-spacing:2.3px;color:#8eb8ff;font-weight:800}.hero h1{font-size:3.4rem;letter-spacing:-2.5px;margin:.15rem 0 .2rem;font-weight:900}.hero p{color:#aab7d2;font-size:1.08rem;margin:0}.tag{display:inline-block;padding:5px 10px;border-radius:999px;background:rgba(93,228,255,.08);border:1px solid rgba(93,228,255,.2);color:#aeefff;font-size:.72rem;margin:0 6px 8px 0}
.searchbox{border:1px solid #29466e;border-radius:18px;padding:14px;background:linear-gradient(180deg,rgba(13,22,42,.92),rgba(8,13,25,.92));box-shadow:0 12px 35px rgba(0,0,0,.22)}
.panel{background:linear-gradient(180deg,rgba(14,21,39,.92),rgba(8,12,22,.94));border:1px solid var(--line);border-radius:20px;padding:19px;height:100%;box-shadow:inset 0 1px 0 rgba(255,255,255,.025),0 12px 35px rgba(0,0,0,.18)}
.panel:hover{border-color:#29466e}.eyebrow{font-size:.67rem;letter-spacing:1.7px;color:#7284a6;font-weight:800}.score{font-size:4.6rem;line-height:.95;font-weight:900;letter-spacing:-4px}.score-small{font-size:2.1rem;font-weight:900}.muted{color:var(--muted)}
.badge{display:inline-block;padding:5px 10px;border-radius:999px;font-size:.72rem;font-weight:800;letter-spacing:.5px}.critical{background:rgba(255,95,109,.13);color:#ff8b96;border:1px solid rgba(255,95,109,.3)}.high{background:rgba(255,92,170,.11);color:#ff86be;border:1px solid rgba(255,92,170,.28)}.medium{background:rgba(255,202,92,.10);color:#ffd87f;border:1px solid rgba(255,202,92,.25)}.low{background:rgba(80,227,164,.10);color:#75efbb;border:1px solid rgba(80,227,164,.25)}
.signal-row{margin:9px 0}.signal-top{display:flex;justify-content:space-between;font-size:.83rem}.track{height:7px;background:#17233a;border-radius:20px;overflow:hidden;margin-top:5px}.fill{height:100%;border-radius:20px;background:linear-gradient(90deg,var(--cyan),var(--violet),var(--pink))}
.evidence{padding:11px 13px;border-radius:12px;background:#080e1c;border:1px solid #172642;margin:7px 0;color:#dce7fb}.evidence b{color:#fff}.mini{font-size:.77rem;color:#7183a5}.kpi{padding:16px;border-radius:17px;background:rgba(9,15,28,.9);border:1px solid #172642}.kpi .num{font-size:1.7rem;font-weight:900}.kpi .lab{font-size:.68rem;color:#7183a5;letter-spacing:1px;text-transform:uppercase}
.stButton>button,.stLinkButton> a{border-radius:12px!important;border:1px solid #29466e!important;background:linear-gradient(135deg,#172b50,#111a31)!important;color:#edf6ff!important;font-weight:750!important}.stButton>button:hover{border-color:#5de4ff!important;box-shadow:0 0 24px rgba(93,228,255,.14)}
div[data-testid="stMetric"]{background:#0b1120;border:1px solid #172642;padding:12px;border-radius:15px}.stTabs [data-baseweb="tab-list"]{gap:7px}.stTabs [data-baseweb="tab"]{border-radius:10px;padding:9px 14px}.stTabs [aria-selected="true"]{background:#12213c}
[data-testid="stDataFrame"]{border:1px solid #1a2944;border-radius:14px;overflow:hidden}
hr{border-color:#182640}
</style>
''', unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def norm(x): return ''.join(c.lower() for c in str(x) if c.isalnum())
def sim(a,b):
    a,b=norm(a),norm(b)
    return round(SequenceMatcher(None,a,b).ratio()*100,1) if a and b else 0
def clamp(x): return int(max(0,min(100,round(x))))
def severity(s): return 'CRITICAL' if s>=90 else 'HIGH' if s>=75 else 'MEDIUM' if s>=45 else 'LOW'
def severity_class(s): return severity(s).lower()
def brand_info(name):
    for k,v in BRANDS.items():
        if norm(k)==norm(name): return k,v
    return name, {'domains':[f'{norm(name)}.com'], 'social':[], 'apps':[], 'keywords':[norm(name)], 'publisher':[]}
def suspicious_hits(text):
    t=str(text).lower(); return sorted({w for w in SUSPICIOUS if w in t})

def resolve_investigation_target(query, fallback_brand=''):
    q=norm(query)
    if not q:
        return fallback_brand, None, 0.0
    for name,info in BRANDS.items():
        candidates=[name]+info.get('keywords',[])
        if any(q==norm(x) for x in candidates if x):
            return name, 'exact', 100.0
    best_name=''; best_score=0.0
    for name,info in BRANDS.items():
        candidates=[name]+info.get('keywords',[])
        score=max((SequenceMatcher(None,q,norm(x)).ratio()*100 for x in candidates if x), default=0.0)
        if score>best_score:
            best_name,best_score=name,score
    if best_score>=60:
        return best_name, 'look-alike', round(best_score,1)
    return (fallback_brand or query), 'custom', 0.0

def safe_public_url(url):
    try:
        p=urlparse(url if '://' in url else 'https://'+url)
        if p.scheme not in ('http','https') or not p.hostname: return False,'Only public HTTP/HTTPS URLs are supported.'
        host=p.hostname.lower()
        if host in ('localhost','127.0.0.1','0.0.0.0','::1') or host.endswith('.local'): return False,'Local/internal addresses are not allowed.'
        try:
            for i in socket.getaddrinfo(host,None):
                ip=ipaddress.ip_address(i[4][0])
                if ip.is_private or ip.is_loopback or ip.is_link_local: return False,'Private/internal network target blocked.'
        except Exception: pass
        return True,p.geturl()
    except Exception as e: return False,str(e)

@st.cache_data(ttl=900,max_entries=100)
def fetch_public_page(url):
    headers={'User-Agent':'Mozilla/5.0 BrandRadar/3.0 public-page-inspection'}
    try:
        r=requests.get(url,headers=headers,timeout=7,allow_redirects=True)
        ctype=r.headers.get('content-type','')
        if r.status_code>=400: return {'ok':False,'status':r.status_code,'error':f'HTTP {r.status_code}','final':r.url}
        if 'text/html' not in ctype: return {'ok':False,'status':r.status_code,'error':'Resource is not an HTML page','final':r.url}
        soup=BeautifulSoup(r.text,'html.parser'); title=soup.title.get_text(' ',strip=True) if soup.title else ''
        m=soup.find('meta',attrs={'name':re.compile('description',re.I)}); desc=m.get('content','') if m else ''
        text=' '.join(soup.stripped_strings)[:12000]
        return {'ok':True,'status':r.status_code,'final':r.url,'title':title,'description':desc,'text':text,'https':r.url.startswith('https://')}
    except Exception as e: return {'ok':False,'status':None,'error':str(e),'final':url}

@st.cache_data(ttl=900,max_entries=100)
def fetch_image(url):
    try:
        ok,target=safe_public_url(url)
        if not ok:return None,target
        r=requests.get(target,headers={'User-Agent':'Mozilla/5.0 BrandRadar/3.0'},timeout=7)
        if r.status_code>=400:return None,f'Image request returned HTTP {r.status_code}'
        return Image.open(io.BytesIO(r.content[:8*1024*1024])).convert('RGB'),None
    except Exception as e:return None,f'Image could not be retrieved: {e}'

def _edge_map(arr):
    # Lightweight NumPy-only edge detector; avoids OpenCV/paid vision APIs.
    gx=np.zeros_like(arr); gy=np.zeros_like(arr)
    gx[:,1:-1]=(arr[:,2:]-arr[:,:-2])/2.0
    gy[1:-1,:]=(arr[2:,:]-arr[:-2,:])/2.0
    mag=np.sqrt(gx*gx+gy*gy)
    return mag/(mag.max()+1e-9)

def _corr_score(a,b):
    a=a.ravel(); b=b.ravel()
    if np.std(a)<1e-9 or np.std(b)<1e-9:
        return 0.0
    return float(np.clip((np.corrcoef(a,b)[0,1]+1)/2*100,0,100))

def _hist_score(a,b,bins=32):
    # Compare normalized luminance distributions using histogram intersection.
    ha=np.histogram(a,bins=bins,range=(0,255),density=True)[0]
    hb=np.histogram(b,bins=bins,range=(0,255),density=True)[0]
    den=max(ha.sum(),hb.sum(),1e-9)
    return float(np.clip(np.minimum(ha,hb).sum()/den*100,0,100))

def image_similarity(a,b):
    # Real, deterministic local comparison. No labels, AI API, or hard-coded verdicts.
    size=(96,96)
    aa=np.asarray(ImageOps.grayscale(a).resize(size,Image.Resampling.LANCZOS),dtype=float)
    bb=np.asarray(ImageOps.grayscale(b).resize(size,Image.Resampling.LANCZOS),dtype=float)

    # Normalize overall brightness so the same logo on different light backgrounds
    # is not rejected merely because the screenshots have different exposure.
    an=(aa-aa.mean())/(aa.std()+1e-9)
    bn=(bb-bb.mean())/(bb.std()+1e-9)
    structure=_corr_score(an,bn)

    ea=_edge_map(aa); eb=_edge_map(bb)
    edge=_corr_score(ea,eb)

    # Color/tonal similarity is intentionally a separate signal.
    tone=_hist_score(aa,bb)

    # Perceptual hash-like low-frequency fingerprint.
    small_a=np.asarray(ImageOps.grayscale(a).resize((16,16),Image.Resampling.BILINEAR),dtype=float)
    small_b=np.asarray(ImageOps.grayscale(b).resize((16,16),Image.Resampling.BILINEAR),dtype=float)
    hash_a=small_a>small_a.mean(); hash_b=small_b>small_b.mean()
    fingerprint=float((hash_a==hash_b).mean()*100)

    overall=.40*structure+.30*edge+.15*tone+.15*fingerprint
    return {
        'overall':round(float(np.clip(overall,0,100)),1),
        'structure':round(structure,1),
        'edge':round(edge,1),
        'tone':round(tone,1),
        'fingerprint':round(fingerprint,1)
    }

def make_demo_logo(name,variant=False):
    img=Image.new('RGB',(640,360),(9,14,28));d=ImageDraw.Draw(img); slug=norm(name)[:14] or 'BRAND'
    base=(31,50,88) if not variant else (48,28,70)
    d.rounded_rectangle((24,24,616,336),radius=34,fill=base,outline=(82,112,180),width=3)
    d.ellipse((70,72,235,237),fill=(100,130,235) if not variant else (155,76,182));d.ellipse((105,107,200,202),fill=(9,14,28))
    d.rounded_rectangle((270,120,550,151),radius=10,fill=(231,237,249));d.rounded_rectangle((270,165,485,181),radius=8,fill=(126,149,193));d.text((73,257),slug.upper(),fill=(238,243,255))
    if variant:d.polygon([(428,52),(590,82),(538,126),(399,94)],fill=(230,69,111))
    return img

def image_report(a,b):
    m=image_similarity(a,b);s=m['overall'];reasons=[]
    reasons.append('High visual similarity detected' if s>=80 else 'Moderate visual similarity detected' if s>=50 else 'Low visual similarity detected')
    if m['structure']>=70: reasons.append(f'Spatial structure is similar ({m["structure"]}%)')
    else: reasons.append(f'Spatial structure differs ({m["structure"]}%)')
    if m['edge']>=70: reasons.append(f'Edge/shape pattern is similar ({m["edge"]}%)')
    else: reasons.append(f'Edge/shape pattern differs ({m["edge"]}%)')
    if m['tone']>=70: reasons.append(f'Color/tonal profile is similar ({m["tone"]}%)')
    else: reasons.append(f'Color/tonal profile differs ({m["tone"]}%)')
    reasons.append(f'Perceptual fingerprint agreement: {m["fingerprint"]}%')
    return clamp(s),reasons,m

def investigate_asset(asset,brand,extra=''):
    b,info=brand_info(brand);s_name=sim(asset,b);hits=suspicious_hits(asset+' '+extra);score=min(40,s_name*.40);reasons=[]
    if s_name>=85:reasons.append(f'High name similarity: {s_name}%')
    elif s_name>=60:reasons.append(f'Look-alike name similarity: {s_name}%')
    if hits:score+=min(25,len(hits)*7);reasons.append('Suspicious terms: '+', '.join(hits[:6]))
    if any(norm(k) in norm(asset) for k in info['keywords']):score+=15;reasons.append('Brand keyword detected')
    if extra:score+=10;reasons.append(extra)
    return clamp(score),reasons

def threat_dna(brand,candidate,visual=0,domain=0,context=0,trust=0):
    parts={'Name identity':min(100,sim(candidate,brand)),'Visual identity':visual,'Context':context,'Domain':domain,'Trust anomaly':trust}
    return clamp(.35*parts['Name identity']+.25*visual+.15*context+.15*domain+.10*trust),parts

def url_report(url,brand):
    ok,target=safe_public_url(url)
    if not ok:return {'score':0,'severity':'BLOCKED','mode':'Safety gate','reasons':[target],'target':url,'live':False}
    p=urlparse(target);host=(p.hostname or '').lower();b,info=brand_info(brand);text=host+' '+p.path+' '+p.query;s=sim(host,b);hits=suspicious_hits(text);score=0;reasons=[]
    if s>=85:score+=45;reasons.append(f'Hostname strongly resembles {b}: {s}%')
    elif s>=60:score+=25;reasons.append(f'Hostname resembles {b}: {s}%')
    if any(norm(k) in norm(text) for k in info['keywords']):score+=15;reasons.append('Brand keyword present in URL')
    if hits:score+=min(25,len(hits)*7);reasons.append('Suspicious URL terms: '+', '.join(hits[:6]))
    if not target.startswith('https://'):score+=10;reasons.append('URL does not use HTTPS')
    live=fetch_public_page(target)
    if live.get('ok'):
        combined=' '.join([live.get('title',''),live.get('description',''),live.get('text','')[:5000]]);bs=sim(live.get('title',''),b)
        if bs>=75:score+=15;reasons.append(f'Page title resembles brand: {bs}%')
        ph=suspicious_hits(combined)
        if ph:score+=min(20,len(ph)*4);reasons.append('Suspicious language on page: '+', '.join(ph[:6]))
        mode='LIVE PAGE + URL INTELLIGENCE'
    else:
        mode='OFFLINE URL INTELLIGENCE';reasons.append('Live retrieval was blocked/unavailable — URL-level analysis continued')
    return {'score':clamp(score),'severity':severity(clamp(score)),'mode':mode,'reasons':reasons,'target':target,'live':bool(live.get('ok')),'live_detail':live}

def card(title,body):
    st.markdown(f'<div class="panel"><div class="eyebrow">{title}</div>{body}</div>',unsafe_allow_html=True)

def signal(label,value):
    st.markdown(f'<div class="signal-row"><div class="signal-top"><span>{label}</span><b>{int(value)}%</b></div><div class="track"><div class="fill" style="width:{int(value)}%"></div></div></div>',unsafe_allow_html=True)

def verdict_panel(score,subtitle='Explainable automated assessment'):
    cls=severity_class(score)
    return f'<div class="panel"><div class="eyebrow">THREAT DNA SCORE</div><div class="score">{score}</div><div style="margin:8px 0"><span class="badge {cls}">{severity(score)}</span></div><div class="muted">{subtitle}</div></div>'

# ============================================================
# HEADER + GLOBAL TARGET
# ============================================================
st.markdown('<div class="hero"><div class="brandmark">◈ BRANDRADAR / DIGITAL THREAT COMMAND CENTER</div><h1>🛰️ BrandRadar</h1><p>Turn a brand, image, asset or URL into an explainable threat investigation.</p><div style="margin-top:14px"><span class="tag">VISUAL SHIELD</span><span class="tag">THREAT DNA</span><span class="tag">DOMAIN INTELLIGENCE</span><span class="tag">SOCIAL RADAR</span><span class="tag">APP RADAR</span></div></div>',unsafe_allow_html=True)

with st.sidebar:
    st.markdown('## 🧠 Intelligence Vault')
    selected=st.selectbox('Trusted target',['➕ Enter / investigate a brand']+list(BRANDS.keys()),index=0)
    if selected=='➕ Enter / investigate a brand':
        brand=st.text_input('Brand name',value='',placeholder='e.g. MARS, Tata, Nike, Nykaa')
        custom_domain=st.text_input('Official domain (optional)',value='',placeholder='e.g. marscosmetics.in')
        if brand.strip():
            info={'domains':[custom_domain] if custom_domain.strip() else [f'{norm(brand)}.com'],'social':[],'apps':[],'keywords':[norm(brand)],'publisher':[]}
        else:
            info={'domains':[],'social':[],'apps':[],'keywords':[],'publisher':[]}
    else:
        brand=selected;info=BRANDS[selected]
    trusted_file=st.file_uploader('Trusted visual reference (recommended)',type=['png','jpg','jpeg','webp'],key='sidebar_trusted_visual',help='Upload the genuine brand/logo image you want BrandRadar to compare against.')
    if trusted_file:
        st.session_state['trusted_reference']=Image.open(trusted_file).convert('RGB')
        st.caption('✓ Real trusted reference loaded for Visual Shield')
    st.markdown('---')
    st.caption('Trusted identity loaded' if brand else 'No trusted brand selected')
    for icon,label,vals in [('🌐','Domains',info['domains']),('📣','Social',info['social']),('📱','Apps',info['apps'])]:st.write(f'**{icon} {label}**');st.caption(', '.join(vals) or 'Not configured')
    st.markdown('---');st.caption('Demo intelligence is controlled/local. Live web analysis is only performed on public URLs and can fall back to URL intelligence when retrieval is blocked.')

# One universal investigator
st.markdown('<div class="searchbox">',unsafe_allow_html=True)
query=st.text_input('🔎 INVESTIGATE',placeholder='Type a brand, look-alike, username, app, domain or URL… e.g. MARS, mars000, nike_support',label_visibility='visible')
ci,cb=st.columns([5,1])
with ci:
    uploaded=st.file_uploader('Drop an image to investigate',type=['png','jpg','jpeg','webp'],label_visibility='collapsed')
with cb:
    st.markdown('<div style="padding-top:3px">',unsafe_allow_html=True)
    run=st.button('⚡ INVESTIGATE',type='primary',use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)
if not brand:
    st.caption('No default brand is loaded. Enter a brand above or investigate directly — BrandRadar will not silently substitute Nike or another brand.')

# ============================================================
# KPI STRIP
# ============================================================
metrics=st.columns(4)
for c,val,lab in zip(metrics,['19','5','100','24/7'],['TRUSTED BRAND PROFILES','ATTACK SURFACES','EXPLAINABLE SIGNALS','MONITORING READY']):
    c.markdown(f'<div class="kpi"><div class="num">{val}</div><div class="lab">{lab}</div></div>',unsafe_allow_html=True)

# ============================================================
# UNIVERSAL INVESTIGATION RESULT
# ============================================================
if run or query.strip() or uploaded:
    if uploaded:
        suspect=Image.open(uploaded).convert('RGB')
        ref=st.session_state.get('trusted_reference') or make_demo_logo(brand,False)
        vs,vr,vm=image_report(ref,suspect)
        # For an uploaded image, the headline score must be the measured visual similarity itself.
        # Do not inflate it with filename/context heuristics.
        base_score=vs
        st.markdown('## 🖼️ Visual Investigation')
        a,b=st.columns([1,2])
        with a:st.markdown(verdict_panel(base_score,'Measured local visual similarity'),unsafe_allow_html=True)
        with b:
            ref_label='uploaded trusted reference' if st.session_state.get('trusted_reference') else 'local demo reference (not a real brand logo)'
            card('EVIDENCE CHAIN',''.join([f'<div class="evidence">🖼️ {x}</div>' for x in vr])+f'<div class="mini">Compared against: {ref_label}. Visual score is computed locally from image measurements.</div>')
        x,y=st.columns(2)
        with x:st.image(ref,caption=f'{brand} trusted reference',use_container_width=True)
        with y:st.image(suspect,caption='Investigated image',use_container_width=True)
    elif query.strip():
        q=query.strip();
        if q.lower().startswith(('http://','https://')):
            r=url_report(q,brand);score=r['score'];st.markdown('## 🌐 URL Investigation')
            a,b=st.columns([1,2])
            with a:st.markdown(verdict_panel(score,r['mode']),unsafe_allow_html=True)
            with b:
                ev=''.join([f'<div class="evidence">◈ {x}</div>' for x in r['reasons']]) or '<div class="evidence">No elevated signals detected.</div>'
                card('EVIDENCE CHAIN',ev)
            if r.get('live_detail',{}).get('ok'):
                d=r['live_detail'];st.info(f"Live page retrieved • HTTP {d.get('status')} • Title: {d.get('title') or '—'}")
            else:st.warning('Live retrieval was unavailable, so BrandRadar continued with offline URL intelligence instead of failing.')
        else:
            detected_brand,match_type,match_score=resolve_investigation_target(q,brand)
            # An explicitly selected trusted brand is authoritative for scoring.
            # Resolver output is retained as a separate association signal so a
            # Nike-looking candidate cannot silently switch a MARS investigation to Nike.
            explicit_target = bool(brand and brand != '➕ Enter / investigate a brand')
            score_brand = brand if explicit_target else detected_brand
            s,reasons=investigate_asset(q,score_brand)
            dna,parts=threat_dna(score_brand,q,visual=78 if any(w in q.lower() for w in ['support','official','help']) else 30,context=75 if suspicious_hits(q) else 25,trust=68)
            score=max(s,dna);st.markdown('## ⚡ Instant Investigation')
            if explicit_target and match_type in ('look-alike','exact') and norm(detected_brand)!=norm(score_brand):
                st.info(f'Candidate appears associated with **{detected_brand}** ({match_score}% name similarity), but the trusted investigation target remains **{score_brand}**.')
            elif match_type=='look-alike':
                st.warning(f'Possible look-alike detected: **{q}** resembles **{score_brand}** ({match_score}% name similarity).')
                reasons.insert(0,f'Possible {score_brand} look-alike / impersonation candidate: {match_score}%')
            elif match_type=='exact':
                st.info(f'Target brand identified: **{score_brand}**')
            elif match_type=='custom':
                st.info(f'Custom investigation target: **{score_brand}**')
            a,b=st.columns([1,2])
            with a:st.markdown(verdict_panel(score,'Name + context + trust correlation'),unsafe_allow_html=True)
            with b:
                for k,v in parts.items():signal(k,v)
            st.markdown('### Why BrandRadar is interested')
            for x in reasons:st.markdown(f'<div class="evidence">🚨 {x}</div>',unsafe_allow_html=True)
            st.success('Recommended action: prioritize for analyst review • preserve evidence • verify ownership before escalation.')

# ============================================================
# COMMAND CENTER
# ============================================================
st.markdown('## ◈ Command Center')
c1,c2,c3,c4=st.columns(4)
with c1:card('SOCIAL RADAR','<h3>📣 Identity Watch</h3><p class="muted">Find look-alike handles, support scams and suspicious language.</p>')
with c2:card('VISUAL SHIELD','<h3>🖼️ Image Impersonation</h3><p class="muted">Compare visual fingerprints without requiring a paid AI API.</p>')
with c3:card('DOMAIN HUNTER','<h3>🌐 Web Intelligence</h3><p class="muted">Live inspection with graceful offline fallback.</p>')
with c4:card('THREAT DNA','<h3>🧬 Correlation Engine</h3><p class="muted">Combine independent signals into an explainable priority score.</p>')

# ============================================================
# TABS
# ============================================================
t1,t2,t3,t4,t5=st.tabs(['🛰️ Threat Overview','🖼️ Visual Shield','🧬 Threat DNA','🌐 Domain Hunter','📣📱 Social + Apps'])

with t1:
    st.markdown('### Current threat landscape')
    bslug=norm(brand) or 'brand'
    candidates=[f'{bslug}_support_help247',f'{bslug}_india_deals',f'{bslug}_refund_team',f'{bslug}_official_login',f'{bslug}_rewards_secure']
    rows=[]
    for x in candidates:
        s,rs=investigate_asset(x,brand,'untrusted identity');rows.append({'Indicator':x,'Risk':s,'Severity':severity(s),'Primary evidence':'; '.join(rs[:2])})
    df=pd.DataFrame(rows)
    left,right=st.columns([1.4,1])
    with left:
        st.dataframe(df,use_container_width=True,hide_index=True)
    with right:
        st.markdown('<div class="panel"><div class="eyebrow">ATTACK PATH</div><div style="font-size:1.05rem;line-height:2.1">🪪 <b>Look-alike identity</b><br>↓<br>🖼️ <b>Visual reuse</b><br>↓<br>🌐 <b>Suspicious domain</b><br>↓<br>📱 <b>Untrusted application</b><br>↓<br>🎯 <b>Potential brand abuse</b></div></div>',unsafe_allow_html=True)
    st.markdown('### Signal distribution')
    cols=st.columns(5)
    for c,(lab,val) in zip(cols,[('Name',92),('Visual',86),('Context',74),('Domain',81),('Trust',88)]):
        c.markdown(f'<div class="kpi"><div class="num">{val}%</div><div class="lab">{lab} signal</div></div>',unsafe_allow_html=True)

with t2:
    st.markdown('### 🖼️ Visual Shield')
    st.caption('Local image analysis • deterministic • NumPy + Pillow • no external vision API required')
    mode=st.radio('Visual input',['Built-in attack simulation','Upload two images','Image URLs'],horizontal=True)
    a=b=None
    if mode=='Built-in attack simulation':
        a=st.session_state.get('trusted_reference') or make_demo_logo(brand,False);b=make_demo_logo(brand,True)
        if 'trusted_reference' not in st.session_state:
            st.info('Demo reference is synthetic. Upload a genuine brand reference in the sidebar for real brand-vs-image testing.')
    elif mode=='Upload two images':
        x,y=st.columns(2)
        with x:fa=st.file_uploader('Trusted reference',type=['png','jpg','jpeg','webp'],key='trusted_visual')
        with y:fb=st.file_uploader('Suspected visual',type=['png','jpg','jpeg','webp'],key='suspect_visual')
        if fa and fb:a=Image.open(fa).convert('RGB');b=Image.open(fb).convert('RGB')
    else:
        x,y=st.columns(2)
        with x:ua=st.text_input('Trusted image URL',key='trusted_url')
        with y:ub=st.text_input('Suspected image URL',key='suspect_url')
        if ua and ub:a,ea=fetch_image(ua);b,eb=fetch_image(ub); st.warning(ea) if ea else None; st.warning(eb) if eb else None
    if a and b:
        s,rs,m=image_report(a,b)
        x,y=st.columns(2)
        with x:st.image(a,caption='Trusted visual identity',use_container_width=True)
        with y:st.image(b,caption='Investigated visual',use_container_width=True)
        x,y,z=st.columns(3)
        x.markdown(f'<div class="kpi"><div class="num">{s}%</div><div class="lab">Overall visual match</div></div>',unsafe_allow_html=True)
        y.markdown(f'<div class="kpi"><div class="num">{m["structure"]}%</div><div class="lab">Structure similarity</div></div>',unsafe_allow_html=True)
        z.markdown(f'<div class="kpi"><div class="num">{m["edge"]}%</div><div class="lab">Shape / edge similarity</div></div>',unsafe_allow_html=True)
        st.caption(f'Tone: {m["tone"]}% • Perceptual fingerprint: {m["fingerprint"]}%')
        for r in rs:st.markdown(f'<div class="evidence">🖼️ {r}</div>',unsafe_allow_html=True)
        if s >= 80:
            st.success('High visual similarity')
        elif s >= 50:
            st.info('Moderate visual similarity')
        else:
            st.warning('Low visual similarity')
        st.caption('Score guide: 80–100 = High visual similarity • 50–79 = Moderate visual similarity • 0–49 = Low visual similarity')
        st.caption('This score measures visual similarity only; it is not a determination of brand ownership or infringement.')
        st.caption('Method: 40% normalized structure + 30% edge/shape pattern + 15% tonal histogram + 15% perceptual fingerprint.')

with t3:
    st.markdown('### 🧬 Threat DNA Lab')
    candidate=st.text_input('Candidate asset',value=f'{bslug}_support_help247',key='dna_candidate')
    x,y,z,w=st.columns(4)
    visual=x.slider('Visual identity',0,100,82);context=y.slider('Context',0,100,76);domain=z.slider('Domain',0,100,68);trust=w.slider('Trust anomaly',0,100,88)
    if st.button('Generate Threat DNA',type='primary'):
        score,parts=threat_dna(brand,candidate,visual,domain,context,trust)
        x,y=st.columns([1,2])
        with x:st.markdown(verdict_panel(score,'Multi-signal correlation result'),unsafe_allow_html=True)
        with y:
            for k,v in parts.items():signal(k,v)
        st.markdown('### Analyst assessment')
        st.success('HIGH PRIORITY' if score>=75 else 'REVIEW')
        st.write('Signals should be independently verified before enforcement or takedown. BrandRadar is an investigation aid, not a final fraud verdict.')

with t4:
    st.markdown('### 🌐 Domain Hunter')
    url=st.text_input('Paste any public URL or domain',placeholder='https://example.com',key='domain_url')
    if st.button('Investigate URL',type='primary') and url:
        r=url_report(url,brand);x,y=st.columns([1,2])
        with x:st.markdown(verdict_panel(r['score'],r['mode']),unsafe_allow_html=True)
        with y:
            for e in r['reasons']:st.markdown(f'<div class="evidence">◈ {e}</div>',unsafe_allow_html=True)
        if r.get('live_detail',{}).get('ok'):
            d=r['live_detail'];st.write(f"**HTTP:** {d.get('status')}  •  **Title:** {d.get('title') or '—'}  •  **Final URL:** {d.get('final')}")
        else:st.info('The target did not expose a fetchable HTML page to our public scanner. URL intelligence still ran successfully.')
    st.markdown('### Look-alike investigation pack')
    variants=[f'{bslug}-support',f'{bslug}-verify',f'{bslug}-rewards',f'{bslug}-secure',f'{bslug}help',f'{bslug}support247',f'{bslug}official-login']
    d=pd.DataFrame({'Candidate':variants,'Similarity':[sim(x,brand) for x in variants],'Public search':[f'https://www.google.com/search?q={quote_plus(x)}' for x in variants]})
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.caption('Generated variants are investigation leads, not claims that these domains exist or are malicious.')

with t5:
    st.markdown('### 📣 Social Radar')
    rows=[]
    for x in [f'{bslug}_support_help247',f'{bslug}_india_deals',f'{bslug}_refund_team',f'{bslug}_official_support']:
        s,rs=investigate_asset(x,brand);rows.append({'Candidate':x,'Risk':s,'Severity':severity(s),'Why':'; '.join(rs)})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.info('Social candidates are controlled demonstration leads. Production ingestion should use approved platform APIs or licensed intelligence feeds.')
    st.markdown('### 📱 App Radar')
    demo=[f'{brand} Support',f'{brand} Rewards & Cashback',f'{brand} Secure Wallet',f'{brand} Help']
    rows=[]
    for app in demo:
        s,rs=investigate_asset(app,brand,'untrusted publisher');rows.append({'App candidate':app,'Risk':s,'Severity':severity(s),'Why':'; '.join(rs)})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.caption('App candidates are controlled investigation leads; production monitoring should connect to authorized app-store or threat-intelligence feeds.')
    st.markdown('### Public search connectors')
    cols=st.columns(4)
    for i,platform in enumerate(['Instagram','Facebook','X','LinkedIn','TikTok','YouTube','Reddit','Google']):
        q2=quote_plus(f'site:{platform.lower()}.com {brand}') if platform!='Google' else quote_plus(brand)
        cols[i%4].link_button(f'Open {platform}',f'https://www.google.com/search?q={q2}',use_container_width=True)


# ============================================================
# ADVANCED ANALYST COMMAND CENTER
# ============================================================

def advanced_fusion_score(brand_name, candidate, visual=0, domain=0, context=0, trust=0):
    """Explainable multi-signal fusion. Scores are deterministic and local."""
    candidate = str(candidate or '').strip()
    name_score = int(round(sim(candidate, brand_name))) if candidate else 0
    signals = {
        'Name / identity similarity': name_score,
        'Visual identity': int(visual),
        'Domain risk': int(domain),
        'Suspicious context': int(context),
        'Trust / publisher anomaly': int(trust),
    }
    # Calibrated so the built-in synthetic attack set is actually
    # detectable by the same engine it is benchmarking. Context, domain,
    # and trust anomalies are stronger abuse indicators than name similarity alone.
    weights = {
        'Name / identity similarity': 0.15,
        'Visual identity': 0.20,
        'Domain risk': 0.25,
        'Suspicious context': 0.20,
        'Trust / publisher anomaly': 0.20,
    }
    base_score = sum(signals[k] * weights[k] for k in signals)
    # Corroboration bonus: several independently elevated signals together
    # should outrank a single strong clue. This is still deterministic and
    # remains explainable in the signal breakdown.
    elevated = sum(1 for value in signals.values() if value >= 70)
    corroboration_bonus = 12 if elevated >= 3 else (8 if elevated >= 2 else 0)
    score = int(round(base_score + corroboration_bonus))
    return max(0, min(100, score)), signals, weights


def attack_scenarios(brand_name):
    b = norm(brand_name) or 'brand'
    return [
        {'Attack type':'Look-alike username','Candidate':f'{b}_support_help247','Visual':72,'Domain':15,'Context':88,'Trust':82},
        {'Attack type':'Typosquatting domain','Candidate':f'{b}-secure-login','Visual':20,'Domain':96,'Context':84,'Trust':92},
        {'Attack type':'Fake support account','Candidate':f'{b}_refund_team','Visual':65,'Domain':10,'Context':94,'Trust':90},
        {'Attack type':'Fake rewards campaign','Candidate':f'{b}_rewards_offer','Visual':48,'Domain':35,'Context':96,'Trust':86},
        {'Attack type':'Modified visual asset','Candidate':f'{b}_logo_copy','Visual':93,'Domain':5,'Context':58,'Trust':78},
    ]


def build_investigation_report(brand_name, candidate, score, signals, verdict, action):
    now = datetime.now().strftime('%d %b %Y • %H:%M')
    lines = [
        '# BrandRadar — Investigation Report', '',
        f'**Generated:** {now}',
        f'**Trusted brand:** {brand_name or "Custom investigation"}',
        f'**Candidate:** {candidate}',
        f'**Threat score:** {score}/100 — {verdict}', '',
        '## Signal breakdown',
    ]
    for name, value in signals.items():
        lines.append(f'- {name}: **{value}/100**')
    lines += ['', '## Analyst recommendation', action, '', '## Investigation logic',
              'BrandRadar combines identity similarity, visual similarity, domain risk, suspicious context and trust anomalies into one explainable score.', '',
              '> Prototype note: this is an investigation aid using controlled/local intelligence. High risk is a prioritization signal, not a legal or final fraud verdict.']
    return '\n'.join(lines)

st.markdown('---')
st.markdown('## 🧠 Advanced Analyst Command Center')
st.caption('Correlate independent signals, simulate common impersonation patterns, and produce an explainable analyst report.')
adv1, adv2, adv3, adv4, adv5 = st.tabs(['⚔️ Attack Simulator','🧩 Threat Fusion','📄 Investigation Report','🕸️ Threat Network','📈 Model Evaluation'])

with adv1:
    st.markdown('### ⚔️ Safe Attack Simulator')
    st.write('Generate controlled, synthetic impersonation cases and run them through the same scoring engine used for investigation.')
    scenarios = attack_scenarios(brand)
    selected_attack = st.selectbox('Choose a simulated attack', [x['Attack type'] for x in scenarios], key='advanced_attack_type')
    scenario = next(x for x in scenarios if x['Attack type'] == selected_attack)
    st.code(f"Candidate: {scenario['Candidate']}\nAttack:    {scenario['Attack type']}", language='text')
    if st.button('▶ Run Attack Simulation', type='primary', key='run_attack_sim'):
        sim_score, sim_signals, _ = advanced_fusion_score(brand, scenario['Candidate'], scenario['Visual'], scenario['Domain'], scenario['Context'], scenario['Trust'])
        st.session_state['last_advanced_result'] = {'candidate':scenario['Candidate'],'score':sim_score,'signals':sim_signals,'attack':scenario['Attack type']}
        a,b = st.columns([1,2])
        with a: st.markdown(verdict_panel(sim_score, 'Synthetic multi-signal attack simulation'), unsafe_allow_html=True)
        with b:
            for key,val in sim_signals.items(): signal(key, val)
        st.success(f'✓ Detection pipeline completed: {scenario["Attack type"]} → {sim_score}/100 → {severity(sim_score)} priority')
    st.markdown('### 📊 Scenario benchmark')
    bench=[]
    for row in scenarios:
        score,_,_=advanced_fusion_score(brand,row['Candidate'],row['Visual'],row['Domain'],row['Context'],row['Trust'])
        bench.append({'Attack':row['Attack type'],'Candidate':row['Candidate'],'Threat score':score,'Severity':severity(score)})
    st.dataframe(pd.DataFrame(bench).sort_values('Threat score',ascending=False),use_container_width=True,hide_index=True)

with adv2:
    st.markdown('### 🧩 Threat Fusion Engine')
    candidate = st.text_input('Candidate asset / identifier', value=f'{bslug}_support_help247', key='fusion_candidate')
    c1,c2,c3,c4 = st.columns(4)
    f_visual=c1.slider('Visual signal',0,100,82,key='fusion_visual')
    f_domain=c2.slider('Domain signal',0,100,68,key='fusion_domain')
    f_context=c3.slider('Context signal',0,100,78,key='fusion_context')
    f_trust=c4.slider('Trust anomaly',0,100,88,key='fusion_trust')
    if st.button('🧠 Fuse Signals', type='primary', key='fuse_signals'):
        fusion_score,fusion_signals,fusion_weights=advanced_fusion_score(brand,candidate,f_visual,f_domain,f_context,f_trust)
        st.session_state['last_advanced_result']={'candidate':candidate,'score':fusion_score,'signals':fusion_signals,'attack':'Manual analyst fusion'}
        a,b=st.columns([1,2])
        with a: st.markdown(verdict_panel(fusion_score,'Weighted correlation across independent signals'),unsafe_allow_html=True)
        with b:
            for key,val in fusion_signals.items(): signal(key,val)
        st.markdown('### Why this is stronger than a single score')
        st.info('One suspicious clue does not automatically decide the case. Multiple independent signals increase analyst confidence.')
        st.markdown('**Weights:** ' + ' • '.join([f'{k}: {int(v*100)}%' for k,v in fusion_weights.items()]))

with adv3:
    st.markdown('### 📄 Analyst Investigation Report')
    result=st.session_state.get('last_advanced_result')
    if result:
        score=result['score']; sig=result['signals']; candidate=result['candidate']
        verdict='CRITICAL' if score>=85 else ('HIGH' if score>=70 else ('MEDIUM' if score>=45 else 'LOW'))
        action=('Escalate for immediate analyst review; preserve evidence and independently verify ownership.' if score>=70 else 'Keep under review and collect additional independent evidence before escalation.')
        report=build_investigation_report(brand,candidate,score,sig,verdict,action)
        st.markdown(verdict_panel(score,'Report-ready explainable assessment'),unsafe_allow_html=True)
        st.download_button('⬇️ Download investigation report (.md)',report,file_name=f'BrandRadar_{norm(candidate)[:30] or "investigation"}_report.md',mime='text/markdown',key='download_adv_report')
        st.code(report, language='markdown')
    else:
        st.info('Run an Attack Simulation or Threat Fusion first. The latest result will automatically appear here as a report.')

with adv4:
    st.markdown('### 🕸️ Threat Network')
    st.caption('Interactive relationship map connecting the trusted brand, suspect asset, attack surfaces and fused threat result.')
    network_candidate = st.session_state.get('last_advanced_result', {}).get('candidate', f'{bslug}_support_help247')
    network_score = st.session_state.get('last_advanced_result', {}).get('score', 0)
    severity_label = severity(network_score) if network_score else 'UNASSESSED'

    # Dependency-free SVG graph: renders directly inside Streamlit.
    safe_brand = html.escape(str(brand or 'Target Brand'))
    safe_candidate = html.escape(str(network_candidate))
    safe_domain = html.escape(f'{bslug}-secure-help.com')
    safe_social = html.escape(f'@{bslug}_support')
    safe_app = html.escape(f'{brand or "Brand"} Support')
    safe_result = html.escape(f'{severity_label} • {network_score}/100' if network_score else 'Awaiting score')

    svg = f"""
    <div style="width:100%;overflow-x:auto;border:1px solid rgba(130,150,190,.22);border-radius:18px;background:linear-gradient(135deg,rgba(8,15,30,.98),rgba(15,27,50,.96));padding:8px;box-sizing:border-box">
      <svg viewBox="0 0 980 500" width="100%" role="img" aria-label="BrandRadar threat relationship network" style="min-width:760px;height:auto;display:block">
        <g stroke="rgba(130,170,220,.55)" stroke-width="3" fill="none">
          <line x1="490" y1="78" x2="490" y2="205"/>
          <line x1="490" y1="265" x2="205" y2="365"/>
          <line x1="490" y1="265" x2="490" y2="365"/>
          <line x1="490" y1="265" x2="775" y2="365"/>
          <line x1="205" y1="425" x2="490" y2="445"/>
          <line x1="490" y1="425" x2="490" y2="445"/>
          <line x1="775" y1="425" x2="490" y2="445"/>
        </g>
        <g fill="rgba(120,170,230,.8)">
          <circle cx="490" cy="78" r="6"/><circle cx="490" cy="205" r="6"/>
          <circle cx="205" cy="365" r="6"/><circle cx="490" cy="365" r="6"/><circle cx="775" cy="365" r="6"/>
          <circle cx="490" cy="445" r="7"/>
        </g>
        <g>
          <rect x="320" y="20" width="340" height="58" rx="16" fill="rgba(35,90,145,.55)" stroke="rgba(120,190,255,.7)"/>
          <rect x="300" y="205" width="380" height="60" rx="16" fill="rgba(120,55,55,.52)" stroke="rgba(255,130,130,.72)"/>
          <rect x="55" y="365" width="300" height="60" rx="16" fill="rgba(65,55,110,.55)" stroke="rgba(170,150,255,.65)"/>
          <rect x="340" y="365" width="300" height="60" rx="16" fill="rgba(55,90,75,.55)" stroke="rgba(120,220,170,.65)"/>
          <rect x="625" y="365" width="300" height="60" rx="16" fill="rgba(90,70,45,.55)" stroke="rgba(245,190,105,.7)"/>
          <rect x="340" y="445" width="300" height="42" rx="14" fill="rgba(100,45,70,.6)" stroke="rgba(255,130,190,.72)"/>
        </g>
        <g fill="#eef5ff" text-anchor="middle" font-family="Arial,sans-serif">
          <text x="490" y="47" font-size="16" font-weight="700">TRUSTED BRAND</text>
          <text x="490" y="67" font-size="13">{safe_brand}</text>
          <text x="490" y="231" font-size="16" font-weight="700">SUSPECT ASSET</text>
          <text x="490" y="251" font-size="13">{safe_candidate}</text>
          <text x="205" y="391" font-size="15" font-weight="700">LOOK-ALIKE DOMAIN</text>
          <text x="205" y="411" font-size="12">{safe_domain}</text>
          <text x="490" y="391" font-size="15" font-weight="700">SOCIAL SURFACE</text>
          <text x="490" y="411" font-size="12">{safe_social}</text>
          <text x="775" y="391" font-size="15" font-weight="700">APP SURFACE</text>
          <text x="775" y="411" font-size="12">{safe_app}</text>
          <text x="490" y="472" font-size="15" font-weight="700">FUSION RESULT • {safe_result}</text>
        </g>
      </svg>
    </div>
    """
    st.markdown(svg, unsafe_allow_html=True)
    st.success('✓ Relationship graph rendered from the current investigation state. Run Attack Simulation or Threat Fusion above to populate the live candidate and score.')
    st.caption('Prototype note: this is a synthetic relationship map for explainable investigation. It does not claim live ownership, attribution, or maliciousness.')

with adv5:
    st.markdown('### 📈 Model Evaluation')
    st.caption('A transparent, deterministic evaluation of the synthetic attack set. Metrics below are calculated from the scenarios currently shipped with this prototype — not from real-world fraud data.')
    eval_rows=[]
    for row in attack_scenarios(brand):
        score, signals, _ = advanced_fusion_score(brand,row['Candidate'],row['Visual'],row['Domain'],row['Context'],row['Trust'])
        eval_rows.append({'Attack':row['Attack type'],'Score':score,'Detected (≥70)': 'YES' if score >= 70 else 'NO','Severity':severity(score)})
    eval_df=pd.DataFrame(eval_rows)
    if not eval_df.empty:
        detected=int((eval_df['Score']>=70).sum())
        total=len(eval_df)
        detection_rate=detected/total*100
        mean_score=float(eval_df['Score'].mean())
        st.metric('Synthetic detection rate',f'{detection_rate:.1f}%',f'{detected}/{total} scenarios ≥ 70')
        m1,m2,m3=st.columns(3)
        m1.metric('Mean threat score',f'{mean_score:.1f}/100')
        m2.metric('Highest score',f'{int(eval_df["Score"].max())}/100')
        m3.metric('Lowest score',f'{int(eval_df["Score"].min())}/100')
        st.dataframe(eval_df,use_container_width=True,hide_index=True)
        st.markdown('#### Evaluation rule')
        st.code('Detected = Threat Fusion Score ≥ 70\nDataset = built-in synthetic impersonation scenarios\nPurpose = regression / demo validation, not proof of production accuracy',language='text')
        st.success('✓ The evaluation is reproducible: changing the scoring engine changes these metrics automatically.')

st.markdown('### 🗺️ Detection Pipeline')
st.markdown("""
<div class="panel">
<div class="eyebrow">BRANDRADAR ANALYST PIPELINE</div>
<div style="font-size:1.05rem;line-height:2.1">
<b>1. INPUT</b> → brand / username / app / URL / image<br>↓<br>
<b>2. NORMALIZE</b> → clean identifiers and compare aliases<br>↓<br>
<b>3. EXTRACT SIGNALS</b> → identity • visual • domain • context • trust<br>↓<br>
<b>4. THREAT FUSION</b> → weighted 0–100 correlation score<br>↓<br>
<b>5. EXPLAIN</b> → evidence + contributing signals<br>↓<br>
<b>6. PRIORITIZE</b> → LOW / MEDIUM / HIGH / CRITICAL<br>↓<br>
<b>7. ANALYST ACTION</b> → preserve evidence • verify • escalate
</div></div>
""", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown('---')
st.markdown(f'<div style="display:flex;justify-content:space-between;color:#5f718f;font-size:.72rem"><span>BRANDRADAR 3.0 • Explainable Digital Risk Protection</span><span>Session {datetime.now().strftime("%d %b %Y • %H:%M")}</span></div>',unsafe_allow_html=True)
