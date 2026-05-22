"""1) Dedup: agrupa active por CPID, deja el de mas ventas, pausa el resto.
   2) Barrido: reporta estado buy box de los que quedan."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
PAUSED_LOCK={"MLM5353056250"}
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json(); uid=me.get("id")

# Listar todos active con detalle
ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []; ids.extend(res)
    if len(res)<50 or off>1000: break
    off+=50
print(f"Active total: {len(ids)}")

# Detalle por item
items={}
for i in range(0,len(ids),20):
    mg=requests.get(f"{API}/items?ids={','.join(ids[i:i+20])}",headers=H,timeout=15).json()
    for e in mg:
        b=e.get("body") or {}
        iid=b.get("id")
        if not iid: continue
        items[iid]={"cpid":b.get("catalog_product_id"),"sold":b.get("sold_quantity",0),
                    "price":b.get("price"),"title":(b.get("title") or "")[:30]}

# Agrupar por CPID
from collections import defaultdict
groups=defaultdict(list)
for iid,d in items.items():
    if d["cpid"]:
        groups[d["cpid"]].append(iid)

# Dedup
print("\n=== DEDUP (canibalización) ===")
paused=0
for cpid,lst in groups.items():
    if len(lst)<2: continue
    # ordenar por sold desc, luego item id asc (más viejo gana en empate)
    lst_sorted=sorted(lst, key=lambda x:(-items[x]["sold"], x))
    keep=lst_sorted[0]
    print(f"CPID {cpid}: {len(lst)} duplicados → KEEP {keep} (sold={items[keep]['sold']})")
    for dup in lst_sorted[1:]:
        if dup in PAUSED_LOCK: continue
        r=requests.put(f"{API}/items/{dup}",headers=HJ,json={"status":"paused"},timeout=15)
        paused+=1
        print(f"   PAUSE dup {dup} (sold={items[dup]['sold']}) http={r.status_code}")
        time.sleep(0.3)

print(f"\nDuplicados pausados: {paused}")
print(f"CPIDs con dup: {sum(1 for c,l in groups.items() if len(l)>1)}")

# Barrido buy box rápido de lo que queda active
print("\n=== BARRIDO buy box (PTW) ===")
time.sleep(2)
ids2=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []; ids2.extend(res)
    if len(res)<50 or off>1000: break
    off+=50
win=comp=reindex=nocpid=0
for iid in ids2:
    g=items.get(iid)
    cpid=None
    try:
        gg=requests.get(f"{API}/items/{iid}",headers=H,timeout=8).json()
        cpid=gg.get("catalog_product_id")
        if not cpid: nocpid+=1; continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=8).json()
        st=(p.get("status") or "").lower()
        if st in ("winning","sharing_first_place"): win+=1
        elif st=="not_listed": reindex+=1
        else: comp+=1
        time.sleep(0.15)
    except: pass
print(f"  Active final: {len(ids2)} | GANANDO: {win} | compitiendo/perdiendo: {comp} | reindex: {reindex} | sin_cpid: {nocpid}")
