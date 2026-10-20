# 5. Contraseñas con bcrypt y sesión con JWT

Aceptada el 20/10/2026.

## Contexto

Las contraseñas se guardan hasheadas y el inicio de sesión sigue el OAuth2 Password Flow, para que Swagger y el frontend usen el mismo formulario. La forma más difundida en FastAPI es hashear con passlib, pero passlib no se mantiene desde 2020 y falla con las versiones actuales de bcrypt. Además, la API no guarda sesiones, así que cada pedido tiene que traer algo que identifique al usuario.

## Decisión

Usamos la librería bcrypt directamente, sin passlib. Al iniciar sesión, la API entrega un JWT firmado con HS256 usando la clave `CLAVE_JWT`, que lleva el id del usuario y vence a las 8 horas, lo que alcanza para una jornada de trabajo. En cada pedido la dependencia `usuario_actual` valida el token y vuelve a leer al usuario y su unidad de la base.

Para no revelar qué usuarios existen, el login responde lo mismo si el usuario no existe, si la contraseña es incorrecta o si el usuario está inactivo. Cuando el usuario no existe, la contraseña se compara igual contra un hash ficticio, así el tiempo de respuesta también es el mismo.

## Consecuencias

Desactivar un usuario corta su acceso en el pedido siguiente, aunque tenga un token vigente, porque el usuario se lee de nuevo en cada pedido. Cerrar sesión borra el token del navegador, pero ese token sigue siendo válido hasta que vence. Si se cambia `CLAVE_JWT`, se cierran todas las sesiones. bcrypt no acepta contraseñas de más de 72 bytes, y el login las rechaza como incorrectas.
