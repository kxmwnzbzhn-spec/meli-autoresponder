import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}

IID="MLM5705329722"

# 1) Verify item exists and status
g=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=10).json()
print(f"\n=== ITEM {IID} ===",flush=True)
print(f"  title: {g.get('title','?')[:80]}",flush=True)
print(f"  status: {g.get('status')} sub_status: {g.get('sub_status')}",flush=True)
print(f"  seller_id: {g.get('seller_id')}",flush=True)
print(f"  health: {g.get('health')}",flush=True)

# 2) Get ALL questions on this item (answered + pending)
q=requests.get(f"https://api.mercadolibre.com/questions/search?item={IID}&sort_fields=date_created&sort_types=DESC&limit=50",headers=H,timeout=15).json()
print(f"\n=== QUESTIONS on {IID}: total={q.get('total','?')} ===",flush=True)
for question in q.get("questions",[])[:20]:
    qtext=question.get("text","")[:120]
    qid=question.get("id")
    qdate=question.get("date_created","")
    status=question.get("status","")
    from_user=question.get("from",{}).get("id","?")
    ans=question.get("answer") or {}
    atext=ans.get("text","")[:200] if ans else ""
    adate=ans.get("date_created","") if ans else ""
    print(f"\n  QID {qid} [{status}] {qdate}",flush=True)
    print(f"    Q [{from_user}]: {qtext}",flush=True)
    if atext:
        print(f"    A ({adate}): {atext}",flush=True)
