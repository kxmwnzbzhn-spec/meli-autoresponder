#!/usr/bin/env python3
"""Clone 23 Alejandra catalog listings to DIDER, one visible, unlimited restock."""
import base64, json, os, requests, time
API="https://api.mercadolibre.com"; T=40
ALE=3629038896; DIDER=3654003391
SOURCES=["MLM3445690083","MLM3445690103","MLM3445703067","MLM3445690081","MLM3445703061","MLM3445690101","MLM3445703045","MLM3445652295","MLM3445652291","MLM3445703069","MLM3445703049","MLM3445652297","MLM3445703043","MLM3445690073","MLM3445652303","MLM3445652319","MLM3445703035","MLM3445690105","MLM3445690091","MLM3445652289","MLM3445690115","MLM3445690077","MLM3445703037"]

def token(app,secret,refresh,path):
 r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":app,"client_secret":secret,"refresh_token":refresh},timeout=T)
 r.raise_for_status(); x=r.json(); open(path,"w").write(x.get("refresh_token","")); return x["access_token"]
at=token(os.environ["MELI_APP_ID_NEW"],os.environ["MELI_APP_SECRET_NEW"],os.environ["MELI_REFRESH_TOKEN_ALE"],"/tmp/ale_rotated_token")
dt=token(os.environ["MELI_APP_ID"],os.environ["MELI_APP_SECRET"],os.environ["MELI_REFRESH_TOKEN_DIDER"],"/tmp/dider_rotated_token")
AH={"Authorization":f"Bearer {at}"}; DH={"Authorization":f"Bearer {dt}"}; DJ={**DH,"Content-Type":"application/json"}
for H,uid,name in ((AH,ALE,"ALE"),(DH,DIDER,"DIDER")):
 m=requests.get(f"{API}/users/me",headers=H,timeout=T); m.raise_for_status()
 if int(m.json().get("id") or 0)!=uid: raise RuntimeError(f"Token incorrecto {name}")

def get(iid,H):
 r=requests.get(f"{API}/items/{iid}",headers=H,timeout=T); r.raise_for_status(); return r.json()
def seller_ids():
 out=[]; off=0
 while True:
  r=requests.get(f"{API}/users/{DIDER}/items/search",headers=DH,params={"limit":100,"offset":off},timeout=T); r.raise_for_status()
  b=r.json().get("results") or []; out+=b
  if len(b)<100:return out
  off+=100
def attrs(s):
 out=[]; seen=set()
 for a in s.get("attributes") or []:
  aid=a.get("id")
  if aid not in {"GTIN","EAN","UPC","ITEM_CONDITION","GRADING"} or aid in seen: continue
  val=str(a.get("value_name") or "").strip()
  if aid in {"GTIN","EAN","UPC"}:
   if not (val.isdigit() and 8<=len(val)<=14): continue
   aid="GTIN"
  x={"id":aid}
  if a.get("value_id"):x["value_id"]=a["value_id"]
  if a.get("value_name"):x["value_name"]=a["value_name"]
  out.append(x); seen.add(aid)
 if "ITEM_CONDITION" not in seen:
  out.append({"id":"ITEM_CONDITION","value_name":{"new":"Nuevo","used":"Usado","refurbished":"Reacondicionado"}[s["condition"]]})
 return out

SBU=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}
def bounds(s):
 cpid=s.get("catalog_product_id")
 r=requests.get(f"{SBU}/rest/v1/meli_catalog_strategy",headers=SBH,params={"catalog_product_id":f"eq.{cpid}","active":"eq.true","select":"floor,ceiling","limit":"1"},timeout=15)
 if r.status_code==200 and r.json():
  z=r.json()[0]
  if z.get("floor") is not None and z.get("ceiling") is not None:return float(z["floor"]),float(z["ceiling"]),"strategy"
 title=(s.get("title") or "").lower()
 if "clip 5" in title or "clip5" in title:return 599.0,799.0,"ale-clip5"
 return 420.0,499.0,"ale-catalog"

sources={i:get(i,AH) for i in SOURCES}
for iid,s in sources.items():
 if int(s.get("seller_id") or 0)!=ALE:raise RuntimeError(f"{iid} no pertenece a Alejandra")
 if not s.get("catalog_product_id") or not s.get("catalog_listing"):raise RuntimeError(f"{iid} no es catálogo")
current={}
for iid in seller_ids():
 try:
  x=get(iid,DH)
  if not x.get("deleted"):current.setdefault((x.get("catalog_product_id"),x.get("condition")),[]).append(x)
 except Exception:pass

created=[]; mapping={}; price_cfg={}
for oid in SOURCES:
 s=sources[oid]; key=(s["catalog_product_id"],s["condition"])
 candidates=current.get(key) or []
 n=next((x for x in candidates if x.get("status") in {"active","paused"}),None)
 floor,ceiling,bsource=bounds(s)
 if n:nid=n["id"]
 else:
  ship=s.get("shipping") or {}
  p={"site_id":"MLM","family_name":(s.get("family_name") or s.get("title") or "Producto")[:60],"category_id":s["category_id"],
     "price":min(ceiling,max(floor,float(s.get("price") or ceiling))),"currency_id":"MXN","available_quantity":1,
     "buying_mode":"buy_it_now","listing_type_id":s.get("listing_type_id") or "gold_special","condition":s["condition"],
     "catalog_product_id":s["catalog_product_id"],"catalog_listing":True,"attributes":attrs(s),
     "shipping":{"mode":"me2","local_pick_up":bool(ship.get("local_pick_up")),"free_shipping":bool(ship.get("free_shipping"))}}
  r=requests.post(f"{API}/items",headers=DJ,json=p,timeout=60)
  print(f"CREATE {oid} HTTP={r.status_code} {r.text[:600]}",flush=True)
  if r.status_code not in (200,201):raise RuntimeError(f"{oid}: create failed {r.status_code} {r.text[:1200]}")
  nid=r.json()["id"]; created.append(nid); current.setdefault(key,[]).append(get(nid,DH))
 u=requests.put(f"{API}/items/{nid}",headers=DJ,json={"status":"active","available_quantity":1},timeout=T)
 if u.status_code not in (200,201):raise RuntimeError(f"{nid}: activate failed {u.status_code} {u.text[:700]}")
 z=get(nid,DH)
 if int(z.get("seller_id") or 0)!=DIDER or z.get("status")!="active" or int(z.get("available_quantity") or 0)!=1 or z.get("catalog_product_id")!=s.get("catalog_product_id") or z.get("condition")!=s.get("condition"):
  raise RuntimeError(f"{oid}->{nid}: verification failed")
 mapping[oid]=nid; price_cfg[nid]={"floor":floor,"ceiling":ceiling,"source":bsource,"source_item":oid,"catalog_product_id":s["catalog_product_id"]}
 print(f"MAPPED {oid}->{nid} qty=1 bounds={floor}-{ceiling} source={bsource}",flush=True)

repo="kxmwnzbzhn-spec/meli-autoresponder"; GH={"Authorization":f"Bearer {os.environ['GH_TOKEN']}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
def update(path,transform):
 url=f"https://api.github.com/repos/{repo}/contents/{path}"; r=requests.get(url,headers=GH,timeout=T); r.raise_for_status(); meta=r.json()
 old=json.loads(base64.b64decode(meta["content"]).decode()); new=transform(old)
 body=base64.b64encode((json.dumps(new,ensure_ascii=False,indent=2)+"\n").encode()).decode()
 u=requests.put(url,headers=GH,json={"message":"Add Alejandra clones to DIDER automation","content":body,"sha":meta["sha"]},timeout=T); u.raise_for_status()
 return new,u.json()["commit"]["sha"]
all_ids,stock_sha=update("config/dider_autostock_unlimited.json",lambda old:list(dict.fromkeys(old+list(mapping.values()))))
all_bounds,bounds_sha=update("config/dider_price_bounds.json",lambda old:{**old,**price_cfg})
if not all(i in all_ids and i in all_bounds for i in mapping.values()):raise RuntimeError("Config incompleta")
print("DIDER_CLONE_RESULT="+json.dumps({"requested":23,"created":len(created),"mapping":mapping,"stock_total":len(all_ids),"priced_total":len(all_bounds),"stock_commit":stock_sha,"bounds_commit":bounds_sha},ensure_ascii=False),flush=True)
