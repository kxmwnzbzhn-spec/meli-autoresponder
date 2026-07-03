import os, requests
SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
H={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json","Prefer":"return=minimal"}
requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=H,
  json={"account":"ASVA","item_id":"MLM5634575706","default_qty":1,"product_name":"Charge 6 IP67 Caja Abierta","reason":"Autostock caja abierta $599 2026-07-03"},timeout=8)
requests.post(f"{SB}/rest/v1/meli_user_directives",headers=H,
  json={"account":"ASVA","scope":"item","scope_value":"MLM5634575706","directive_type":"caja_abierta_republish","raw_user_message":"pausa MLM5576391292 y republica como caja abierta $599 con disclaimer daños estéticos no afectan funcionamiento"},timeout=8)
requests.post(f"{SB}/rest/v1/meli_no_replenish_items",headers=H,
  json={"item_id":"MLM5576391292","reason":"Original de caja nueva pausado - reemplazado por MLM5634575706 caja abierta $599"},timeout=8)
