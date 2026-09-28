# Sistema Logístico Policial

## Primera entrega: definición del problema

Universidad Tecnológica Nacional

Tecnicatura Universitaria en Programación a Distancia

Trabajo Final Integrador, Grupo 161

Mariano Rodríguez Arce y Raul Robino

---

Contenido

1. Contexto
2. Problema
3. Actores
4. Cómo se realiza actualmente el proceso
5. Qué podría aportar una solución informática

## 1. Contexto

Las fuerzas de seguridad federales operan y administran un volumen considerable de bienes logísticos críticos para cumplir sus funciones: armamento, elementos de protección personal como los chalecos balísticos, munición, vehículos operativos, que llamamos móviles, y equipos de comunicaciones o radios. Estos recursos no siempre son de uso individual permanente: se asignan, se prestan temporalmente, se transfieren entre unidades y, eventualmente, se dan de baja.

La organización se estructura en tres niveles jerárquicos:

- **Unidad Operacional**: es la unidad de base, como una comisaría, un destacamento o una división. Cuenta con una **División Logística** propia, responsable del control del armamento, los chalecos, la munición y los móviles asignados a esa unidad.
- **Unidad Regional**: agrupa a varias Unidades Operacionales de una zona geográfica y tiene su propia división logística, que supervisa y coordina la logística de las unidades bajo su dependencia.
- **Dirección Logística**: es el nivel central que administra y controla a las Unidades Regionales. En este modelo hay seis a nivel nacional.

Dentro de la División Logística de cada Unidad Operacional trabajan roles específicos: uno o más Oficiales de Sala de Armas, a cargo del armamento, los chalecos y la munición, y uno o más Oficiales Auxiliares Logísticos, a cargo del resto de las operaciones logísticas, principalmente la flota de móviles y los equipos de comunicaciones. Las órdenes que originan un movimiento de bienes, por ejemplo la entrega de un bien dispuesta desde una instancia superior hacia una Unidad Operacional o una Unidad Regional, se dan habitualmente de manera informal, por correo electrónico o por teléfono, y no existe un circuito formal de autorización dentro del proceso. Una vez hecho el movimiento, la Unidad Regional puede revisar los movimientos que informan sus Unidades Operacionales, y la Dirección Logística los que informa cada Unidad Regional, para verificar que la información cargada sea correcta.

Hoy el control de estos recursos se hace con actas de entrega y recepción en papel, complementadas de forma no sistemática con planillas Excel que cada unidad lleva por su cuenta. No existe un sistema centralizado que permita saber en cualquier momento dónde está cada bien, quién lo tiene asignado y cuál es su historial de movimientos.

Para este proyecto modelamos una organización de seguridad ficticia y genérica, sin reproducir procesos, denominaciones ni datos de ninguna institución real, para no exponer información sensible o confidencial.

## 2. Problema

El problema concreto a resolver es la **falta de trazabilidad y control centralizado sobre los bienes logísticos operativos** de una fuerza de seguridad: armamento, chalecos balísticos, munición, móviles y equipos de comunicaciones.

El proceso actual, basado en actas de papel y planillas Excel aisladas por unidad, genera estos problemas:

- **Falta de trazabilidad**: no es posible saber de forma rápida y confiable quién tiene asignado un bien, dónde está o en qué estado se encuentra.
- **Duplicación e inconsistencia de registros**: la misma información se carga a mano en distintos soportes, como las actas físicas, las planillas de cada unidad, los reportes diarios y mensuales y las respuestas a pedidos puntuales de la Dirección Logística. Eso produce datos desactualizados o contradictorios y aumenta el riesgo de errores al transcribir.
- **Falta de visibilidad consolidada**: ni la Unidad Regional ni la Dirección Logística tienen una forma ágil de conocer el estado y la disponibilidad de los bienes en las unidades que dependen de ellas, salvo pidiéndole información puntual a cada una. Lo único con lo que cuentan para saber el estado, la disponibilidad y la ubicación de los bienes son las planillas Excel de los reportes periódicos, que muchas veces llegan desactualizadas por el desfasaje propio del envío mensual.
- **Sin revisión sistemática de lo informado**: no existe una instancia formal en la que la Unidad Regional o la Dirección Logística revisen los movimientos informados por el nivel inferior para verificar que los datos sean correctos, por ejemplo el número de serie de un arma o el móvil declarado. Esa verificación queda librada a controles informales.
- **Pérdida irrecuperable de actas**: como no se guarda de forma sistemática una copia escaneada de las actas de entrega, cuando una se extravía, algo frecuente con las actas antiguas, se pierde para siempre el registro de ese movimiento.

El sistema a desarrollar busca resolver este problema para los siguientes tipos de bienes: **armamento, chalecos balísticos, munición, móviles y equipos de comunicaciones**.

## 3. Actores

- **Oficial de Sala de Armas**, de la División Logística de la Unidad Operacional: recibe, entrega y controla el armamento, los chalecos balísticos y el stock de munición de su unidad.
- **Oficial Auxiliar Logístico**, de la División Logística de la Unidad Operacional: se ocupa de las operaciones logísticas que no le corresponden a Sala de Armas, principalmente la asignación de móviles, con el control de su estado, el kilometraje y el mantenimiento, y los equipos de comunicaciones.
- **Oficial o usuario final**: es la mínima expresión del proceso y quien en definitiva tiene asignado o a su cargo cada bien, ya sea el armamento y el chaleco vinculados a su persona, el equipo de comunicaciones que porta o el móvil que tiene asignado de forma permanente o temporal.
- **Oficial Logístico de la Unidad Regional**: integra la división logística de la Unidad Regional y revisa los movimientos que informan las Unidades Operacionales de su Regional para verificar que la información cargada sea correcta.
- **Dirección Logística**, en el nivel central: administra y controla a las seis Unidades Regionales, revisa los movimientos que informa cada una y tiene una visión consolidada a nivel nacional.

## 4. Cómo se realiza actualmente el proceso

Hoy cada movimiento de un bien, ya sea una entrega, un préstamo temporal, una devolución, una transferencia entre unidades o una baja, se documenta con un **acta de entrega y recepción en papel**. La firman el responsable del área, que puede ser Sala de Armas o el Oficial Auxiliar Logístico, y el oficial o la unidad que recibe. La orden que da origen al movimiento se transmite habitualmente por correo electrónico o por teléfono y no queda documentada dentro de un circuito formal.

El criterio establecido para volcar la información de los bienes logísticos es el **parte mensual**. Debería actualizarse a medida que se producen movimientos durante el mes, para que al comienzo del mes siguiente cada Unidad Operacional envíe un parte con todos sus bienes actualizados a esa fecha y los movimientos del mes vencido resaltados. En la práctica, como se envía recién a comienzos de cada mes, la Unidad Regional y la Dirección Logística acceden a esa información con ese desfasaje. A esto se suman un estado diario de la flota vehicular y, ante **requerimientos puntuales de la Dirección Logística**, como saber cuántas camionetas patrulleras están en servicio operativo, una planilla modelo que Dirección distribuye para que cada Unidad Operacional la complete. Esa información sube a la Unidad Regional, donde se verifica, unifica y consolida, y recién entonces se reenvía a la Dirección Logística. Este circuito obliga a cargar de nuevo, en cada parte o requerimiento, información que ya estaba registrada en las actas y planillas locales, lo que multiplica la duplicación de datos y el riesgo de errores al transcribir. Se sigue usando igual **porque permite dejar constancia de lo que cada unidad declara y certifica tener en un momento determinado**.

No existe un repositorio único ni un sistema informático centralizado. La información queda dispersa entre actas físicas archivadas y planillas locales, y para consultar el estado o la ubicación de un bien hay que revisar esos registros a mano o comunicarse directamente con la unidad.

El acta en papel, además, es un soporte del que no se puede prescindir: es el respaldo legal del movimiento y va a seguir siendo necesaria aunque exista un sistema informático. El problema es que hoy no se guarda de forma sistemática una copia escaneada de las actas, así que si el original se pierde o se deteriora, algo que suele pasar con las actas antiguas, el registro se pierde sin posibilidad de recuperarlo.

Como notificación informativa de estos movimientos existe además un **sistema informático de Partes Logísticos**, ya desactualizado. En él, la Unidad Operacional, la Unidad Regional y la Dirección Logística generan un parte tanto por la entrega como por la recepción de un bien, por ejemplo la asignación de armamento a un oficial, la entrega o recepción de un móvil o la recepción de munición. Este sistema es solo informativo: no permite adjuntar el acta ni otra documentación de respaldo, y no contempla que la instancia superior revise lo que el nivel inferior vuelca en esos partes.

## 5. Qué podría aportar una solución informática

Un sistema informático centralizado permitiría:

- **Trazabilidad completa y en tiempo real**: saber en todo momento quién tiene asignado cada bien, en qué unidad está y cuál es su historial completo de movimientos, sin depender de consultar actas o planillas a mano.
- **Registro único y consistente**: eliminar la duplicación de información entre las actas en papel, las planillas Excel de cada unidad y los reportes periódicos o pedidos puntuales. Esos reportes se generarían automáticamente a partir de los datos ya cargados, sin discrepancias entre unidades y sin volver a cargar el mismo dato. La constancia de qué unidad declaró o certificó cada bien en un momento determinado, que es el motivo por el que hoy se sostiene el circuito manual, se puede conservar igual en el sistema sin necesidad de la doble carga.
- **Visibilidad de disponibilidad y stock**: consultar al instante la cantidad de bienes disponibles, por ejemplo el stock de munición o los móviles operativos, sin relevamientos manuales y en cualquiera de los tres niveles.
- **Base para reportes y control**: generar información consolidada por unidad, por Unidad Regional o a nivel nacional para la toma de decisiones, por ejemplo sobre bienes fuera de servicio o vencimientos de mantenimiento de la flota.
- **Resguardo digital de las actas**: adjuntar una copia escaneada de cada acta de entrega al registrar el movimiento, sin reemplazar el papel, que sigue siendo indispensable, para que su extravío no implique perder el registro para siempre.
- **Reemplazo del sistema de Partes Logísticos**: generar automáticamente el parte informativo al declarar una entrega o una recepción y enviarlo a la instancia superior, de la Unidad Operacional a la Unidad Regional y de esta a la Dirección Logística, que como es la instancia máxima no tiene a quién elevarlo. Además, esa instancia superior podría revisar el parte y verificar que la información cargada sea correcta, por ejemplo el número de serie del armamento o el móvil declarado.
- **Estadísticas para la toma de decisiones operativas**: con toda la información centralizada y actualizada se pueden generar estadísticas que hoy no se obtienen sin un relevamiento manual, como la disponibilidad histórica de móviles por unidad, el consumo de munición o los bienes con mayor rotación o más tiempo fuera de servicio. Sirven de apoyo para decisiones operativas en cualquiera de los tres niveles.
