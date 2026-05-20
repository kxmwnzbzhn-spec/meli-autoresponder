"""URGENTE: cerrar MLM5363034852 + pausar TODOS los perfumes Yiriam"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id")

# 1) Close MLM5363034852
print("=== CLOSE MLM5363034852 ===")
g=requests.get(f"{API}/items/MLM5363034852",headers=H,timeout=10).json()
print(f"  pre: status={g.get('status')} price={g.get('price')}")
if g.get("status")=="active":
    r=requests.put(f"{API}/items/MLM5363034852",headers=HJ,json={"status":"paused"},timeout=15)
    print(f"  pause http={r.status_code}")
    time.sleep(0.5)
r2=requests.put(f"{API}/items/MLM5363034852",headers=HJ,json={"status":"closed"},timeout=15)
print(f"  close http={r2.status_code}")

# 2) Listar TODOS los active de Yiriam
print(f"\n=== LIST + PAUSE PERFUMES (domain=MLM-PERFUMES) ===")
all_items=[]
offset=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    res=r.get("results") or []
    all_items.extend(res)
    if len(res)<50 or offset>500: break
    offset+=50
print(f"  Total active: {len(all_items)}")

# Multi-get para filtrar por domain
perfume_items=[]
chunks=[all_items[i:i+20] for i in range(0,len(all_items),20)]
for ch in chunks:
    mg=requests.get(f"{API}/items?ids={','.join(ch)}",headers=H,timeout=15).json()
    for ent in mg:
        b=ent.get("body") or {}
        dom=(b.get("domain_id") or "")
        cat=(b.get("category_id") or "")
        if dom=="MLM-PERFUMES" or cat.startswith("MLM127"):  # MLM1271/1272/1273 = perfumes
            perfume_items.append({"id":b.get("id"),"title":(b.get("title") or "")[:40],"price":b.get("price"),"domain":dom,"cat":cat})

print(f"  Perfumes encontrados: {len(perfume_items)}")
for p in perfume_items:
    print(f"    {p['id']} ${p['price']} cat={p['cat']} '{p['title']}'")

# Pausar todos
print(f"\n=== PAUSE {len(perfume_items)} perfumes ===")
ok=err=0
for p in perfume_items:
    iid=p["id"]
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
    if r.status_code<300:
        ok+=1
        print(f"  PAUSE {iid} http={r.status_code}")
    else:
        err+=1
        print(f"  FAIL {iid} http={r.status_code} {r.text[:80]}")
    time.sleep(0.25)
print(f"\n  ok={ok} err={err}")

# IDs for blacklist
print(f"\n=== IDS_TO_BLACKLIST ===")
for p in perfume_items:
    print(f'  "{p["id"]}",')
