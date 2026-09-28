# Sistema Logístico Policial

## Primera entrega: propuesta de MVP

Universidad Tecnológica Nacional

Tecnicatura Universitaria en Programación a Distancia

Trabajo Final Integrador, Grupo 161

Mariano Rodríguez Arce y Raul Robino

---

Contenido

1. Propuesta de MVP
2. Bienes logísticos que ingresan al MVP
3. Principales operaciones permitidas
4. Flujo completo de un movimiento
5. Reglas de negocio que no deben violarse
6. Información que puede consultar cada rol y nivel
7. Criterios de éxito

## 1. Propuesta de MVP

El MVP se concentra en la trazabilidad centralizada de los bienes logísticos que se identifican de forma individual. Cubre el recorrido completo de cada bien: su responsable, que puede ser una unidad o un oficial, la entrega y la recepción, la documentación, el estado actual y el historial.

La revisión la hace el nivel jerárquico superior después del hecho, no como una autorización previa. Dejamos fuera de esta etapa la gestión del stock consumible, como la munición, los atributos avanzados de la flota, como el kilometraje, el estado operativo, el mantenimiento y el historial de reparaciones, y el equipamiento policial, como uniformes, equipos de escritura o equipos de contención. Todo eso queda planteado para versiones futuras.

## 2. Bienes logísticos que ingresan al MVP

Ingresan los cuatro bienes logísticos que comparten el mismo patrón de dominio, una identidad individual única y el mismo mecanismo de tenencia:

- Armamento
- Chalecos balísticos
- Móviles
- Equipos de comunicaciones

Justificación del recorte:

- Los cuatro se identifican por un código alfanumérico propio, que es el número de serie en el armamento, los chalecos y las radios, y la patente o el número interno en los móviles. Su historial se sigue por esa identidad, no por cantidad.
- **El responsable** de un bien logístico puede ser una **Unidad**, ya sea Operacional, Regional o la Dirección Logística, o un **Oficial** puntual cuando tiene una dotación permanente asignada. No hace falta definir una persona física responsable dentro de la Unidad, como un “Jefe de Unidad”: alcanza con registrar a qué Unidad pertenece el bien. Este mecanismo es igual para los cuatro tipos de bien y para las tres instancias. El sistema lo opera únicamente el personal logístico designado de cada instancia, que es Sala de Armas o el Oficial Auxiliar Logístico en una Unidad Operacional y el personal logístico correspondiente en una Regional o en la Dirección. El oficial usuario final no tiene acceso al sistema.
- **Munición** queda fuera porque se gestiona por cantidad y no por identidad individual. Es un patrón de datos distinto al de los bienes individualizables, y resolverlo junto con la trazabilidad complica el MVP sin necesidad. Por eso el armamento va a conservar un campo informativo fijo con la dotación reglamentaria de munición, o SBO, que es el Stock Básico Operativo, por ejemplo “50 cartuchos”, sin movimientos ni historial de stock propio.
- Los **atributos avanzados del móvil**, como el kilometraje, el estado operativo y el mantenimiento, quedan afuera por la misma razón que la munición: son datos con lógica y periodicidad propias que no cambian el objetivo central del MVP.
- El **equipamiento policial** queda fuera porque son los bienes más diversos del ecosistema logístico policial, con formas de gestión y asignación distintas a las de los bienes elegidos para el MVP.

## 3. Principales operaciones permitidas

Sobre un bien logístico:

- **Alta**: ingreso inicial del bien al sistema. Solo la puede hacer la Dirección Logística.
- **Entrega**: mueve el bien de una Unidad u Oficial de origen a una Unidad u Oficial de destino. Cubre por igual lo que antes llamábamos préstamo temporal, devolución o transferencia entre unidades u oficiales, porque en la práctica todas son una entrega. Cuando el origen o el destino es una Unidad, el responsable pasa a ser esa Unidad. Cuando es un Oficial puntual, se trata de una asignación de dotación permanente. Si el destino es un Oficial, la entrega es atómica y el responsable cambia en el mismo acto. Si el destino es otra Unidad, el bien queda pendiente de recepción y el responsable sigue siendo el origen hasta que la unidad receptora confirme la recepción.
- **Recepción**: el destino confirma que recibió el bien entregado. No se usa cuando la entrega fue una dotación permanente a un oficial. Recién al confirmarse cambian el responsable y la ubicación.
- **Baja**: retiro definitivo de circulación, con un motivo explícito.

Sobre un movimiento ya cargado:

- **Revisión**: el nivel jerárquico superior lo marca como revisado u observado.
- **Rectificación**: corrección trazable de un dato de fondo del movimiento, es decir quién, qué o cuándo, sin alterar el registro original.
- **Anulación**: es un borrado lógico, o soft delete, que solo puede hacer un rol superior y que deja constancia del motivo. El movimiento nunca se borra físicamente.

## 4. Flujo completo de un movimiento

1. La orden que origina el movimiento se transmite de forma informal, por mail o por teléfono, como ocurre hoy.
2. Se produce el movimiento físico y se labra el acta en papel.
3. Se carga la Entrega en el sistema con el bien afectado, la Unidad u Oficial de origen, la Unidad u Oficial de destino, la ubicación de destino cuando el destino es una Unidad, la fecha en que ocurrió el movimiento, la fecha de carga automática, el oficial que carga y el acta escaneada. El responsable de cada lado queda determinado por lo que se carga: la Unidad seleccionada, o el oficial puntual si es una dotación permanente.
4. Si el destino es un Oficial con dotación permanente, la entrega es atómica: el responsable cambia en el mismo acto y el flujo sigue directo en el paso 6. En cualquier otro caso, el bien queda **“pendiente de recepción”** y el origen sigue siendo el responsable.
5. El destino confirma la **Recepción** y recién ahí cambian el responsable y la ubicación.
6. El movimiento atómico o ya recibido queda **“pendiente de revisión”**.
7. El nivel superior correspondiente revisa la información cargada. La Unidad Regional revisa a sus Unidades Operacionales y la Dirección Logística a las Unidades Regionales.
8. Lo marca como **“revisado”** u **“observado”**. Si lo observa, indica el motivo.
9. Si fue observado, la unidad que lo cargó lo corrige: con una edición directa si es un dato descriptivo equivocado, o con una rectificación trazable si afecta al hecho del movimiento.
10. El movimiento corregido vuelve a quedar disponible para revisión.
11. Finalmente, la última instancia de revisión es la Dirección Logística, que confirma la recepción del parte del movimiento, y así queda confirmado por todas las instancias siguiendo la cadena de mando.

## 5. Reglas de negocio que no deben violarse

- Un bien logístico tiene **un único responsable vigente** en todo momento y nunca hay dos responsables a la vez. Mientras una Entrega está pendiente de recepción, el responsable sigue siendo el origen, así que no queda un hueco sin responsable.
- El responsable de un bien puede ser una Unidad, ya sea Operacional, Regional o la Dirección Logística, o un Oficial puntual con una dotación permanente. La ubicación, que sale de una lista fija de cada instancia, solo se registra mientras el responsable es una Unidad.
- La confirmación de **Recepción** es obligatoria para toda Entrega, salvo cuando el destino es una dotación permanente a un oficial. En ese caso la Entrega es atómica y no requiere una Recepción aparte.
- Ningún movimiento histórico se edita libremente en sus datos de fondo, es decir quién, qué y cuándo, ni se borra físicamente. Solo se corrige con una rectificación trazable, o se anula con motivo mediante un borrado lógico que únicamente puede hacer un rol superior.
- El rol revisor **nunca edita** el movimiento: solo lo marca como revisado u observado. La corrección siempre la hace quien lo cargó.
- No hay autorización previa obligatoria. La revisión es posterior al hecho y no bloquea el movimiento antes de que ocurra.
- El oficial usuario final no tiene acceso al sistema. Solo lo opera el personal logístico designado de cada instancia: Unidad Operacional, Unidad Regional o Dirección Logística.
- Toda Entrega debe llevar adjunta el acta escaneada correspondiente.

## 6. Información que puede consultar cada rol y nivel

| Rol | Alcance de consulta | Operaciones que puede realizar |
|---|---|---|
| Oficial de Sala de Armas, en la Unidad Operacional | Armamento y chalecos de su Unidad Operacional | Carga entregas, recepciones y bajas |
| Oficial Auxiliar Logístico, en la Unidad Operacional | Móviles y equipos de comunicación de su Unidad Operacional | Carga altas, entregas, recepciones y bajas |
| Oficial Logístico de Unidad Regional | Bienes propios de su Unidad Regional y movimientos de todas las Unidades Operacionales de su Regional | Carga movimientos de sus bienes propios. Revisa los de las Unidades Operacionales y los marca como revisados u observados. |
| Dirección Logística | Bienes propios de la Dirección y movimientos de todas las Unidades Regionales | Da de alta los bienes y carga movimientos de sus bienes propios. Revisa los de las Unidades Regionales y los marca como revisados u observados. |

## 7. Criterios de éxito

Como se trata de una organización ficticia, la idea es contrastar directamente con los problemas identificados en el análisis:

1. **Trazabilidad en una sola consulta**: dado cualquier bien logístico, el sistema muestra su responsable actual y su historial completo de movimientos, sin recurrir a actas físicas ni comunicarse con la unidad.
2. **Cero recarga manual del mismo dato**: un movimiento se carga una sola vez y ese mismo registro alimenta tanto el historial del bien como el parte informativo hacia el nivel superior.
3. **Visibilidad consolidada sin desfasaje mensual**: la Unidad Regional y la Dirección Logística consultan en cualquier momento el estado y la disponibilidad de los bienes que dependen de ellas, sin esperar el parte mensual.
4. **100% de los movimientos con instancia de revisión**: todo movimiento cargado pasa por un estado explícito, que puede ser pendiente, revisado u observado, y así se reemplaza el control informal actual.
5. **Resguardo digital del acta en cada movimiento**: toda carga debe llevar el acta escaneada, lo que elimina el riesgo de perder para siempre el original en papel.
