"""1) Set qty=1 a las 46 listings Alchemia en ASVA.
2) Postear a Supabase meli_managed_stock cada una con real_stock=100."""
import os, requests, time
API="https://api.mercadolibre.com"

tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]
},timeout=20).json()
T=tok["access_token"]; print(f"NEW_RT_ASVA={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

SB_URL=os.environ["SUPABASE_URL_PROXY"]
SB_KEY=os.environ["SUPABASE_SERVICE_KEY"]

# 46 Alchemia listings (23 nuevos + 23 ya existentes)
IDS=[
 "MLM2967772739","MLM2967805695","MLM2967785553","MLM2967805717","MLM2967772751",
 "MLM2967785571","MLM2967772767","MLM2967805739","MLM2967772777","MLM2967805753",
 "MLM2967805759","MLM2967772787","MLM2967759903","MLM2967759907","MLM2967805775",
 "MLM2967759915","MLM2967772809","MLM2967772817","MLM2967772829","MLM2967805809",
 "MLM2967759935","MLM2967785655","MLM2967785667",
 "MLM2378074941","MLM3849137034","MLM2378087893","MLM2954229423","MLM2945250605",
 "MLM5374718702","MLM2945214721","MLM2598943053","MLM2594259115","MLM2594259089",
 "MLM2592601259","MLM2592360377","MLM2592715459","MLM2592715389","MLM2592360231",
 "MLM2592664137","MLM4436268412","MLM2592715211","MLM5374722276","MLM2592360045",
 "MLM4436177528","MLM2592740671","MLM2594564705",
]

ok_qty=0; err_qty=0; sb_ok=0; sb_err=0
rows=[]
for i,sid in enumerate(IDS,1):
    g=requests.get(f"{API}/items/{sid}",headers=H,params={"attributes":"id,title,status,available_quantity,sub_status"},timeout=15).json()
    cur_qty=g.get("available_quantity",0); st=g.get("status"); title=(g.get("title") or "")[:50]
    # Set qty=1 + active if paused/out_of_stock
    payload={"available_quantity":1}
    if st=="paused":
        payload["status"]="active"
    r=requests.put(f"{API}/items/{sid}",headers=HJ,json=payload,timeout=20)
    if r.status_code in (200,201):
        ok_qty+=1
        print(f"[{i:2}/46] {sid} qty {cur_qty}->1 status {st}->active OK '{title}'")
    else:
        err_qty+=1
        print(f"[{i:2}/46] {sid} ERR {r.status_code} {r.text[:100]}")
    rows.append({"item_id":sid,"account":"ASVA","real_stock":100,"qty_visible":1,"product_name":title})
    time.sleep(0.3)

# Upsert to Supabase
print(f"\n--- Upserting {len(rows)} rows to meli_managed_stock ---")
try:
    r=requests.post(f"{SB_URL}/rest/v1/meli_managed_stock",
        headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal,resolution=merge-duplicates"},
        json=rows, timeout=30)
    print(f"Supabase upsert: {r.status_code} {r.text[:200] if r.status_code>=400 else 'OK'}")
    if r.status_code<300: sb_ok=len(rows)
    else: sb_err=len(rows)
except Exception as e:
    print(f"Supabase exc: {e}"); sb_err=len(rows)

print(f"\n=== DONE === qty_ok={ok_qty} qty_err={err_qty} supabase_ok={sb_ok} supabase_err={sb_err}")
