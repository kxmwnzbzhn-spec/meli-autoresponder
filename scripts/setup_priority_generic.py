"""Generic: identify owner across all accounts, set qty=1, register in priority_replenish."""
import os, requests, sys
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=representation"}

ITEM=os.environ["TARGET_ITEM"]
USER_MSG=os.environ.get("RAW_MSG", f"priority replenish qty=1 {ITEM}")

ACCS=[
  ("CLARIBEL","MELI_REFRESH_TOKEN_CLARIBEL"),
  ("ASVA","MELI_REFRESH_TOKEN_ASVA"),
  ("MAYRELY","MELI_REFRESH_TOKEN_MAYRELY"),
  ("BREN","MELI_REFRESH_TOKEN_BREN"),
  ("DILCIE","MELI_REFRESH_TOKEN_DILCIE"),
  ("MILDRED","MELI_REFRESH_TOKEN_MILDRED"),
  ("JUAN","MELI_REFRESH_TOKEN_JUAN"),
  ("RAYMUNDO","MELI_REFRESH_TOKEN_RAYMUNDO"),
  ("WILBERT","MELI_REFRESH_TOKEN_WILBERT"),
  ("ANGEL","MELI_REFRESH_TOKEN_ANGEL"),
  ("AH","MELI_REFRESH_TOKEN_AH"),
  ("MC","MELI_REFRESH_TOKEN_MC"),
  ("AHA","MELI_REFRESH_TOKEN_OFICIAL"),
  ("ANGEL_DAMIAN","MELI_REFRESH_TOKEN_ANGEL_DAMIAN"),
  ("ASGARI","MELI_REFRESH_TOKEN_ASGARI"),
  ("YC_NEW","MELI_REFRESH_TOKEN"),
  ("RAYMUNDO_MAY","MELI_REFRESH_TOKEN_RAYMUNDO_MAY"),
]

owner=None; AT=None; META=None
for nick,sec in ACCS:
    rt=os.environ.get(sec)
    if not rt: continue
    try:
        r=requests.post(f"{API}/oauth/token",data={
          "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
          "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=15).json()
        at=r.get("access_token")
        if not at: continue
        h={"Authorization":f"Bearer {at}"}
        g=requests.get(f"{API}/items/{ITEM}",headers=h,timeout=10).json()
        if g.get("id")!=ITEM: continue
        me=requests.get(f"{API}/users/me",headers=h,timeout=8).json()
        if me.get("id")==g.get("seller_id"):
            owner=nick; AT=at; META=g
            print(f">>> OWNER={nick} | seller={me.get('id')} | new_rt={r.get('refresh_token')}")
            break
    except: continue

if not owner:
    print(f"NOT FOUND owner for {ITEM}"); sys.exit(1)

H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
print(f"[ITEM] status={META.get('status')} sub={META.get('sub_status')} qty={META.get('available_quantity')} inv={META.get('inventory_id')} price={META.get('price')}")
print(f"  title={META.get('title')}")

# Set qty=1 + activate
r1=requests.put(f"{API}/items/{ITEM}",headers=HJ,json={"available_quantity":1,"status":"active"},timeout=15)
print(f"[SET qty=1 active] HTTP {r1.status_code}: {r1.text[:300]}")

# Register priority
row={"item_id":ITEM,"account":owner,"default_qty":1}
rp=requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
    headers={**SBH,"Prefer":"return=representation,resolution=merge-duplicates"},
    json=row,timeout=15)
print(f"[PRIORITY] HTTP {rp.status_code}: {rp.text[:300]}")

# Directive
d={"account":owner,"scope":"item","scope_value":ITEM,
   "directive_type":"priority_replenish","value_numeric":1,"raw_user_message":USER_MSG}
rd=requests.post(f"{SBU}/rest/v1/meli_user_directives",headers=SBH,json=d,timeout=15)
print(f"[DIRECTIVE] HTTP {rd.status_code}: {rd.text[:200]}")

g2=requests.get(f"{API}/items/{ITEM}",headers=H,timeout=10).json()
print(f"[VERIFY] status={g2.get('status')} qty={g2.get('available_quantity')}")
