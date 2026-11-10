# HU-22. Sala de situación

Contrato local de la [issue #79](https://github.com/RalbertR/Proyecto_Final_Grupo161/issues/79). Todos los pedidos requieren un token de sesión en `Authorization: Bearer <token>`.

La sala muestra a la Regional y a la Dirección dónde se demoran las actas y qué parte del equipamiento está fuera de servicio en cada unidad que alcanzan según la RN-01.

## Consultar

`GET /api/situacion`

| Parámetro | Contenido |
|---|---|
| `regional_id` | Opcional. Solo para Dirección: muestra esa Regional y sus unidades. |

Sin `regional_id`, la Regional ve su Regional y sus unidades, y Dirección ve todas, incluida la propia.

Responde **200**:

```json
{
  "unidades": [
    {
      "id": 4,
      "nombre": "Unidad Operacional A",
      "nivel": "OPERACIONAL",
      "tipos": [
        { "tipo_bien": "ARMAMENTO", "total": 20, "fuera_de_servicio": 1 },
        { "tipo_bien": "CHALECO", "total": 19, "fuera_de_servicio": 0 },
        { "tipo_bien": "MOVIL", "total": 6, "fuera_de_servicio": 1 },
        { "tipo_bien": "EQUIPO_COMUNICACIONES", "total": 15, "fuera_de_servicio": 1 }
      ],
      "abiertas": 3
    }
  ],
  "grupos": [
    { "etapa": "POR_RECIBIR", "cantidad": 5, "dias_mas_antigua": 5 },
    { "etapa": "EN_REVISION", "cantidad": 8, "dias_mas_antigua": 9 },
    { "etapa": "OBSERVADA", "cantidad": 2, "dias_mas_antigua": 4 },
    { "etapa": "DEVUELTA", "cantidad": 0, "dias_mas_antigua": null }
  ],
  "demoradas": [
    {
      "movimiento_id": 19,
      "numero_acta": "0019/2026",
      "etapa": "EN_REVISION",
      "unidad_id": 2,
      "unidad": "Unidad Regional Norte",
      "dias": 9
    }
  ]
}
```

- `unidades` va en orden de jerarquía: Dirección, y después cada Regional seguida de sus unidades. `tipos` trae siempre los cuatro tipos en el mismo orden, con ceros si no hay bienes. Solo se cuentan los bienes que no están de baja.
- `abiertas` es la cantidad de actas que esperan que esa unidad haga el próximo paso.
- `grupos` trae siempre las cuatro etapas en ese orden. `dias_mas_antigua` es null cuando no hay actas en la etapa.
- `demoradas` trae hasta cinco actas, de la que más días lleva en su etapa a la que menos.

## Grupos

Cada acta abierta se cuenta una sola vez, a la unidad que tiene que hacer el próximo paso, y aparece si esa unidad está en el alcance. Los días son días completos desde que el acta entró en la etapa. Los cambios de estado no se cuentan.

| Etapa | Acta | Unidad responsable | Desde |
|---|---|---|---|
| `POR_RECIBIR` | Pendiente de recepción. | La de destino. | La carga o la última versión. |
| `EN_REVISION` | Aplicada y pendiente de revisión. | La que tiene que revisarla. | La aceptación, la carga si no tuvo recepción, o la última corrección. |
| `OBSERVADA` | Aplicada y observada. | La que la registró. | La última observación. |
| `DEVUELTA` | Devuelta al origen. | La de origen. | La última devolución. |

## Errores

| Código | Cuándo |
|---|---|
| 401 | Sin token o con un token vencido. |
| 403 | El usuario es de una Unidad Operacional. |
| 422 | Una Regional manda `regional_id`, o Dirección manda el de una unidad que no es una Regional. |
