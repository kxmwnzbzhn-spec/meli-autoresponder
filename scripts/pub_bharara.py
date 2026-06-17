import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Check current competition on CPID
CPID="MLM37110181"
i=requests.get(f"{API}/products/{CPID}/items?limit=30",headers=H,timeout=15).json()
print(f"competidores CPID {CPID}:")
ps=[]
for r2 in (i.get("results") or [])[:25]:
  p=r2.get("price"); s=r2.get("status"); iid=r2.get("item_id") or r2.get("id"); sold=r2.get("sold_quantity")
  if p and s=="active":
    ps.append((p,iid))
    print(f"  ${p} {iid} sold={sold}")
ps.sort()
print(f"\nmin/median/max activos: ${ps[0][0]} / ${ps[len(ps)//2][0]} / ${ps[-1][0]}")

# Buy box winner
bb=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json().get("buy_box_winner")
print(f"\nbuy_box_winner: {bb}")

# Estado de nuestro item
our="MLM3018313225"
g=requests.get(f"{API}/items/{our}?attributes=id,price,status,catalog_listing,buying_mode",headers=H,timeout=15).json()
print(f"\nNuestro item: {g}")
