import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
SELLER=me["id"]
print(f"ASVA seller={SELLER}")

# Search recent questions on ASVA's items + filter by text
all_q=[]
offset=0
while True:
  r=requests.get(f"{API}/questions/search",headers=H,
    params={"seller_id":SELLER,"limit":50,"offset":offset,"sort":"date_created","sort.direction":"desc"},timeout=20)
  if r.status_code!=200:
    print(f"HTTP {r.status_code}: {r.text[:200]}"); break
  j=r.json()
  qs=j.get("questions",[])
  if not qs: break
  all_q.extend(qs)
  total=j.get("total") or j.get("paging",{}).get("total",0)
  print(f"fetched {len(qs)} (running total {len(all_q)}/{total})")
  offset+=50
  if offset>=total or len(all_q)>=300: break

print(f"\n=== Total preguntas ASVA: {len(all_q)} ===")

# Filter by keyword
KEYWORDS=["inspira","inspirado","original","es real"]
hits=[]
for q in all_q:
  txt=(q.get("text") or "").lower()
  if any(k in txt for k in KEYWORDS):
    hits.append(q)
print(f"matches with keywords {KEYWORDS}: {len(hits)}")
for q in hits[:20]:
  print(f"\n--- Q {q.get('id')} ---")
  print(f"  date: {q.get('date_created')}")
  print(f"  item: {q.get('item_id')}")
  print(f"  from: user {q.get('from',{}).get('id')}")
  print(f"  text: {q.get('text','')}")
  ans=q.get("answer")
  if ans:
    print(f"  answer ({ans.get('date_created')}): {ans.get('text','')}")
  else:
    print(f"  answer: NONE")
  print(f"  status: {q.get('status')}")
