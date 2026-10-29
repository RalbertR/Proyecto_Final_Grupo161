USE logistica_policial;

ALTER TABLE unidad
  ADD COLUMN nivel_superior ENUM('DIRECCION','REGIONAL','OPERACIONAL')
    AS (CASE nivel WHEN 'REGIONAL' THEN 'DIRECCION' WHEN 'OPERACIONAL' THEN 'REGIONAL' END) STORED,
  ADD CONSTRAINT uq_unidad_nivel UNIQUE (id, nivel);

ALTER TABLE unidad DROP FOREIGN KEY fk_unidad_superior, DROP INDEX fk_unidad_superior;

ALTER TABLE unidad ADD CONSTRAINT fk_unidad_superior
  FOREIGN KEY (unidad_superior_id, nivel_superior) REFERENCES unidad (id, nivel);
