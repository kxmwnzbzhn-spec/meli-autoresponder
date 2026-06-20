import os, requests, json
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ADRIAN"]
AT=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":RT},timeout=20).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

queries=[
 "aromatizante artesanal","fragancia hogar","home fragrance",
 "body splash","body mist","colonia artesanal","colonia unisex",
 "loción corporal aromática","spray corporal perfumado","mist corporal",
 "agua perfume aromaterapia","perfume artesanal mexicano",
 "feromonas","perfume nicho mexicano","desodorante perfume",
 "atomizador perfume","piedra aromática","incienso liquido",
 "atomizador feromonas","spray aromático","loción artesanal",
 "splash corporal","perfumería de autor","perfume sin alcohol",
 "agua de tocador","eau fraiche","agua perfumada","aceite perfumado",
 "óleo perfume","oleo aromatico","perfume sólido","perfume en barra"
]
seen=set()
for q in queries:
    r=requests.get(f"{API}/sites/MLM/domain_discovery/search",params={"q":q,"limit":3},headers=H,timeout=15)
    try:
        for d in r.json():
            key=(d.get("domain_id"),d.get("category_id"))
            if key in seen: continue
            seen.add(key)
            print(f"q='{q[:30]}' → {d.get('domain_id')} | {d.get('domain_name')} | cat={d.get('category_id')} ({d.get('category_name')})")
    except: pass
