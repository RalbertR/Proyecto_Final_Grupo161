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
  DECLARE bloqueado INT UNSIGNED;
  DECLARE vigente SMALLINT UNSIGNED;
  IF NEW.movimiento_id IS NOT NULL THEN
    SELECT id INTO bloqueado FROM movimiento WHERE id = NEW.movimiento_id FOR UPDATE;
    SET vigente = (SELECT COALESCE(MAX(version), 0)
                   FROM rectificacion
                   WHERE movimiento_id = NEW.movimiento_id);
  ELSE
    SELECT id INTO bloqueado FROM cambio_estado_operativo
    WHERE id = NEW.cambio_estado_id FOR UPDATE;
    SET vigente = (SELECT COALESCE(MAX(version), 0)
                   FROM rectificacion_cambio_estado
                   WHERE cambio_estado_id = NEW.cambio_estado_id);
  END IF;
  IF NEW.version_revisada <> vigente THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'La revision no corresponde a la version vigente';
  END IF;
END//

CREATE TRIGGER trg_rectificacion_bloqueo BEFORE INSERT ON rectificacion FOR EACH ROW
BEGIN
  DECLARE bloqueado INT UNSIGNED;
  SELECT id INTO bloqueado FROM movimiento WHERE id = NEW.movimiento_id FOR UPDATE;
END//

CREATE TRIGGER trg_rect_cambio_bloqueo BEFORE INSERT ON rectificacion_cambio_estado
FOR EACH ROW
BEGIN
  DECLARE bloqueado INT UNSIGNED;
  SELECT id INTO bloqueado FROM cambio_estado_operativo
  WHERE id = NEW.cambio_estado_id FOR UPDATE;
END//

DELIMITER ;

CREATE OR REPLACE VIEW v_movimiento_vigente AS
SELECT mv.id,
       mv.tipo,
       mv.estado,
       mv.estado_revision,
       COALESCE(r.fecha_hecho, mv.fecha_hecho) AS fecha_hecho,
       CASE WHEN r.id IS NULL THEN mv.numero_acta ELSE r.numero_acta END AS numero_acta,
       CASE WHEN r.id IS NULL THEN mv.descripcion ELSE r.descripcion END AS descripcion,
       COALESCE(r.version, 0) AS version_vigente,
       mv.fecha_carga,
       mv.usuario_id,
       mv.unidad_registrante_id,
       mv.unidad_origen_id,
       mv.oficial_origen_id,
       mv.unidad_destino_id,
       mv.oficial_destino_id,
       mv.motivo
FROM movimiento mv
LEFT JOIN rectificacion r
       ON r.movimiento_id = mv.id
      AND r.version = (SELECT MAX(r2.version) FROM rectificacion r2 WHERE r2.movimiento_id = mv.id);

CREATE OR REPLACE VIEW v_cambio_estado_vigente AS
SELECT c.id,
       c.bien_id,
       c.orden,
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
SELECT c.bien_id, 'CAMBIO_ESTADO', c.id, c.orden, 'CAMBIO_ESTADO', DATE(c.fecha), NULL, NULL,
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
WHERE c.estado_revision = 'PENDIENTE';
