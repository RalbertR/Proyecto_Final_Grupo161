CREATE DATABASE IF NOT EXISTS logistica_policial
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE logistica_policial;

CREATE TABLE unidad (
  id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre              VARCHAR(100) NOT NULL,
  nivel               ENUM('DIRECCION','REGIONAL','OPERACIONAL') NOT NULL,
  unidad_superior_id  INT UNSIGNED NULL,
  activa              BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_unidad_nombre UNIQUE (nombre),
  CONSTRAINT fk_unidad_superior FOREIGN KEY (unidad_superior_id) REFERENCES unidad (id),
  CONSTRAINT ck_unidad_superior CHECK ((nivel = 'DIRECCION') = (unidad_superior_id IS NULL))
) ENGINE = InnoDB;

CREATE TABLE ubicacion (
  id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  unidad_id  INT UNSIGNED NOT NULL,
  nombre     VARCHAR(100) NOT NULL,
  activa     BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_ubicacion_nombre UNIQUE (unidad_id, nombre),
  CONSTRAINT uq_ubicacion_unidad UNIQUE (id, unidad_id),
  CONSTRAINT fk_ubicacion_unidad FOREIGN KEY (unidad_id) REFERENCES unidad (id)
) ENGINE = InnoDB;

CREATE TABLE oficial (
  id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  legajo     VARCHAR(20) NOT NULL,
  apellido   VARCHAR(80) NOT NULL,
  nombre     VARCHAR(80) NOT NULL,
  unidad_id  INT UNSIGNED NOT NULL,
  activo     BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT uq_oficial_legajo UNIQUE (legajo),
  CONSTRAINT uq_oficial_unidad UNIQUE (id, unidad_id),
  CONSTRAINT fk_oficial_unidad FOREIGN KEY (unidad_id) REFERENCES unidad (id)
) ENGINE = InnoDB;

CREATE TABLE usuario (
  id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre_usuario   VARCHAR(50) NOT NULL,
  hash_contrasena  VARCHAR(255) NOT NULL,
  unidad_id        INT UNSIGNED NOT NULL,
  oficial_id       INT UNSIGNED NULL,
  activo           BOOLEAN NOT NULL DEFAULT TRUE,
  fecha_alta       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_usuario_nombre UNIQUE (nombre_usuario),
  CONSTRAINT uq_usuario_oficial UNIQUE (oficial_id),
  CONSTRAINT fk_usuario_unidad FOREIGN KEY (unidad_id) REFERENCES unidad (id),
  CONSTRAINT fk_usuario_oficial FOREIGN KEY (oficial_id) REFERENCES oficial (id)
) ENGINE = InnoDB;

CREATE TABLE tipo_bien (
  codigo  VARCHAR(30) PRIMARY KEY,
  nombre  VARCHAR(60) NOT NULL
) ENGINE = InnoDB;

CREATE TABLE tipo_vehiculo (
  id      SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre  VARCHAR(60) NOT NULL,
  CONSTRAINT uq_tipo_vehiculo UNIQUE (nombre)
) ENGINE = InnoDB;

CREATE TABLE tipo_tarea (
  id      SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre  VARCHAR(60) NOT NULL,
  CONSTRAINT uq_tipo_tarea UNIQUE (nombre)
) ENGINE = InnoDB;

CREATE TABLE bien (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tipo_bien         VARCHAR(30) NOT NULL,
  marca             VARCHAR(60) NOT NULL,
  modelo            VARCHAR(60) NOT NULL,
  numero_serie      VARCHAR(50) NULL,
  descripcion       VARCHAR(255) NULL,
  estado_operativo  ENUM('EN_SERVICIO','FUERA_DE_SERVICIO') NOT NULL DEFAULT 'EN_SERVICIO',
  de_baja           BOOLEAN NOT NULL DEFAULT FALSE,
  unidad_id         INT UNSIGNED NOT NULL,
  oficial_id        INT UNSIGNED NULL,
  ubicacion_id      INT UNSIGNED NULL,
  CONSTRAINT uq_bien_tipo UNIQUE (id, tipo_bien),
  CONSTRAINT uq_bien_serie UNIQUE (tipo_bien, marca, numero_serie),
  CONSTRAINT fk_bien_tipo FOREIGN KEY (tipo_bien) REFERENCES tipo_bien (codigo),
  CONSTRAINT fk_bien_unidad FOREIGN KEY (unidad_id) REFERENCES unidad (id),
  CONSTRAINT fk_bien_oficial FOREIGN KEY (oficial_id, unidad_id)
    REFERENCES oficial (id, unidad_id) ON UPDATE CASCADE,
  CONSTRAINT fk_bien_ubicacion FOREIGN KEY (ubicacion_id, unidad_id)
    REFERENCES ubicacion (id, unidad_id),
  CONSTRAINT ck_bien_serie CHECK ((tipo_bien = 'MOVIL') = (numero_serie IS NULL))
) ENGINE = InnoDB;

CREATE TABLE armamento (
  bien_id        INT UNSIGNED PRIMARY KEY,
  tipo_bien      VARCHAR(30) NOT NULL DEFAULT 'ARMAMENTO',
  calibre        VARCHAR(20) NOT NULL,
  sbo_cartuchos  SMALLINT UNSIGNED NOT NULL,
  CONSTRAINT fk_armamento_bien FOREIGN KEY (bien_id, tipo_bien) REFERENCES bien (id, tipo_bien),
  CONSTRAINT ck_armamento_tipo CHECK (tipo_bien = 'ARMAMENTO')
) ENGINE = InnoDB;

CREATE TABLE chaleco (
  bien_id            INT UNSIGNED PRIMARY KEY,
  tipo_bien          VARCHAR(30) NOT NULL DEFAULT 'CHALECO',
  talle              VARCHAR(10) NOT NULL,
  nivel_proteccion   VARCHAR(10) NOT NULL,
  fecha_vencimiento  DATE NOT NULL,
  CONSTRAINT fk_chaleco_bien FOREIGN KEY (bien_id, tipo_bien) REFERENCES bien (id, tipo_bien),
  CONSTRAINT ck_chaleco_tipo CHECK (tipo_bien = 'CHALECO')
) ENGINE = InnoDB;

CREATE TABLE movil (
  bien_id           INT UNSIGNED PRIMARY KEY,
  tipo_bien         VARCHAR(30) NOT NULL DEFAULT 'MOVIL',
  patente           VARCHAR(10) NOT NULL,
  numero_interno    VARCHAR(20) NOT NULL,
  anio              SMALLINT UNSIGNED NOT NULL,
  tipo_vehiculo_id  SMALLINT UNSIGNED NOT NULL,
  tipo_tarea_id     SMALLINT UNSIGNED NOT NULL,
  CONSTRAINT uq_movil_patente UNIQUE (patente),
  CONSTRAINT uq_movil_interno UNIQUE (numero_interno),
  CONSTRAINT fk_movil_bien FOREIGN KEY (bien_id, tipo_bien) REFERENCES bien (id, tipo_bien),
  CONSTRAINT fk_movil_tipo_vehiculo FOREIGN KEY (tipo_vehiculo_id) REFERENCES tipo_vehiculo (id),
  CONSTRAINT fk_movil_tipo_tarea FOREIGN KEY (tipo_tarea_id) REFERENCES tipo_tarea (id),
  CONSTRAINT ck_movil_tipo CHECK (tipo_bien = 'MOVIL'),
  CONSTRAINT ck_movil_anio CHECK (anio BETWEEN 1950 AND 2100)
) ENGINE = InnoDB;

CREATE TABLE equipo_comunicaciones (
  bien_id      INT UNSIGNED PRIMARY KEY,
  tipo_bien    VARCHAR(30) NOT NULL DEFAULT 'EQUIPO_COMUNICACIONES',
  tipo_equipo  ENUM('PORTATIL','VEHICULAR','BASE') NOT NULL,
  CONSTRAINT fk_equipo_bien FOREIGN KEY (bien_id, tipo_bien) REFERENCES bien (id, tipo_bien),
  CONSTRAINT ck_equipo_tipo CHECK (tipo_bien = 'EQUIPO_COMUNICACIONES')
) ENGINE = InnoDB;

CREATE TABLE documento (
  id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre_original         VARCHAR(255) NOT NULL,
  tipo_mime               VARCHAR(100) NOT NULL,
  tamano_bytes            BIGINT UNSIGNED NOT NULL,
  hash_sha256             CHAR(64) NOT NULL,
  ruta_almacenamiento     VARCHAR(500) NOT NULL,
  usuario_id              INT UNSIGNED NOT NULL,
  fecha_carga             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reemplaza_documento_id  INT UNSIGNED NULL,
  motivo_reemplazo        VARCHAR(255) NULL,
  CONSTRAINT uq_documento_hash UNIQUE (hash_sha256),
  CONSTRAINT uq_documento_reemplazo UNIQUE (reemplaza_documento_id),
  CONSTRAINT fk_documento_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id),
  CONSTRAINT fk_documento_reemplazo FOREIGN KEY (reemplaza_documento_id) REFERENCES documento (id),
  CONSTRAINT ck_documento_hash CHECK (hash_sha256 REGEXP '^[0-9a-f]{64}$'),
  CONSTRAINT ck_documento_tamano CHECK (tamano_bytes > 0),
  CONSTRAINT ck_documento_reemplazo CHECK ((reemplaza_documento_id IS NULL) = (motivo_reemplazo IS NULL))
) ENGINE = InnoDB;

CREATE TABLE movimiento (
  id                     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tipo                   ENUM('ALTA','ENTREGA','REUBICACION','TRASLADO','BAJA') NOT NULL,
  estado                 ENUM('PENDIENTE','APLICADO','RECHAZADO','ANULADO') NOT NULL,
  estado_revision        ENUM('NO_APLICA','PENDIENTE','REVISADO','OBSERVADO') NOT NULL,
  numero_acta            VARCHAR(30) NULL,
  fecha_hecho            DATE NOT NULL,
  fecha_carga            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  usuario_id             INT UNSIGNED NOT NULL,
  unidad_registrante_id  INT UNSIGNED NOT NULL,
  unidad_origen_id       INT UNSIGNED NULL,
  oficial_origen_id      INT UNSIGNED NULL,
  unidad_destino_id      INT UNSIGNED NULL,
  oficial_destino_id     INT UNSIGNED NULL,
  motivo                 VARCHAR(500) NULL,
  descripcion            VARCHAR(500) NULL,
  anulado_por_id         INT UNSIGNED NULL,
  fecha_anulacion        DATETIME NULL,
  motivo_anulacion       VARCHAR(500) NULL,
  CONSTRAINT fk_mov_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id),
  CONSTRAINT fk_mov_unidad_registrante FOREIGN KEY (unidad_registrante_id) REFERENCES unidad (id),
  CONSTRAINT fk_mov_unidad_origen FOREIGN KEY (unidad_origen_id) REFERENCES unidad (id),
  CONSTRAINT fk_mov_oficial_origen FOREIGN KEY (oficial_origen_id) REFERENCES oficial (id),
  CONSTRAINT fk_mov_unidad_destino FOREIGN KEY (unidad_destino_id) REFERENCES unidad (id),
  CONSTRAINT fk_mov_oficial_destino FOREIGN KEY (oficial_destino_id) REFERENCES oficial (id),
  CONSTRAINT fk_mov_anulado_por FOREIGN KEY (anulado_por_id) REFERENCES usuario (id),
  CONSTRAINT ck_mov_fechas CHECK (fecha_hecho <= DATE(fecha_carga)),
  CONSTRAINT ck_mov_oficial_misma_unidad CHECK (
    (oficial_origen_id IS NULL AND oficial_destino_id IS NULL) OR tipo = 'TRASLADO'
    OR unidad_origen_id = unidad_destino_id),
  CONSTRAINT ck_mov_alta CHECK (tipo <> 'ALTA' OR (
    unidad_origen_id IS NULL AND oficial_origen_id IS NULL
    AND unidad_destino_id IS NOT NULL AND oficial_destino_id IS NULL
    AND estado_revision = 'NO_APLICA')),
  CONSTRAINT ck_mov_entrega CHECK (tipo <> 'ENTREGA' OR (
    unidad_origen_id IS NOT NULL AND unidad_destino_id IS NOT NULL
    AND NOT (unidad_origen_id = unidad_destino_id
             AND oficial_origen_id IS NULL AND oficial_destino_id IS NULL))),
  CONSTRAINT ck_mov_reubicacion CHECK (tipo <> 'REUBICACION' OR (
    unidad_origen_id IS NOT NULL AND unidad_origen_id = unidad_destino_id
    AND oficial_origen_id IS NULL AND oficial_destino_id IS NULL
    AND estado_revision = 'NO_APLICA')),
  CONSTRAINT ck_mov_traslado CHECK (tipo <> 'TRASLADO' OR (
    oficial_origen_id IS NOT NULL AND oficial_origen_id = oficial_destino_id
    AND unidad_origen_id IS NOT NULL AND unidad_destino_id IS NOT NULL
    AND unidad_origen_id <> unidad_destino_id)),
  CONSTRAINT ck_mov_baja CHECK (tipo <> 'BAJA' OR (
    unidad_origen_id IS NOT NULL AND oficial_origen_id IS NULL
    AND unidad_destino_id IS NULL AND oficial_destino_id IS NULL
    AND motivo IS NOT NULL)),
  CONSTRAINT ck_mov_acta CHECK (
    (tipo NOT IN ('ENTREGA','TRASLADO','BAJA') OR numero_acta IS NOT NULL)
    AND (tipo <> 'REUBICACION' OR numero_acta IS NULL)),
  CONSTRAINT ck_mov_pendiente CHECK (estado NOT IN ('PENDIENTE','RECHAZADO') OR tipo = 'TRASLADO'
    OR (tipo = 'ENTREGA' AND unidad_origen_id <> unidad_destino_id)),
  CONSTRAINT ck_mov_anulacion CHECK (
    (estado = 'ANULADO' AND anulado_por_id IS NOT NULL
      AND fecha_anulacion IS NOT NULL AND motivo_anulacion IS NOT NULL)
    OR (estado <> 'ANULADO' AND anulado_por_id IS NULL
      AND fecha_anulacion IS NULL AND motivo_anulacion IS NULL))
) ENGINE = InnoDB;

CREATE INDEX ix_mov_revision ON movimiento (estado_revision, unidad_registrante_id);
CREATE INDEX ix_mov_fecha_hecho ON movimiento (fecha_hecho);

CREATE TABLE movimiento_bien (
  movimiento_id         INT UNSIGNED NOT NULL,
  bien_id               INT UNSIGNED NOT NULL,
  ubicacion_origen_id   INT UNSIGNED NULL,
  ubicacion_destino_id  INT UNSIGNED NULL,
  PRIMARY KEY (movimiento_id, bien_id),
  CONSTRAINT fk_mb_movimiento FOREIGN KEY (movimiento_id) REFERENCES movimiento (id),
  CONSTRAINT fk_mb_bien FOREIGN KEY (bien_id) REFERENCES bien (id),
  CONSTRAINT fk_mb_ubicacion_origen FOREIGN KEY (ubicacion_origen_id) REFERENCES ubicacion (id),
  CONSTRAINT fk_mb_ubicacion_destino FOREIGN KEY (ubicacion_destino_id) REFERENCES ubicacion (id)
) ENGINE = InnoDB;

CREATE TABLE recepcion (
  id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  movimiento_id   INT UNSIGNED NOT NULL,
  resultado       ENUM('ACEPTADO','RECHAZADO') NOT NULL,
  motivo_rechazo  VARCHAR(500) NULL,
  usuario_id      INT UNSIGNED NOT NULL,
  fecha           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_recepcion_movimiento UNIQUE (movimiento_id),
  CONSTRAINT fk_recepcion_movimiento FOREIGN KEY (movimiento_id) REFERENCES movimiento (id),
  CONSTRAINT fk_recepcion_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id),
  CONSTRAINT ck_recepcion_rechazo CHECK ((resultado = 'RECHAZADO') = (motivo_rechazo IS NOT NULL))
) ENGINE = InnoDB;

CREATE TABLE rectificacion (
  id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  movimiento_id  INT UNSIGNED NOT NULL,
  version        SMALLINT UNSIGNED NOT NULL,
  fecha_hecho    DATE NOT NULL,
  numero_acta    VARCHAR(30) NULL,
  descripcion    VARCHAR(500) NULL,
  motivo         VARCHAR(500) NOT NULL,
  usuario_id     INT UNSIGNED NOT NULL,
  fecha          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_rectificacion_version UNIQUE (movimiento_id, version),
  CONSTRAINT fk_rectificacion_movimiento FOREIGN KEY (movimiento_id) REFERENCES movimiento (id),
  CONSTRAINT fk_rectificacion_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id),
  CONSTRAINT ck_rectificacion_version CHECK (version >= 1),
  CONSTRAINT ck_rectificacion_fecha CHECK (fecha_hecho <= DATE(fecha))
) ENGINE = InnoDB;

CREATE TABLE movimiento_documento (
  movimiento_id  INT UNSIGNED NOT NULL,
  documento_id   INT UNSIGNED NOT NULL,
  PRIMARY KEY (movimiento_id, documento_id),
  CONSTRAINT fk_md_movimiento FOREIGN KEY (movimiento_id) REFERENCES movimiento (id),
  CONSTRAINT fk_md_documento FOREIGN KEY (documento_id) REFERENCES documento (id)
) ENGINE = InnoDB;

CREATE TABLE cambio_estado_operativo (
  id                     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  bien_id                INT UNSIGNED NOT NULL,
  estado_anterior        ENUM('EN_SERVICIO','FUERA_DE_SERVICIO') NOT NULL,
  estado_nuevo           ENUM('EN_SERVICIO','FUERA_DE_SERVICIO') NOT NULL,
  observaciones          VARCHAR(500) NOT NULL,
  documento_id           INT UNSIGNED NULL,
  estado_revision        ENUM('NO_APLICA','PENDIENTE','REVISADO','OBSERVADO') NOT NULL,
  usuario_id             INT UNSIGNED NOT NULL,
  unidad_registrante_id  INT UNSIGNED NOT NULL,
  fecha                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cambio_bien FOREIGN KEY (bien_id) REFERENCES bien (id),
  CONSTRAINT fk_cambio_documento FOREIGN KEY (documento_id) REFERENCES documento (id),
  CONSTRAINT fk_cambio_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id),
  CONSTRAINT fk_cambio_unidad FOREIGN KEY (unidad_registrante_id) REFERENCES unidad (id),
  CONSTRAINT ck_cambio_estados CHECK (estado_anterior <> estado_nuevo),
  CONSTRAINT ck_cambio_informe CHECK (estado_nuevo <> 'FUERA_DE_SERVICIO' OR documento_id IS NOT NULL)
) ENGINE = InnoDB;

CREATE INDEX ix_cambio_revision ON cambio_estado_operativo (estado_revision, unidad_registrante_id);

CREATE TABLE rectificacion_cambio_estado (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  cambio_estado_id  INT UNSIGNED NOT NULL,
  version           SMALLINT UNSIGNED NOT NULL,
  observaciones     VARCHAR(500) NOT NULL,
  documento_id      INT UNSIGNED NULL,
  motivo            VARCHAR(500) NOT NULL,
  usuario_id        INT UNSIGNED NOT NULL,
  fecha             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_rect_cambio_version UNIQUE (cambio_estado_id, version),
  CONSTRAINT fk_rect_cambio_cambio FOREIGN KEY (cambio_estado_id) REFERENCES cambio_estado_operativo (id),
  CONSTRAINT fk_rect_cambio_documento FOREIGN KEY (documento_id) REFERENCES documento (id),
  CONSTRAINT fk_rect_cambio_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id),
  CONSTRAINT ck_rect_cambio_version CHECK (version >= 1)
) ENGINE = InnoDB;

CREATE TABLE revision (
  id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  movimiento_id       INT UNSIGNED NULL,
  cambio_estado_id    INT UNSIGNED NULL,
  resultado           ENUM('REVISADO','OBSERVADO') NOT NULL,
  motivo_observacion  VARCHAR(500) NULL,
  usuario_id          INT UNSIGNED NOT NULL,
  fecha               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_revision_movimiento FOREIGN KEY (movimiento_id) REFERENCES movimiento (id),
  CONSTRAINT fk_revision_cambio FOREIGN KEY (cambio_estado_id) REFERENCES cambio_estado_operativo (id),
  CONSTRAINT fk_revision_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id),
  CONSTRAINT ck_revision_objeto CHECK ((movimiento_id IS NULL) <> (cambio_estado_id IS NULL)),
  CONSTRAINT ck_revision_motivo CHECK (resultado <> 'OBSERVADO' OR motivo_observacion IS NOT NULL)
) ENGINE = InnoDB;

CREATE TABLE traslado_oficial (
  id                     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  oficial_id             INT UNSIGNED NOT NULL,
  unidad_origen_id       INT UNSIGNED NOT NULL,
  unidad_destino_id      INT UNSIGNED NOT NULL,
  movimiento_id          INT UNSIGNED NULL,
  estado                 ENUM('PENDIENTE','CONFIRMADO','RECHAZADO','ANULADO') NOT NULL DEFAULT 'PENDIENTE',
  usuario_solicitante_id INT UNSIGNED NOT NULL,
  fecha_solicitud        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  usuario_resolucion_id  INT UNSIGNED NULL,
  fecha_resolucion       DATETIME NULL,
  motivo_resolucion      VARCHAR(500) NULL,
  oficial_pendiente_id   INT UNSIGNED AS (IF(estado = 'PENDIENTE', oficial_id, NULL)) STORED,
  CONSTRAINT uq_traslado_movimiento UNIQUE (movimiento_id),
  CONSTRAINT uq_oficial_un_traslado_pendiente UNIQUE (oficial_pendiente_id),
  CONSTRAINT fk_traslado_oficial FOREIGN KEY (oficial_id) REFERENCES oficial (id),
  CONSTRAINT fk_traslado_unidad_origen FOREIGN KEY (unidad_origen_id) REFERENCES unidad (id),
  CONSTRAINT fk_traslado_unidad_destino FOREIGN KEY (unidad_destino_id) REFERENCES unidad (id),
  CONSTRAINT fk_traslado_movimiento FOREIGN KEY (movimiento_id) REFERENCES movimiento (id),
  CONSTRAINT fk_traslado_solicitante FOREIGN KEY (usuario_solicitante_id) REFERENCES usuario (id),
  CONSTRAINT fk_traslado_resolucion FOREIGN KEY (usuario_resolucion_id) REFERENCES usuario (id),
  CONSTRAINT ck_traslado_unidades CHECK (unidad_origen_id <> unidad_destino_id),
  CONSTRAINT ck_traslado_resolucion CHECK (
    (estado = 'PENDIENTE') = (usuario_resolucion_id IS NULL AND fecha_resolucion IS NULL)),
  CONSTRAINT ck_traslado_motivo CHECK (
    estado NOT IN ('RECHAZADO','ANULADO') OR motivo_resolucion IS NOT NULL)
) ENGINE = InnoDB;

DELIMITER //

CREATE TRIGGER trg_bien_tenencia_ins BEFORE INSERT ON bien FOR EACH ROW
BEGIN
  IF NOT ((NEW.de_baja AND NEW.oficial_id IS NULL AND NEW.ubicacion_id IS NULL)
       OR (NOT NEW.de_baja AND ((NEW.oficial_id IS NULL) <> (NEW.ubicacion_id IS NULL)))) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Tenencia invalida: un bien activo tiene oficial o ubicacion, no ambos, y uno de baja no tiene ninguno';
  END IF;
END//

CREATE TRIGGER trg_bien_tenencia_upd BEFORE UPDATE ON bien FOR EACH ROW
BEGIN
  IF NOT ((NEW.de_baja AND NEW.oficial_id IS NULL AND NEW.ubicacion_id IS NULL)
       OR (NOT NEW.de_baja AND ((NEW.oficial_id IS NULL) <> (NEW.ubicacion_id IS NULL)))) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Tenencia invalida: un bien activo tiene oficial o ubicacion, no ambos, y uno de baja no tiene ninguno';
  END IF;
END//

CREATE TRIGGER trg_mb_bien_bloqueado BEFORE INSERT ON movimiento_bien FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1
             FROM movimiento_bien mb
             JOIN movimiento m ON m.id = mb.movimiento_id
             WHERE mb.bien_id = NEW.bien_id
               AND m.estado = 'PENDIENTE'
               AND m.id <> NEW.movimiento_id) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El bien tiene un movimiento pendiente y no admite otro';
  END IF;
END//

DELIMITER ;

CREATE VIEW v_inventario_unidad AS
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
               WHERE mb.bien_id = b.id AND mv.estado = 'PENDIENTE') AS con_movimiento_pendiente
FROM bien b
JOIN unidad u          ON u.id = b.unidad_id
LEFT JOIN movil m      ON m.bien_id = b.id
LEFT JOIN ubicacion ub ON ub.id = b.ubicacion_id
LEFT JOIN oficial o    ON o.id = b.oficial_id
WHERE b.de_baja = FALSE;

CREATE VIEW v_movimiento_vigente AS
SELECT mv.id,
       mv.tipo,
       mv.estado,
       mv.estado_revision,
       COALESCE(r.fecha_hecho, mv.fecha_hecho) AS fecha_hecho,
       CASE WHEN r.id IS NULL THEN mv.numero_acta ELSE r.numero_acta END AS numero_acta,
       CASE WHEN r.id IS NULL THEN mv.descripcion ELSE r.descripcion END AS descripcion,
       r.version AS version_vigente,
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

CREATE VIEW v_cambio_estado_vigente AS
SELECT c.id,
       c.bien_id,
       c.estado_anterior,
       c.estado_nuevo,
       CASE WHEN r.id IS NULL THEN c.observaciones ELSE r.observaciones END AS observaciones,
       CASE WHEN r.id IS NULL THEN c.documento_id ELSE r.documento_id END AS documento_id,
       r.version AS version_vigente,
       c.estado_revision,
       c.usuario_id,
       c.unidad_registrante_id,
       c.fecha
FROM cambio_estado_operativo c
LEFT JOIN rectificacion_cambio_estado r
       ON r.cambio_estado_id = c.id
      AND r.version = (SELECT MAX(r2.version) FROM rectificacion_cambio_estado r2 WHERE r2.cambio_estado_id = c.id);

CREATE VIEW v_historial_bien AS
SELECT mb.bien_id,
       'MOVIMIENTO' AS registro,
       v.id AS registro_id,
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
       v.usuario_id
FROM movimiento_bien mb
JOIN v_movimiento_vigente v ON v.id = mb.movimiento_id
UNION ALL
SELECT c.bien_id, 'CAMBIO_ESTADO', c.id, 'CAMBIO_ESTADO', DATE(c.fecha), NULL, NULL,
       NULL, NULL, NULL, NULL, NULL, NULL,
       c.estado_nuevo, c.observaciones, c.estado_revision, c.usuario_id
FROM v_cambio_estado_vigente c;

CREATE VIEW v_bandeja_revision AS
SELECT u.unidad_superior_id AS unidad_revisora_id,
       'MOVIMIENTO' AS registro,
       v.id AS registro_id,
       v.tipo AS evento,
       v.fecha_hecho AS fecha,
       v.unidad_registrante_id,
       v.usuario_id,
       v.descripcion AS detalle
FROM v_movimiento_vigente v
JOIN unidad u ON u.id = v.unidad_registrante_id
WHERE v.estado = 'APLICADO'
  AND v.estado_revision = 'PENDIENTE'
UNION ALL
SELECT u.unidad_superior_id, 'CAMBIO_ESTADO', c.id, 'CAMBIO_ESTADO', DATE(c.fecha),
       c.unidad_registrante_id, c.usuario_id, c.observaciones
FROM v_cambio_estado_vigente c
JOIN unidad u ON u.id = c.unidad_registrante_id
WHERE c.estado_revision = 'PENDIENTE';
