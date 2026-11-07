USE logistica_policial;

ALTER TABLE movimiento
  MODIFY COLUMN estado ENUM('PENDIENTE','APLICADO','RECHAZADO','ANULADO','DEVUELTO') NOT NULL,
  ADD CONSTRAINT ck_mov_devuelto CHECK (
    estado <> 'DEVUELTO' OR (tipo = 'ENTREGA' AND unidad_origen_id <> unidad_destino_id));

ALTER TABLE recepcion DROP CHECK ck_recepcion_rechazo;

ALTER TABLE recepcion
  ADD INDEX ix_recepcion_movimiento (movimiento_id),
  DROP INDEX uq_recepcion_movimiento;

ALTER TABLE recepcion
  RENAME COLUMN motivo_rechazo TO motivo,
  MODIFY COLUMN resultado ENUM('ACEPTADO','RECHAZADO','DEVUELTO') NOT NULL,
  ADD COLUMN movimiento_resuelto_id INT UNSIGNED
    AS (IF(resultado = 'DEVUELTO', NULL, movimiento_id)) STORED,
  ADD CONSTRAINT uq_recepcion_resuelta UNIQUE (movimiento_resuelto_id),
  ADD CONSTRAINT ck_recepcion_motivo CHECK ((resultado = 'ACEPTADO') = (motivo IS NULL));

CREATE TABLE recepcion_novedad (
  recepcion_id  INT UNSIGNED NOT NULL,
  bien_id       INT UNSIGNED NOT NULL,
  PRIMARY KEY (recepcion_id, bien_id),
  CONSTRAINT fk_novedad_recepcion FOREIGN KEY (recepcion_id) REFERENCES recepcion (id),
  CONSTRAINT fk_novedad_bien FOREIGN KEY (bien_id) REFERENCES bien (id)
) ENGINE = InnoDB;

DROP TRIGGER trg_mb_bien_bloqueado;

DELIMITER //

CREATE TRIGGER trg_mb_bien_bloqueado BEFORE INSERT ON movimiento_bien
FOR EACH ROW PRECEDES trg_mb_orden
BEGIN
  IF EXISTS (SELECT 1
             FROM movimiento_bien mb
             JOIN movimiento m ON m.id = mb.movimiento_id
             WHERE mb.bien_id = NEW.bien_id
               AND m.estado IN ('PENDIENTE','DEVUELTO')
               AND m.id <> NEW.movimiento_id) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El bien tiene un movimiento pendiente y no admite otro';
  END IF;
END//

DELIMITER ;

CREATE OR REPLACE VIEW v_inventario_unidad AS
SELECT b.unidad_id,
       u.nombre AS unidad,
       b.id AS bien_id,
       b.tipo_bien,
       COALESCE(b.numero_serie, m.patente) AS identificacion,
       b.marca,
       b.modelo,
       b.estado_operativo,
       CASE WHEN b.oficial_id IS NOT NULL THEN 'DOTACION' ELSE 'DEPOSITO' END AS tenencia,
       ub.nombre AS ubicacion,
       o.legajo AS oficial_legajo,
       CONCAT(o.apellido, ', ', o.nombre) AS oficial,
       EXISTS (SELECT 1
               FROM movimiento_bien mb
               JOIN movimiento mv ON mv.id = mb.movimiento_id
               WHERE mb.bien_id = b.id AND mv.estado IN ('PENDIENTE','DEVUELTO')) AS con_movimiento_pendiente
FROM bien b
JOIN unidad u          ON u.id = b.unidad_id
LEFT JOIN movil m      ON m.bien_id = b.id
LEFT JOIN ubicacion ub ON ub.id = b.ubicacion_id
LEFT JOIN oficial o    ON o.id = b.oficial_id
WHERE b.de_baja = FALSE;
