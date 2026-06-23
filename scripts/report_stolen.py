import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Test on a known-popular CPID: MLM44715070 (which we use in Adrián)
for cpid in ["MLM44715070","MLM37108208","MLM68969359"]:
  print(f"\n=== {cpid} ===")
  # Full product dump
  p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
  # Look at all keys at root
  for k in sorted(p.keys()):
    v=p[k]
    if isinstance(v,(str,int,float,bool,type(None))):
      print(f"  {k}: {v}")
    elif isinstance(v,(list,dict)):
      print(f"  {k}: <{type(v).__name__} len={len(v)}>")
  # buy_box_winner deep dump
  bbw=p.get("buy_box_winner")
  if bbw:
    print("  buy_box_winner keys:",list(bbw.keys()))
    print("  buy_box_winner:",{k:v for k,v in bbw.items() if k in ("sold_quantity","price","item_id","seller_id","status")})
  
  # Try /products/{cpid}/items
  it=requests.get(f"{API}/products/{cpid}/items?limit=50",headers=H,timeout=15)
  print(f"  /items HTTP {it.status_code}")
  if it.status_code==200:
    d=it.json()
    items=d.get("results",[]) if isinstance(d,dict) else d
    if not isinstance(items,list): items=[]
    print(f"  items count: {len(items)}")
    total_sold=0
    for ii in items[:30]:
      if isinstance(ii,dict):
        sq=ii.get("sold_quantity",0)
        total_sold+=sq or 0
    print(f"  sold total (top 30): {total_sold}")
