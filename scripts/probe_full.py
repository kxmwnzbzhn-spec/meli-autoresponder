import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}
USER_ID=1668713481

# 1) Search ALL unanswered questions for seller (same API bot uses)
print("\n=== ALL UNANSWERED for ASVA (bot's own query) ===",flush=True)
r=requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={USER_ID}&status=UNANSWERED&limit=20",headers=H,timeout=15).json()
print(f"  total: {r.get('total','?')}  paging: {r.get('paging',{})}",flush=True)
for q in r.get("questions",[])[:10]:
    qid=q.get("id"); qtext=q.get("text","")[:80]; qdate=q.get("date_created","")
    iid=q.get("item_id"); status=q.get("status","")
    print(f"  Q{qid} [{status}] item={iid} {qdate}",flush=True)
    print(f"    {qtext}",flush=True)

# 2) Also try with x-format-new header
print("\n=== ALL UNANSWERED (with x-format-new) ===",flush=True)
H2={**H,"x-format-new":"true"}
r=requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={USER_ID}&status=UNANSWERED&limit=20",headers=H2,timeout=15).json()
print(f"  total: {r.get('total','?')}",flush=True)
for q in r.get("questions",[])[:5]:
    print(f"  Q{q.get('id')} item={q.get('item_id')} status={q.get('status')} {q.get('text','')[:70]}",flush=True)

# 3) Also list ALL questions (any status) on the item Jorge asked about
print("\n=== Find 'Asva Electronics Go 4 - Negro' item ===",flush=True)
r=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&q=Go 4 Negro&limit=20",headers=H,timeout=15).json()
for iid in r.get("results",[])[:10]:
    ig=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,status,price,available_quantity",headers=H,timeout=8).json()
    if 'go 4' in (ig.get("title","").lower()) and 'negro' in ig.get("title","").lower():
        print(f"  {iid} qty={ig.get('available_quantity')} ${ig.get('price')} | {ig.get('title','')[:70]}",flush=True)
