USE logistica_policial;

ALTER TABLE movimiento_bien
  ADD COLUMN estado_operativo ENUM('EN_SERVICIO','FUERA_DE_SERVICIO') NULL;

-- Estado del bien al cargarse el acta: el del último cambio hasta fecha_carga;
-- si no hubo, el anterior al primer cambio posterior; si nunca cambió, el actual.
UPDATE movimiento_bien mb
JOIN movimiento m ON m.id = mb.movimiento_id
JOIN bien b ON b.id = mb.bien_id
SET mb.estado_operativo = COALESCE(
  (SELECT c.estado_nuevo
   FROM cambio_estado_operativo c
   WHERE c.bien_id = mb.bien_id AND c.fecha <= m.fecha_carga
   ORDER BY c.fecha DESC, c.id DESC
   LIMIT 1),
  (SELECT c.estado_anterior
   FROM cambio_estado_operativo c
   WHERE c.bien_id = mb.bien_id AND c.fecha > m.fecha_carga
   ORDER BY c.fecha, c.id
   LIMIT 1),
  b.estado_operativo);

ALTER TABLE movimiento_bien
  MODIFY COLUMN estado_operativo ENUM('EN_SERVICIO','FUERA_DE_SERVICIO') NOT NULL;

DELIMITER //

CREATE TRIGGER trg_mb_estado_operativo BEFORE INSERT ON movimiento_bien
FOR EACH ROW FOLLOWS trg_mb_orden
BEGIN
  SET NEW.estado_operativo = (SELECT estado_operativo FROM bien WHERE id = NEW.bien_id);
END//

DELIMITER ;
