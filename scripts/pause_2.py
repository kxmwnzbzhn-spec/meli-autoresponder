import os, requests, time
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"} if SBK else None

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

USER_MSG="pausa en claribel: 5244434176,5241335830"
for iid in ["MLM5244434176","MLM5241335830"]:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"\n[BEFORE] {iid} status={g.get('status')} sub={g.get('sub_status')} title={(g.get('title') or '')[:80]}")
    rp=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
    print(f"  [PAUSE] HTTP {rp.status_code}: {rp.text[:200]}")
    if SBH:
        # Remove from priority if present
        requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=SBH,timeout=10)
        # Add to no_replenish so bot doesn't auto-reactivate
        requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
            headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
            json={"item_id":iid,"account":"CLARIBEL","reason":"pausa manual usuario"},timeout=10)
        # Directive
        requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
            json={"account":"CLARIBEL","scope":"item","scope_value":iid,
                  "directive_type":"pause","value_numeric":None,"raw_user_message":USER_MSG},timeout=10)
    time.sleep(0.5)
    g2=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"[AFTER] {iid} status={g2.get('status')} sub={g2.get('sub_status')}")
