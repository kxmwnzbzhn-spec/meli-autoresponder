import os, json, requests
API="https://api.mercadolibre.com"; SELLER=3658310023
IDS=json.load(open("config/rosa_153_ids.json"))
rt=os.environ["MELI_REFRESH_TOKEN_ROSA_MARIA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt},timeout=30)
r.raise_for_status(); tok=r.json()
open("/tmp/rot","w").write(tok.get("refresh_token",""))
H={"Authorization":f"Bearer {tok['access_token']}"}
# tomar 3 shipments (uno de cada svc detectado)
samples = {}
from collections import Counter
svc_cnt=Counter()
for sid in IDS[:30]:  # solo 30 para muestreo
 q=requests.get(f"{API}/shipments/{sid}",headers=H,timeout=20)
 if q.status_code!=200: continue
 sh=q.json()
 svc=sh.get("service_id") or 0
 svc_cnt[svc]+=1
 if svc not in samples:
  samples[svc]={
   "service_id": svc,
   "logistic_type": sh.get("logistic_type"),
   "mode": sh.get("mode"),
   "carrier_info": sh.get("carrier_info"),
   "shipping_option": sh.get("shipping_option"),
   "tags": sh.get("tags"),
   "sender_id": sh.get("sender_id"),
  }
print(json.dumps({"svc_cnt":dict(svc_cnt),"samples":samples},indent=2,ensure_ascii=False,default=str))
