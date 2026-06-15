import os, requests, json, time, urllib.parse
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}"}
CPID="MLM39361112"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
print(f"name: {cp.get('name')}")
for a in cp.get("attributes",[])[:20]:
  print(f"  {a.get('id')}: {a.get('value_name')}")
pics=cp.get("pictures") or []
print(f"pictures: {len(pics)}")
# Competing prices
i=requests.get(f"{API}/products/{CPID}/items?limit=30",headers=H,timeout=20).json()
print(f"items en CPID: total={i.get('paging',{}).get('total')}")
prices=[]
for r2 in (i.get("results") or [])[:20]:
  p=r2.get("price"); st=r2.get("status")
  iid=r2.get("item_id") or r2.get("id")
  print(f"  {iid} | ${p} | {st}")
  if p and st=="active": prices.append(p)
prices.sort()
if prices:
  print(f"min/median/max: ${prices[0]} / ${prices[len(prices)//2]} / ${prices[-1]}")
