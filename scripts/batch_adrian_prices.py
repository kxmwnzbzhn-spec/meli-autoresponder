"""Batch price adjustments + 1 close on Adrián."""
import os, requests, time
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_AH={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

USER_MSG="batch precios + 1 eliminar adrian 9 acciones"

# Format: [item_id, action, value]
JOBS=[
    ("MLM2969827141","price",1499),
    ("MLM2969839301","price",999),
    ("MLM2969870623","price",999),
    ("MLM2956230177","close",None),
    ("MLM2969826017","price",1499),
    ("MLM2969827055","price",1499),
    ("MLM2969851661","price",1499),
    ("MLM2969827133","price",1999),
    ("MLM2969839233","price",1999),
]

ok=0; fail=0; errs=[]
for iid, action, val in JOBS:
    print(f"\n=== {iid} {action}={val} ===")
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        st=g.get("status"); cur=g.get("price")
        title=(g.get("title") or "")[:80]
        cpid=g.get("catalog_product_id")
        print(f"  BEFORE status={st} price={cur} cpid={cpid} | {title}")
        
        if action=="close":
            if st=="active":
                requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=12)
                time.sleep(0.4)
            rc=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=12)
            print(f"  CLOSE HTTP {rc.status_code}")
            if rc.status_code in (200,201):
                ok+=1
                requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=SBH,timeout=8)
                requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
                    headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
                    json={"item_id":iid,"account":"ADRIAN","reason":"eliminar por usuario"},timeout=8)
                requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                    json={"account":"ADRIAN","scope":"item","scope_value":iid,
                          "directive_type":"close","value_numeric":None,
                          "raw_user_message":USER_MSG},timeout=8)
                requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
                    json={"account":"ADRIAN","item_id":iid,"action_type":"close",
                          "from_value":str(st),"to_value":"closed",
                          "actor":"claude_cowork","details":USER_MSG},timeout=8)
            else:
                fail+=1; errs.append(f"{iid} CLOSE {rc.status_code}: {rc.text[:160]}")
        else:
            # Price change
            rp=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":val},timeout=12)
            print(f"  PRICE {cur}→{val} HTTP {rp.status_code}: {rp.text[:200]}")
            if rp.status_code in (200,201):
                ok+=1
                # Pin price directive (item-level)
                requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                    json={"account":"ADRIAN","scope":"item","scope_value":iid,
                          "directive_type":"pin_price","value_numeric":val,
                          "raw_user_message":USER_MSG},timeout=8)
                # Also CPID-level if exists
                if cpid:
                    requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                        json={"account":"ADRIAN","scope":"cpid","scope_value":cpid,
                              "directive_type":"pin_price","value_numeric":val,
                              "raw_user_message":USER_MSG},timeout=8)
                    # Update strategy floor=ceiling=val
                    requests.patch(f"{SBU}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{cpid}",
                        headers={**SBH,"Prefer":"return=minimal"},
                        json={"floor":val,"ceiling":val,"active":True},timeout=8)
                requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
                    json={"account":"ADRIAN","item_id":iid,"action_type":"pin_price",
                          "from_value":str(cur),"to_value":str(val),
                          "actor":"claude_cowork","details":USER_MSG},timeout=8)
            else:
                fail+=1; errs.append(f"{iid} PRICE {rp.status_code}: {rp.text[:200]}")
        
        # Verify
        g2=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        print(f"  AFTER status={g2.get('status')} price={g2.get('price')}")
    except Exception as e:
        fail+=1; errs.append(f"{iid} EXC {e}")
        print(f"  EXC {e}")
    time.sleep(0.2)

print(f"\n=== SUMMARY ok={ok} fail={fail} ===")
if errs:
    for e in errs[:10]: print(f"  ERR: {e}")
