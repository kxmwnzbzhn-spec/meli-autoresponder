"""Probar endpoints MELI para encontrar el código de autorización diario."""
import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]  # JUAN
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID=me["id"]
print(f"JUAN ({me.get('nickname')}) ID={USER_ID}\n")

# Try multiple endpoints
endpoints = [
    f"/users/me",
    f"/users/{USER_ID}",
    f"/myaccount/seller_billing_data",
    f"/myaccount/seller/code",
    f"/myaccount/seller/security_code",
    f"/myaccount/security/access_code",
    f"/security/codes/{USER_ID}",
    f"/users/{USER_ID}/security_code",
    f"/users/{USER_ID}/access_code",
    f"/sellers/{USER_ID}/security_code",
    f"/sellers/{USER_ID}/access_code",
    f"/marketplace/security/daily_code",
    f"/sites/MLM/users/{USER_ID}/access_code",
    f"/shipments/access_code",
    f"/post-purchase/v1/sellers/me/access_code",
    f"/users/me/access_code",
    f"/users/me/security_code",
    f"/sellers/me/access_code",
    f"/shipments/access_code/me",
    f"/users/{USER_ID}/security",
    f"/users/{USER_ID}/operator_code",
    f"/operators/me/code",
    f"/me/access_code",
    f"/access_code",
    f"/access_code/me",
    f"/users/{USER_ID}/pickup_code",
    f"/shipments/me/pickup_code",
    f"/security/access_code/{USER_ID}",
    f"/security/users/{USER_ID}",
    f"/security/me",
]

found = []
for ep in endpoints:
    try:
        rr = requests.get(f"https://api.mercadolibre.com{ep}", headers=H, timeout=8)
        body = rr.text[:500]
        marker = ""
        if rr.status_code == 200:
            # Check if response contains "code", "pin", or 8-char alphanumeric
            import re
            if re.search(r'\b[0-9A-F]{8}\b', body, re.IGNORECASE) or "code" in body.lower() or "pin" in body.lower() or "access" in body.lower():
                marker = " ← POSSIBLE!"
                found.append((ep, body[:200]))
        print(f"  {ep:55} → {rr.status_code}{marker}")
    except Exception as e:
        print(f"  {ep:55} → ERR: {e}")

print(f"\n=== POSSIBLE matches ===")
for ep, b in found:
    print(f"  {ep}")
    print(f"    {b}")
