# Lo ejecuta la imagen de MySQL la primera vez, solo en producción.
# Crea la base con los scripts de migraciones y deja al usuario de la
# aplicación solo con permisos sobre los datos. En desarrollo no se usa
# porque las pruebas necesitan TRUNCATE.
for archivo in /migraciones/*.sql; do
  mysql_note "Corriendo $archivo"
  docker_process_sql < "$archivo"
done

# La imagen da el grant sobre el nombre con el _ escapado, porque en un
# GRANT el _ es comodín. El REVOKE tiene que usar el mismo nombre.
docker_process_sql <<-EOSQL
	REVOKE ALL PRIVILEGES ON \`logistica\\_policial\`.* FROM '$MYSQL_USER'@'%';
	GRANT SELECT, INSERT, UPDATE, DELETE ON \`logistica\\_policial\`.* TO '$MYSQL_USER'@'%';
EOSQL
