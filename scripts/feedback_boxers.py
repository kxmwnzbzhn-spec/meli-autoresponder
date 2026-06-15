import os, requests, json, time, base64
from datetime import datetime, timezone, timedelta
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
ITEM_TARGET="MLM2976325463"
SELLER=3417664339

for a in range(5):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(6)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}

# 1) Get all orders that include this item
print(f"\n=== Fetching orders for item {ITEM_TARGET} ===")
all_orders=[]
offset=0
while True:
  r=requests.get(f"{API}/orders/search",headers=H,
    params={"seller":SELLER,"item":ITEM_TARGET,"sort":"date_desc","limit":50,"offset":offset},timeout=20)
  if r.status_code!=200:
    print(f"ERR HTTP {r.status_code}: {r.text[:200]}"); break
  j=r.json()
  res=j.get("results",[])
  all_orders.extend(res)
  total=j.get("paging",{}).get("total",0)
  print(f"  fetched {len(res)} (total {len(all_orders)}/{total})")
  offset+=50
  if offset>=total or not res: break
print(f"\n=== TOTAL ORDERS WITH ITEM: {len(all_orders)} ===")

# 2) Group by pack_id, dedupe buyers
packs={}
for o in all_orders:
  pid=str(o.get("pack_id") or o.get("id"))
  buyer=(o.get("buyer") or {}).get("id")
  status=o.get("status")
  date_closed=o.get("date_closed") or o.get("date_created")
  if not pid or not buyer: continue
  packs.setdefault(pid,{"buyer":buyer,"status":status,"date":date_closed,"orders":[]})
  packs[pid]["orders"].append(o.get("id"))

print(f"\nunique pack_ids: {len(packs)}")

# 3) For each pack, check existing post-sale messages — skip if seller already messaged in last 7 days
MSG=("Hola! Gracias por tu compra del Pack 3 Boxers Calvin Klein de Elite Market. "
     "Esperamos que la talla te haya quedado perfecta y disfrutes la comodidad de la microfibra premium. "
     "Tu opinión es muy importante para nosotros: si te gustó tu compra, agradeceríamos mucho que dejaras "
     "una calificación de 5 estrellas y un breve comentario en la publicación. "
     "Si algo no cumplió tu expectativa o tienes alguna duda, escríbenos por aquí antes de calificar — "
     "resolvemos cualquier detalle de inmediato. Saludos cordiales — Elite Market.")
print(f"\n[msg length] {len(MSG)} chars\n")

now=datetime.now(timezone.utc)
sent=0; skipped=0; failed=0
for pid,info in list(packs.items())[:200]:
  buyer=info["buyer"]
  # Check existing messages
  try:
    m=requests.get(f"{API}/messages/packs/{pid}/sellers/{SELLER}",
      headers=H,params={"tag":"post_sale","limit":20},timeout=12)
    if m.status_code==200:
      mj=m.json(); msgs=mj.get("messages") or mj.get("results") or []
      if isinstance(mj,list): msgs=mj
      # If seller sent any post-sale message in last 7 days, skip
      already=False
      for x in msgs:
        f=(x.get("from") or {}).get("user_id")
        dt=x.get("message_date",{}).get("created") or x.get("date_created") or ""
        if f==SELLER and dt:
          try:
            d=datetime.fromisoformat(dt.replace("Z","+00:00"))
            if (now-d).days<7: already=True; break
          except: pass
      if already:
        skipped+=1
        print(f"  [SKIP recent msg] pack={pid} buyer={buyer}")
        continue
  except: pass
  
  # SEND
  HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"true"}
  payload={"from":{"user_id":SELLER},"to":{"user_id":buyer},"text":MSG}
  try:
    rs=requests.post(f"{API}/messages/packs/{pid}/sellers/{SELLER}?tag=post_sale",
      headers=HJ,json=payload,timeout=20)
    if rs.status_code<300:
      sent+=1
      print(f"  ✅ pack={pid} buyer={buyer}")
    else:
      failed+=1
      print(f"  ❌ pack={pid} HTTP {rs.status_code}: {rs.text[:150]}")
  except Exception as e:
    failed+=1; print(f"  ❌ pack={pid} EXC {e}")
  time.sleep(0.4)  # rate limit

print(f"\n=== END  sent={sent}  skipped={skipped}  failed={failed} ===")

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
  requests.put(f"https://api.github.com/repos/{R}/actions/secrets/MELI_REFRESH_TOKEN_AH",
    headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
