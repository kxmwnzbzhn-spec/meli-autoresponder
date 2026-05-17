-- =====================================================================
-- Sprint 1 — Funciones de negocio (v2, alineado con apply_stock_delta real)
-- =====================================================================
-- Target file: inventory_platform/schema/03_procurement_cost_functions.sql
--
-- Real apply_stock_delta (de 01_init.sql) tiene 10 parámetros:
--   apply_stock_delta(p_sku TEXT, p_warehouse TEXT, p_delta INT, p_type TEXT,
--                     p_event_id BIGINT DEFAULT NULL,
--                     p_order_id TEXT DEFAULT NULL,
--                     p_mlm_id TEXT DEFAULT NULL,
--                     p_account_id INT DEFAULT NULL,
--                     p_reason TEXT DEFAULT NULL,
--                     p_author TEXT DEFAULT 'system')
--   RETURNS BIGINT (id del stock_movement creado)
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. helpers
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION cost_method_for(p_sku text)
RETURNS cost_method_enum
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(
        (SELECT method FROM cost_methods WHERE sku = p_sku),
        ((SELECT value #>> '{}' FROM app_config WHERE key = 'cost_method_default'))::cost_method_enum,
        'weighted_avg'::cost_method_enum
    );
$$;

CREATE OR REPLACE FUNCTION po_audit_append(p_po_id uuid, p_event jsonb)
RETURNS void LANGUAGE sql AS $$
    UPDATE purchase_orders
       SET audit = audit || jsonb_build_array(
           p_event || jsonb_build_object('ts', now())
       )
     WHERE id = p_po_id;
$$;

-- ---------------------------------------------------------------------
-- 2. compute_landed_cost — prorrateo flete + otros
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION compute_landed_cost(p_po_id uuid)
RETURNS TABLE(
    po_item_id        uuid,
    sku               text,
    qty_ordered       int,
    base_unit_mxn     numeric,
    flete_unit_mxn    numeric,
    otros_unit_mxn    numeric,
    landed_unit_mxn   numeric
)
LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_po          purchase_orders%ROWTYPE;
    v_basis       text;
    v_total_basis numeric;
    v_total_flete numeric;
    v_total_otros numeric;
BEGIN
    SELECT * INTO v_po FROM purchase_orders WHERE id = p_po_id;
    IF v_po.id IS NULL THEN RAISE EXCEPTION 'PO_NOT_FOUND %', p_po_id; END IF;

    v_basis       := v_po.prorrateo_basis;
    v_total_flete := COALESCE(v_po.costo_flete_total_mxn, 0);
    v_total_otros := COALESCE(v_po.otros_costos_mxn, 0);

    SELECT CASE v_basis
        WHEN 'value'  THEN SUM(i.qty_ordered * i.unit_cost_origen * v_po.tipo_cambio_mxn)
        WHEN 'weight' THEN SUM(i.qty_ordered * COALESCE(i.peso_kg_unit, 0))
        WHEN 'volume' THEN SUM(i.qty_ordered * COALESCE(i.volumen_m3_unit, 0))
        WHEN 'qty'    THEN SUM(i.qty_ordered)::numeric
    END INTO v_total_basis
    FROM purchase_order_items i WHERE i.po_id = p_po_id;

    IF v_total_basis IS NULL OR v_total_basis = 0 THEN
        v_basis := 'qty';
        SELECT SUM(i.qty_ordered)::numeric INTO v_total_basis
          FROM purchase_order_items i WHERE i.po_id = p_po_id;
    END IF;

    RETURN QUERY
    SELECT
        i.id AS po_item_id, i.sku, i.qty_ordered,
        (i.unit_cost_origen * v_po.tipo_cambio_mxn)::numeric AS base_unit_mxn,
        CASE v_basis
            WHEN 'value'  THEN ((i.qty_ordered * i.unit_cost_origen * v_po.tipo_cambio_mxn) / v_total_basis * v_total_flete) / i.qty_ordered
            WHEN 'weight' THEN ((i.qty_ordered * COALESCE(i.peso_kg_unit,0))                / v_total_basis * v_total_flete) / i.qty_ordered
            WHEN 'volume' THEN ((i.qty_ordered * COALESCE(i.volumen_m3_unit,0))             / v_total_basis * v_total_flete) / i.qty_ordered
            WHEN 'qty'    THEN (i.qty_ordered::numeric                                       / v_total_basis * v_total_flete) / i.qty_ordered
        END AS flete_unit_mxn,
        CASE v_basis
            WHEN 'value'  THEN ((i.qty_ordered * i.unit_cost_origen * v_po.tipo_cambio_mxn) / v_total_basis * v_total_otros) / i.qty_ordered
            WHEN 'weight' THEN ((i.qty_ordered * COALESCE(i.peso_kg_unit,0))                / v_total_basis * v_total_otros) / i.qty_ordered
            WHEN 'volume' THEN ((i.qty_ordered * COALESCE(i.volumen_m3_unit,0))             / v_total_basis * v_total_otros) / i.qty_ordered
            WHEN 'qty'    THEN (i.qty_ordered::numeric                                       / v_total_basis * v_total_otros) / i.qty_ordered
        END AS otros_unit_mxn,
        ((i.unit_cost_origen * v_po.tipo_cambio_mxn) +
            CASE v_basis
              WHEN 'value'  THEN ((i.qty_ordered * i.unit_cost_origen * v_po.tipo_cambio_mxn) / v_total_basis * (v_total_flete + v_total_otros)) / i.qty_ordered
              WHEN 'weight' THEN ((i.qty_ordered * COALESCE(i.peso_kg_unit,0))                / v_total_basis * (v_total_flete + v_total_otros)) / i.qty_ordered
              WHEN 'volume' THEN ((i.qty_ordered * COALESCE(i.volumen_m3_unit,0))             / v_total_basis * (v_total_flete + v_total_otros)) / i.qty_ordered
              WHEN 'qty'    THEN (i.qty_ordered::numeric                                       / v_total_basis * (v_total_flete + v_total_otros)) / i.qty_ordered
            END
        ) AS landed_unit_mxn
    FROM purchase_order_items i
    WHERE i.po_id = p_po_id
    ORDER BY i.created_at;
END;
$$;

COMMENT ON FUNCTION compute_landed_cost(uuid) IS
'Prorratea flete+otros entre items según prorrateo_basis. No escribe a cost_layers.';

-- ---------------------------------------------------------------------
-- 3. receive_po — recepción transaccional (ALINEADO con apply_stock_delta real)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION receive_po(
    p_po_id            uuid,
    p_items            jsonb,
    p_received_by      text,
    p_idempotency_key  text DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
    v_po               purchase_orders%ROWTYPE;
    v_item             jsonb;
    v_po_item_id       uuid;
    v_qty_now          int;
    v_poi              purchase_order_items%ROWTYPE;
    v_cost             record;
    v_all_complete     boolean;
    v_total_items_recv int := 0;
    v_layer_id         uuid;
    v_mov_id           bigint;
    v_result           jsonb := '[]'::jsonb;
BEGIN
    -- 1. Idempotencia
    IF p_idempotency_key IS NOT NULL
       AND EXISTS (SELECT 1 FROM purchase_order_receipts
                    WHERE po_id = p_po_id AND idempotency_key = p_idempotency_key)
    THEN
        RETURN jsonb_build_object('status','duplicate','message','idempotency_key already processed');
    END IF;

    -- 2. Lock PO
    SELECT * INTO v_po FROM purchase_orders WHERE id = p_po_id FOR UPDATE;
    IF v_po.id IS NULL THEN RAISE EXCEPTION 'PO_NOT_FOUND %', p_po_id; END IF;
    IF v_po.estado NOT IN ('sent','in_transit','partially_received') THEN
        RAISE EXCEPTION 'PO_INVALID_STATE % (estado=%)', p_po_id, v_po.estado;
    END IF;

    -- 3. Procesar items
    FOR v_item IN SELECT jsonb_array_elements(p_items->'items') LOOP
        v_po_item_id := (v_item->>'po_item_id')::uuid;
        v_qty_now    := (v_item->>'qty_now')::int;

        IF v_qty_now IS NULL OR v_qty_now <= 0 THEN
            RAISE EXCEPTION 'INVALID_QTY for po_item_id=% qty_now=%', v_po_item_id, v_qty_now;
        END IF;

        SELECT * INTO v_poi
          FROM purchase_order_items
         WHERE id = v_po_item_id AND po_id = p_po_id FOR UPDATE;
        IF v_poi.id IS NULL THEN
            RAISE EXCEPTION 'PO_ITEM_NOT_FOUND % in po %', v_po_item_id, p_po_id;
        END IF;
        IF v_poi.qty_received + v_qty_now > v_poi.qty_ordered THEN
            RAISE EXCEPTION 'OVER_RECEIVE sku=% ordered=% already=% now=%',
                v_poi.sku, v_poi.qty_ordered, v_poi.qty_received, v_qty_now;
        END IF;

        -- 3.a Landed cost (snapshot completo de PO, mismo para todas las recepciones parciales)
        SELECT * INTO v_cost
          FROM compute_landed_cost(p_po_id)
         WHERE po_item_id = v_po_item_id;

        -- 3.b cost_layer
        INSERT INTO cost_layers(
            sku, warehouse, source_type, source_id,
            qty_recibida, qty_restante,
            costo_unitario_base_mxn, fletes_prorrateados_mxn, otros_prorrateados_mxn
        ) VALUES (
            v_poi.sku, v_po.warehouse_destino_code, 'purchase', p_po_id,
            v_qty_now, v_qty_now,
            v_cost.base_unit_mxn, v_cost.flete_unit_mxn, v_cost.otros_unit_mxn
        ) RETURNING id INTO v_layer_id;

        -- 3.c qty_received += qty_now
        UPDATE purchase_order_items
           SET qty_received = qty_received + v_qty_now
         WHERE id = v_po_item_id;

        -- 3.d Stock movement vía apply_stock_delta (FIRMA REAL, named params)
        SELECT apply_stock_delta(
            p_sku         => v_poi.sku,
            p_warehouse   => v_po.warehouse_destino_code,
            p_delta       => v_qty_now,
            p_type        => 'purchase',
            p_event_id    => NULL,
            p_order_id    => p_po_id::text,         -- usamos order_id slot para po_id
            p_mlm_id      => NULL,
            p_account_id  => NULL,
            p_reason      => format('PO %s receive', v_po.po_number),
            p_author      => COALESCE(p_received_by, 'system')
        ) INTO v_mov_id;

        v_total_items_recv := v_total_items_recv + 1;
        v_result := v_result || jsonb_build_object(
            'po_item_id',       v_po_item_id,
            'sku',              v_poi.sku,
            'qty_recv',         v_qty_now,
            'cost_layer_id',    v_layer_id,
            'stock_movement_id',v_mov_id,
            'landed_unit_mxn',  v_cost.landed_unit_mxn
        );
    END LOOP;

    -- 4. Nuevo estado
    SELECT bool_and(qty_received >= qty_ordered) INTO v_all_complete
      FROM purchase_order_items WHERE po_id = p_po_id;

    IF v_all_complete THEN
        UPDATE purchase_orders
           SET estado = 'received', fecha_received = CURRENT_DATE
         WHERE id = p_po_id;
        PERFORM po_audit_append(p_po_id, jsonb_build_object('action','received','by',p_received_by));
    ELSE
        UPDATE purchase_orders SET estado = 'partially_received' WHERE id = p_po_id;
        PERFORM po_audit_append(p_po_id, jsonb_build_object('action','partial_receive','by',p_received_by,'items',v_total_items_recv));
    END IF;

    -- 5. Idempotencia
    IF p_idempotency_key IS NOT NULL THEN
        INSERT INTO purchase_order_receipts(po_id, idempotency_key, payload, received_by)
        VALUES (p_po_id, p_idempotency_key, p_items, p_received_by);
    END IF;

    RETURN jsonb_build_object(
        'status','ok',
        'po_number', v_po.po_number,
        'items_received', v_total_items_recv,
        'all_complete', v_all_complete,
        'detail', v_result
    );
END;
$$;

COMMENT ON FUNCTION receive_po(uuid,jsonb,text,text) IS
'Recepción PO. Crea cost_layers, llama apply_stock_delta(type=purchase), actualiza estado. Idempotente.';

-- ---------------------------------------------------------------------
-- 4. consume_cost_fifo
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION consume_cost_fifo(
    p_sku            text,
    p_warehouse      text,
    p_qty            int,
    p_sale_order_id  text DEFAULT NULL,
    p_stock_movement_id bigint DEFAULT NULL
)
RETURNS numeric
LANGUAGE plpgsql AS $$
DECLARE
    v_remaining        int := p_qty;
    v_total_cogs       numeric := 0;
    v_layer            record;
    v_take             int;
    v_layer_cost       numeric;
    v_consumed_ids     uuid[] := ARRAY[]::uuid[];
    v_consumed_detail  jsonb  := '[]'::jsonb;
BEGIN
    IF p_qty IS NULL OR p_qty <= 0 THEN RAISE EXCEPTION 'INVALID_QTY %', p_qty; END IF;

    FOR v_layer IN
        SELECT id, qty_restante, costo_landed_mxn
          FROM cost_layers
         WHERE sku = p_sku
           AND warehouse = p_warehouse
           AND qty_restante > 0
           AND archived = false
         ORDER BY fecha ASC, id ASC
         FOR UPDATE
    LOOP
        EXIT WHEN v_remaining <= 0;
        v_take       := LEAST(v_layer.qty_restante, v_remaining);
        v_layer_cost := v_take * v_layer.costo_landed_mxn;

        UPDATE cost_layers SET qty_restante = qty_restante - v_take WHERE id = v_layer.id;

        v_total_cogs      := v_total_cogs + v_layer_cost;
        v_remaining       := v_remaining - v_take;
        v_consumed_ids    := array_append(v_consumed_ids, v_layer.id);
        v_consumed_detail := v_consumed_detail || jsonb_build_object(
            'layer_id', v_layer.id, 'qty', v_take, 'cost_unit', v_layer.costo_landed_mxn
        );
    END LOOP;

    IF v_remaining > 0 THEN
        RAISE EXCEPTION 'INSUFFICIENT_COSTED_STOCK sku=% wh=% requested=% short=%',
            p_sku, p_warehouse, p_qty, v_remaining;
    END IF;

    INSERT INTO cogs_movements(
        sku, warehouse, qty, cogs_total_mxn, method_used,
        sale_order_id, stock_movement_id, cost_layer_ids, consumed_per_layer
    ) VALUES (
        p_sku, p_warehouse, p_qty, v_total_cogs, 'fifo'::cost_method_enum,
        p_sale_order_id, p_stock_movement_id, v_consumed_ids, v_consumed_detail
    );

    RETURN v_total_cogs;
END;
$$;

-- ---------------------------------------------------------------------
-- 5. consume_cost_weighted_avg
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION consume_cost_weighted_avg(
    p_sku            text,
    p_warehouse      text,
    p_qty            int,
    p_sale_order_id  text DEFAULT NULL,
    p_stock_movement_id bigint DEFAULT NULL
)
RETURNS numeric
LANGUAGE plpgsql AS $$
DECLARE
    v_avg_cost        numeric;
    v_total_qty       int;
    v_total_cogs_inv  numeric;
    v_total_cogs      numeric;
    v_remaining       int := p_qty;
    v_layer           record;
    v_take            int;
    v_consumed_ids    uuid[] := ARRAY[]::uuid[];
    v_consumed_detail jsonb  := '[]'::jsonb;
BEGIN
    IF p_qty IS NULL OR p_qty <= 0 THEN RAISE EXCEPTION 'INVALID_QTY %', p_qty; END IF;

    SELECT SUM(qty_restante), SUM(qty_restante * costo_landed_mxn)
      INTO v_total_qty, v_total_cogs_inv
      FROM cost_layers
     WHERE sku = p_sku AND warehouse = p_warehouse
       AND qty_restante > 0 AND archived = false;

    IF v_total_qty IS NULL OR v_total_qty < p_qty THEN
        RAISE EXCEPTION 'INSUFFICIENT_COSTED_STOCK sku=% wh=% requested=% available=%',
            p_sku, p_warehouse, p_qty, COALESCE(v_total_qty,0);
    END IF;

    v_avg_cost   := v_total_cogs_inv / v_total_qty;
    v_total_cogs := p_qty * v_avg_cost;

    FOR v_layer IN
        SELECT id, qty_restante FROM cost_layers
         WHERE sku = p_sku AND warehouse = p_warehouse
           AND qty_restante > 0 AND archived = false
         ORDER BY fecha ASC, id ASC FOR UPDATE
    LOOP
        EXIT WHEN v_remaining <= 0;
        v_take := LEAST(v_layer.qty_restante, v_remaining);
        UPDATE cost_layers SET qty_restante = qty_restante - v_take WHERE id = v_layer.id;
        v_remaining       := v_remaining - v_take;
        v_consumed_ids    := array_append(v_consumed_ids, v_layer.id);
        v_consumed_detail := v_consumed_detail || jsonb_build_object(
            'layer_id', v_layer.id, 'qty', v_take, 'cost_unit', v_avg_cost
        );
    END LOOP;

    INSERT INTO cogs_movements(
        sku, warehouse, qty, cogs_total_mxn, method_used,
        sale_order_id, stock_movement_id, cost_layer_ids, consumed_per_layer
    ) VALUES (
        p_sku, p_warehouse, p_qty, v_total_cogs, 'weighted_avg'::cost_method_enum,
        p_sale_order_id, p_stock_movement_id, v_consumed_ids, v_consumed_detail
    );

    RETURN v_total_cogs;
END;
$$;

-- ---------------------------------------------------------------------
-- 6. consume_cost dispatcher
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION consume_cost(
    p_sku                text,
    p_warehouse          text,
    p_qty                int,
    p_sale_order_id      text DEFAULT NULL,
    p_stock_movement_id  bigint DEFAULT NULL
)
RETURNS numeric LANGUAGE plpgsql AS $$
DECLARE v_method cost_method_enum;
BEGIN
    v_method := cost_method_for(p_sku);
    IF v_method = 'fifo' THEN
        RETURN consume_cost_fifo(p_sku, p_warehouse, p_qty, p_sale_order_id, p_stock_movement_id);
    ELSE
        RETURN consume_cost_weighted_avg(p_sku, p_warehouse, p_qty, p_sale_order_id, p_stock_movement_id);
    END IF;
END;
$$;

COMMENT ON FUNCTION consume_cost(text,text,int,text,bigint) IS
'Dispatcher COGS. Llamar desde process_event.py después de apply_stock_delta exitoso en venta.';

-- ---------------------------------------------------------------------
-- 7. cancel_po
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION cancel_po(p_po_id uuid, p_reason text, p_by text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE v_po purchase_orders%ROWTYPE;
BEGIN
    SELECT * INTO v_po FROM purchase_orders WHERE id = p_po_id FOR UPDATE;
    IF v_po.id IS NULL THEN RAISE EXCEPTION 'PO_NOT_FOUND %', p_po_id; END IF;
    IF v_po.estado NOT IN ('draft','sent','in_transit') THEN
        RAISE EXCEPTION 'PO_CANNOT_CANCEL estado=% (use reverse_po para parcialmente recibidas)', v_po.estado;
    END IF;
    UPDATE purchase_orders SET estado = 'cancelled' WHERE id = p_po_id;
    PERFORM po_audit_append(p_po_id, jsonb_build_object('action','cancel','by',p_by,'reason',p_reason));
    RETURN jsonb_build_object('status','ok','po_number',v_po.po_number,'estado','cancelled');
END;
$$;

-- ---------------------------------------------------------------------
-- 8. update_po_status
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_po_status(
    p_po_id uuid, p_new_status po_status_enum, p_by text, p_note text DEFAULT NULL
) RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
    v_po purchase_orders%ROWTYPE;
    v_valid text[];
BEGIN
    SELECT * INTO v_po FROM purchase_orders WHERE id = p_po_id FOR UPDATE;
    IF v_po.id IS NULL THEN RAISE EXCEPTION 'PO_NOT_FOUND %', p_po_id; END IF;

    v_valid := CASE v_po.estado::text
        WHEN 'draft'              THEN ARRAY['sent','cancelled']
        WHEN 'sent'               THEN ARRAY['in_transit','cancelled']
        WHEN 'in_transit'         THEN ARRAY['partially_received','received','cancelled']
        WHEN 'partially_received' THEN ARRAY['received']
        ELSE ARRAY[]::text[]
    END;

    IF NOT (p_new_status::text = ANY (v_valid)) THEN
        RAISE EXCEPTION 'PO_INVALID_TRANSITION % -> %', v_po.estado, p_new_status;
    END IF;

    UPDATE purchase_orders SET estado = p_new_status WHERE id = p_po_id;
    PERFORM po_audit_append(p_po_id, jsonb_build_object('action','status_change','from',v_po.estado,'to',p_new_status,'by',p_by,'note',p_note));
    RETURN jsonb_build_object('status','ok','from',v_po.estado,'to',p_new_status);
END;
$$;

-- ---------------------------------------------------------------------
-- 9. Sanity check — usa tabla stock directa (no la vista pivotada)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION cost_layers_sanity_check()
RETURNS TABLE(issue text, sku text, warehouse text, layer_id uuid, detail jsonb)
LANGUAGE sql STABLE AS $$
    -- 9.1 Capas overflow (qty_restante > qty_recibida)
    SELECT 'qty_restante_overflow'::text, cl.sku, cl.warehouse, cl.id,
           jsonb_build_object('qty_recibida',cl.qty_recibida,'qty_restante',cl.qty_restante)
      FROM cost_layers cl
     WHERE cl.qty_restante > cl.qty_recibida
    UNION ALL
    -- 9.2 Stock físico sin cost layer activa que lo respalde
    SELECT 'stock_sin_costed'::text, s.sku, s.warehouse, NULL::uuid,
           jsonb_build_object('stock_qty', s.qty, 'costed_qty', COALESCE(c.tot, 0))
      FROM stock s
      LEFT JOIN (
          SELECT sku, warehouse, SUM(qty_restante) AS tot
            FROM cost_layers
           WHERE archived = false
           GROUP BY sku, warehouse
      ) c ON c.sku = s.sku AND c.warehouse = s.warehouse
     WHERE s.qty > 0
       AND (c.tot IS NULL OR c.tot < s.qty)
    UNION ALL
    -- 9.3 PO recibidas sin cost_layer asociada
    SELECT 'po_received_no_layer'::text, NULL::text, NULL::text, NULL::uuid,
           jsonb_build_object('po_id', p.id, 'po_number', p.po_number, 'fecha_received', p.fecha_received)
      FROM purchase_orders p
     WHERE p.estado = 'received'
       AND NOT EXISTS (SELECT 1 FROM cost_layers cl WHERE cl.source_id = p.id AND cl.source_type = 'purchase');
$$;

COMMENT ON FUNCTION cost_layers_sanity_check() IS
'Detecta inconsistencias. Correr 1×día por GH Action; alertar a Telegram si devuelve filas.';

-- ---------------------------------------------------------------------
-- 10. Helpers de reporting (opcional, útil para dashboard)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION margin_for_sale(
    p_sku text, p_warehouse text, p_qty int, p_unit_price_mxn numeric
) RETURNS jsonb LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_avg_cost numeric;
BEGIN
    SELECT costo_promedio_mxn INTO v_avg_cost
      FROM v_cost_current WHERE sku = p_sku AND warehouse = p_warehouse;
    IF v_avg_cost IS NULL THEN
        RETURN jsonb_build_object('status','no_cost_data','sku',p_sku);
    END IF;
    RETURN jsonb_build_object(
        'sku',                p_sku,
        'qty',                p_qty,
        'unit_price_mxn',     p_unit_price_mxn,
        'unit_cost_mxn',      v_avg_cost,
        'unit_margin_mxn',    (p_unit_price_mxn - v_avg_cost),
        'margin_pct',         ROUND(((p_unit_price_mxn - v_avg_cost) / NULLIF(p_unit_price_mxn,0)) * 100, 2),
        'total_revenue_mxn',  (p_qty * p_unit_price_mxn),
        'total_cogs_mxn',     (p_qty * v_avg_cost),
        'total_margin_mxn',   (p_qty * (p_unit_price_mxn - v_avg_cost))
    );
END;
$$;

COMMIT;

-- =====================================================================
-- FIN funciones Sprint 1 (v2)
-- =====================================================================
