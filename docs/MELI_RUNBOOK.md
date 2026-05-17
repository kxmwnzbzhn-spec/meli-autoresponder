# MELI Runbook — Elite Market

Operational reference for working with Mercado Libre across the 9 Elite Market seller accounts.
**Owner:** Sr. Luis Vargas · **Last updated:** 2026-05-17

---

## Acceso a cuentas MELI — cómo verificar

Las 9 cuentas MELI tienen refresh_tokens guardados como GH Actions secrets:

| Secret name | Cuenta | MELI user_id |
|---|---|---|
| `MELI_APP_ID` | App ID compartida | `5211907102822632` |
| `MELI_APP_SECRET` | App secret compartido | — |
| `MELI_REFRESH_TOKEN_WILBERT` | Wilbert | 3367276814 |
| `MELI_REFRESH_TOKEN_YC_NEW` | Yiriam (YC_NEW) | 3364413125 |
| `MELI_REFRESH_TOKEN_JUAN` | Juan | 2681696373 |
| `MELI_REFRESH_TOKEN_RAYMUNDO` | Raymundo | 3338633403 |
| `MELI_REFRESH_TOKEN_CLARIBEL` | Claribel | 3348766821 |
| `MELI_REFRESH_TOKEN_ASVA` | Asva | 1668713481 |
| `MELI_REFRESH_TOKEN_MILDRED` | Mildred | (pendiente captura) |
| `MELI_REFRESH_TOKEN_DILCIE` | Dilcie | 3355056011 |
| `MELI_REFRESH_TOKEN_BREN` | Bren | 2400722448 |

**Vigencias:**

- `refresh_token` → 6 meses
- `access_token` → 6 horas (refrescable on-demand)

Si un refresh_token está cerca de expirar, el flujo OAuth completo está en `scripts/exchange_code_<account>.py` — corre el script, agarra el código del callback, y se actualiza el secret.

---

## Cómo verificar cualquier dato MELI desde el chat

Patrón estándar (un solo dispatch):

1. Escribir script Python en `scripts/check_<tema>.py` que use el refresh_token correspondiente vía `os.environ[...]`
2. Subir con `gh_upsert_file`
3. Crear workflow `.github/workflows/check_<tema>.yml` con el secret en `env`
4. `dispatch` + `wait_run` + leer logs
5. **NUNCA hardcodear tokens** — siempre via env vars del workflow

### Template one-shot

```python
# scripts/check.py
import os, requests
RT = os.environ["MELI_REFRESH_TOKEN_WILBERT"]   # cambia por la cuenta que necesites
T = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": RT
}).json()["access_token"]
H = {"Authorization": f"Bearer {T}"}

# Tu query a MELI aquí
r = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(r)
```

Workflow correspondiente:

```yaml
name: check
on: { workflow_dispatch: {} }
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install requests
      - env:
          MELI_APP_ID: ${{ secrets.MELI_APP_ID }}
          MELI_APP_SECRET: ${{ secrets.MELI_APP_SECRET }}
          MELI_REFRESH_TOKEN_WILBERT: ${{ secrets.MELI_REFRESH_TOKEN_WILBERT }}
        run: python scripts/check.py
```

Templates a copiar: cualquier `pause_*.py` o `clone_*.py` ya existente en `scripts/` sigue este patrón exacto.

---

## Endpoints MELI más usados

| Endpoint | Uso |
|---|---|
| `POST /oauth/token` | refresh access token |
| `GET /users/me` | verifica auth + user_id |
| `GET /users/{uid}/items/search?status=active` | lista items del seller |
| `GET /items/{id}` | detalle item |
| `GET /items/{id}/price_to_win?version=v2` | status catálogo + price to win (para war pricing) |
| `GET /orders/search?seller={uid}&order.status=paid` | órdenes pagadas |
| `GET /orders/{id}` | detalle orden (procesamiento webhook) |
| `GET/PUT/POST /items/{id}/description` | descripción del item |
| `POST /pictures/items/upload` | upload imagen (multipart, `files={"file":(...)}`) |
| `GET /products/{cpid}` | catálogo MELI — producto |
| `GET /products/{cpid}/items` | listings competidores en el catálogo |
| `GET /products/search?status=active&site_id=MLM&q=...` | buscar catálogos |

---

## Quirks MELI ya descubiertos — no los re-descubras

**Pricing y catálogo**

- `catalog_listing=true` **rechaza** `original_price` → `field_not_updatable`. Si necesitas tachar precio, no puedes hacerlo en catalog. Workaround: usar listing clásico.
- Publicar en catálogo necesita `title` + `category_id` en body, **no solo el CPID**.
- `condition=refurbished` **no permitido** en `MLM59800` (Bocinas). Usa `new` o `used`.

**Estructura del item**

- `subtitle` **NO es un campo válido** en `POST /items`. Si lo mandas, ignored o error según versión.
- `description` con `plain_text` **rechaza emojis** → usa ASCII puro, o usa formato HTML en el campo `text`.
- Items recién creados: la primera vez **`PUT /description`** (no POST). POST es para actualizar después.
- Items con `variations` en estado `closed` no permiten modificar variations → usa `/items/{id}/relist` con `[{id, price, quantity}]` (**NO** `available_quantity`).
- Items en `under_review` + `forbidden` no se modifican; clonarlos puede chocar con `seller.optin.fake` (cuenta marcada).
- **Title máximo 60 chars** en MLM59800.

**Pre-modificación obligatorio**

- ANTES de modificar un item, valida que `seller_id` del item match con el `user_id` del access_token. Si no match → vas a tocar un item ajeno o el endpoint falla con `forbidden`.

---

## Color del producto — REGLA CRÍTICA

**Fuente de verdad:**

1. Primario: `item.variation_attributes` con `id="COLOR"` → `value_name`
2. Fallback: `GET /items/{id}/variations/{vid}` → `attribute_combinations`

**NUNCA leas el color del título.** Color equivocado = reclamo + sanción al seller.

```python
def get_color(item):
    for attr in item.get("variation_attributes", []):
        if attr.get("id") == "COLOR":
            return attr.get("value_name")
    # Fallback: leer del primer variation_combinations
    for v in item.get("variations", []):
        for ac in v.get("attribute_combinations", []):
            if ac.get("id") == "COLOR":
                return ac.get("value_name")
    return None  # nunca derives del título
```

---

## Productos usados / reacondicionados — INDICADOR OBLIGATORIO

Si `condition='used'` (o `'refurbished'`, o `'generic_mirror'` para espejo 1:1):

- En listings activos: **banda visible** "PRODUCTO USADO" / "REACONDICIONADO" / "CALIDAD ESPEJO 1:1"
- En descripciones: prefijo "USADO — " en title (cuando el espacio lo permita)
- En reportes/dashboards: columna `Cond` siempre visible, no la escondas en filtros default
- En `process_event.py` y futuros bots: chequea `condition` antes de auto-publicar → bloquea promoción a destacado si no es `new`

El campo `products.condition` en la DB acepta exactamente: `'new'`, `'used'`, `'refurbished'`, `'generic_mirror'` (ver `01_init.sql`).

---

## Seguridad operacional

| Regla | Razón |
|---|---|
| Nunca hardcodear refresh_tokens en repo, ni siquiera en comentarios | Repos privados se pueden filtrar; refresh_tokens duran 6 meses |
| Cualquier verificación = workflow + secret, no script local con token pegado | Audit trail vía GH Actions logs |
| Si una cuenta se penaliza, **NO** intentes auto-modificar items hasta entender por qué | Sanciones se acumulan; mejor diagnóstico humano primero |
| Rotación: al detectar `invalid_grant` en refresh, alertar Telegram + reauth manual | Refresh fallido = cuenta queda en read-only |
| Nunca uses un token de cuenta A para mutar items de cuenta B | MELI bloquea por `forbidden` pero también marca patrón sospechoso |

---

## Quirks de procesamiento de órdenes

- Órdenes `cancelled` / `invalid` → skip (ya manejado en `process_event.py`)
- Órdenes `paid` → procesar normalmente
- Órdenes con `pack_id` (combo) → fetch `/packs/{pack_id}` para items reales
- Órdenes FULL (`logistic_type=fulfillment`) → stock se descontó en MELI cuando enviamos al CD; el evento `orders_v2` igual llega pero el decremento físico ya pasó en `transito → meli_full` (Sprint 3 modelará esto)
- Devoluciones (`claims`) → topic separado, ver Sprint 4 M6

---

## Referencias internas

- Schema base: [`inventory_platform/schema/01_init.sql`](../inventory_platform/schema/01_init.sql)
- Procurement + Cost layers: [`inventory_platform/schema/02_procurement_cost_layers.sql`](../inventory_platform/schema/02_procurement_cost_layers.sql)
- Funciones COGS / PO: [`inventory_platform/schema/03_procurement_cost_functions.sql`](../inventory_platform/schema/03_procurement_cost_functions.sql)
- Procesamiento de eventos: [`inventory_platform/scripts/process_event.py`](../inventory_platform/scripts/process_event.py)
- War pricing scripts: `scripts/war_*.py`, `scripts/yir_replenish.py`, `scripts/wilbert_replenish.py`
- Answer bot: `scripts/answer_all_accounts.py`
- OAuth re-exchange: `scripts/exchange_code_<account>.py`
