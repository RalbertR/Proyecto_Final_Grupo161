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
