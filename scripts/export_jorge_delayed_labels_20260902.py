#!/usr/bin/env python3
import json, os, requests, sys, time
from datetime import datetime, timedelta, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
sys.path.insert(0, os.path.dirname(__file__))
from daily_run import build_pdf, clean_title, get_condition, INCLUDED_SUBS

API="https://api.mercadolibre.com"; UID=3640697853; T=30; TARGET=138
OUT="ETIQUETAS_JORGE_DEMORADAS_2026-09-02.pdf"
session=requests.Session()
session.mount("https://",HTTPAdapter(max_retries=Retry(total=10,backoff_factor=2,status_forcelist=[429,500,502,503,504],allowed_methods=["GET"],respect_retry_after_header=True)))
requests.get=session.get
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_JORGE_LUIS"]},timeout=T)
r.raise_for_status(); tok=r.json(); open("/tmp/jorge_rotated_token","w").write(tok["refresh_token"])
at=tok["access_token"]; H={"Authorization":f"Bearer {at}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=UID: raise RuntimeError(f"Token incorrecto: {me.json().get('id')}")
now=datetime.now(timezone.utc); start=now-timedelta(days=365); orders=[]; off=0
while True:
 q=requests.get(f"{API}/orders/search",headers=H,params={"seller":UID,"order.status":"paid","order.date_created.from":start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),"order.date_created.to":now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),"limit":50,"offset":off},timeout=T); q.raise_for_status()
 b=q.json().get("results") or []; orders+=b
 if not b or off+len(b)>=q.json().get("paging",{}).get("total",0): break
 off+=len(b); time.sleep(0.7)
by_sid={}
for o in orders:
 sid=(o.get("shipping") or {}).get("id")
 if sid: by_sid.setdefault(str(sid),[]).append(o)
ships=[]
for idx,(sid,olist) in enumerate(by_sid.items()):
 sr=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=T)
 if sr.status_code!=200: continue
 sh=sr.json()
 if sh.get("status")!="ready_to_ship" or sh.get("substatus") not in INCLUDED_SUBS: continue
 comp=[]; used=False
 for order in olist:
  for it in order.get("order_items") or []:
   obj=it.get("item") or {}; title,_=clean_title(obj,H); qty=it.get("quantity",1); cond=get_condition(obj,H)
   if cond=="used": used=True; comp.append(f"USADO {qty} {title}")
   else: comp.append(f"{qty} {title}")
 if not comp: continue
 buyer=(olist[0].get("buyer") or {}).get("nickname","?")
 created=min((o.get("date_created") or "") for o in olist)
 ships.append({"sid":sid,"account":"JorgeLuis","buyer":buyer,"comp_lines":comp,"has_used":used,"n_prods":len(comp),"at":at,"substatus":sh.get("substatus"),"created":created})
 if idx and idx%100==0: print(f"scanned={idx}/{len(by_sid)}",flush=True)
 time.sleep(0.18)
if len(ships)<TARGET: raise RuntimeError(f"Solo hay {len(ships)} envios accionables; no se puede formar el lote de {TARGET}")
ships.sort(key=lambda s:(s["created"],s["sid"]))
excluded_newest=[s["sid"] for s in ships[TARGET:]]
ships=ships[:TARGET]
ships.sort(key=lambda s:(s["substatus"],s["sid"]))
pages,fail=build_pdf(ships,OUT)
manifest={"generated_at":datetime.now(timezone.utc).isoformat(),"criterion":"138 envios demorados originales; se excluyen altas posteriores al corte","unique_shipments":len(ships),"pages":pages,"failed":fail,"excluded_newer_count":len(excluded_newest),"substatus_counts":{}}
for s in ships: manifest["substatus_counts"][s["substatus"]]=manifest["substatus_counts"].get(s["substatus"],0)+1
open("ETIQUETAS_JORGE_DEMORADAS_2026-09-02.json","w").write(json.dumps(manifest,ensure_ascii=False,indent=2))
print("JORGE_DELAYED_PDF="+json.dumps(manifest,ensure_ascii=False),flush=True)
if fail or pages!=TARGET: raise RuntimeError(f"PDF incompleto: target={TARGET} pages={pages} fail={len(fail)}")
