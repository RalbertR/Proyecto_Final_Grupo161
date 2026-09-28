# Sistema Logístico Policial

Trabajo Final Integrador de la Tecnicatura Universitaria en Programación a Distancia, Universidad Tecnológica Nacional.

Grupo 161: Mariano Rodríguez Arce y Raul Robino.

## Descripción

Sistema web que centraliza la trazabilidad de los bienes logísticos de una fuerza de seguridad: armamento, chalecos balísticos, móviles y equipos de comunicaciones. Registra quién tiene cada bien, dónde está, qué movimientos tuvo y qué actas los respaldan, y permite que el nivel superior revise lo que cargan las unidades que dependen de él. Lo usa el personal logístico de la Dirección Logística, de las Unidades Regionales y de las Unidades Operacionales.

La organización y todos los datos del proyecto son ficticios.

## Estado del proyecto

Estamos en la etapa de análisis y diseño. El repositorio tiene la documentación, el script de la base de datos y la estructura de carpetas, todavía sin código. La codificación empieza cuando el tutor apruebe la segunda entrega.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Base de datos | MySQL 8 |
| Backend | Python con FastAPI, Pydantic y SQLModel |
| Estructura de la base | Scripts SQL versionados en /database |
| Autenticación | JWT |
| Frontend | React con Tailwind |

La justificación de cada tecnología está en la sección 5 del documento de diseño.

## Estructura del repositorio

```text
/docs                  entregas, documento de diseño y diagrama entidad-relación
/database
  /migraciones         scripts de creación de la base, numerados en orden
  /semillas            carga inicial de unidades, oficiales y bienes
/backend
  /app                 un paquete por módulo
  /tests               pruebas automatizadas
/frontend              aplicación React con Tailwind
```

## Entregas

### Primera entrega: definición del problema y propuesta de MVP

- [Definición del problema](docs/1ra%20Entrega%20-%20Analisis%20-%20Proyecto%20Final%20-%20Grupo%20161.md)
- [Propuesta de MVP](docs/1ra%20Entrega%20-%20Propuesta%20de%20MVP%20-%20Proyecto%20Final%20-%20Grupo%20161.md)

### Segunda entrega: diseño y módulos

- [Documento de diseño y módulos](docs/Diseno%20y%20modulos%20-%20Proyecto%20Final%20-%20Grupo%20161.md)
- [Diagrama entidad-relación](docs/diagrama_entidad_relacion.png)
- [Script de creación de la base de datos](database/migraciones/001_esquema.sql)
