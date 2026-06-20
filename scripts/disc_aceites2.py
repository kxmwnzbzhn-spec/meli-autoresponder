import os, requests, json
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ADRIAN"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":RT},timeout=20).json()
AT=r["access_token"]; H={"Authorization":f"Bearer {AT}"}
print("Adrian OK uid:",requests.get(f"{API}/users/me",headers=H,timeout=15).json().get("id"))

print("\n=== domain_discovery ampliada ===")
for q in ["aceite esencial puro","aceite esencial difusor aromaterapia","esencia aromatica natural","aceite para difusor",
          "aceite de lavanda","aceite eucalipto aromaterapia","aromaterapia","difusor aceite esencial",
          "aceite perfume","aceite corporal","aceites perfumeria","esencia perfume"]:
    rr=requests.get(f"{API}/sites/MLM/domain_discovery/search",params={"q":q,"limit":3},headers=H,timeout=15)
    try:
        rows=rr.json()
        if rows:
            print(f"q='{q}'")
            for d in rows: print(f"   {d.get('domain_id')} | {d.get('domain_name')} | cat={d.get('category_id')} ({d.get('category_name')})")
    except: pass

print("\n=== buscar en árbol de categorías MLM ===")
# raíz categorías y descender hacia belleza/salud/aromaterapia
r=requests.get(f"{API}/sites/MLM/categories",headers=H,timeout=20).json()
for c in r:
    if any(k in (c.get('name') or '').lower() for k in ["belleza","salud","hogar","perfum"]):
        print(f"  ROOT {c['id']} {c['name']}")

# busqueda directa de items con "aceite esencial" y ver sus categorías y dominios
print("\n=== buscar items reales 'aceite esencial' en sitio MLM ===")
rr=requests.get(f"{API}/sites/MLM/search",params={"q":"aceite esencial 100% puro","limit":10},headers=H,timeout=15)
try:
    seen=set()
    for r in rr.json().get("results") or []:
        cid=r.get("category_id"); dom=r.get("domain_id")
        if (cid,dom) in seen: continue
        seen.add((cid,dom))
        print(f"   dom={dom} | cat={cid} | {r.get('title','')[:60]}")
except Exception as e: print("err",e)
