"""Dump items reales del shipment 47119719346 (Wilbert)."""
import os, requests, json
APP_ID="5211907102822632"; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
at=requests.post("https://api.mercadolibre.com/oauth/token",data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {at}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json(); uid=me["id"]
# Busca la orden por shipping.id
qr=requests.get("https://api.mercadolibre.com/orders/search",headers=H,
    params={"seller":uid,"shipping.id":"47119719346"}).json()
for o in qr.get("results",[]):
    print(f"Order {o.get('id')}")
    for it in o.get("order_items",[]):
        io_obj=it.get("item",{})
        print(f"  item_id={io_obj.get('id')}")
        print(f"  title={io_obj.get('title')!r}")
        print(f"  variation_id={io_obj.get('variation_id')}")
        print(f"  variation_attributes={json.dumps(io_obj.get('variation_attributes'),ensure_ascii=False)}")
        print(f"  qty={it.get('quantity')}")
        # detalle del item
        iid=io_obj.get('id')
        if iid:
            d=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,params={"attributes":"title,condition,attributes"}).json()
            print(f"  item.title_full={d.get('title')!r}  condition={d.get('condition')}")
            for a in (d.get('attributes') or []):
                if a.get('id') in ('MODEL','BRAND','LINE','COLOR'):
                    print(f"     {a.get('id')}={a.get('value_name')!r}")
