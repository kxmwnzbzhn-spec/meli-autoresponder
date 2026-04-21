import os,requests,time,json,re
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# 1) Buscar catalog para Kurky MFK
def search_best(q, must_have, must_not_have=None):
    must_not_have=must_not_have or []
    r=requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={q}",headers=H,timeout=15).json()
    print(f"Search '{q}':")
    for item in r.get("results",[])[:8]:
        print(f"  {item.get('id')} | {item.get('name')}")
    # Pick first that matches all must_have and none of must_not_have
    for item in r.get("results",[])[:10]:
        name=(item.get("name") or "").lower()
        if any(b in name for b in must_not_have): continue
        if all(g in name for g in must_have):
            return item.get("id"), item.get("name")
    return None, None

print("=== KURKY MFK ===")
ckid, cknm = search_best("Maison Francis Kurkdjian Kurky", ["kurky","kurkdjian"])
print(f"  -> {ckid} {cknm}")

print("\n=== CARTIER LA PANTHERE ===")
cpid, cpnm = search_best("Cartier La Panthere EDP", ["cartier","panthere","parfum"], ["reloj","watch"])
print(f"  -> {cpid} {cpnm}")
