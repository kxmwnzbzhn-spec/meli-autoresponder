import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Stock REAL (lo maneja el bot por detras)
STOCK_REAL={
    "Rosa":      {"id":"MLM2886523677","max":200},
    "Aqua":      {"id":"MLM5235934108","max":200},
    "Azul":      {"id":"MLM2886523697","max":200},
    "Negro":     {"id":"MLM5235934132","max":15},
    "Rojo":      {"id":"MLM5235946486","max":200},
    "Camuflaje": {"id":"MLM5235934150","max":200},
}

# 1) Ajustar available_quantity a 1 en MELI (escasez visible)
print("=== PONER available_quantity=1 VISIBLE ===")
for color,info in STOCK_REAL.items():
    iid=info["id"]
    rp=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"available_quantity":1},timeout=20)
    print(f"  {color} {iid}: {rp.status_code}")
    if rp.status_code not in (200,201):
        print(f"    err: {rp.text[:300]}")
    time.sleep(1)

# 2) Actualizar stock_config_asva.json con real vs visible
try:
    cfg=json.load(open("stock_config_asva.json")) if os.path.exists("stock_config_asva.json") else {}
except: cfg={}

for color,info in STOCK_REAL.items():
    iid=info["id"]
    cfg[iid]={
        "color":color,
        "line":"Go4-Generica",
        "stock":info["max"],          # real
        "max_stock":info["max"],      # target replenish
        "visible_qty":1,               # el bot repone a 1 cuando baje
        "hidden_stock":True,           # flag: mantener escasez
        "active":True,
    }
json.dump(cfg,open("stock_config_asva.json","w"),indent=2,ensure_ascii=False)
print(f"\nstock_config_asva.json actualizado: 6 items Go4-Generica")
print(f"Stock real total: {sum(x['max'] for x in STOCK_REAL.values())} unidades")
print(f"Stock visible en MELI: 1 por publicacion (escasez)")

# 3) Actualizar bot autoresponder logic si hace falta — verify que reconoce hidden_stock
print("\n=== VERIFY LOGICA BOT ===")
# Por ahora solo imprimir estado
for color,info in STOCK_REAL.items():
    iid=info["id"]
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,available_quantity,status",headers=H).json()
    print(f"  {color} {iid}: available={d.get('available_quantity')} status={d.get('status')}")
