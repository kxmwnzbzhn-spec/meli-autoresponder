"""Close ALL Adrián items except Calvin Klein Boxers."""
import os, requests, time
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]; print(f"seller={uid} nick={me.get('nickname')}")

# Get ALL items (active + paused), then we'll filter and close
all_ids=[]
for st in ["active","paused"]:
    off=0
    while off<5000:
        s=requests.get(f"{API}/users/{uid}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=20).json()
        ids=s.get("results") or []
        all_ids.extend(ids)
        if len(ids)<50: break
        off+=50
print(f"\nTotal items (active+paused): {len(all_ids)}")

# Multiget to get titles
items={}
for i in range(0,len(all_ids),20):
    batch=",".join(all_ids[i:i+20])
    try:
        mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,status,sub_status"},timeout=15).json()
    except: continue
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        items[b["id"]]={"title":b.get("title") or "","status":b.get("status"),"sub":b.get("sub_status") or []}

# Classify
keep=[]; close=[]
for iid,info in items.items():
    t=info["title"].lower()
    is_ck_boxer=("calvin klein" in t) and ("boxer" in t or "brief" in t or "calzoncillo" in t)
    if is_ck_boxer:
        keep.append((iid,info["title"],info["status"]))
    else:
        close.append((iid,info["title"],info["status"]))

print(f"\nKEEP (Calvin Klein Boxers): {len(keep)}")
for iid,t,st in keep:
    print(f"  ✅ {iid} [{st}] {t[:75]}")
print(f"\nCLOSE: {len(close)}")
for iid,t,st in close[:60]:
    print(f"  ❌ {iid} [{st}] {t[:75]}")
if len(close)>60:
    print(f"  ... +{len(close)-60} more")

# Execute close: paused → closed, active → paused → closed
ok=0; fail=0; errs=[]
for iid,t,st in close:
    try:
        if st=="active":
            rp1=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=12)
            if rp1.status_code not in (200,201):
                fail+=1; errs.append((iid,"pause",rp1.status_code,rp1.text[:120])); continue
        # Now close
        rp2=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=12)
        if rp2.status_code in (200,201):
            ok+=1
            # Remove from priority + add no_replenish + directive
            requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{iid}",headers=SBH,timeout=8)
            requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
                headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
                json={"item_id":iid,"account":"ADRIAN","reason":"cerrado masivo, dejar solo CK Boxers"},timeout=8)
            requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,
                json={"account":"ADRIAN","scope":"item","scope_value":iid,
                      "directive_type":"close","value_numeric":None,
                      "raw_user_message":"finaliza todas las publicaciones de adrian solo deja activo el boxer calvin klein"},timeout=8)
        else:
            fail+=1; errs.append((iid,"close",rp2.status_code,rp2.text[:120]))
    except Exception as e:
        fail+=1; errs.append((iid,"exc",None,str(e)[:120]))
    time.sleep(0.15)

print(f"\n=== SUMMARY ===")
print(f"  Kept: {len(keep)}")
print(f"  ✅ Closed: {ok}")
print(f"  ❌ Failed: {fail}")
if errs:
    print(f"  First errors:")
    for e in errs[:10]:
        print(f"    {e}")

# Telegram
TG=os.environ.get("TELEGRAM_BOT_TOKEN",""); CID=os.environ.get("TELEGRAM_CHAT_ID","")
if TG and CID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
        json={"chat_id":CID,"text":f"Adrián cierre masivo: kept={len(keep)} closed={ok} fail={fail}"},timeout=10)
