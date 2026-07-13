import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_KARIME"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_KARIME: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

ITEMS=[
  ("MLM3129467021","Negra"),
  ("MLM3129476473","Rosa"),
  ("MLM3129467131","Roja"),
  ("MLM3129476561","Celeste"),
]

for iid, cname in ITEMS:
    print(f"\n=== {iid} ({cname}) ===",flush=True)
    # PUT BRAND=JBL
    payload={"attributes":[{"id":"BRAND","value_name":"JBL"}]}
    r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=payload,timeout=15).json()
    if r.get("error"):
        print(f"  ❌ err: {json.dumps(r)[:500]}",flush=True)
    else:
        # Check BRAND after
        brand_after=None
        for a in r.get("attributes",[]):
            if a.get("id")=="BRAND":
                brand_after=a.get("value_name"); break
        print(f"  ✅ BRAND: {brand_after}",flush=True)
    
    # Also fix title if wanted — new title with JBL
    new_title=f"Bocina Bluetooth Portatil Jbl Go 4 Ip67 Reacondicionada {cname}"[:60]
    r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"title":new_title},timeout=15).json()
    if r2.get("error"):
        print(f"  title update err: {r2.get('message','?')}",flush=True)
    else:
        print(f"  title: {r2.get('title','?')[:70]}",flush=True)
