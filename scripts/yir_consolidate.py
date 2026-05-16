import os,requests,time
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
def tok(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]
TY=tok(RT_Y)
HY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}
H={"Authorization":f"Bearer {TY}"}

# Close my 3 newer duplicates
DUPS=["MLM2935445653","MLM5353154356","MLM2935274091"]
for iid in DUPS:
    r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HY,json={"status":"paused"})
    r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HY,json={"status":"closed"})
    print(f"CLOSE_DUP {iid} pause={r1.status_code} close={r2.status_code}")

# Reactivate user's 2
print()
# MLM2935286629 paused/out_of_stock → set qty=1 active
r=requests.put(f"https://api.mercadolibre.com/items/MLM2935286629",headers=HY,json={"available_quantity":1})
print(f"MLM2935286629 set qty=1 http={r.status_code}")
time.sleep(0.5)
r=requests.put(f"https://api.mercadolibre.com/items/MLM2935286629",headers=HY,json={"status":"active"})
print(f"  activate http={r.status_code} {r.text[:150] if r.status_code>=300 else ''}")
time.sleep(0.5)
# MLM2935286669 closed/paused_by_seller → relist
r=requests.post(f"https://api.mercadolibre.com/items/MLM2935286669/relist",headers=HY,json={"quantity":1,"listing_type_id":"gold_pro"})
print(f"MLM2935286669 relist http={r.status_code} {r.text[:200]}")
if r.status_code<300:
    print(f"  NEW_ID={r.json().get('id')}")

# Verify all 12
print("\n=== Final state user's 12 ===")
USER_IDS=["MLM2935286605","MLM2935286537","MLM2935286615","MLM2935286651","MLM2935286681","MLM2935286703","MLM2935298361","MLM2935286669","MLM2935286557","MLM2935286629","MLM5353056250","MLM5353056406"]
for iid in USER_IDS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    print(f"  {iid} st={g.get('status'):<8} sub={g.get('sub_status')} qty={g.get('available_quantity')} ${g.get('price')}")
