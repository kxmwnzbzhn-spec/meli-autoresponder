"""Audit live cross-cuenta: items por status, tokens vivos."""
import os, requests, json
API="https://api.mercadolibre.com"

ACCOUNTS=[
  (1668713481,"MELI_REFRESH_TOKEN_ASVA","Asva"),
  (2400722448,"MELI_REFRESH_TOKEN_BREN","Bren"),
  (3348766821,"MELI_REFRESH_TOKEN_CLARIBEL","Claribel"),
  (3355056011,"MELI_REFRESH_TOKEN_DILCIE","Dilcie"),
  (2681696373,"MELI_REFRESH_TOKEN_JUAN","Juan"),
  (3338633403,"MELI_REFRESH_TOKEN_RAYMUNDO","Raymundo"),
  (3294280577,"MELI_REFRESH_TOKEN_RMAYCHI","RMAYCHI"),
  (3367276814,"MELI_REFRESH_TOKEN_WILBERT","Wilbert"),
  (3417664339,"MELI_REFRESH_TOKEN_AH","Adrian"),
  (3364413125,"MELI_REFRESH_TOKEN_YC_NEW","Yiriam"),
  (3009687392,"MELI_REFRESH_TOKEN_ANGEL","Angel"),
  (3419500448,"MELI_REFRESH_TOKEN_MAYRELY","Mayrely"),
]

def refresh(sec):
    if sec not in os.environ: return None,None,"no_env"
    try:
        r=requests.post(f"{API}/oauth/token",data={
            "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
            "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ[sec]
        },timeout=15).json()
        if "access_token" in r: return r["access_token"], r.get("refresh_token"), "ok"
        return None,None,f"err:{r.get('error','unknown')}"
    except Exception as e: return None,None,f"exc:{e}"

print("=== Cuenta x Status x Conteo ===")
print(f"{'Cuenta':<10} {'token':<10} {'active':>7} {'paused':>7} {'u_review':>9} {'closed':>7} {'oos_paused':>11}")
print("-"*80)
rotated={}
for uid,sec,nick in ACCOUNTS:
    at,rt,status=refresh(sec)
    rotated[sec]=rt
    if not at:
        print(f"{nick:<10} {status:<10}")
        continue
    H={"Authorization":f"Bearer {at}"}
    counts={"active":0,"paused":0,"under_review":0,"closed":0}
    oos=0
    for st in ("active","paused","under_review","closed"):
        try:
            r=requests.get(f"{API}/users/{uid}/items/search?status={st}&limit=50",headers=H,timeout=10).json()
            counts[st]=r.get("paging",{}).get("total",0)
        except: pass
    # Quick scan first 50 paused for OOS detection
    try:
        r=requests.get(f"{API}/users/{uid}/items/search?status=paused&limit=50",headers=H,timeout=10).json()
        ids=r.get("results",[])
        if ids:
            mg=requests.get(f"{API}/items",headers=H,params={"ids":",".join(ids[:50]),"attributes":"id,sub_status,inventory_id"},timeout=15).json()
            for x in mg:
                if x.get("code")==200:
                    b=x["body"]
                    if "out_of_stock" in (b.get("sub_status") or []) and not b.get("inventory_id"):
                        oos+=1
    except: pass
    print(f"{nick:<10} {'ok':<10} {counts['active']:>7} {counts['paused']:>7} {counts['under_review']:>9} {counts['closed']:>7} {oos:>11}")

print("\nROTATED_TOKENS=", json.dumps(rotated))
