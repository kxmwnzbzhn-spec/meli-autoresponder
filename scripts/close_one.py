import os, requests
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"} if SBK else None

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

ITEM="MLM2967318097"
USER_MSG="cierra esta publicacion en claribel 2967318097"

g=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[BEFORE] status={g.get('status')} sub={g.get('sub_status')} price={g.get('price')} title={g.get('title')}")

# Step 1: must first pause (closed requires paused or already closed state)
if g.get("status")=="active":
    rp=requests.put(f"{API}/items/{ITEM}",headers=HJ,json={"status":"paused"},timeout=15)
    print(f"[PAUSE] HTTP {rp.status_code}: {rp.text[:200]}")

# Step 2: close
rc=requests.put(f"{API}/items/{ITEM}",headers=HJ,json={"status":"closed"},timeout=15)
print(f"[CLOSE] HTTP {rc.status_code}: {rc.text[:300]}")

# Step 3: Supabase — lock from future replenishing + add directive
if SBH:
    # Remove from priority_replenish if present
    rd=requests.delete(f"{SBU}/rest/v1/meli_priority_replenish?item_id=eq.{ITEM}",headers=SBH,timeout=10)
    print(f"[priority DELETE] HTTP {rd.status_code}")
    # Add to no_replenish_items
    rn=requests.post(f"{SBU}/rest/v1/meli_no_replenish_items",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json={"item_id":ITEM,"account":"CLARIBEL","reason":"cerrado por usuario"},timeout=10)
    print(f"[no_replenish UPSERT] HTTP {rn.status_code}")
    # Directive
    rdi=requests.post(f"{SBU}/rest/v1/meli_user_directives",
        headers={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"},
        json={"account":"CLARIBEL","scope":"item","scope_value":ITEM,
              "directive_type":"close","value_numeric":None,"raw_user_message":USER_MSG},timeout=10)
    print(f"[DIRECTIVE close] HTTP {rdi.status_code}")
    # Actions log
    rl=requests.post(f"{SBU}/rest/v1/meli_actions_log",
        headers={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"},
        json={"account":"CLARIBEL","item_id":ITEM,"action_type":"close",
              "from_value":str(g.get('status')),"to_value":"closed",
              "actor":"claude_cowork","details":USER_MSG},timeout=10)
    print(f"[ACTLOG] HTTP {rl.status_code}")

# Verify
g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"\n[AFTER] status={g2.get('status')} sub={g2.get('sub_status')}")
