"""
GET de cada catalog_product_id para detectar dominio, marca, título y duplicados.
"""
import os, json, requests
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
AT=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":RT},timeout=20).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

IDS=["MLM70245995","MLM70246250","MLM70246080","MLM52129383","MLM70112010",
     "MLM70063829","MLM70063831","MLM70063753","MLM70064197","MLM70063777",
     "MLM69963991","MLM69794759","MLM69794803","MLM69795006"]

seen={}
out=[]
for cid in IDS:
    r=requests.get(f"{API}/products/{cid}",headers=H,timeout=15)
    if r.status_code!=200:
        print(f"{cid} → HTTP {r.status_code} {r.text[:200]}")
        continue
    p=r.json()
    name=p.get("name") or ""
    dom=p.get("domain_id"); status=p.get("status")
    brand=""
    for a in p.get("attributes",[]):
        if a.get("id")=="BRAND":
            brand=(a.get("values") or [{}])[0].get("name","")
    npics=len(p.get("pictures") or [])
    key=name.strip().lower()
    dup="DUP" if key in seen else ""
    seen[key]=cid
    print(f"{cid} {dup} dom={dom} brand={brand[:25]:25s} status={status} pics={npics} | {name[:80]}")
    out.append({"id":cid,"name":name,"dom":dom,"brand":brand,"status":status,"npics":npics,"dup":bool(dup)})

print("\n--- TOTALS ---")
print(f"unique: {len([o for o in out if not o['dup']])}, duplicates: {len([o for o in out if o['dup']])}, errors: {len(IDS)-len(out)}")
