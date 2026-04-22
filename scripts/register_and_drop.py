import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# (item_id, model, color, cpid, floor)
BOCINAS=[
    ("MLM2880774951","Charge 6","Roja","MLM58806550",720),
    ("MLM2880762579","Charge 6","Camuflaje","MLM58829227",720),
    ("MLM2880803051","Charge 6","Negra","MLM51435334",720),
    ("MLM5223214318","Flip 7","Roja","MLM48958711",640),
    ("MLM2880762535","Clip 5","Morada","MLM45586155",690),
    ("MLM2880794089","Grip","Negra","MLM59802579",565),
    ("MLM5223449418","Sony XB100","Negra","MLM25912333",500),
    ("MLM2880762595","Go Essential 2","Azul","MLM44711997",430),
    ("MLM2880775007","Go Essential 2","Roja","MLM44712071",430),
    ("MLM2880763019","Go 4","Roja","MLM64389753",430),
    ("MLM5223451400","Go 4","Rosa","MLM65831856",430),
    ("MLM5223214798","Go 4","Azul Marino","MLM44731712",430),
    ("MLM2880774949","Go 3","Negra","MLM44709174",430),
    ("MLM2880763001","Charge 6","Azul","",720),  # sin cpid, solo bajar
]

# 1) Cargar catalog_listings.json existente
CFG_PATH="catalog_listings.json"
try:
    with open(CFG_PATH) as f: cfg=json.load(f)
except: cfg={}

# 2) Para cada bocina, agregar al config si tiene cpid
for iid,model,color,cpid,floor in BOCINAS:
    if not cpid: continue
    cfg[cpid]={
        "catalog_item_id": iid,
        "traditional_item_id": None,
        "label": f"JBL {model} {color}" if "Sony" not in model else f"Sony XB100 {color}",
        "floor": floor,
        "step": 10,
        "active": True,
        "sync_price_to_traditional": False,
        "sync_stock": False,
        "floor_alerted": False
    }

with open(CFG_PATH,"w") as f: json.dump(cfg,f,indent=2,ensure_ascii=False)
print(f"catalog_listings.json actualizado con {len(BOCINAS)} bocinas")

# 3) Bajar $10 a cada una (arriba del floor)
print("\n=== Bajando $10 proactivamente ===")
changed=0; at_floor=0
for iid,model,color,cpid,floor in BOCINAS:
    it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    if it.get("status")!="active":
        print(f"  SKIP {iid}: {it.get('status')}")
        continue
    p=int(it.get("price") or 0)
    new_p = p - 10
    if new_p < floor:
        print(f"  FLOOR {iid} [{model} {color}] ${p} (floor ${floor})")
        at_floor+=1
        continue
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price":new_p},timeout=20)
    if r.status_code in (200,201):
        print(f"  OK {iid} [{model:<16} {color:<12}] ${p} → ${new_p} (floor ${floor})")
        changed+=1
    else:
        print(f"  ERR {iid}: {r.status_code} {r.text[:150]}")
    time.sleep(0.5)

print(f"\nBajadas: {changed}, En floor: {at_floor}")
