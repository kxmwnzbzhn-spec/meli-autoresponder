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

USER_MSG="pausa todo esto de claribel: 2967317661,2967317613,2967304909,2967292197,2967292287,2967279077,2967292331,2967304869,2967317701,2967317609"
IDS=["MLM2967317661","MLM2967317613","MLM2967304909","MLM2967292197","MLM2967292287",
     "MLM2967279077","MLM2967292331","MLM2967304869","MLM2967317701","MLM2967317609"]

ok=0; fail=0
for iid in IDS:
    try:
        g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        ttl=(g.get("title") or "")[:75]
        st=g.get("status")
        print(f"\n{iid} [BEFORE] status={st} | {ttl}")
        if st=="paused":
            print(f"  already paused, skip PUT")
        else:
            rp=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15)
            print(f"  [PAUSE] HTTP {rp.status_code}: {rp.text[:160]}")
            if rp.status_code in (200,201): ok+=1
            else: fail+=1; continue
        if SBH:
            requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=SBH,timeout=10)
            requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
                headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
                json={"item_id":iid,"account":"CLARIBEL","reason":"pausa manual usuario"},timeout=10)
            requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                json={"account":"CLARIBEL","scope":"item","scope_value":iid,
                      "directive_type":"pause","value_numeric":None,"raw_user_message":USER_MSG},timeout=10)
        if st=="paused": ok+=1
    except Exception as e:
        fail+=1; print(f"  EXC {e}")
    time.sleep(0.3)

print(f"\n=== SUMMARY ok={ok} fail={fail} ===")
