import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

print("=== BUSCAR Flip 7 Morado/Purple/Violet ===")
queries=["JBL Flip 7 purple","JBL Flip 7 violet","JBL FLIP7PURAM","Jbl Flip 7 morado","JBL Flip 7 PUR","flip7 morado","altavoz JBL morado","Flip 7 JBLFLIP7PUR"]
for q in queries:
    # items live
    s=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={q}&limit=10",headers=H).json()
    for r_ in (s.get("results") or [])[:10]:
        t=r_.get("title","")
        if ("Flip 7" in t or "flip7" in t.lower()) and ("morad" in t.lower() or "purpl" in t.lower() or "violet" in t.lower() or "PUR" in t):
            print(f"  ITEM {r_.get('id')}: {t[:80]}")
    # products
    ps=requests.get(f"https://api.mercadolibre.com/products/search?site_id=MLM&q={q}&limit=10",headers=H).json()
    for p in (ps.get("results") or [])[:10]:
        name=p.get("name","")
        col=next((a.get("value_name") for a in (p.get("attributes") or []) if a.get("id")=="COLOR"),"")
        if ("Flip 7" in name or "flip7" in name.lower()) and (col and ("Morad" in col or "Purpl" in col or "Violet" in col)):
            print(f"  PRODUCT {p.get('id')}: {name[:70]} COLOR={col} pics={len(p.get('pictures') or [])}")
