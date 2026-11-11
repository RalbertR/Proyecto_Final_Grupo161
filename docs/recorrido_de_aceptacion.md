# Recorrido de aceptación

Pasos para recorrer el sistema publicado con cada usuario de demostración y comprobar que hace lo que tiene que hacer. La URL y la contraseña están en la sección Sistema desplegado del [README](../README.md#sistema-desplegado). Conviene hacerlo con los datos de demostración recién cargados, porque el recorrido registra entregas, revisiones y cambios de estado. Cada paso se hace en una computadora y en un celular.

## Unidad Operacional A

Usuario `aux.unidad_a`.

| Paso | Qué hacer | Qué tiene que pasar |
|---|---|---|
| A1 | Entrar con el usuario y la contraseña. | El inicio muestra la fecha, el resumen por tipo de bien y los pendientes de la unidad, con los mismos números que el menú. |
| A2 | Abrir Inventario y filtrar Armamento. | Se ven solo los bienes de A con su tenencia. Los que tienen un movimiento pendiente no se pueden elegir. |
| A3 | Elegir dos armas en depósito, tocar Nueva entrega, elegir la Unidad Operacional B, cargar un número de acta nuevo y registrar. | La vista previa muestra el acta como se imprime. Al registrar, el acta queda pendiente de recepción y las armas quedan marcadas en el inventario. |
| A4 | Tocar Imprimir acta. | Se abre la hoja A4 y el diálogo de impresión del navegador. |
| A5 | Adjuntar un PDF al acta. | El PDF aparece en la lista del acta. |
| A6 | Elegir una radio en depósito y tocar Asignar a oficial. | Solo aparecen los oficiales que no tienen una radio. Al asignar, la radio pasa a la dotación del oficial. |
| A7 | Elegir un bien en dotación y tocar Registrar devolución. | La ubicación viene propuesta y el bien vuelve a depósito. |
| A8 | En la página de un móvil, tocar Cambiar estado, completar las observaciones y adjuntar el informe técnico. | El móvil queda fuera de servicio y el cambio queda pendiente de revisión. |
| A9 | En Devueltas, corregir un acta, cambiar el bien con novedad por otro y reenviar. | El acta vuelve a Por recibir del destino. |
| A10 | Abrir por URL la página de un bien de otra unidad. | El sistema avisa que no tiene acceso a ese bien. |

## Unidad Operacional B

Usuario `aux.unidad_b`.

| Paso | Qué hacer | Qué tiene que pasar |
|---|---|---|
| B1 | Entrar y abrir Por recibir. | Están las actas que le mandaron, con el origen y la cantidad de bienes. |
| B2 | Abrir el acta de A, tildar cada bien como controlado y aceptar. | La ubicación viene propuesta. Los bienes pasan al inventario de B. |
| B3 | Abrir otra acta, marcar un bien con novedad y rechazarla a la unidad de origen con un motivo. | El acta pasa a Devueltas de la unidad de origen. |
| B4 | Abrir la página de un bien recibido. | La línea de custodia muestra el paso del origen a B y el acta que lo respalda. |

## Unidad Operacional C

Usuario `aux.unidad_c`.

| Paso | Qué hacer | Qué tiene que pasar |
|---|---|---|
| C1 | Entrar. | El menú no tiene Revisión ni Sala de situación. |
| C2 | Abrir por URL la página de Revisión. | Vuelve al inicio. |
| C3 | Recibir el acta que reenvió A. | Los bienes pasan al inventario de C. |
| C4 | Abrir Inventario. | Se ven solo los bienes de C. |

## Unidad Regional Norte

Usuario `logistico.regional_norte`.

| Paso | Qué hacer | Qué tiene que pasar |
|---|---|---|
| N1 | Entrar. | El menú suma Revisión y Sala de situación. El inicio muestra lo que hay para revisar. |
| N2 | En Revisión, abrir una entrega con PDF, tildar cada dato y tocar Revisado. | El PDF se ve al lado de los datos. El acta sale de la bandeja. |
| N3 | Abrir otra acta y observarla con un motivo. | El acta pasa a Observados de la unidad que la registró. |
| N4 | Después de que la unidad corrige el acta observada, revisarla de nuevo. | El acta aparece como Corregida, con el dato anterior tachado y el historial de la observación y la corrección. |
| N5 | Abrir el cambio de estado del móvil, abrir el informe y confirmar. | El cambio sale de la bandeja. |
| N6 | Abrir Inventario. | El filtro de unidad ofrece la Regional, A y B, y no C. |
| N7 | Abrir Sala de situación, tocar un número de la tabla y después Ver en el inventario. | El inventario se abre filtrado por esa unidad y ese tipo de bien. |

## Unidad Regional Sur

Usuario `logistico.regional_sur`.

| Paso | Qué hacer | Qué tiene que pasar |
|---|---|---|
| S1 | En Revisión, abrir un acta de C, tildar cada dato y tocar Revisado. | La bandeja tiene solo lo que registra C y el acta sale de ella. |
| S2 | Abrir Inventario. | El filtro de unidad ofrece la Regional Sur y C. |
| S3 | Abrir Sala de situación. | La tabla tiene la Regional Sur y C. |

## Dirección Logística

Usuario `logistico.direccion`.

| Paso | Qué hacer | Qué tiene que pasar |
|---|---|---|
| D1 | Entrar. | El menú no tiene Observados, porque lo que registra la Dirección no se revisa. |
| D2 | En Revisión, abrir un acta de una Regional, tildar cada dato y tocar Revisado. | La bandeja tiene solo lo que registran las Regionales y el acta sale de ella. |
| D3 | Abrir Inventario. | El filtro de unidad ofrece todas las unidades. |
| D4 | Abrir Sala de situación y elegir la Unidad Regional Sur. | La tabla pasa a mostrar solo la Regional Sur y C. |

## Resultado del 10/11/2026

Se recorrió en https://logistica.nano-rodriguez.com con los datos que tenía el servidor ese día. En la computadora se usó Chrome a 1440 × 900 px y se hicieron todos los pasos. Para el celular se usó Chrome con la pantalla de 390 × 844 px. Ahí se repitieron las pantallas de cada usuario y, con datos nuevos, una recepción de A y una revisión de la Regional Norte.

| Usuario | Computadora | Celular |
|---|---|---|
| Unidad Operacional A | Todos los pasos bien. A8 muestra la fecha del día siguiente, ver #84. | Bien. La ventana de recepción se corre de costado, ver #85. |
| Unidad Operacional B | Todos los pasos bien. | Bien. Las ventanas de corrección se corren de costado, ver #85. |
| Unidad Operacional C | Todos los pasos bien. | Bien. |
| Unidad Regional Norte | Todos los pasos bien. N5 muestra dos fechas distintas para el mismo cambio, ver #84. | Bien. La página de Revisión se corre de costado, ver #85. |
| Unidad Regional Sur | Todos los pasos bien. | Bien. La página de Revisión se corre de costado, ver #85. |
| Dirección Logística | Todos los pasos bien. | Bien. |

Fallas cargadas:

- #84 Después de las 21 h las fechas del sistema quedan con el día siguiente.
- #85 En el celular la página de Revisión se corre de costado.

Detalles menores que no se cargaron como falla:

- En la página de un bien de otra unidad, el aviso de que no tiene acceso ofrece Reintentar, que no cambia nada.
- El botón dice Rechazar a la unidad de origen y el aviso final dice Acta devuelta al origen.
- Confirmar un cambio de estado cierra la ventana sin aviso, mientras que la revisión de un acta muestra Acta revisada.
- El visor del PDF en la revisión tarda unos segundos en mostrar el acta.
