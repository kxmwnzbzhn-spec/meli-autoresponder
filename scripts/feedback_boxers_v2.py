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

# 1) Get ALL orders
print(f"\n=== Fetching orders for item {ITEM_TARGET} ===")
all_orders=[]
offset=0
while True:
  r=requests.get(f"{API}/orders/search",headers=H,
    params={"seller":SELLER,"item":ITEM_TARGET,"sort":"date_desc","limit":50,"offset":offset},timeout=20)
  if r.status_code!=200: break
  j=r.json(); res=j.get("results",[]); all_orders.extend(res)
  total=j.get("paging",{}).get("total",0)
  offset+=50
  if offset>=total or not res: break
print(f"TOTAL orders: {len(all_orders)}")

# 2) Filter to delivered shipments
print(f"\n=== Filtering delivered shipments ===")
delivered=[]
already_msg=[]
no_ship=[]
pre_deliv=[]

for o in all_orders:
  pid=str(o.get("pack_id") or o.get("id"))
  buyer=(o.get("buyer") or {}).get("id")
  ship_id=(o.get("shipping") or {}).get("id")
  if not (pid and buyer): continue
  if not ship_id:
    no_ship.append(pid); continue
  try:
    s=requests.get(f"{API}/shipments/{ship_id}",headers=H,timeout=8).json()
    sstatus=s.get("status")
    delivered_at=(s.get("status_history") or {}).get("date_delivered") or s.get("date_delivered")
    if sstatus=="delivered":
      delivered.append({"pack_id":pid,"buyer":buyer,"shipment_id":ship_id,"delivered_at":delivered_at})
    else:
      pre_deliv.append({"pack_id":pid,"status":sstatus})
  except: continue

print(f"  delivered: {len(delivered)}")
print(f"  pre-delivered (paid/ready_to_ship/shipped): {len(pre_deliv)}")
print(f"  no shipping: {len(no_ship)}")

# 3) For each DELIVERED pack, skip if already messaged in last 30 days
print(f"\n=== Sending feedback messages to delivered packs ===")
MSG=("Hola! Espero que ya hayas recibido tu Pack 3 Boxers Calvin Klein de Elite Market y todo esté en orden. "
     "Mi nombre es Luis del equipo Elite Market y quería confirmarte que la talla quedó perfecta y la calidad cumplió tus expectativas. "
     "Si todo bien, agradecería mucho que dejaras una calificación honesta en la publicación cuando puedas — "
     "tu opinión nos ayuda a seguir trayendo producto premium a buen precio. "
     "Si algo no salió como esperabas o tienes cualquier detalle, contéstame por aquí antes de calificar y lo resolvemos al momento. "
     "Saludos cordiales — Elite Market.")
print(f"[msg length] {len(MSG)} chars")

now=datetime.now(timezone.utc)
sent=0; skipped=0; failed=0
fail_reasons={}
for d in delivered[:200]:
  pid=d["pack_id"]; buyer=d["buyer"]
  # Check existing seller msgs in last 30 days
  already=False
  try:
    m=requests.get(f"{API}/messages/packs/{pid}/sellers/{SELLER}",
      headers=H,params={"tag":"post_sale","limit":20},timeout=10)
    if m.status_code==200:
      mj=m.json(); msgs=mj.get("messages") or mj.get("results") or []
      if isinstance(mj,list): msgs=mj
      for x in msgs:
        f=(x.get("from") or {}).get("user_id"); dt=x.get("message_date",{}).get("created") or x.get("date_created") or ""
        if f==SELLER and dt:
          try:
            dd=datetime.fromisoformat(dt.replace("Z","+00:00"))
            if (now-dd).days<30: already=True; break
          except: pass
  except: pass
  if already:
    skipped+=1; continue
  # SEND
  HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json","x-format-new":"true"}
  payload={"from":{"user_id":SELLER},"to":{"user_id":buyer},"text":MSG}
  rs=requests.post(f"{API}/messages/packs/{pid}/sellers/{SELLER}?tag=post_sale",
    headers=HJ,json=payload,timeout=20)
  if rs.status_code<300:
    sent+=1
    print(f"  ✅ pack={pid} buyer={buyer} (delivered_at={d['delivered_at']})")
  else:
    failed+=1
    err_code=rs.json().get("message","?") if rs.headers.get("content-type","").startswith("application/json") else rs.text[:100]
    fail_reasons[err_code]=fail_reasons.get(err_code,0)+1
    if failed<=5:
      print(f"  ❌ pack={pid} HTTP {rs.status_code}: {rs.text[:200]}")
  time.sleep(0.35)

print(f"\n=== END  sent={sent}  skipped={skipped}  failed={failed} ===")
print(f"fail reasons: {fail_reasons}")

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
