"""Close 3 Adrián items permanently."""
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

USER_MSG="borra esto de adrian 2969851675,2969824469,2969825021"
IDS=["MLM2969851675","MLM2969824469","MLM2969825021"]

ok=0; fail=0
for iid in IDS:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        st=g.get("status")
        print(f"\n[BEFORE] {iid} status={st} title={(g.get('title') or '')[:80]}")
        if st=="active":
            rp1=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=12)
            print(f"  [PAUSE] HTTP {rp1.status_code}")
            time.sleep(0.5)
        # Close
        rp2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=12)
        print(f"  [CLOSE] HTTP {rp2.status_code}: {rp2.text[:200]}")
        if rp2.status_code in (200,201):
            ok+=1
            requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=SBH,timeout=8)
            requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
                headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
                json={"item_id":iid,"account":"ADRIAN","reason":"borrado/cerrado por usuario"},timeout=8)
            requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                json={"account":"ADRIAN","scope":"item","scope_value":iid,
                      "directive_type":"close","value_numeric":None,"raw_user_message":USER_MSG},timeout=8)
            requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
                json={"account":"ADRIAN","item_id":iid,"action_type":"close",
                      "from_value":str(st),"to_value":"closed",
                      "actor":"claude_cowork","details":USER_MSG},timeout=8)
        else:
            fail+=1
        g2=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        print(f"  [AFTER] status={g2.get('status')} sub={g2.get('sub_status')}")
    except Exception as e:
        fail+=1; print(f"  EXC: {e}")
    time.sleep(0.3)

print(f"\n=== SUMMARY ok={ok} fail={fail} ===")
