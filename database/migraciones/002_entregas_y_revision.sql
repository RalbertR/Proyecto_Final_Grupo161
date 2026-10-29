USE logistica_policial;

ALTER TABLE unidad
  ADD COLUMN nivel_superior ENUM('DIRECCION','REGIONAL','OPERACIONAL')
    AS (CASE nivel WHEN 'REGIONAL' THEN 'DIRECCION' WHEN 'OPERACIONAL' THEN 'REGIONAL' END) STORED,
  ADD CONSTRAINT uq_unidad_nivel UNIQUE (id, nivel);

ALTER TABLE unidad DROP FOREIGN KEY fk_unidad_superior, DROP INDEX fk_unidad_superior;

ALTER TABLE unidad ADD CONSTRAINT fk_unidad_superior
  FOREIGN KEY (unidad_superior_id, nivel_superior) REFERENCES unidad (id, nivel);

ALTER TABLE bien ADD COLUMN ultimo_orden INT UNSIGNED NOT NULL DEFAULT 0;

ALTER TABLE movimiento_bien
  ADD COLUMN orden INT UNSIGNED NULL,
  ADD CONSTRAINT uq_mb_orden UNIQUE (bien_id, orden);

ALTER TABLE cambio_estado_operativo
  ADD COLUMN orden INT UNSIGNED NOT NULL DEFAULT 0,
  ADD CONSTRAINT uq_cambio_orden UNIQUE (bien_id, orden);

UPDATE movimiento_bien mb
JOIN (SELECT mb2.movimiento_id,
             mb2.bien_id,
             ROW_NUMBER() OVER (PARTITION BY mb2.bien_id
                                ORDER BY m.fecha_hecho, m.fecha_carga, m.id) AS n
      FROM movimiento_bien mb2
      JOIN movimiento m ON m.id = mb2.movimiento_id
      WHERE m.estado = 'APLICADO') x
  ON x.movimiento_id = mb.movimiento_id AND x.bien_id = mb.bien_id
SET mb.orden = x.n;

UPDATE bien b
SET b.ultimo_orden = (SELECT COALESCE(MAX(mb.orden), 0)
                      FROM movimiento_bien mb
                      WHERE mb.bien_id = b.id);

DELIMITER //

CREATE TRIGGER trg_mb_orden BEFORE INSERT ON movimiento_bien
FOR EACH ROW FOLLOWS trg_mb_bien_bloqueado
BEGIN
  IF (SELECT estado FROM movimiento WHERE id = NEW.movimiento_id) = 'APLICADO' THEN
    UPDATE bien SET ultimo_orden = ultimo_orden + 1 WHERE id = NEW.bien_id;
    SET NEW.orden = (SELECT ultimo_orden FROM bien WHERE id = NEW.bien_id);
  ELSE
    SET NEW.orden = NULL;
  END IF;
END//

CREATE TRIGGER trg_mov_orden AFTER UPDATE ON movimiento FOR EACH ROW
BEGIN
  IF OLD.estado <> 'APLICADO' AND NEW.estado = 'APLICADO' THEN
    UPDATE bien b
    JOIN movimiento_bien mb ON mb.bien_id = b.id
    SET b.ultimo_orden = b.ultimo_orden + 1
    WHERE mb.movimiento_id = NEW.id;

    UPDATE movimiento_bien mb
    JOIN bien b ON b.id = mb.bien_id
    SET mb.orden = b.ultimo_orden
    WHERE mb.movimiento_id = NEW.id;
  END IF;
END//

CREATE TRIGGER trg_cambio_orden BEFORE INSERT ON cambio_estado_operativo FOR EACH ROW
BEGIN
  UPDATE bien SET ultimo_orden = ultimo_orden + 1 WHERE id = NEW.bien_id;
  SET NEW.orden = (SELECT ultimo_orden FROM bien WHERE id = NEW.bien_id);
END//

DELIMITER ;

ALTER TABLE revision ADD COLUMN version_revisada SMALLINT UNSIGNED NOT NULL;

DELIMITER //

CREATE TRIGGER trg_revision_version BEFORE INSERT ON revision FOR EACH ROW
BEGIN
  DECLARE vigente SMALLINT UNSIGNED;
  IF NEW.movimiento_id IS NOT NULL THEN
    SET vigente = (SELECT COALESCE(MAX(version), 0)
                   FROM rectificacion
                   WHERE movimiento_id = NEW.movimiento_id);
  ELSE
    SET vigente = (SELECT COALESCE(MAX(version), 0)
                   FROM rectificacion_cambio_estado
                   WHERE cambio_estado_id = NEW.cambio_estado_id);
  END IF;
  IF NEW.version_revisada <> vigente THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'La revision no corresponde a la version vigente';
  END IF;
END//

DELIMITER ;
