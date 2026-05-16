import os,requests,json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
YIR=["MLM2935286605","MLM2935286537","MLM2935286615","MLM2935286651","MLM2935286681","MLM2935286703","MLM2935298361","MLM5353104620","MLM2935286557","MLM2935286629","MLM5353056250","MLM5353056406"]
print(f"{'ID':<18} {'st':<8} {'sub':<22} {'qty':>3} {'sold':>4} {'$':>5}  title")
for iid in YIR:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
    sub=','.join(g.get('sub_status',[]) or [])
    print(f"{iid:<18} {g.get('status','?')[:8]:<8} {sub[:22]:<22} {g.get('available_quantity',0):>3} {g.get('sold_quantity',0):>4} {g.get('price',0):>5}  {(g.get('title') or '')[:40]}")

# Check unanswered questions
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
q=requests.get(f"https://api.mercadolibre.com/questions/search?seller_id={uid}&status=UNANSWERED&limit=50",headers=H).json()
print(f"\nPreguntas UNANSWERED: {q.get('total',0)}")
for x in q.get("questions",[])[:8]:
    print(f"  {x.get('id')} item={x.get('item_id')} '{(x.get('text') or '')[:60]}' {x.get('date_created','')[:10]}")
