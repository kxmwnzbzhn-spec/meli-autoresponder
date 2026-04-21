import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
sid=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()["id"]
# UNANSWERED questions
q=requests.get(f"https://api.mercadolibre.com/my/received_questions/search?status=UNANSWERED&limit=50",headers=H).json()
print(f"UNANSWERED total: {q.get('total')}")
for qu in q.get("questions",[])[:20]:
    print(f"  q{qu.get('id')} item={qu.get('item_id')} | {qu.get('text','')[:80]} | status={qu.get('status')}")
