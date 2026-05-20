#!/usr/bin/env python3
"""Force re-index de items not_listed: PUT price ligeramente distinto.
Esto hace que MELI re-evalúe la elegibilidad en catálogo."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

ITEMS=["MLM2940047227","MLM2940047233"]
for iid in ITEMS:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cur=g.get("price")
    cpid=g.get("catalog_product_id")
    # Bajamos $5 para forzar re-index + ser competitivos
    new=cur-5
    print(f"{iid} cpid={cpid} cur=${cur} → ${new}")
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":new},timeout=15)
    print(f"  PUT price http={r.status_code}")
    time.sleep(1)
    # Verificar PTW post
    p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW post: status={p.get('status')} ptw={p.get('price_to_win')}")
