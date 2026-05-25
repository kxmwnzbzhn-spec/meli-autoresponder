import os, requests
import meli_token
SET=["MLM5291774150","MLM5291785036","MLM2909183147","MLM5390371996","MLM2950790163"]
DEL="MLM2954614913"
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
for IID in SET:
    b=requests.get(f"{API}/items/{IID}?attributes=price,title",headers=H,timeout=20).json()
    r=requests.put(f"{API}/items/{IID}",headers=HJ,json={"price":499},timeout=20)
    f=requests.get(f"{API}/items/{IID}?attributes=price",headers=H,timeout=20).json()
    print(f"SET {IID} '{b.get('title','')[:30]}' {b.get('price')}->{f.get('price')} http={r.status_code}")
# eliminar la clon
it=requests.get(f"{API}/items/{DEL}?attributes=seller_id,status,title",headers=H,timeout=20).json()
print(f"\nDEL {DEL} '{it.get('title','')[:30]}' status={it.get('status')}")
if it.get("status")=="active": print("  pause:",requests.put(f"{API}/items/{DEL}",headers=HJ,json={'status':'paused'},timeout=20).status_code)
print("  close:",requests.put(f"{API}/items/{DEL}",headers=HJ,json={'status':'closed'},timeout=20).status_code)
print("  delete:",requests.put(f"{API}/items/{DEL}",headers=HJ,json={'deleted':'true'},timeout=20).status_code)
print("DONE")
