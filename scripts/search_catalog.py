import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
# Buscar generic speakers en catalogo
for q in ["Bocina generica bluetooth portatil ip67","bocina bluetooth impermeable","flip 7","altavoz portatil bluetooth"]:
    d=requests.get(f"https://api.mercadolibre.com/products/search?site_id=MLM&q={q}&limit=5",headers=H).json()
    print(f"=== {q} ===")
    for p in (d.get("results") or [])[:5]:
        print(f"  {p.get('id')} | {p.get('name')[:70]} | brand={p.get('attributes',[])}")
