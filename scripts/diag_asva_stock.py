import os, requests, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
SELLER=me.get("id"); print(f"ASVA seller_id={SELLER}")

# 1) Check the 3 items in priority
ITEMS=["MLM5511675206","MLM2378087893","MLM3849137034"]
print("\n=== Estado actual items en priority_replenish ===")
for IID in ITEMS:
  g=requests.get(f"{API}/items/{IID}",headers=H,timeout=10).json()
  status=g.get("status"); qty=g.get("available_quantity"); sub=g.get("sub_status")
  print(f"  {IID} | status={status} | qty={qty} | sub={sub} | sold={g.get('sold_quantity')} | title={g.get('title','')[:60]}")

# 2) Find ALL ASVA perfume items (category MLM1271) to see if some need to be added
print(f"\n=== ASVA active perfumes (MLM1271) ===")
off=0; total_perfumes=0
sample_low_stock=[]
while True:
  r=requests.get(f"{API}/users/{SELLER}/items/search?status=active&category=MLM1271&limit=50&offset={off}",headers=H,timeout=12)
  if r.status_code!=200: break
  j=r.json(); res=j.get("results") or []
  total=j.get("paging",{}).get("total",0)
  for IID in res:
    if IID in ITEMS: continue
    g=requests.get(f"{API}/items/{IID}",headers=H,timeout=8).json()
    qty=g.get("available_quantity",0)
    sold=g.get("sold_quantity",0)
    sub=g.get("sub_status",[]) or []
    if qty<=2 or "out_of_stock" in sub:
      sample_low_stock.append((IID,qty,sold,sub,g.get("title","")[:60]))
  total_perfumes+=len(res)
  off+=50
  if off>=total or not res: break

print(f"Total ASVA active perfumes: {total_perfumes}")
print(f"Low stock (≤2) or OOS perfumes NOT in priority_replenish: {len(sample_low_stock)}")
for x in sample_low_stock[:30]:
  print(f"  {x[0]} | qty={x[1]} | sold={x[2]} | sub={x[3]} | {x[4]}")
