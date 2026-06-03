"""Get full action_guide options for the pack to find STOCK_UNAVAILABLE template."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

PACK="2000013319647593"
rr=requests.get(f"{API}/messages/action_guide/packs/{PACK}",headers=H,timeout=15)
print(f"HTTP {rr.status_code}")
d=rr.json()
print(f"\nTotal options: {len(d.get('options',[]))}")
for opt in d.get("options",[]):
    print(f"\n--- option id={opt.get('id')} type={opt.get('type')} enabled={opt.get('enabled')}")
    print(f"    internal_desc={opt.get('internal_description','')[:80]}")
    for t in (opt.get("templates") or []):
        mlm=(t.get("texts") or {}).get("mlm",{})
        html=(mlm.get("html") or "")[:100]
        print(f"    template_id={t.get('id')} text={html}")
