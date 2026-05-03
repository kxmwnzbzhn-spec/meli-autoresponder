#!/usr/bin/env python3
"""Setea floor_price hardcoded para items específicos en stock_config_raymundo.json
y refuerza la lógica del war_universal para respetar el floor por item."""
import os, json

# Items a actualizar con floor_price absoluto
TARGETS = {
    "MLM2891189883": 449,   # Go 4 Azul - usuario explicito $449 minimo
    "MLM5246052014": 449,   # Go 4 Rojo - usuario explicito $449 minimo
}

CFG_PATH = "stock_config_raymundo.json"

with open(CFG_PATH) as f:
    cfg = json.load(f)

for iid, floor in TARGETS.items():
    if iid not in cfg:
        cfg[iid] = {}
    cfg[iid]["floor_price"] = floor
    cfg[iid]["floor_locked_by_user"] = True
    print(f"  ✅ {iid} → floor_price={floor} (locked)")

with open(CFG_PATH, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print(f"\nstock_config_raymundo.json actualizado.")
