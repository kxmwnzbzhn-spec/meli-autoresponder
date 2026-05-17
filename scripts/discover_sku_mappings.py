#!/usr/bin/env python3
"""Escanea las 9 cuentas y sugiere mapping MLM→SKU canonico via clasificador. Output: inventory/sku_to_mlm_suggested.json para revision."""
import os,json,base64,re,requests
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
GHT=os.environ["GH_TOKEN"]
REPO="kxmwnzbzhn-spec/meli-autoresponder"
GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}

def tok(rt):
    if not rt: return None
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt}).json()
    return r.get("access_token")

# Classifier: title -> SKU canonical
MODEL_RX=[
  (r"flip\s*7","FLIP7"),(r"clip\s*7","CLIP7"),(r"charge\s*6","CHARGE6"),
  (r"clip\s*5","CLIP5"),(r"clip\s*4","CLIP4"),(r"go\s*4","GO4"),(r"go\s*3","GO3"),
  (r"grip","GRIP"),(r"xb[\s\-]*100","XB100"),(r"bose|soundlink","BOSE"),
  (r"redmi buds","REDMI-BUDS-4-LITE"),(r"dashcam","DASHCAM-ASV-DC170"),
]
COLOR_RX=[(r"camuflaj|camo|squad|verde musg","CAMUFLAJE"),(r"aqua|celeste","AQUA"),
  (r"azul marino|azul oscuro","AZUL-MARINO"),(r"morad|violet|purpur","MORADO"),
  (r"rosa|pink","ROSA"),(r"roj","ROJO"),(r"blanc","BLANCO"),(r"azul","AZUL"),(r"negr","NEGRO")]

def classify(title):
    t=(title or "").lower()
    m=None
    for rx,mn in MODEL_RX:
        if re.search(rx,t): m=mn; break
    if not m:
        return ("UNCLASSIFIED",None)
    if m in ("XB100","DASHCAM-ASV-DC170","REDMI-BUDS-4-LITE"): return (m, t[:60])
    c=None
    for rx,cn in COLOR_RX:
        if re.search(rx,t): c=cn; break
    if m=="GO4" and c=="AZUL": c="AZUL-MARINO"
    sku=f"JBL-{m}-{c or 'XX'}" if m in ("FLIP7","CLIP7","CHARGE6","CLIP5","CLIP4","GO4","GO3","GRIP") else f"{m}-{c or 'XX'}"
    return (sku,t[:60])

ACCOUNTS=[("Wilbert","MELI_REFRESH_TOKEN_WILBERT"),("Yiriam","MELI_REFRESH_TOKEN_YC_NEW"),("Juan","MELI_REFRESH_TOKEN_JUAN"),("Raymundo","MELI_REFRESH_TOKEN_RAYMUNDO"),("Claribel","MELI_REFRESH_TOKEN_CLARIBEL"),("Asva","MELI_REFRESH_TOKEN_ASVA"),("Mildred","MELI_REFRESH_TOKEN_MILDRED"),("Dilcie","MELI_REFRESH_TOKEN_DILCIE"),("Bren","MELI_REFRESH_TOKEN_BREN")]

by_mlm={}; by_sku={}
for name,env in ACCOUNTS:
    T=tok(os.environ.get(env,""))
    if not T: continue
    H={"Authorization":f"Bearer {T}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    uid=me.get("id")
    if not uid: continue
    ids=[]
    for st in ("active","paused"):
        off=0
        while True:
            r=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H,timeout=15).json()
            res=r.get("results",[])
            if not res: break
            ids+=res; off+=100
            if off>=r.get("paging",{}).get("total",0): break
    for i in range(0,len(ids),20):
        batch=",".join(ids[i:i+20])
        r=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,status",headers=H).json()
        for x in r:
            b=x.get("body",{}) or {}
            mlm=b.get("id")
            if not mlm: continue
            sku,sample=classify(b.get("title",""))
            by_mlm[mlm]={"sku":sku,"title":b.get("title","")[:80],"account":name,"status":b.get("status")}
            by_sku.setdefault(sku,[]).append(mlm)
    print(f"  {name}: {len(ids)} items")

out={"_meta":{"description":"AUTO suggestions. Revisar y mover entradas validas a sku_to_mlm.json"},"by_mlm":by_mlm,"by_sku":by_sku}
# Commit suggested map
content=base64.b64encode(json.dumps(out,indent=2,ensure_ascii=False).encode()).decode()
# Get existing sha if any
r=requests.get(f"https://api.github.com/repos/{REPO}/contents/inventory/sku_to_mlm_suggested.json",headers=GHH).json()
body={"message":"discover MLM→SKU suggestions","content":content}
if "sha" in r: body["sha"]=r["sha"]
u=requests.put(f"https://api.github.com/repos/{REPO}/contents/inventory/sku_to_mlm_suggested.json",headers={**GHH,"Content-Type":"application/json"},json=body)
print(f"commit: {u.status_code}, suggested {len(by_mlm)} MLMs across {len(by_sku)} SKUs")
