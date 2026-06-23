import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Check current state of return 143755516 and claim 5530358522
print("=== CLAIM 5530358522 STATE ===")
c=requests.get(f"{API}/post-purchase/v1/claims/5530358522",headers=H,timeout=15).json()
print("stage:",c.get("stage"),"status:",c.get("status"),"resolution:",c.get("resolution"))
print("respondent actions:",[a.get("action") for p in c.get("players",[]) if p.get("role")=="respondent" for a in p.get("available_actions",[])])
print("related:",c.get("related_entities"))

print("\n=== CLAIM 5530353540 STATE ===")
c=requests.get(f"{API}/post-purchase/v1/claims/5530353540",headers=H,timeout=15).json()
print("stage:",c.get("stage"),"status:",c.get("status"),"resolution:",c.get("resolution"))
print("respondent actions:",[a.get("action") for p in c.get("players",[]) if p.get("role")=="respondent" for a in p.get("available_actions",[])])

print("\n=== RETURN 143755516 STATE ===")
ret=requests.get(f"{API}/marketplace/v2/claims/5530358522/returns",headers=H,timeout=15).json()
print("status:",ret.get("status"),"status_money:",ret.get("status_money"),"date_closed:",ret.get("date_closed"))

print("\n=== REVIEWS for 143755516 ===")
rv=requests.get(f"{API}/marketplace/v2/returns/143755516/reviews",headers=H,timeout=15)
print(rv.status_code, rv.text[:500])
print("\n=== REVIEWS for 150143661 ===")
rv=requests.get(f"{API}/marketplace/v2/returns/150143661/reviews",headers=H,timeout=15)
print(rv.status_code, rv.text[:500])
