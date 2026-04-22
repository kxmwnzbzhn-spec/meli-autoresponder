import os,requests,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

RETRY=["MLM5224043294","MLM2880903119"]
for iid in RETRY:
    for attempt in range(5):
        body={"shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[{"id":73328,"rule":{"default":False,"free_mode":"country","value":None}}]}}
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json=body,timeout=30)
        print(f"{iid} attempt {attempt+1}: {r.status_code}")
        if r.status_code in (200,201):
            time.sleep(2)
            it=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
            fs=it.get("shipping",{}).get("free_shipping")
            print(f"   verified: free_shipping={fs}")
            if fs: break
        time.sleep(3)
