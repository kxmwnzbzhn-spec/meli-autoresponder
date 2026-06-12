import os, requests, json, base64, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
ORDER="2000016755298724"
PACK_ID="2000013323144453"

for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}

print(f"\n========== ORDER {ORDER} ==========")
o=requests.get(f"{API}/orders/{ORDER}",headers=H,timeout=15)
print(f"HTTP {o.status_code}")
if o.status_code==200:
  od=o.json()
  print(f"  status: {od.get('status')} | date_created: {od.get('date_created')} | total_amount: {od.get('total_amount')}")
  print(f"  buyer: {od.get('buyer',{}).get('id')} ({od.get('buyer',{}).get('nickname')})")
  print(f"  seller: {od.get('seller',{}).get('id')}")
  items=od.get("order_items",[])
  for it in items:
    item=it.get("item",{})
    print(f"  item: {item.get('id')} | {item.get('title')[:80]}")
    print(f"    qty={it.get('quantity')} unit_price={it.get('unit_price')}")
  ship=od.get("shipping",{})
  print(f"  shipping_id: {ship.get('id')}")
  if ship.get('id'):
    s=requests.get(f"{API}/shipments/{ship.get('id')}",headers=H,timeout=15)
    if s.status_code==200:
      sd=s.json()
      print(f"  shipment status: {sd.get('status')} sub={sd.get('substatus')} mode={sd.get('mode')}")
      print(f"  tracking: {sd.get('tracking_number')} carrier: {sd.get('shipping_option',{}).get('shipping_method',{}).get('display_name')}")
      print(f"  delivered_at: {sd.get('status_history',{}).get('date_delivered')}")
else:
  print(f"  body: {o.text[:400]}")

print(f"\n========== CLAIMS ON ORDER / PACK ==========")
c=requests.get(f"{API}/post-purchase/v1/claims/search",headers=H,
  params={"order_id":ORDER,"limit":20},timeout=15)
print(f"by order_id HTTP {c.status_code} total={c.json().get('paging',{}).get('total') if c.status_code==200 else 'err'}")
cp=requests.get(f"{API}/post-purchase/v1/claims/search",headers=H,
  params={"pack_id":PACK_ID,"limit":20},timeout=15)
print(f"by pack_id  HTTP {cp.status_code} total={cp.json().get('paging',{}).get('total') if cp.status_code==200 else 'err'}")
# Merge claims
if c.status_code==200 and cp.status_code==200:
  d1=c.json().get("data",[]); d2=cp.json().get("data",[])
  seen=set(); merged=[]
  for x in d1+d2:
    if x.get("id") in seen: continue
    seen.add(x.get("id")); merged.append(x)
  class FakeR: pass
  c=FakeR(); c.status_code=200; c._j={"paging":{"total":len(merged)},"data":merged}
  c.json=lambda: c._j
print(f"HTTP {c.status_code}")
if c.status_code==200:
  cd=c.json()
  data=cd.get("data",[])
  print(f"  total claims: {cd.get('paging',{}).get('total')} returned: {len(data)}")
  for claim in data:
    cid=claim.get("id")
    print(f"\n  ---- CLAIM {cid} ----")
    print(f"    type: {claim.get('type')} | stage: {claim.get('stage')} | status: {claim.get('status')}")
    print(f"    reason: {claim.get('reason_id')} | fulfilled: {claim.get('fulfilled')}")
    print(f"    date_created: {claim.get('date_created')} | last_updated: {claim.get('last_updated')}")
    print(f"    resolution: {claim.get('resolution')}")
    for p in claim.get("players",[]):
      acts=[a.get('action') for a in p.get('available_actions') or []]
      print(f"    player {p.get('role')} ({p.get('type')}) user={p.get('user_id')} actions={acts}")
    for re in claim.get("related_entities",[]) or []:
      print(f"    related: {re.get('type')} {re.get('id')}")

    # Detail
    d=requests.get(f"{API}/post-purchase/v1/claims/{cid}/detail",headers=H,timeout=15)
    if d.status_code==200:
      dd=d.json()
      print(f"\n    detail.title: {dd.get('title')}")
      print(f"    detail.problem: {dd.get('problem')}")
      print(f"    detail.description: {dd.get('description')}")
      print(f"    detail.due_date: {dd.get('due_date')}")
      print(f"    detail.action_responsible: {dd.get('action_responsible')}")

    # Reason
    if claim.get('reason_id'):
      rs=requests.get(f"{API}/post-purchase/v1/claims/reasons/{claim.get('reason_id')}",headers=H,timeout=15)
      if rs.status_code==200:
        rj=rs.json()
        print(f"    reason.name: {rj.get('name')}")
        print(f"    reason.detail: {rj.get('detail')}")

    # Affects reputation
    ar=requests.get(f"{API}/post-purchase/v1/claims/{cid}/affects-reputation",headers=H,timeout=15)
    if ar.status_code==200:
      arj=ar.json()
      print(f"    reputation: {arj.get('affects_reputation')} incentive: {arj.get('has_incentive')} due_date: {arj.get('due_date')}")

    # Action history
    ah=requests.get(f"{API}/post-purchase/v1/claims/{cid}/actions-history",headers=H,timeout=15)
    if ah.status_code==200:
      print("    actions_history:")
      for a in ah.json():
        print(f"      {a.get('date_created','')[:19]} | {a.get('player_role'):11} | {a.get('action_name')} (stage={a.get('claim_stage')})")

    # Messages
    msgs=requests.get(f"{API}/post-purchase/v1/claims/{cid}/messages",headers=H,timeout=15)
    if msgs.status_code==200:
      mm=msgs.json()
      msglist=mm.get('messages') if isinstance(mm,dict) else mm
      if msglist:
        print(f"    messages ({len(msglist)}):")
        for m in msglist[:10]:
          who=m.get('sender_role') or m.get('player_role')
          dt=m.get('date_created','')[:19]
          txt=(m.get('message') or m.get('text') or '')[:200]
          print(f"      {dt} | {who}: {txt}")

# Sync RT
try: import nacl.encoding, nacl.public
except: os.system("pip install pynacl -q"); import nacl.encoding, nacl.public
GHT=os.environ.get("GH_PAT")
if GHT and NEW_RT:
  GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
  R="kxmwnzbzhn-spec/meli-autoresponder"
  pk=requests.get(f"https://api.github.com/repos/{R}/actions/secrets/public-key",headers=GHH,timeout=15).json()
  pub=nacl.public.PublicKey(base64.b64decode(pk["key"]))
  sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
  enc=base64.b64encode(sealed).decode()
  requests.put(f"https://api.github.com/repos/{R}/actions/secrets/MELI_REFRESH_TOKEN_ASVA",
    headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
