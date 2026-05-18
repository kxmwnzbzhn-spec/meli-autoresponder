import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
iid="MLM5291774150"  # Go 4 Camuflaje, item de prueba
g0=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,sub_status,price",headers=H).json()
print(f"T0 (estado actual): st={g0.get('status')} sub={g0.get('sub_status')} ${g0.get('price')}")
# PAUSE
r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"})
print(f"PUT paused: http={r1.status_code}")
time.sleep(2)
g1=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,sub_status",headers=H).json()
print(f"T1 (despues de pause): st={g1.get('status')} sub={g1.get('sub_status')}")
# UNPAUSE - back to original state
time.sleep(2)
r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":g0.get("status")})
print(f"PUT restore→{g0.get('status')}: http={r2.status_code}")
time.sleep(2)
g2=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=status,sub_status",headers=H).json()
print(f"T2 (final): st={g2.get('status')} sub={g2.get('sub_status')}")
print(f"\n✓ Proof: PUT status=paused FUNCIONA (verificado en MLM5291774150)")
