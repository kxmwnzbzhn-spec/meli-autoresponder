"""Restaurar precios que bajé mal por bug. Subimos por encima del low_ext y
dejamos al war v4 que confirme via PTW."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
H2={"Authorization":f"Bearer {T}"}

# Items que iba a $X y bajaron mal a $Y. Subimos a un precio razonable arriba del low_ext
RESTORE={
    "MLM5291772416": 599,   # era $699 → ahora $444 → subir a $599 (low_ext=$449, test reputation win)
    "MLM2940047233": 548,   # era $551 → bajamos $533, restaurar a $548 (low_ext=$543)
    "MLM5291774150": 614,   # era $619 → bajamos $610, restaurar a $614 (low_ext=$615)
    "MLM5363034842": 446,   # era $447 → bajamos $437, restaurar a $446 (low_ext=$444 según último audit)
}

for iid, price in RESTORE.items():
    g=requests.get(f"{API}/items/{iid}",headers=H2,timeout=10).json()
    print(f"{iid} cur={g.get('price')} → restore ${price}")
    r=requests.put(f"{API}/items/{iid}",headers=H,json={"price":price},timeout=15)
    print(f"  http={r.status_code}")
    time.sleep(0.5)
    # PTW post
    p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H2,timeout=10).json()
    print(f"  PTW: {p.get('status')} ptw={p.get('price_to_win')}")
