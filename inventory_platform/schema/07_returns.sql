-- =====================================================================
-- Devoluciones MELI automáticas — tabla returns + audit
-- =====================================================================
-- Cuando MELI fira webhook 'claims' y la claim resultó en devolución
-- aceptada (resolution.reason='product_returned' o similar), el handler
-- en process_event.py procesa: +qty a stock.devolucion + cost_layer al
-- 30% del landed actual + audit en returns.
--
-- Idempotencia: claim_id UNIQUE → mismo claim no duplica inventario.
-- =====================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS returns (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               uuid,
    claim_id                text NOT NULL UNIQUE,           -- idempotencia
    order_id                text,
    account_id              int REFERENCES accounts(id),
    mlm_id                  text,
    variation_id            bigint,
    sku                     text REFERENCES products(sku),
    qty                     int NOT NULL CHECK (qty > 0),
    original_warehouse      text,                            -- de donde salió en la venta original
    target_warehouse        text NOT NULL DEFAULT 'devolucion',
    resolution_status       text,                            -- claim.status
    resolution_reason       text,                            -- claim.resolution.reason
    refund_amount_mxn       numeric(12,2),
    decided_at              timestamptz,
    cost_layer_id           uuid,                            -- la capa creada para esta devolución
    stock_movement_id       bigint REFERENCES stock_movements(id),
    raw_claim               jsonb,
    raw_order               jsonb,
    processed_at            timestamptz NOT NULL DEFAULT now(),
    notes                   text
);

CREATE INDEX IF NOT EXISTS idx_returns_claim       ON returns(claim_id);
CREATE INDEX IF NOT EXISTS idx_returns_order       ON returns(order_id);
CREATE INDEX IF NOT EXISTS idx_returns_sku         ON returns(sku);
CREATE INDEX IF NOT EXISTS idx_returns_processed   ON returns(processed_at);

COMMENT ON TABLE returns IS
'Devoluciones MELI procesadas (claim_id único). Cada fila representa una venta devuelta físicamente, que sumó qty al stock.devolucion y creó cost_layer al 30% del landed original.';

-- ---------------------------------------------------------------------
-- Función helper: procesa una devolución (transaccional)
-- ---------------------------------------------------------------------
-- Input: claim_id, order_id, account_id, mlm_id, variation_id, sku, qty,
--        refund_amount, resolution_reason, raw_claim_jsonb, raw_order_jsonb
-- Output: jsonb con resultado
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION process_return(
    p_claim_id          text,
    p_order_id          text,
    p_account_id        int,
    p_mlm_id            text,
    p_variation_id      bigint,
    p_sku               text,
    p_qty               int,
    p_refund_amount     numeric DEFAULT NULL,
    p_resolution_status text DEFAULT NULL,
    p_resolution_reason text DEFAULT NULL,
    p_raw_claim         jsonb DEFAULT NULL,
    p_raw_order         jsonb DEFAULT NULL,
    p_devol_cost_factor numeric DEFAULT 0.30
) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    v_existing_id   uuid;
    v_movement_id   bigint;
    v_layer_id      uuid;
    v_current_landed numeric;
    v_devol_cost    numeric;
    v_original_warehouse text;
BEGIN
    -- 1. Idempotencia
    SELECT id INTO v_existing_id FROM returns WHERE claim_id = p_claim_id;
    IF v_existing_id IS NOT NULL THEN
        RETURN jsonb_build_object('status','duplicate','return_id',v_existing_id,'claim_id',p_claim_id);
    END IF;

    -- 2. Sanity: producto existe
    IF NOT EXISTS (SELECT 1 FROM products WHERE sku = p_sku) THEN
        RAISE EXCEPTION 'SKU_NOT_FOUND %', p_sku;
    END IF;

    -- 3. Estimar costo del item devuelto = 30% del landed promedio en bodega_main
    SELECT costo_promedio_mxn INTO v_current_landed
      FROM v_cost_current
     WHERE sku = p_sku AND warehouse = 'bodega_main';
    v_devol_cost := COALESCE(v_current_landed, 0) * p_devol_cost_factor;

    -- 4. Determinar warehouse original (informativo)
    IF p_variation_id IS NOT NULL THEN
        SELECT warehouse INTO v_original_warehouse
          FROM resolve_sale_target(p_mlm_id, p_variation_id);
    ELSE
        SELECT warehouse INTO v_original_warehouse
          FROM resolve_sale_target(p_mlm_id, NULL);
    END IF;
    v_original_warehouse := COALESCE(v_original_warehouse, 'bodega_main');

    -- 5. Incrementar stock en devolucion vía apply_stock_delta
    SELECT apply_stock_delta(
        p_sku, 'devolucion', p_qty, 'return_meli',
        NULL, p_order_id, p_mlm_id, p_account_id,
        format('Devolución MELI claim=%s reason=%s', p_claim_id, COALESCE(p_resolution_reason,'?')),
        'meli_webhook_claim'
    ) INTO v_movement_id;

    -- 6. Crear cost_layer en devolucion para esta unidad devuelta
    INSERT INTO cost_layers(
        sku, warehouse, source_type, source_id,
        qty_recibida, qty_restante,
        costo_unitario_base_mxn, fletes_prorrateados_mxn, otros_prorrateados_mxn
    ) VALUES (
        p_sku, 'devolucion', 'return_meli', NULL,
        p_qty, p_qty,
        v_devol_cost, 0, 0
    ) RETURNING id INTO v_layer_id;

    -- 7. Insertar fila de audit en returns
    INSERT INTO returns(
        claim_id, order_id, account_id, mlm_id, variation_id, sku, qty,
        original_warehouse, target_warehouse,
        resolution_status, resolution_reason, refund_amount_mxn,
        cost_layer_id, stock_movement_id, raw_claim, raw_order
    ) VALUES (
        p_claim_id, p_order_id, p_account_id, p_mlm_id, p_variation_id, p_sku, p_qty,
        v_original_warehouse, 'devolucion',
        p_resolution_status, p_resolution_reason, p_refund_amount,
        v_layer_id, v_movement_id, p_raw_claim, p_raw_order
    );

    RETURN jsonb_build_object(
        'status', 'ok',
        'claim_id', p_claim_id,
        'sku', p_sku,
        'qty', p_qty,
        'target_warehouse', 'devolucion',
        'cost_layer_id', v_layer_id,
        'devol_cost_mxn', v_devol_cost,
        'stock_movement_id', v_movement_id
    );
END;
$$;

COMMENT ON FUNCTION process_return IS
'Transaccional: marca devolución MELI como procesada. Suma stock devolucion + cost_layer al 30% del landed actual + audit. Idempotente por claim_id.';

INSERT INTO schema_migrations(id, description)
VALUES ('sprint1_returns_v1', 'returns table + process_return() para devoluciones MELI automáticas')
ON CONFLICT (id) DO NOTHING;

COMMIT;
