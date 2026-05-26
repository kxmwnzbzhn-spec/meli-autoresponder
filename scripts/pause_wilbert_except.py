import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
for ACC,UID in [("JUAN",2681696373),("RAYMUNDO",3338633403),("YC_NEW",3364413125),("AH",3417664339)]:
    AT=meli_token.refresh(os.environ[f"MELI_REFRESH_TOKEN_{ACC}"]).json()["access_token"]
    H={"Authorization":f"Bearer {AT}"}
    print(f"\n### {ACC} (user_id {UID}) ###")
    for path in [
      f"/post-purchase/v1/claims/search?stage=claim&status=opened&players.role=respondent&players.user_id={UID}&limit=5",
      f"/post-purchase/v2/claims/search?status=opened&player_role=respondent&user_id={UID}&limit=5",
    ]:
        r=requests.get(f"{API}{path}",headers=H,timeout=20)
        ct=r.headers.get("content-type","")
        print(f"  GET {path[:55]}... -> {r.status_code}")
        if r.status_code<300 and "json" in ct:
            j=r.json()
            res=j.get("data") or j.get("results") or []
            paging=j.get("paging") or {}
            print(f"    total={paging.get('total','?')} returned={len(res)}")
            for it in res[:2]:
                print(f"    claim_id={it.get('id')} status={it.get('status')} reason={(it.get('reason_id') or it.get('reason'))}")
            break
print("\nDONE")
