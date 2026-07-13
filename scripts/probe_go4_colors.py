import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Known Go 4 CPIDs from history (Mayrely tasks 129-139):
# Negra: MLM44710240
# Celeste: MLM61262890
# Rosa: MLM46998439
# Rojo: search or MLM44710313 (?)

CPIDS_TO_PROBE={
  "Negra": "MLM44710240",
  "Celeste": "MLM61262890",
  "Rosa": "MLM46998439",
  "Roja": "MLM44710313",  # may not be red - verify
}

# Also search Go 4 red
print(f"\n=== SEARCH JBL Go 4 Roja/Rojo ===",flush=True)
s=requests.get("https://api.mercadolibre.com/products/search?site_id=MLM&q=JBL Go 4 roja",headers=H,timeout=15).json()
for r in s.get("results",[])[:5]:
    print(f"  {r.get('id')}: {r.get('name','?')[:70]}",flush=True)

for color, cpid in CPIDS_TO_PROBE.items():
    p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=10).json()
    name=p.get("name","?")
    dom=p.get("domain_id","?")
    pics=[pic.get("url") for pic in p.get("pictures",[])[:6] if pic.get("url")]
    color_attr=None
    for a in p.get("attributes",[]):
        if a.get("id")=="COLOR":
            color_attr=a.get("value_name"); break
    cat=None
    for a in p.get("attributes",[]):
        if a.get("id")=="ITEM_CATEGORY":
            cat=a.get("value_id"); break
    print(f"\n{color} → {cpid}",flush=True)
    print(f"  name: {name[:80]}",flush=True)
    print(f"  domain: {dom}  color_attr: {color_attr}  cat: {cat}  pics: {len(pics)}",flush=True)
