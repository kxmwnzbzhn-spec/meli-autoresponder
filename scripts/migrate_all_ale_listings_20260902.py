#!/usr/bin/env python3
import base64, json, os, requests
API="https://api.mercadolibre.com"; SELLER=3629038896; T=35
OLD_IDS=[
"MLM6154086230","MLM6154085738","MLM6154084238","MLM6154084098","MLM6154083792","MLM6154083626",
"MLM6154083256","MLM6154083254","MLM6154081360","MLM6154019214","MLM6154007142","MLM6154007138",
"MLM6153842386","MLM6153842376","MLM6153682306","MLM3438315613","MLM3438314633","MLM3438313975",
"MLM3438313813","MLM3438311607","MLM3438304095","MLM3438303611","MLM3438302377","MLM3438302291",
"MLM3438302099","MLM3438302091","MLM3438301787","MLM3438301603","MLM3438301245","MLM3438299333"]
KNOWN={"MLM3438301245":"MLM3441573873"}

r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=T)
r.raise_for_status(); tok=r.json(); open("/tmp/ale_rotated_token","w").write(tok["refresh_token"])
H={"Authorization":f"Bearer {tok['access_token']}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=SELLER: raise RuntimeError("Token no corresponde a Alejandra")

def get(i):
 r=requests.get(f"{API}/items/{i}",headers=H,timeout=T); r.raise_for_status(); return r.json()
def all_ids():
 out=[]; off=0
 while True:
  r=requests.get(f"{API}/users/{SELLER}/items/search",headers=H,params={"limit":100,"offset":off},timeout=T); r.raise_for_status()
  b=r.json().get("results") or []; out+=b
  if len(b)<100: return out
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
  if a.get("value_id"): x["value_id"]=a["value_id"]
  if a.get("value_name"): x["value_name"]=a["value_name"]
  out.append(x); seen.add(aid)
 if "ITEM_CONDITION" not in seen:
  out.append({"id":"ITEM_CONDITION","value_name":{"new":"Nuevo","used":"Usado","refurbished":"Reacondicionado"}[s["condition"]]})
 return out
def create(s):
 ship=s.get("shipping") or {}
 p={"site_id":"MLM","family_name":(s.get("family_name") or s.get("title") or "Producto")[:60],"category_id":s["category_id"],
 "price":s["price"],"currency_id":s.get("currency_id") or "MXN","available_quantity":1,"buying_mode":s.get("buying_mode") or "buy_it_now",
 "listing_type_id":s.get("listing_type_id") or "gold_special","condition":s["condition"],"catalog_product_id":s["catalog_product_id"],
 "catalog_listing":True,"attributes":attrs(s),"shipping":{"mode":"me2","local_pick_up":bool(ship.get("local_pick_up")),"free_shipping":bool(ship.get("free_shipping"))}}
 terms=[]
 for term in s.get("sale_terms") or []:
  if term.get("id") in {"WARRANTY_TYPE","WARRANTY_TIME"}:
   x={"id":term["id"]}
   if term.get("value_id"): x["value_id"]=term["value_id"]
   if term.get("value_name"): x["value_name"]=term["value_name"]
   terms.append(x)
 if terms:p["sale_terms"]=terms
 r=requests.post(f"{API}/items",headers=HJ,json=p,timeout=50)
 print(f"CREATE {s['id']} HTTP={r.status_code} {r.text[:500]}",flush=True)
 if r.status_code in (200,201): return r.json()["id"]
 if r.status_code==400 and "seller.optin.fake" in r.text:
  classic=dict(p)
  classic.pop("catalog_product_id",None); classic.pop("catalog_listing",None); classic.pop("family_name",None)
  classic["title"]=(s.get("title") or "Producto")[:60]
  classic["pictures"]=[{"source":x.get("secure_url") or x.get("url")} for x in (s.get("pictures") or []) if x.get("secure_url") or x.get("url")]
  full=[]
  for a in s.get("attributes") or []:
   if not a.get("id") or (not a.get("value_id") and not a.get("value_name")): continue
   x={"id":a["id"]}
   if a.get("value_id"): x["value_id"]=a["value_id"]
   if a.get("value_name"): x["value_name"]=a["value_name"]
   full.append(x)
  classic["attributes"]=full
  r=requests.post(f"{API}/items",headers=HJ,json=classic,timeout=50)
  print(f"CREATE_CLASSIC {s['id']} HTTP={r.status_code} {r.text[:500]}",flush=True)
  if r.status_code in (200,201): return r.json()["id"]
 raise RuntimeError(f"{s['id']} clone failed {r.status_code} {r.text[:1200]}")

sources={i:get(i) for i in OLD_IDS}
current={}
for iid in all_ids():
 if iid in OLD_IDS: continue
 try:
  x=get(iid)
  if x.get("deleted"): continue
  current.setdefault((x.get("catalog_product_id"),x.get("condition")),[]).append(x)
  current.setdefault(("classic",x.get("title"),x.get("condition"),float(x.get("price") or 0)),[]).append(x)
 except Exception: pass

mapping={}; created=[]
for oid in OLD_IDS:
 s=sources[oid]
 if not s.get("catalog_product_id") or not s.get("catalog_listing"): raise RuntimeError(f"{oid} no es catálogo")
 nid=KNOWN.get(oid)
 if nid:
  n=get(nid)
 else:
  candidates=current.get((s.get("catalog_product_id"),s.get("condition")),[])
  if not candidates:
   candidates=current.get(("classic",s.get("title"),s.get("condition"),float(s.get("price") or 0)),[])
  n=candidates[0] if candidates else None
  nid=n["id"] if n else create(s)
  if not n: created.append(nid)
 n=get(nid)
 if not (n.get("status")=="active" and int(n.get("available_quantity") or 0)==1 and float(n.get("price") or 0)==float(s.get("price") or 0)):
  u=requests.put(f"{API}/items/{nid}",headers=HJ,json={"price":s["price"],"available_quantity":1,"status":"active"},timeout=T)
  if u.status_code not in (200,201):
   ship=s.get("shipping") or {}
   classic={"site_id":"MLM","title":(s.get("title") or "Producto")[:60],"category_id":s["category_id"],"price":s["price"],
    "currency_id":s.get("currency_id") or "MXN","available_quantity":1,"buying_mode":s.get("buying_mode") or "buy_it_now",
    "listing_type_id":s.get("listing_type_id") or "gold_special","condition":s["condition"],"attributes":attrs(s),
    "pictures":[{"source":x.get("secure_url") or x.get("url")} for x in (s.get("pictures") or []) if x.get("secure_url") or x.get("url")],
    "shipping":{"mode":"me2","local_pick_up":bool(ship.get("local_pick_up")),"free_shipping":bool(ship.get("free_shipping"))}}
   rr=requests.post(f"{API}/items",headers=HJ,json=classic,timeout=50)
   print(f"REPLACE_WITH_CLASSIC {s['id']} HTTP={rr.status_code} {rr.text[:500]}",flush=True)
   if rr.status_code not in (200,201): raise RuntimeError(f"{nid} activation failed and classic fallback failed {rr.status_code} {rr.text[:900]}")
   nid=rr.json()["id"]; created.append(nid)
  n=get(nid)
 checks=[nid not in OLD_IDS,int(n.get("seller_id") or 0)==SELLER,n.get("status")=="active",int(n.get("available_quantity") or 0)==1,(n.get("catalog_product_id")==s.get("catalog_product_id") or (not n.get("catalog_listing") and n.get("category_id")==s.get("category_id"))),n.get("condition")==s.get("condition")]
 if not all(checks): raise RuntimeError(f"{oid}->{nid} verify failed {checks}")
 mapping[oid]=nid
 print(f"MAPPED {oid}->{nid}",flush=True)

new_ids=list(dict.fromkeys(mapping.values()))
if len(new_ids)!=len(OLD_IDS): raise RuntimeError(f"Esperaba {len(OLD_IDS)} clones únicos, obtuve {len(new_ids)}")
# Publish the new persistent autostock configuration before retiring originals.
repo="kxmwnzbzhn-spec/meli-autoresponder"; path="config/ale_autostock_migrated_ids.json"
GH={"Authorization":f"Bearer {os.environ['GH_TOKEN']}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
url=f"https://api.github.com/repos/{repo}/contents/{path}"
g=requests.get(url,headers=GH,timeout=T); g.raise_for_status(); sha=g.json()["sha"]
body=json.dumps(new_ids,ensure_ascii=False,indent=2)+"\n"
g=requests.put(url,headers=GH,json={"message":"Switch Alejandra autostock to cloned listings","content":base64.b64encode(body.encode()).decode(),"sha":sha},timeout=T)
g.raise_for_status()
print("AUTOSTOCK_CONFIG_COMMIT="+g.json()["commit"]["sha"],flush=True)

retired=[]
for oid in OLD_IDS:
 c=requests.put(f"{API}/items/{oid}",headers=HJ,json={"status":"closed"},timeout=T)
 d=requests.delete(f"{API}/items/{oid}",headers=H,timeout=T)
 final=get(oid)
 if final.get("status")=="active": raise RuntimeError(f"{oid} siguió activo")
 retired.append({"id":oid,"close_http":c.status_code,"delete_http":d.status_code,"status":final.get("status"),"deleted":final.get("deleted")})
 print(f"RETIRED {oid} close={c.status_code} delete={d.status_code} status={final.get('status')} deleted={final.get('deleted')}",flush=True)

for nid in new_ids:
 n=get(nid)
 if n.get("status")!="active" or int(n.get("available_quantity") or 0)!=1: raise RuntimeError(f"{nid} no quedó activo con una pieza")
print("ALE_MIGRATION_RESULT="+json.dumps({"old_count":len(OLD_IDS),"new_count":len(new_ids),"created_now":len(created),"mapping":mapping,"retired":retired},ensure_ascii=False),flush=True)
