#!/usr/bin/env python3
"""Yiriam ops 19-may-2026:
1) Pausar MLM2909179597 (no reactivar)
2) Finalizar MLM2923681279 (status=closed)
3) Probar PTW v2 en todos los items war para ver qué tan agresivo es el max-up
4) Listar competidores via /products/{cpid}/items
"""
import os,time,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"

WAR_ITEMS=[
  "MLM5291774150","MLM5291785036","MLM2909183147","MLM2916942827",
  "MLM2940047221","MLM5363034834","MLM5363034838","MLM2940047227","MLM5363034842",
  "MLM2940047233","MLM5363023022",
  "MLM5363147400","MLM5363034850","MLM5363023026","MLM5363034852","MLM5363147404",
  "MLM2940047245","MLM5363147408","MLM5363023032","MLM5363147410","MLM5363034856",
  "MLM5363147416","MLM2940047249","MLM5363147422","MLM5363034860",
  "MLM2940662359","MLM5364336572","MLM5364336602",
]

T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

print("=== PAUSAR MLM2909179597 ===")
g=requests.get(f"{API}/items/MLM2909179597",headers=H,timeout=15).json()
print(f"  pre-status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')}")
r=requests.put(f"{API}/items/MLM2909179597",headers=HJ,json={"status":"paused"},timeout=15)
print(f"  PAUSE http={r.status_code}")

print("\n=== FINALIZAR MLM2923681279 ===")
g=requests.get(f"{API}/items/MLM2923681279",headers=H,timeout=15).json()
print(f"  pre-status={g.get('status')} qty={g.get('available_quantity')} price={g.get('price')} cpid={g.get('catalog_product_id')}")
# Closed requires pause first if active
if g.get("status")=="active":
    r1=requests.put(f"{API}/items/MLM2923681279",headers=HJ,json={"status":"paused"},timeout=15)
    print(f"  PAUSE http={r1.status_code}")
    time.sleep(0.5)
r2=requests.put(f"{API}/items/MLM2923681279",headers=HJ,json={"status":"closed"},timeout=15)
print(f"  CLOSE http={r2.status_code} body={r2.text[:200]}")

print("\n=== AUDIT WAR: PTW v2 + competidores ===")
print(f"{'item':<16} {'cur':>6} {'ptw':>6} {'status':<10} {'cpid':<14} {'low_comp':>8}  title")
for iid in WAR_ITEMS:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        st=g.get("status"); cur=g.get("price"); cpid=g.get("catalog_product_id") or ""
        title=(g.get("title") or "")[:35]
        if st!="active":
            print(f"{iid:<16} {str(cur):>6} {'-':>6} {st:<10} {cpid:<14} {'-':>8}  {title}")
            continue
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        ptw=p.get("price_to_win") or 0
        ptw_st=p.get("status") or "?"
        low=""
        if cpid:
            pr=requests.get(f"{API}/products/{cpid}/items?limit=20",headers=H,timeout=10).json()
            results=pr.get("results") or pr.get("listings") or []
            comps=[]
            for r in results:
                rid=r.get("item_id") or r.get("id")
                rp=r.get("price")
                if rid and rid!=iid and rp:
                    comps.append((rid,rp))
            comps.sort(key=lambda x: x[1])
            if comps:
                low=f"{comps[0][1]}"
        print(f"{iid:<16} {str(cur):>6} {str(ptw):>6} {ptw_st:<10} {cpid:<14} {low:>8}  {title}")
        time.sleep(0.3)
    except Exception as e:
        print(f"  ERR {iid}: {e}")
