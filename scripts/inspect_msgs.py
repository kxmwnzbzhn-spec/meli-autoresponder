import os, requests, json, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
INPUT="2000013380386965"

for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=15)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED RT] {NEW_RT}")
H={"Authorization":f"Bearer {AT}"}

# Try as order first
print(f"\n=== as ORDER {INPUT} ===")
g=requests.get(f"{API}/orders/{INPUT}",headers=H,timeout=12)
print(f"HTTP {g.status_code}")
ORDER_ID=PACK_ID=None
SELLER=None; BUYER=None; PRODUCT=None
if g.status_code==200:
  od=g.json()
  ORDER_ID=str(od.get("id"))
  PACK_ID=str(od.get("pack_id") or od.get("id"))
  SELLER=od.get("seller",{}).get("id"); BUYER=od.get("buyer",{}).get("id")
  print(f"  order_id={ORDER_ID} pack_id={PACK_ID} seller={SELLER} buyer={BUYER}")
  items=od.get("order_items",[])
  if items:
    PRODUCT=items[0]["item"]["title"]
    print(f"  product: {PRODUCT[:100]}")
  print(f"  status: {od.get('status')} | total: {od.get('total_amount')}")
else:
  print(f"  body: {g.text[:300]}")
  # Try as pack
  print(f"\n=== as PACK {INPUT} ===")
  p=requests.get(f"{API}/packs/{INPUT}",headers=H,timeout=12)
  print(f"HTTP {p.status_code}")
  if p.status_code==200:
    pd=p.json()
    PACK_ID=str(pd.get("id"))
    orders=pd.get("orders",[])
    print(f"  pack_id={PACK_ID} orders={[o.get('id') for o in orders]}")
    if orders:
      ORDER_ID=str(orders[0]["id"])
      # Get order detail
      o2=requests.get(f"{API}/orders/{ORDER_ID}",headers=H,timeout=12).json()
      SELLER=o2.get("seller",{}).get("id"); BUYER=o2.get("buyer",{}).get("id")
      items=o2.get("order_items",[])
      if items:
        PRODUCT=items[0]["item"]["title"]
      print(f"  order_id={ORDER_ID} seller={SELLER} buyer={BUYER}")
      print(f"  product: {PRODUCT[:100] if PRODUCT else '?'}")

if not (PACK_ID and SELLER):
  print("ABORT: not found"); raise SystemExit(1)

# Read post-sale messages
print(f"\n=== POST-SALE MESSAGES ===")
m=requests.get(f"{API}/messages/packs/{PACK_ID}/sellers/{SELLER}",
  headers=H,params={"tag":"post_sale","limit":50},timeout=15)
print(f"HTTP {m.status_code}")
if m.status_code==200:
  mj=m.json()
  msgs=mj.get("messages") or mj.get("results") or []
  if isinstance(mj,list): msgs=mj
  print(f"  total: {len(msgs)}")
  for x in msgs:
    f=x.get("from") or {}
    t=x.get("to") or {}
    txt=(x.get("text") or {}).get("plain") or x.get("message") or ""
    msg_id=x.get("id")
    dt=x.get("message_date",{}).get("created") or x.get("date_created","")
    print(f"  {dt[:19]} | {msg_id} | from {f.get('user_id')} -> to {t.get('user_id')}")
    print(f"    text: {txt[:400]}")
else:
  print(f"  body: {m.text[:500]}")

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
