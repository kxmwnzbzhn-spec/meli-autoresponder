import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Test on the actual problematic question
QID=13630009789  # the "es clon entonces" one

# 1) Look at the question itself
r=requests.get(f"https://api.mercadolibre.com/questions/{QID}",headers=H,timeout=8)
print(f"\nGET question → {r.status_code}",flush=True)
print(r.text[:500],flush=True)

# 2) Try to spam-mark or delete
for method, ep, body in [
    ("DELETE", f"/questions/{QID}", None),
    ("POST", f"/questions/{QID}/spam", None),
    ("POST", f"/questions/{QID}/report", {"reason":"brand_mention"}),
    ("PUT", f"/questions/{QID}", {"deleted":True}),
    ("PUT", f"/questions/{QID}", {"status":"BANNED"}),
    ("PUT", f"/questions/{QID}", {"status":"DELETED"}),
]:
    r=requests.request(method, f"https://api.mercadolibre.com{ep}", headers=H, json=body if body else None, timeout=8)
    print(f"\n{method} {ep} → {r.status_code}",flush=True)
    print(f"  {r.text[:250]}",flush=True)
