#!/usr/bin/env python3
import os,requests,json,time
API="https://api.mercadolibre.com"; SELLER=3629038896
IDS=["MLM6154084098","MLM6154081360","MLM3438311607","MLM3438302099","MLM6154084238","MLM3438302091","MLM6154083792","MLM3438313813","MLM3438314633","MLM6154007142","MLM6154007138","MLM6154083626","MLM3438301245"]
FLOOR=420; CEILING=499; STEP=10; T=30
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID_NEW"],"client_secret":os.environ["MELI_APP_SECRET_NEW"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ALE"]},timeout=T)
r.raise_for_status(); a=r.json(); open("/tmp/ale_rotated_token","w").write(a["refresh_token"])
H={"Authorization":f"Bearer {a['access_token']}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=T); me.raise_for_status()
if int(me.json()["id"])!=SELLER: raise RuntimeError(f"Token no corresponde a Alejandra: {me.json()['id']}")

items={}; groups={}
for iid in IDS:
 g=requests.get(f"{API}/items/{iid}",headers=H,timeout=T); g.raise_for_status(); x=g.json()
 if int(x.get("seller_id") or 0)!=SELLER: raise RuntimeError(f"{iid} no pertenece a Alejandra")
 cp=x.get("catalog_product_id")
 if not cp or not x.get("catalog_listing"): raise RuntimeError(f"{iid} no es publicación de catálogo")
 items[iid]=x; groups.setdefault(cp,[]).append(iid)

results=[]
for cp,own_ids in groups.items():
 prod=requests.get(f"{API}/products/{cp}",headers=H,timeout=T); prod.raise_for_status()
 bbw=(prod.json().get("buy_box_winner") or {})
 offers=requests.get(f"{API}/products/{cp}/items",headers=H,params={"limit":100},timeout=T)
 offer_rows=(offers.json().get("results") or []) if offers.status_code==200 else []
 external=[]
 for o in offer_rows:
  try: sid=int(o.get("seller_id") or 0)
  except: sid=0
  if sid==SELLER: continue
  if o.get("status") not in (None,"active"): continue
  p=o.get("price")
  if p is not None: external.append(float(p))
 external_min=min(external) if external else None
 active=[iid for iid in own_ids if items[iid].get("status")=="active"]
 if not active:
  results.append({"catalog":cp,"items":own_ids,"action":"skip_no_active"})
  continue
 current=min(float(items[i]["price"]) for i in active)
 bbw_seller=int(bbw.get("seller_id") or 0); bbw_price=bbw.get("price")
 if current>CEILING: target=CEILING; reason="clamp_ceiling"
 elif current<FLOOR: target=FLOOR; reason="clamp_floor"
 elif bbw_seller==SELLER:
  desired=CEILING if external_min is None else min(CEILING,max(FLOOR,int(external_min)-1))
  target=min(desired,int(current)+STEP) if desired>current else max(desired,int(current)-STEP)
  reason="winning_raise_safely" if target>current else "winning_hold_or_match"
 else:
  candidate=int(current)-STEP
  if bbw_price is not None:
   candidate=min(candidate,int(float(bbw_price))-1)
  target=max(FLOOR,min(CEILING,candidate)); reason="losing_undercut"
 target=int(target)
 changes=[]
 # Todos nuestros anuncios del mismo catálogo conservan exactamente el mismo precio:
 # así nunca se subastan a la baja entre sí.
 for iid in active:
  old=float(items[iid]["price"])
  if int(old)!=target:
   u=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":target},timeout=T)
   changes.append({"id":iid,"from":old,"to":target,"http":u.status_code})
   if u.status_code not in (200,201): raise RuntimeError(f"{iid} price update failed {u.status_code}: {u.text[:800]}")
 results.append({"catalog":cp,"items":own_ids,"bbw_seller":bbw_seller,"bbw_price":bbw_price,"external_min":external_min,"current":current,"target":target,"reason":reason,"changes":changes})
 time.sleep(.25)
print("ALE_WATCHDOG_RESULT="+json.dumps({"seller":SELLER,"floor":FLOOR,"ceiling":CEILING,"groups":results},ensure_ascii=False),flush=True)
