USE logistica_policial;

CREATE OR REPLACE VIEW v_historial_bien AS
SELECT mb.bien_id,
       'MOVIMIENTO' AS registro,
       v.id AS registro_id,
       mb.orden,
       v.tipo AS evento,
       v.fecha_hecho AS fecha,
       v.numero_acta,
       v.estado,
       v.unidad_origen_id,
       v.oficial_origen_id,
       mb.ubicacion_origen_id,
       v.unidad_destino_id,
       v.oficial_destino_id,
       mb.ubicacion_destino_id,
       NULL AS estado_operativo_nuevo,
       v.descripcion AS detalle,
       v.estado_revision,
       v.usuario_id,
       v.fecha_carga
FROM movimiento_bien mb
JOIN v_movimiento_vigente v ON v.id = mb.movimiento_id
UNION ALL
SELECT c.bien_id, 'CAMBIO_ESTADO', c.id, c.orden, 'CAMBIO_ESTADO',
       DATE(CONVERT_TZ(c.fecha, '+00:00', '-03:00')), NULL, c.estado,
       NULL, NULL, NULL, NULL, NULL, NULL,
       c.estado_nuevo, c.observaciones, c.estado_revision, c.usuario_id, c.fecha
FROM v_cambio_estado_vigente c;

CREATE OR REPLACE VIEW v_bandeja_revision AS
SELECT u.unidad_superior_id AS unidad_revisora_id,
       'MOVIMIENTO' AS registro,
       v.id AS registro_id,
       v.tipo AS evento,
       v.fecha_hecho AS fecha,
       v.unidad_registrante_id,
       v.usuario_id,
       v.descripcion AS detalle,
       v.version_vigente
FROM v_movimiento_vigente v
JOIN unidad u ON u.id = v.unidad_registrante_id
WHERE v.estado = 'APLICADO'
  AND v.estado_revision = 'PENDIENTE'
UNION ALL
SELECT u.unidad_superior_id, 'CAMBIO_ESTADO', c.id, 'CAMBIO_ESTADO',
       DATE(CONVERT_TZ(c.fecha, '+00:00', '-03:00')),
       c.unidad_registrante_id, c.usuario_id, c.observaciones, c.version_vigente
FROM v_cambio_estado_vigente c
JOIN unidad u ON u.id = c.unidad_registrante_id
WHERE c.estado = 'APLICADO'
  AND c.estado_revision = 'PENDIENTE';
