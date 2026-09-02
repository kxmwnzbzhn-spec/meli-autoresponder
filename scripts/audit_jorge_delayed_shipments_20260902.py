#!/usr/bin/env python3
import json, os, re, requests
from datetime import datetime, timedelta, timezone
API="https://api.mercadolibre.com"; UID=3640697853; TZ=timezone(timedelta(hours=-6)); TODAY=datetime.now(TZ).date(); T=25
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"]},timeout=T)
r.raise_for_status(); tok=r.json(); open("/tmp/jorge_rotated_token","w").write(tok["refresh_token"])
H={"Authorization":f"Bearer {tok['access_token']}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=UID: raise RuntimeError(f"Token incorrecto: {me.json().get('id')}")
now=datetime.now(timezone.utc); start=now-timedelta(days=365); orders=[]; off=0
while True:
 q=requests.get(f"{API}/orders/search",headers=H,params={"seller":UID,"order.status":"paid","order.date_created.from":start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),"order.date_created.to":now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),"limit":50,"offset":off},timeout=T); q.raise_for_status()
 b=q.json().get("results") or []; orders+=b
 if not b or off+len(b)>=q.json().get("paging",{}).get("total",0): break
 off+=len(b)
sids=sorted({str((o.get("shipping") or {}).get("id")) for o in orders if (o.get("shipping") or {}).get("id")})
rows=[]
for i,sid in enumerate(sids):
 r=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=T)
 if r.status_code!=200: continue
 s=r.json(); raw=((s.get("date_handling") or {}).get("estimated_handling_limit") or {}).get("date") or (((s.get("shipping_option") or {}).get("estimated_handling_limit") or {}).get("date"))
 day=None
 if raw:
  try: day=datetime.fromisoformat(re.sub(r"\.\d+","",raw)).astimezone(TZ).date()
  except: pass
 rows.append({"sid":sid,"status":s.get("status"),"substatus":s.get("substatus"),"limit":str(day) if day else None,"late":bool(day and day<TODAY)})
 if i and i%100==0: print(f"scanned={i}/{len(sids)}",flush=True)
from collections import Counter
breakdown=Counter((x["status"],x["substatus"],x["late"]) for x in rows)
a=[x for x in rows if x["status"]=="ready_to_ship" and x["late"]]
b=[x for x in a if x["substatus"]=="ready_to_print"]
c=[x for x in a if x["substatus"] in {"ready_to_print","printing_error","printed","invoice_pending"}]
print("JORGE_DELAYED_AUDIT="+json.dumps({"today":str(TODAY),"orders":len(orders),"shipments":len(rows),"ready_late":len(a),"ready_to_print_late":len(b),"actionable_late":len(c),"breakdown":[{"status":k[0],"substatus":k[1],"late":k[2],"count":v} for k,v in sorted(breakdown.items(),key=lambda z:str(z[0]))],"ready_late_ids":[x["sid"] for x in a]},ensure_ascii=False),flush=True)
