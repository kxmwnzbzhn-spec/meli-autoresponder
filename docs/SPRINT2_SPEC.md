# Sprint 2 — M3 Pricing Engine

**Estado:** Diseño · **Owner:** Sr. Luis Vargas · **Fecha:** 2026-05-17

Objetivo: que cada war script consulte un motor de pricing dinámico que combina
**costo landed real (Sprint 1) + comisión MELI + reglas de margen + price-to-win**
para decidir floor, target y ceiling — en vez de floors hardcodeados por SKU.

---

## 1. Modelo de datos

### 1.1 `pricing_rules`
Reglas declarativas. Aplica en orden de especificidad: `sku` > `line` > `brand` > `*` (default).

| Columna | Tipo | Notas |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid NULL | Multi-tenant ready |
| scope | text NOT NULL CHECK IN ('sku','line','brand','global') | |
| scope_value | text | Valor según scope. NULL si scope='global'. |
| account_id | int REFERENCES accounts NULL | Override por cuenta MELI. NULL = todas. |
| listing_type | text CHECK IN ('gold_pro','gold_premium','silver','bronze','*') DEFAULT '*' | Premium/Clasica MELI |
| margin_floor_pct | numeric(5,2) NOT NULL | Margen mínimo absoluto antes de bloquear venta |
| margin_target_pct | numeric(5,2) NOT NULL | Margen ideal de partida |
| margin_max_pct | numeric(5,2) | Tope superior (evita over-pricing). NULL = sin tope. |
| respect_price_to_win | bool DEFAULT true | Si true, war script puede bajar al `price_to_win` si está sobre floor |
| price_to_win_aggressive_margin | numeric(5,2) | Si activo y price_to_win < target, war se mueve hasta min(target, price_to_win + this_margin) |
| comision_meli_override_pct | numeric(5,2) | Override de comisión MELI si conoces el real del SKU (algunos categorías difieren) |
| shipping_seller_pays_override_mxn | numeric(10,2) | Si conoces el envío fijo del SKU; sino se calcula |
| iva_pct | numeric(5,2) DEFAULT 16.00 | IVA México |
| isr_retencion_pct | numeric(5,2) DEFAULT 0 | 8% si aplicas régimen RIF/ISR retenido por MELI |
| notas | text | |
| archived | bool DEFAULT false | |
| created_by | text | |
| created_at | timestamptz DEFAULT now() | |
| updated_at | timestamptz DEFAULT now() | |

**Resolución de reglas** (función `resolve_pricing_rule(sku, account_id, listing_type)`):
1. Busca match exacto `scope='sku' AND scope_value=sku AND account_id=account AND listing_type=type`
2. Match parcial: `account_id` NULL o `listing_type='*'` (fallbacks)
3. Si nada en `sku`, sube a `line` (lee `products.line`)
4. Si nada en `line`, sube a `brand` (lee `products.brand`)
5. Si nada, usa `scope='global'`
6. Si ni global existe, error: `NO_PRICING_RULE`

### 1.2 `pricing_competitors_history`
Snapshot del `/items/{id}/price_to_win` para tracking longitudinal de competencia.

| Columna | Tipo | Notas |
|---|---|---|
| id | bigserial PK | |
| ts | timestamptz DEFAULT now() | |
| mlm_id | text NOT NULL REFERENCES listings(mlm_id) | |
| sku | text REFERENCES products(sku) | denormalizado |
| catalog_product_id | text | si aplica |
| our_price | numeric(10,2) | precio nuestro al momento del snapshot |
| price_to_win | numeric(10,2) | precio para ganar buy box |
| price_to_win_status | text | available / not_available / not_eligible |
| competitor_price | numeric(10,2) | precio actual del ganador |
| is_winning | bool | si nosotros somos el ganador |
| raw_response | jsonb | snapshot completo del endpoint |

Índices: `(mlm_id, ts DESC)`, `(sku, ts DESC)`.

### 1.3 `pricing_decisions`
Audit: cada vez que `compute_suggested_price` se llama, registra inputs y output.

| Columna | Tipo | Notas |
|---|---|---|
| id | bigserial PK | |
| ts | timestamptz DEFAULT now() | |
| sku | text | |
| mlm_id | text | |
| account_id | int | |
| listing_type | text | |
| rule_id | uuid | la regla que se aplicó |
| unit_cost_mxn | numeric(10,4) | costo landed al momento |
| comision_meli_pct | numeric(5,2) | |
| shipping_seller_mxn | numeric(10,2) | |
| floor_mxn | numeric(10,2) | |
| target_mxn | numeric(10,2) | |
| ceiling_mxn | numeric(10,2) | |
| margin_at_floor_pct | numeric(5,2) | |
| margin_at_target_pct | numeric(5,2) | |
| price_to_win_at_decision | numeric(10,2) | |
| recommended_action | text | hold / lower_to_ptw / raise_to_target / block_sale |
| current_price | numeric(10,2) | precio actual del listing al momento |

---

## 2. Funciones

### 2.1 `compute_suggested_price(p_sku, p_account_id, p_listing_type, p_mlm_id) → jsonb`

Algoritmo:

```
1. cost = SELECT costo_promedio_mxn FROM v_cost_current
            WHERE sku=p_sku AND warehouse='bodega_main'
   IF cost IS NULL → return {error: 'NO_COST_DATA'}

2. rule = resolve_pricing_rule(p_sku, p_account_id, p_listing_type)

3. comm  = rule.comision_meli_override_pct OR default_for(listing_type)
   ship  = rule.shipping_seller_pays_override_mxn OR estimate_shipping(p_sku)
   iva   = rule.iva_pct
   isr   = rule.isr_retencion_pct

4. Para floor / target / ceiling:
   precio = cost / (1 - margin/100 - comm/100 - iva/(100+iva) - isr/100) + ship

   (la fórmula resuelve: precio - (precio * comm) - (precio * isr) - shipping
    - precio * iva/(1+iva) = cost + cost * margin)

5. Si p_mlm_id provided y rule.respect_price_to_win:
   ptw = SELECT price_to_win
           FROM pricing_competitors_history
          WHERE mlm_id=p_mlm_id
       ORDER BY ts DESC LIMIT 1
   IF ptw IS NOT NULL AND ptw >= floor:
      target = min(target, ptw + rule.price_to_win_aggressive_margin)

6. Registrar fila en pricing_decisions

7. Return {
     floor, target, ceiling,
     unit_cost_mxn, comision_pct, shipping_mxn,
     margin_at_floor_pct, margin_at_target_pct,
     rule_id, action
   }
```

### 2.2 `record_price_to_win(p_mlm_id, p_data jsonb) → void`
Llamada desde un job de polling que consulta `/items/{mlm_id}/price_to_win?version=v2`
y persiste el snapshot.

### 2.3 `current_pricing_floor(p_sku, p_account_id, p_listing_type) → numeric`
Helper conveniente para war scripts. Devuelve solo el floor.

---

## 3. Integración con war scripts existentes

Patch para `scripts/war_wilbert.py` y similares:

**Antes (floor hardcodeado):**
```python
FLOORS = {
    'MLM2910806817': 950,
    'MLM3011234567': 1820,
    # ...
}
floor = FLOORS.get(mlm_id)
```

**Después (floor dinámico desde DB):**
```python
cur.execute(
    "SELECT current_pricing_floor(%s, %s, %s)",
    (sku, account_id, listing_type)
)
floor = cur.fetchone()[0]
if floor is None:
    print(f"⚠ Sin pricing_rule para {sku}, skip")
    continue
```

Cada war script: 5-10 líneas modificadas. Tabla `pricing_rules` se vuelve el lugar único de mantenimiento.

---

## 4. Comisiones MELI default

| listing_type | comisión |
|---|---|
| `gold_premium` (Premium con MSI) | 16.5% |
| `gold_pro` (Clásica) | 13.5% |
| `silver` | 11.0% |
| `bronze` (gratis) | 0% (pero sin posicionamiento) |

Override por SKU vía `pricing_rules.comision_meli_override_pct` si el real difiere
(p.ej. categorías nicho con tarifas especiales).

Shipping: si `shipping=me2 free_shipping` y precio > $399, MELI cobra al seller
~$50-90 según peso. Aproximación inicial: `estimate_shipping(sku)` lee
`products.peso_kg_unit` (si Sprint 1 lo tiene) o usa default de $70.

---

## 5. Jobs / workflows nuevos

| Workflow | Cron | Qué hace |
|---|---|---|
| `inv_price_to_win_poll` | cada 30 min | Recorre todos los listings activos, llama `/items/{id}/price_to_win`, persiste en `pricing_competitors_history` |
| `inv_pricing_recompute` | cada hora | Para cada listing, calcula `compute_suggested_price`. Si `recommended_action != 'hold'`, alerta Telegram o aplica via war script |
| `inv_pricing_seed_rules` | dispatch manual | Bulk insert de pricing_rules desde CSV |

---

## 6. CSV template para pricing rules

`inventory_platform/data/pricing_rules_seed.csv`:

```csv
scope,scope_value,account_id,listing_type,margin_floor_pct,margin_target_pct,margin_max_pct,respect_price_to_win,price_to_win_aggressive_margin,comision_meli_override_pct,notas
global,,,*,8.00,22.00,45.00,true,3.00,,Regla default global
brand,JBL,,*,10.00,18.00,35.00,true,2.00,,Bocinas JBL muy peleadas, margen 10-18%
line,Bocinas,,*,10.00,20.00,40.00,true,2.50,,Categoria audio
brand,Dior,,*,15.00,30.00,55.00,true,5.00,,Perfume premium, margen amplio
brand,Lattafa,,*,20.00,40.00,70.00,true,8.00,,Perfume nicho, margen alto
sku,JBL-GO4-NEGRO,,*,12.00,18.00,30.00,true,1.50,,SKU estrella, agresivo
sku,JBL-GO4-NEGRO,,gold_premium,12.00,16.00,28.00,true,1.00,16.50,Premium Wilbert
```

---

## 7. Checklist Sprint 2

- [ ] DDL en `inventory_platform/schema/04_pricing.sql`
- [ ] Funciones en `inventory_platform/schema/05_pricing_functions.sql`
- [ ] Script `scripts/poll_price_to_win.py` + workflow
- [ ] Script `scripts/recompute_pricing.py` + workflow
- [ ] Script `scripts/seed_pricing_rules.py` + workflow
- [ ] Patch a `war_*.py` scripts (al menos `war_wilbert.py` y `war_yiriam_perfumes.py` primero)
- [ ] CSV inicial `pricing_rules_seed.csv` con reglas reales
- [ ] Tests SQL: validar `compute_suggested_price` con casos extremos (costo=0, sin price_to_win, sin rule)
- [ ] Documentación en `docs/PRICING.md`

---

## 8. Riesgos

| Riesgo | Mitigación |
|---|---|
| Reglas mal calibradas → vendemos bajo costo | Función bloquea sale si `target_mxn < floor_mxn` o si `margin < 0%`; alerta Telegram |
| Price-to-win API tiene rate limits | Polling cada 30 min × 9 cuentas × ~500 listings = 4500/30min < límite MELI (10k/hora) |
| Competencia detecta nuestra estrategia y nos "trolea" | War scripts no bajan automáticamente bajo floor, ven do absoluto |
| Costos landed obsoletos (PO antigua + flete actual cambió) | Cron mensual recomputa `v_cost_current` y alerta si delta > 15% |

---

## 9. Sprint 3 lookahead

Una vez M3 estable, Sprint 3 introduce:
- `warehouses` formales (bodega_electronica, bodega_perfume, bodega_ropa, devolucion, transito_proveedor, transito_meli_full)
- `stock_transfers` entre bodegas
- `damages` (mermas, productos dañados)
- Multi-warehouse routing en `process_event.py` (qué bodega descontamos por listing)
