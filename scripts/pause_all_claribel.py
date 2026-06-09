"""Pause ALL active items in Claribel."""
import os, requests, time
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]; nick=me.get("nickname")
print(f"seller={uid} nick={nick}")

USER_MSG="pausa todas las publicaciones de claribel"

ids=[]; off=0
while off<5000:
    s=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=20).json()
    res=s.get("results") or []
    ids.extend(res)
    if len(res)<50: break
    off+=50
print(f"\nActive items: {len(ids)}")

ok=0; fail=0; errs=[]
for iid in ids:
    try:
        rp=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=12)
        if rp.status_code in (200,201):
            ok+=1
            requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=SBH,timeout=8)
            requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
                headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
                json={"item_id":iid,"account":"CLARIBEL","reason":"pausa masiva usuario"},timeout=8)
            requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                json={"account":"CLARIBEL","scope":"item","scope_value":iid,
                      "directive_type":"pause","value_numeric":None,"raw_user_message":USER_MSG},timeout=8)
        else:
            fail+=1
            if len(errs)<10: errs.append(f"{iid}:{rp.status_code}:{rp.text[:120]}")
    except Exception as e:
        fail+=1
        if len(errs)<10: errs.append(f"{iid}:EXC:{e}")
    time.sleep(0.08)

print(f"\n=== SUMMARY ===")
print(f"  active total: {len(ids)}")
print(f"  ✅ paused: {ok}")
print(f"  ❌ failed: {fail}")
if errs:
    print("  errors sample:")
    for e in errs[:10]: print(f"    {e}")

requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
    json={"account":"CLARIBEL","item_id":"BULK","action_type":"pause_all",
          "from_value":f"active={len(ids)}",
          "to_value":f"paused={ok} failed={fail}",
          "actor":"claude_cowork",
          "details":"pausa masiva de claribel por usuario"},timeout=10)

TG=os.environ.get("TELEGRAM_BOT_TOKEN",""); CID=os.environ.get("TELEGRAM_CHAT_ID","")
if TG and CID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
        json={"chat_id":CID,"text":f"CLARIBEL pausa masiva: ok={ok} fail={fail} de {len(ids)} activos"},timeout=10)
