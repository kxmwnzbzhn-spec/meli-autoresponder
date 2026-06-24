import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Read bounds from Supabase
SB="https://wnuhslmryspnypbxbfjf.supabase.co"
SBH={"apikey":os.environ["SUPABASE_SERVICE_KEY"],"Authorization":f"Bearer {os.environ['SUPABASE_SERVICE_KEY']}"}
strats=requests.get(f"{SB}/rest/v1/meli_catalog_strategy?active=eq.true&select=catalog_product_id,floor,ceiling",headers=SBH,timeout=15).json()
bounds={s["catalog_product_id"]:(float(s["floor"]),float(s["ceiling"])) for s in strats if s.get("floor") and s.get("ceiling")}
print(f"loaded {len(bounds)} bounds")

# Mayrely items published today
ITEMS=["MLM3045514191","MLM3045514543","MLM5569350350","MLM5569282738","MLM5569400988","MLM3045606657","MLM3045607131","MLM5569353088","MLM5569353878","MLM3045609271","MLM3045609843","MLM5569443364","MLM3045612883","MLM5569443994","MLM5569446604","MLM3045615611"]
for iid in ITEMS:
  it=requests.get(f"{API}/items/{iid}?attributes=id,title,price,catalog_product_id",headers=HJ,timeout=10).json()
  cpid=it.get("catalog_product_id")
  price=it.get("price")
  if not cpid or not price: continue
  fl,ce = bounds.get(cpid,(None,None))
  if not fl: continue
  if price < fl:
    # FIX: bump to floor
    print(f"⚠️ {iid} {cpid} ${price} < floor ${fl} -> setting to ${fl}")
    rr=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":fl},timeout=20)
    print(f"   PUT: {rr.status_code} {rr.text[:200]}")
  elif price > ce:
    print(f"⚠️ {iid} {cpid} ${price} > ceiling ${ce} -> setting to ${ce}")
    rr=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":ce},timeout=20)
    print(f"   PUT: {rr.status_code} {rr.text[:200]}")
  else:
    print(f"OK {iid} {cpid} ${price} in [{fl},{ce}]")
