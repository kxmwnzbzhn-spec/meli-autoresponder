import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]

CC=5530747987
H={"Authorization":f"Bearer {AT}"}

print("=== Attempt 1: multipart/form-data ===")
files={"message":(None,"Hola, lamentamos el inconveniente. Para procesar el reembolso necesitamos que devuelva el producto en su empaque original mediante el proceso oficial de MercadoLibre. Una vez recibido procesaremos el reembolso. Saludos cordiales — Elite Market.")}
r1=requests.post(f"{API}/post-purchase/v1/claims/{CC}/messages?attached_role=complainant",headers=H,files=files,timeout=20)
print(f"  → {r1.status_code} {r1.text[:400]}")

print("\n=== Attempt 2: with caller.role+stage in body ===")
H2={**H,"Content-Type":"application/json"}
body={"receiver_role":"complainant","message":"test"}
r2=requests.post(f"{API}/post-purchase/v1/claims/{CC}/messages",headers=H2,json=body,timeout=20)
print(f"  → {r2.status_code} {r2.text[:400]}")

# Try with x-caller-id header
print("\n=== Attempt 3: x-caller-id header ===")
H3={**H2,"x-caller-id":"3417664339"}
r3=requests.post(f"{API}/post-purchase/v1/claims/{CC}/messages",headers=H3,json=body,timeout=20)
print(f"  → {r3.status_code} {r3.text[:400]}")

# Try with version
print("\n=== Attempt 4: v2 endpoint ===")
r4=requests.post(f"{API}/v1/claims/{CC}/messages",headers=H2,json=body,timeout=20)
print(f"  → {r4.status_code} {r4.text[:400]}")

# Try the global-selling pattern
print("\n=== Attempt 5: with stage param ===")
r5=requests.post(f"{API}/post-purchase/v1/claims/{CC}/messages?stage=claim",headers=H,files=files,timeout=20)
print(f"  → {r5.status_code} {r5.text[:400]}")

print("\n=== Attempt 6: only message field, form data ===")
r6=requests.post(f"{API}/post-purchase/v1/claims/{CC}/messages",headers=H,data={"message":"test","receiver_role":"complainant"},timeout=20)
print(f"  → {r6.status_code} {r6.text[:400]}")
