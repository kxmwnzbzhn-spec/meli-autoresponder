import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}

IID="MLM5758414962"
r=requests.get(f"https://api.mercadolibre.com/questions/search?item={IID}&sort_fields=date_created&sort_types=DESC&limit=15",headers=H,timeout=15).json()
print(f"\nTotal questions {IID}: {r.get('total','?')}",flush=True)
for q in r.get("questions",[])[:15]:
    qid=q.get("id"); status=q.get("status"); qdate=q.get("date_created")
    qtext=q.get("text","")[:100]
    ans=(q.get("answer") or {}).get("text","")[:150]
    adate=(q.get("answer") or {}).get("date_created","")
    print(f"\nQ{qid} [{status}] {qdate}",flush=True)
    print(f"  Q: {qtext}",flush=True)
    if ans:
        print(f"  A ({adate}): {ans}",flush=True)
