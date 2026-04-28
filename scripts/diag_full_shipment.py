"""Dump full JSON of one shipment to find pickup/handling date."""
import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}
sd = requests.get("https://api.mercadolibre.com/shipments/46925787200",headers=H,timeout=10).json()
print(json.dumps(sd, indent=2, ensure_ascii=False))
