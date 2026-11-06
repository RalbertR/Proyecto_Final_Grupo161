USE logistica_policial;

DELIMITER //

CREATE TRIGGER trg_oficial_unidad BEFORE UPDATE ON oficial FOR EACH ROW
BEGIN
  IF NEW.unidad_id <> OLD.unidad_id
     AND (EXISTS (SELECT 1 FROM bien WHERE oficial_id = OLD.id)
          OR EXISTS (SELECT 1 FROM movimiento
                     WHERE oficial_origen_id = OLD.id OR oficial_destino_id = OLD.id))
     AND NOT EXISTS (SELECT 1
                     FROM traslado_oficial t
                     WHERE t.id = (SELECT MAX(t2.id)
                                   FROM traslado_oficial t2
                                   WHERE t2.oficial_id = OLD.id AND t2.estado = 'CONFIRMADO')
                       AND t.unidad_origen_id = OLD.unidad_id
                       AND t.unidad_destino_id = NEW.unidad_id) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'La unidad de un oficial con bienes o movimientos solo cambia por un traslado confirmado';
  END IF;
END//

CREATE TRIGGER trg_rect_cambio_informe BEFORE INSERT ON rectificacion_cambio_estado
FOR EACH ROW FOLLOWS trg_rect_cambio_bloqueo
BEGIN
  IF NEW.documento_id IS NULL
     AND (SELECT estado_nuevo FROM cambio_estado_operativo
          WHERE id = NEW.cambio_estado_id) = 'FUERA_DE_SERVICIO' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Una rectificacion de un cambio a fuera de servicio debe conservar el informe tecnico';
  END IF;
END//

DELIMITER ;

ALTER TABLE cambio_estado_operativo
  ADD COLUMN estado ENUM('APLICADO','ANULADO') NOT NULL DEFAULT 'APLICADO',
  ADD COLUMN anulado_por_id INT UNSIGNED NULL,
  ADD COLUMN fecha_anulacion DATETIME NULL,
  ADD COLUMN motivo_anulacion VARCHAR(500) NULL,
  ADD CONSTRAINT fk_cambio_anulado_por FOREIGN KEY (anulado_por_id) REFERENCES usuario (id),
  ADD CONSTRAINT ck_cambio_anulacion CHECK (
    (estado = 'ANULADO' AND anulado_por_id IS NOT NULL
      AND fecha_anulacion IS NOT NULL AND motivo_anulacion IS NOT NULL)
    OR (estado <> 'ANULADO' AND anulado_por_id IS NULL
      AND fecha_anulacion IS NULL AND motivo_anulacion IS NULL));

CREATE OR REPLACE VIEW v_cambio_estado_vigente AS
SELECT c.id,
       c.bien_id,
       c.orden,
       c.estado,
       c.estado_anterior,
       c.estado_nuevo,
       CASE WHEN r.id IS NULL THEN c.observaciones ELSE r.observaciones END AS observaciones,
       CASE WHEN r.id IS NULL THEN c.documento_id ELSE r.documento_id END AS documento_id,
       COALESCE(r.version, 0) AS version_vigente,
       c.estado_revision,
       c.usuario_id,
       c.unidad_registrante_id,
       c.fecha
FROM cambio_estado_operativo c
LEFT JOIN rectificacion_cambio_estado r
       ON r.cambio_estado_id = c.id
      AND r.version = (SELECT MAX(r2.version) FROM rectificacion_cambio_estado r2 WHERE r2.cambio_estado_id = c.id);

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
SELECT c.bien_id, 'CAMBIO_ESTADO', c.id, c.orden, 'CAMBIO_ESTADO', DATE(c.fecha), NULL, c.estado,
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
SELECT u.unidad_superior_id, 'CAMBIO_ESTADO', c.id, 'CAMBIO_ESTADO', DATE(c.fecha),
       c.unidad_registrante_id, c.usuario_id, c.observaciones, c.version_vigente
FROM v_cambio_estado_vigente c
JOIN unidad u ON u.id = c.unidad_registrante_id
WHERE c.estado = 'APLICADO'
  AND c.estado_revision = 'PENDIENTE';
