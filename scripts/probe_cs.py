import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
for q in ["Dior Sauvage Elixir","Creed Aventus"]:
    print(f"\n##### {q} #####")
    r=requests.get(f"{API}/products/search",params={"site_id":"MLM","status":"active","q":q},headers=H,timeout=20)
    print("products/search http:",r.status_code)
    try:
        j=r.json(); res=j.get("results") or []
        print("keys:", list(j.keys()), "| n_results:", len(res))
        if res:
            print("first result:", json.dumps(res[0],ensure_ascii=False)[:400])
            cp = res[0]["id"] if isinstance(res[0],dict) else res[0]
            pr=requests.get(f"{API}/products/{cp}",headers=H,timeout=20).json()
            bb=pr.get("buy_box_winner") or {}
            print(f"product {cp}: name={pr.get('name')} bb_price={bb.get('price')}")
            it=requests.get(f"{API}/products/{cp}/items",headers=H,timeout=20).json()
            its=it.get("results") or []
            print("items keys sample:", json.dumps(its[0],ensure_ascii=False)[:300] if its else "none", "| n_offers:", len(its))
    except Exception as e:
        print("ERR", e, r.text[:200])
print("DONE")
