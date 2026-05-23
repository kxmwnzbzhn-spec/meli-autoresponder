#!/usr/bin/env python3
"""Stock cap per-SKU — pausa todas las listings de un SKU cuando llega a 0.

Lee inventory/stock_at_golive_20260518.json (inmutable) e inventory/stock_available.json (dinámico).
Por cada cuenta MELI, cuenta ventas desde golive (2026-05-18 00:00 CDMX) excluyendo cancelled.
Mapea cada venta a SKU canónico via match_patterns. Decrementa available.
Si available <= 0 → identifica TODAS las listings (todas las cuentas) cuyo título match con ese SKU y las pausa.
"""
import os,json,base64,re,requests,datetime as dt
import meli_token

CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ["GH_TOKEN"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN"); TC=os.environ.get("TELEGRAM_CHAT_ID")
REPO="kxmwnzbzhn-spec/meli-autoresponder"
GOLIVE="2026-05-18T00:00:00.000-06:00"
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}

def tg(m):
    if TG and TC:
        try: requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",data={"chat_id":TC,"text":m,"parse_mode":"Markdown"},timeout=10)
        except: pass

def tok(rt):
    if not rt: return None
    r=meli_token.refresh(rt).json()
    return r.get("access_token")

ACCOUNTS=[("Wilbert","MELI_REFRESH_TOKEN_WILBERT"),("Yiriam","MELI_REFRESH_TOKEN_YC_NEW"),("Juan","MELI_REFRESH_TOKEN_JUAN"),("Raymundo","MELI_REFRESH_TOKEN_RAYMUNDO"),("Claribel","MELI_REFRESH_TOKEN_CLARIBEL"),("Asva","MELI_REFRESH_TOKEN_ASVA"),("Mildred","MELI_REFRESH_TOKEN_MILDRED"),("Dilcie","MELI_REFRESH_TOKEN_DILCIE"),("Bren","MELI_REFRESH_TOKEN_BREN")]

# Load golive snapshot + current availability
def gh_get(path):
    r=requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",headers=GHH).json()
    if "content" not in r: return None,None
    return json.loads(base64.b64decode(r["content"])), r["sha"]
def gh_put(path,obj,msg,sha):
    body={"message":msg,"content":base64.b64encode(json.dumps(obj,indent=2,ensure_ascii=False).encode()).decode(),"sha":sha}
    return requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",headers={**GHH,"Content-Type":"application/json"},json=body)

golive,_=gh_get("inventory/stock_at_golive_20260518.json")
avail,avail_sha=gh_get("inventory/stock_available.json")
if not golive or not avail:
    print("ERR no snapshots"); raise SystemExit(1)

# Build patterns dict: sku -> [regex compiled]
patterns={sku:[re.compile(p,re.I) for p in v["match_patterns"]] for sku,v in golive["skus"].items()}

def classify(title):
    t=(title or "").lower()
    # 2-pass: modelo + color
    modelos=[
        ("xb100",["xb100","xb-100","srs-xb100"]),
        ("flip7",["flip 7","flip7"]),
        ("clip5",["clip 5","clip5"]),
        ("clip7",["clip 7","clip7"]),
        ("charge6",["charge 6","charge6"]),
        ("go4",["go 4","go4"]),
        ("go3",["go 3","go3"]),
        ("bose",["bose","soundlink"]),
    ]
    modelo=None
    for m,kws in modelos:
        if any(k in t for k in kws):
            modelo=m; break
    if not modelo: return None
    # color (en orden de especificidad: largos primero)
    if modelo=="xb100": return "SONY-XB100-NEGRO"
    if modelo=="charge6": return None  # no en SKU golive
    if modelo=="clip7": return None  # no en SKU golive
    color=None
    color_rx=[
        (["camuflaj","camo","squad","verde musg"], "CAMUFLAJE"),
        (["aqua","celeste"], "AQUA"),
        (["azul marino","azul oscuro"], "AZUL-MARINO"),
        (["azul"], "AZUL"),
        (["morad","violet","purpur","púrp"], "MORADO"),
        (["rosa","pink"], "ROSA"),
        (["roj"], "ROJO"),
        (["blanc","silver"], "BLANCO"),
        (["negr"], "NEGRO"),
    ]
    for kws,c in color_rx:
        if any(k in t for k in kws): color=c; break
    if not color: return None
    # Map modelo+color → SKU
    M={"go4":"JBL-GO4","go3":"JBL-GO3","clip5":"JBL-CLIP5","flip7":"JBL-FLIP7","bose":"BOSE-SOUNDLINK"}
    if modelo=="go4" and color=="AZUL": color="AQUA"  # tratamos azul plain de go4 como aqua/celeste
    if modelo=="go4" and color=="AZUL-MARINO": return None  # no en SKU golive
    if modelo=="go3" and color!="NEGRO": return None
    if modelo=="bose" and color=="NEGRO": return "BOSE-SOUNDLINK-NEGRO"
    if modelo=="bose" and color=="BLANCO": return "BOSE-SOUNDLINK-BLANCO"
    if modelo=="flip7" and color=="ROJO": return "JBL-FLIP7-ROJO"
    if modelo=="flip7": return None
    sku=f"{M[modelo]}-{color}"
    # Verify SKU exists in golive
    if sku in golive["skus"]: return sku
    # Try AQUA fallback for Go4 with no color
    return None


# Reset sold counter on each run (full recount since golive)
sold_by_sku={sku:0 for sku in golive["skus"]}
unmapped_titles={}

for name,env in ACCOUNTS:
    T=tok(os.environ.get(env,""))
    if not T: continue
    H={"Authorization":f"Bearer {T}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me.get("id")
    if not uid: continue
    off=0
    while True:
        r=requests.get(f"https://api.mercadolibre.com/orders/search?seller={uid}&order.date_created.from={GOLIVE}&limit=50&offset={off}",headers=H,timeout=20).json()
        results=r.get("results",[])
        if not results: break
        for o in results:
            if o.get("status") in ("cancelled","invalid"): continue
            for it in (o.get("order_items") or []):
                title=it.get("item",{}).get("title","")
                qty=int(it.get("quantity",0) or 0)
                sku=classify(title)
                if sku:
                    sold_by_sku[sku]+=qty
                else:
                    unmapped_titles[title[:60]]=unmapped_titles.get(title[:60],0)+qty
        off+=50
        if off>=r.get("paging",{}).get("total",0): break

# Update availability + identify SKUs to pause
to_pause_skus=[]
for sku,s in sold_by_sku.items():
    init=golive["skus"][sku]["initial"]
    new_avail=init-s
    prev=avail["skus"][sku]["available"]
    avail["skus"][sku]["available"]=new_avail
    avail["skus"][sku]["sold_since_golive"]=s
    if new_avail<=0 and not avail["skus"][sku].get("last_pause_triggered"):
        to_pause_skus.append(sku)
    if new_avail<=0:
        avail["skus"][sku]["last_pause_triggered"]=True

avail["_meta"]["updated"]=dt.datetime.utcnow().isoformat()+"Z"
avail["_meta"]["total_sold"]=sum(sold_by_sku.values())
avail["_meta"]["total_available"]=sum(s["available"] for s in avail["skus"].values())

# Commit availability
gh_put("inventory/stock_available.json",avail,f"sync sold_since_golive total={avail['_meta']['total_sold']}",avail_sha)

# Print summary
print(f"=== Stock check {avail['_meta']['updated']} ===")
print(f"Total vendido desde golive: {avail['_meta']['total_sold']}")
print(f"Total disponible: {avail['_meta']['total_available']}")
print(f"\nPor SKU:")
for sku,v in avail["skus"].items():
    flag=" 🚫AGOTADO" if v["available"]<=0 else (" ⚠️BAJO" if v["available"]<10 else "")
    print(f"  {sku:<28} init={v['initial']:>5} sold={v['sold_since_golive']:>4} avail={v['available']:>5}{flag}")

if to_pause_skus:
    print(f"\n🚫 SKUs a pausar (llegaron a 0): {to_pause_skus}")
    # Pause all listings matching these SKUs across all accounts
    for name,env in ACCOUNTS:
        T=tok(os.environ.get(env,""))
        if not T: continue
        H={"Authorization":f"Bearer {T}"}
        HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
        me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
        uid=me.get("id")
        if not uid: continue
        # Listar items active
        ids=[]
        off=0
        while True:
            r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status=active&limit=100&offset={off}",headers=H,timeout=15).json()
            res=r.get("results",[])
            if not res: break
            ids+=res; off+=100
            if off>=r.get("paging",{}).get("total",0): break
        if not ids: continue
        # multiget titles
        for i in range(0,len(ids),20):
            batch=",".join(ids[i:i+20])
            mg=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title",headers=H).json()
            for x in mg:
                b=x.get("body",{}) or {}
                iid=b.get("id"); title=b.get("title","")
                sku=classify(title)
                if sku in to_pause_skus:
                    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
                    print(f"  PAUSE [{name}] {iid} sku={sku} '{title[:40]}' http={r.status_code}")
    tg(f"🚫 *SKU AGOTADO — Pausa automática*\n\n"+"\n".join(f"  `{s}` (init {golive['skus'][s]['initial']})" for s in to_pause_skus))
else:
    print(f"\n✓ Ningún SKU al límite. Próxima corrida en 5 min.")

# Telegram resumen si hay 3+ ventas
if avail['_meta']['total_sold']>=3:
    low=[s for s,v in avail['skus'].items() if 0<v['available']<10]
    msg=f"📊 Stock post-golive\nVendido: {avail['_meta']['total_sold']}/5016 ({100*avail['_meta']['total_sold']/5016:.1f}%)\nDisponible: {avail['_meta']['total_available']}"
    if low: msg+=f"\n⚠️ Bajo: {', '.join(low)}"
    # tg(msg)  # opcional reporte regular

if unmapped_titles:
    print(f"\nUNMAPPED (no se contó a ningún SKU):")
    for t,q in list(unmapped_titles.items())[:10]:
        print(f"  qty={q} '{t}'")
